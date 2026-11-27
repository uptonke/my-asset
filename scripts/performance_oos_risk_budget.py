"""Walk-forward validation of v3.6 on a fixed retrospective universe."""
import json
import math
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from performance_currency_rebalance import CONFIG,OPT,GROUPS,CASH,rebalancing
from run_constrained_optimizer import POLICY,constraint_matrix,feasibility
from cost_walk_forward import trade_cost

METHODS=("buy_hold","strategic_rebalance","minimum_variance","risk_budget")

def initial_weights(cols,buckets):
    # Deterministic equal-weight projection; never use today's actual weights.
    n=len(cols);A,b,bounds,_=constraint_matrix(cols,buckets,POLICY)
    I=np.eye(n);equal=np.full(n,1/n)
    C=np.vstack([np.c_[A,np.zeros_like(A)],np.c_[I,-I],np.c_[-I,-I]])
    result=linprog(np.r_[np.zeros(n),np.ones(n)],A_ub=C,b_ub=np.r_[b,equal,-equal],
        A_eq=np.r_[np.ones(n),np.zeros(n)][None,:],b_eq=[1.],bounds=bounds+[(0.,1.)]*n,method="highs")
    if not result.success or not feasibility(result.x[:n],A,b,bounds):raise ValueError("No feasible initial allocation")
    return result.x[:n]

def advance(state,r,G,cost=0.,target=None):
    w=state["weights"] if target is None else target
    parts=G@(w*r)
    gross=float(parts.sum());net=(1-cost)*(1+gross)-1
    if not math.isfinite(net) or net<=-1:raise ValueError("Invalid return")
    state["nav"]*=1+net;state["gross_nav"]*=1+gross
    state["net"].append(net);state["gross"].append(gross);state["groups"].append(parts.tolist())
    state["weights"]=w*(1+r)/(1+gross)
    return net

def metrics(s,budget):
    x=np.array(s["net"]);g=np.array(s["gross"]);n=len(x)
    curve=np.r_[1.,np.cumprod(1+x)]
    dd=float(np.min(curve/np.maximum.accumulate(curve)-1))
    out={"observations":n,"net_return_pct":float((curve[-1]-1)*100),"gross_return_pct":(s["gross_nav"]-1)*100,
         "annualized_vol_pct":float(np.std(x,ddof=1)*np.sqrt(52)*100) if n>=2 else None,
         "max_drawdown_pct":dd*100,"cost_pct_initial_nav":s["cost"]*100,"turnover_sum_pct":s["turnover"]*100,
         "failed_rebalances":s["failed"],"policy_breach_weeks":s["breach"]}
    # Realized gross group risk uses actual evolving start-of-week weights.
    # Do not attribute one-time execution cost to a security covariance component.
    if n>=20 and np.var(g,ddof=1)>1e-14:
        z=np.array(s["groups"])
        if not np.allclose(z.sum(axis=1),g,atol=1e-12):raise ValueError("Realized group identity")
        shares=np.cov(z.T,g,ddof=1)[:-1,-1]/np.var(g,ddof=1)
        if not np.isclose(shares.sum(),1.,atol=1e-9):raise ValueError("Realized risk identity")
        out.update(realized_gross_risk=[{"bucket":k,"risk_pct":float(v*100),"target_pct":float(t*100)} for k,v,t in zip(GROUPS,shares,budget)],
                   realized_budget_rmse_pp=float(np.sqrt(np.mean((shares-budget)**2))*100))
    return out

