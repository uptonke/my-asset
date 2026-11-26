"""Research-only cost-aware walk-forward. No current portfolio or live signals."""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from run_cost_aware_optimizer import solve,validate_config
from run_constrained_optimizer import POLICY,constraint_matrix,feasibility

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"config/cost_walk_forward.json"
OPT=ROOT/"config/optimizer_phase3.json"
METHODS=("buy_hold","strategic_rebalance","constrained_cvar","cost_aware_cvar","cost_aware_mean_variance")


def load_prices(config):
    import yfinance as yf
    # Exclude possibly unfinished daily candles in any of the time zones.
    end=(pd.Timestamp.now(tz="UTC")-pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    def fetch(symbol,currency):
        obj=yf.Ticker(symbol)
        h=obj.history(start=config["start"],end=end,auto_adjust=True,actions=False,raise_errors=True)
        if h.empty or "Close" not in h or str(obj.fast_info.currency or "").upper()!=currency:
            raise ValueError("Missing or mismatched total-return proxy: "+symbol)
        p=pd.to_numeric(h["Close"],errors="coerce").dropna()
        p.index=pd.to_datetime(p.index).tz_localize(None).normalize()
        if p.index.duplicated().any() or not np.isfinite(p).all() or (p<=0).any():
            raise ValueError("Invalid prices: "+symbol)
        return p.sort_index()
    fx=fetch("TWD=X","TWD")
    marks={}
    for item in config["universe"]:
        px=fetch(item["symbol"],item["currency"])
        marks[item["ticker"]]=px*fx.reindex(px.index) if item["currency"]=="USD" else px
    # Common actual observation dates, not forward-filled holidays.
    return pd.DataFrame(marks).dropna(how="any").sort_index()


def trade_cost(before,target,rates):
    """Solve c = sum_i rate_i |(1-c) target_i - before_i|.
    Weights before and after are fractions of their respective NAVs."""
    before,target,rates=map(lambda x:np.asarray(x,dtype=float),(before,target,rates))
    if not all(np.isfinite(x).all() for x in (before,target,rates)) or min(before.min(),target.min(),rates.min())<-1e-8 or rates.max()>=.1:
        raise ValueError("Invalid trade inputs")
    if not np.isclose(before.sum(),1,atol=1e-7) or not np.isclose(target.sum(),1,atol=1e-7):
        raise ValueError("Trade weights not fully invested")
    lo,hi=0.,min(.99,2*float(rates.max())+1e-12)
    for _ in range(70):
        c=(lo+hi)/2
        if float(rates@np.abs((1-c)*target-before))>c:lo=c
        else:hi=c
    c=(lo+hi)/2
    amounts=(1-c)*target-before
    if abs(c-float(rates@np.abs(amounts)))>1e-10 or abs(float(amounts.sum())+c)>1e-7:
        raise ValueError("Self-financing identity failed")
    return c,float(np.abs(amounts).sum()/2)


def metrics(net,gross,dates,start,fees,turns,failures,folds):
    net=np.asarray(net);gross=np.asarray(gross)
    curve=np.r_[1.,np.cumprod(1+net)]
    elapsed=(dates[-1]-start).days
    ann_obs=len(net)*365.25/max(1,elapsed)
    q=np.quantile(net,.05)
    return {"fold_count":folds,"failed_rebalances":failures,"observations":len(net),
        "net_return_pct":float((curve[-1]-1)*100),"gross_return_pct":float((np.prod(1+gross)-1)*100),
        "net_cagr_pct":float((curve[-1]**(365.25/max(1,elapsed))-1)*100),
        "net_vol_pct":float(np.std(net,ddof=1)*np.sqrt(ann_obs)*100),
        "net_es95_per_observation_pct":float(-np.mean(net[net<=q])*100),
        "net_max_drawdown_pct":float((curve/np.maximum.accumulate(curve)-1).min()*100),
        "paid_cost_pct_initial_nav":fees*100,"avg_nominal_oneway_turnover_pct":float(np.mean(turns)*100),
        "ending_nav_index":float(curve[-1]*100)}


def simulate(prices,config,opt,multiplier,methods=METHODS):
    validate_config(opt)
    items=config["universe"];cols=[x["ticker"] for x in items]
    if len(set(cols))!=len(cols) or set(prices.columns)!=set(cols) or not prices.index.is_monotonic_increasing or prices.index.has_duplicates:
        raise ValueError("Fixed universe or date mismatch")
    prices=prices[cols]
    if not np.isfinite(prices.to_numpy()).all() or (prices<=0).any().any():raise ValueError("Invalid common prices")
    r=prices.pct_change(fill_method=None).iloc[1:]
    ntrain=int(config["training_observations"]);hold=int(config["holding_observations"])
    if ntrain<60 or hold<1 or len(r)<ntrain+1+hold:raise ValueError("Insufficient common history")
    reference=np.array([x["weight"] for x in items],dtype=float)
    buckets={x["ticker"]:x["bucket"] for x in items}
    A,b,bounds,_=constraint_matrix(cols,buckets,POLICY)
    if not feasibility(reference,A,b,bounds):raise ValueError("Strategic start violates policy")
    rates=np.array([opt["cost_bps_per_side"][buckets[t]]/10000*multiplier for t in cols])
    cfg={**opt,"horizon_sessions":hold}
    state={m:{"w":reference.copy(),"nav":1.,"net":[],"gross":[],"fees":0.,"turns":[],"fail":0} for m in methods}
    folds=[];dates=[]
    # Return row i is the close-to-close move ending on date i. Train
    # strictly before execution close; evaluate only subsequent returns.
    for i in range(ntrain,len(r)-hold,hold):
        train=r.iloc[i-ntrain:i];test=r.iloc[i+1:i+1+hold];execution=r.index[i]
        if not train.index[-1]<execution<test.index[0]:raise ValueError("Lookahead guard")
        cov=train.cov().to_numpy()*252.
        shrink=opt["covariance_diagonal_shrinkage"]
        cov=(1-shrink)*cov+shrink*np.diag(np.diag(cov))+np.eye(len(cols))*1e-12
        # Fixed illustrative reference prior; no contemporary or historical
        # view scores. Do not pretend to validate phase-3 subjective BL views.
        mu=opt["risk_aversion"]*cov@reference
        fold={"train_start":str(train.index[0].date()),"train_end":str(train.index[-1].date()),
            "execution_date":str(execution.date()),"test_start":str(test.index[0].date()),"test_end":str(test.index[-1].date()),"methods":{}}
        dates.extend(test.index.tolist())
        for method,st in state.items():
            before=st["w"].copy();status="OK";message="";model={}
            if method=="buy_hold":target=before.copy()
            elif method=="strategic_rebalance":target=reference.copy()
            elif method in ("regime_aware","factor_budget"):
                from performance_risk_research import regime_target,budget_target
                try:
                    w,model=(regime_target(train,pd.Series(before,index=cols),buckets,mu,cov,rates,cfg)
                        if method=="regime_aware" else budget_target(train,pd.Series(before,index=cols),buckets,cfg))
                except Exception:
                    w=None;model={"status":"MODEL_UNAVAILABLE"}
                if w is None:
                    target=before.copy();status="HOLD_"+model.get("status","FAILED");st["fail"]+=1
                else:target=w.to_numpy()
            else:
                use_cost=method!="constrained_cvar"
                floor=float(mu@before)+opt["return_floor_delta_pp"]/100 if use_cost else None
                kind="mean_variance" if method=="cost_aware_mean_variance" else "cvar_cost" if use_cost else "cvar"
                w,info=solve(train,pd.Series(before,index=cols),buckets,mu,cov,rates if use_cost else np.zeros_like(rates),cfg,kind,floor)
                if w is None:
                    target=before.copy();status="HOLD_"+info["status"];message=info.get("message","")[:180];st["fail"]+=1
                else:target=w.to_numpy()
            cost,actual_turn=trade_cost(before,target,rates)
            turn=float(np.abs(target-before).sum()/2)
            if method in ("constrained_cvar","cost_aware_cvar","cost_aware_mean_variance","regime_aware","factor_budget") and status=="OK":
                if not feasibility(target,A,b,bounds) or turn>opt["turnover_cap_pct"]/100+1e-7:
                    raise ValueError("Solver policy failure")
            st["fees"]+=st["nav"]*cost;st["turns"].append(turn)
            st["w"]=target.copy()
            gross=[];net=[]
            for j,x in enumerate(test.to_numpy()):
                ret=float(st["w"]@x)
                if ret<=-1:raise ValueError("Nonpositive portfolio NAV")
                nr=(1-cost)*(1+ret)-1 if j==0 else ret
                st["nav"]*=1+nr
                st["w"]=st["w"]*(1+x)/(1+ret)
                gross.append(ret);net.append(nr)
            st["gross"].extend(gross);st["net"].extend(net)
            fold["methods"][method]={"status":status,"message":message,"model":model,"pretrade_weights":dict(zip(cols,before.tolist())),
                "target_weights":dict(zip(cols,target.tolist())),"ending_weights":dict(zip(cols,st["w"].tolist())),
                "oneoff_cost_pct":cost*100,"nominal_turnover_pct":turn*100,"actual_half_gross_traded_pct":actual_turn*100,
                "gross_return_pct":float((np.prod(1+np.array(gross))-1)*100),
                "net_return_pct":float((np.prod(1+np.array(net))-1)*100)}
        folds.append(fold)
    start=pd.Timestamp(folds[0]["execution_date"])
    aggregate={m:metrics(st["net"],st["gross"],dates,start,st["fees"],st["turns"],st["fail"],len(folds)) for m,st in state.items()}
    return {"cost_multiplier":multiplier,"start":str(start.date()),"end":str(dates[-1].date()),"folds":folds,"aggregate":aggregate}


def build(prices=None,config=None,opt=None):
    config=config or json.loads(CONFIG.read_text());opt=opt or json.loads(OPT.read_text())
    out={"version":"v3.0","status":"BLOCKED","execution_permission":False,"research_only":True,
        "config":config,"optimizer_assumptions":opt,"scenarios":[],
        "notes":["Illustrative fixed universe selected now, not historical investable universe; survivorship/selection bias remains.",
                 "Adjusted Close total-return proxies, revised data, same-calendar-date asynchronous global marks, common actual dates only.",
                 "126 observations train, 21 observations hold; training ends before execution close. No current holdings or view scores.",
                 "Initial allocation pre-funded; costs charged thereafter, including rebalancing of benchmark. No exit liquidation, taxes, integer lots or minimum fees.",
                 "Nominal turnover cap applies to target weight change; self-financing actual traded notional reported separately.",
                 "No automatic constraint relaxation: infeasible fold holds drifted weights and records failure; not a policy-compliant target.",
                 "Cost scenarios re-optimize separately, gross is same realized strategy path before its costs, not a counterfactual zero-cost strategy.",
                 "Excess-return proxy uses fixed reference-implied covariance prior, no BL views; not a test of subjective view model.",
                 "Volatility annualized with observed date frequency; ES is per common observation, not necessarily one calendar day."]}
    try:
        prices=load_prices(config) if prices is None else prices
        out["scenarios"]=[simulate(prices,config,opt,float(m)) for m in config["cost_multipliers"]]
        out["sample"]={"first":str(prices.index[0].date()),"last":str(prices.index[-1].date()),"common_marks":len(prices)}
        out["status"]="OK_RESEARCH_ONLY"
    except Exception as exc:out.update(status="BLOCKED",reason=str(exc)[:300],scenarios=[])
    return out