def validate_oos(ex,returns,config=None,opt=None):
    out={"version":"v3.9","status":"INSUFFICIENT_SAMPLE","execution_permission":False,"available":len(returns),"required":57,
        "notes":["Retrospective fixed current universe, not historical investable universe; selection/survivorship bias remains. Initial weights projected from equal weights, not current portfolio weights.",
                 "52 weekly training observations; one subsequent weekly mark for delayed execution; four following weeks holding. Execution-week return earned on old weights. Training targets never use execution or test returns.",
                 "At execution, reject if drifted weights would breach nominal turnover cap or target violates policy. Failed rebalance holds existing weights, which may remain out of policy.",
                 "Identical dates, initial allocation and one-time self-financing costs for each strategy. No final incomplete fold. Price-only TWD, no dividends. Fixed 10% nominal cap, v3.6 illustrative budgets; no hyperparameter selection.",
                 "Gross risk-share validation uses evolving holdings and gross realized group returns, minimum 20 weeks; net return includes costs. No annualized Sharpe or tail estimate on tiny samples. Not prospective certification."]}
    if len(returns)<57:return out
    config=config or json.loads(CONFIG.read_text());opt=opt or json.loads(OPT.read_text())
    cap=.10
    if cap>opt["turnover_cap_pct"]/100+1e-9:raise ValueError("OOS turnover exceeds policy")
    config={**config,"turnover_caps":[cap]}
    hs=ex["holdings"];cols=[h["ticker"] for h in hs];buckets={h["ticker"]:h["bucket"] for h in hs}
    X=returns[cols].to_numpy(dtype=float)
    if not np.isfinite(X).all() or (X<=-1).any() or not (returns.index.to_series().diff().dropna()==pd.Timedelta(days=7)).all():
        raise ValueError("Invalid contiguous observations")
    G=np.array([[buckets[t]==g for t in cols] for g in GROUPS],dtype=float)
    budget=np.array([config["risk_budget"][g] for g in GROUPS],dtype=float)
    A,b,bounds,_=constraint_matrix(cols,buckets,POLICY)
    start=initial_weights(cols,buckets)
    rates=np.array([0. if t==CASH else opt["cost_bps_per_side"][buckets[t]]/10000 for t in cols])
    state={m:{"weights":start.copy(),"nav":1.,"gross_nav":1.,"net":[],"gross":[],"groups":[],"cost":0.,"turnover":0.,"failed":0,"breach":0} for m in METHODS}
    folds=[]
    for k in range(52,len(X)-4,5):
        train=returns.iloc[k-52:k]
        fold={"train_start":str((train.index[0]-pd.Timedelta(days=7)).date()),"train_end":str(train.index[-1].date()),
              "execution_date":str(returns.index[k].date()),"test_start":str(returns.index[k+1].date()),"test_end":str(returns.index[k+4].date()),"methods":{}}
        for m,s in state.items():
            before=s["weights"].copy();target=None;status="HOLD"
            if m=="strategic_rebalance":
                target=start.copy()
                if np.abs(target-before).sum()/2>cap+1e-7:target=None;status="HOLD_TURNOVER"
            elif m in ("minimum_variance","risk_budget"):
                try:
                    e={"model_nav_twd":1.,"holdings":[{**h,"weight":float(before[i]),"market_value_twd":float(before[i])} for i,h in enumerate(hs)]}
                    report=rebalancing(e,train,[],config=config,opt=opt)
                    row=next(r for r in report["candidates"] if r["objective"]==m)
                    status=row["status"]
                    if status=="RESEARCH_ONLY":target=np.array([t["target_pct"]/100 for t in row["trades"]])
                except Exception:status="FAILED"
            target_at_signal=None if target is None else target.tolist()
            # One full observation between last training mark and execution.
            nav0=s["nav"]
            advance(s,X[k],G)
            if not feasibility(s["weights"],A,b,bounds):s["breach"]+=1
            cost=0.;turn=0.
            if target is not None:
                turn=float(np.abs(target-s["weights"]).sum()/2)
                if turn>cap+1e-7 or not feasibility(target,A,b,bounds):
                    target=None;status="HOLD_EXECUTION_CONSTRAINT";turn=0.
                else:
                    cost,_=trade_cost(s["weights"],target,rates)
                    s["cost"]+=s["nav"]*cost;s["turnover"]+=turn;status="REBALANCED"
            if m!="buy_hold" and target is None:s["failed"]+=1
            for j in range(k+1,k+5):
                advance(s,X[j],G,cost=cost if j==k+1 else 0.,target=target if j==k+1 else None)
                if not feasibility(s["weights"],A,b,bounds):s["breach"]+=1
            fold["methods"][m]={"status":status,"signal_weights":dict(zip(cols,target_at_signal)) if target_at_signal is not None else None,
                "turnover_pct":turn*100,"cost_pct":cost*100,"net_return_pct":(s["nav"]/nav0-1)*100}
        folds.append(fold)
    if not folds:return out
    out.update(status="RESEARCH_ONLY",fold_count=len(folds),evaluation_weeks=len(folds)*5,
        start=str(returns.index[51].date()),end=folds[-1]["test_end"],initial_weights=dict(zip(cols,map(float,start))),
        aggregates={m:metrics(s,budget) for m,s in state.items()},folds=folds)
    return out
