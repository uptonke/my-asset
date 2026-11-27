"""v3.5/v3.6: private FX decomposition and constrained research reallocation."""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog,minimize
from performance_coverage import quote
from run_constrained_optimizer import POLICY,constraint_matrix,feasibility
from cost_walk_forward import trade_cost,OPT

CONFIG=Path(__file__).resolve().parents[1]/"config/risk_rebalance_v36.json"
GROUPS=("global_equity","taiwan_equity","crypto","gold","cash")
CASH="__TWD_CASH__"

def historical_fx(pnl):
    """Existing trade-leg P&L, no missing-value imputation or ledger edits."""
    out={"version":"v3.5","execution_permission":False,"windows":{},
         "notes":["Actual window P&L decomposition uses existing date-only trade-leg marks; execution difference is not pure FX slippage.",
                  "Endpoint-only and missing assets remain unresolved, not zero FX. No new income or dividend accounting."]}
    keys=("price_twd","fx_twd","interaction_twd","execution_vs_close_twd")
    for label,p in pnl.items():
        try:
            rows=[];tot=dict.fromkeys(keys,0.);unallocated=0.
            for r in p["rows"]:
                complete=all(r.get(k) is not None for k in keys)
                row={"ticker":r["ticker"],"bucket":r.get("bucket"),"pnl_twd":r["pnl_twd"],
                     **{k:r.get(k) for k in keys},"status":"DECOMPOSED" if complete else "ENDPOINT_ONLY"}
                if complete:
                    if not math.isclose(math.fsum(row[k] for k in keys),r["pnl_twd"],abs_tol=.01):
                        raise ValueError("Trade leg identity")
                    for k in keys:tot[k]+=row[k]
                else:unallocated+=r["pnl_twd"]
                rows.append(row)
            err=p["actual_pnl_twd"]-math.fsum(tot.values())-unallocated-p["explicit_other_cashflow_twd"]-p["unexplained_twd"]
            if abs(err)>.02:raise ValueError("Window identity")
            out["windows"][label]={"start":p["start"],"end":p["end"],"status":"PARTIAL" if p.get("missing") or any(r["status"]!="DECOMPOSED" for r in rows) or p.get("status")=="PARTIAL" else "RESEARCH_ONLY",
                **tot,"actual_pnl_twd":p["actual_pnl_twd"],"unallocated_asset_pnl_twd":unallocated,
                "other_cashflow_twd":p["explicit_other_cashflow_twd"],"unexplained_twd":p["unexplained_twd"],
                "fx_plus_interaction_twd":tot["fx_twd"]+tot["interaction_twd"],"identity_error_twd":err,
                "missing":p.get("missing",[]),"rows":rows}
        except Exception:out["windows"][label]={"status":"UNAVAILABLE","reason":"P&L decomposition failed"}
    return out

def currency_risk(ex,market,returns):
    """Same complete weekly dates and weights as v3.3, no currency proxy fill."""
    cols=[h["ticker"] for h in ex["holdings"]]
    w=np.array([h["weight"] for h in ex["holdings"]])
    usd=np.array([h["currency"]=="USD" for h in ex["holdings"]],dtype=float)
    X=returns[cols].to_numpy(dtype=float)
    if len(X)<26 or not np.isfinite(X).all() or not np.isclose(w.sum(),1.):raise ValueError("Insufficient sample")
    f=[]
    for d in returns.index:
        if usd.any():
            a=quote(market["fx"],d-pd.Timedelta(days=7),4,"USD/TWD","portfolio FX","FX")
            b=quote(market["fx"],d,4,"USD/TWD","portfolio FX","FX")
            f.append(b/a-1.)
        else:f.append(0.)
    F=np.asarray(f)[:,None]*usd[None,:]
    L=(1+X)/(1+F)-1
    I=L*F
    if not np.allclose(L+F+I,X,atol=1e-12):raise ValueError("Currency return identity")
    # Return components of fixed-weight weekly rebalanced hypothetical exposure.
    Z=np.column_stack([L@w,F@w,I@w]);p=X@w
    cov=np.cov(Z,rowvar=False,ddof=1)*52.
    total=float(np.var(p,ddof=1)*52.)
    if total<=1e-14 or not np.isclose(cov.sum(),total,atol=1e-12):raise ValueError("Currency variance identity")
    vol=math.sqrt(total);rc=cov.sum(axis=1)/vol
    if not np.isclose(rc.sum(),vol,atol=1e-10):raise ValueError("Currency Euler identity")
    rows=[{"component":k,"standalone_ann_vol_pct":float(math.sqrt(max(0,cov[i,i]))*100),
           "component_ann_vol_pp":float(rc[i]*100),"risk_share_pct":float(rc[i]/vol*100)}
          for i,k in enumerate(("local_price","fx_translation","interaction"))]
    neutral=float(np.std(Z[:,0],ddof=1)*math.sqrt(52)*100)
    asset=[]
    for j,h in enumerate(ex["holdings"]):
        c=F[:,j]*w[j];interaction=I[:,j]*w[j]
        fxrc=float(np.cov(c,p,ddof=1)[0,1]*52./vol*100)
        irc=float(np.cov(interaction,p,ddof=1)[0,1]*52./vol*100)
        asset.append({"ticker":h["ticker"],"currency":h["currency"],"weight_pct":float(w[j]*100),
                      "fx_component_ann_vol_pp":fxrc,"interaction_component_ann_vol_pp":irc})
    if not math.isclose(sum(r["fx_component_ann_vol_pp"] for r in asset),rows[1]["component_ann_vol_pp"],abs_tol=1e-8):raise ValueError("FX security identity")
    return {"status":"RESEARCH_ONLY","start":str((returns.index[0]-pd.Timedelta(days=7)).date()),"end":str(returns.index[-1].date()),
            "observations":len(X),"annualized_vol_pct":vol*100,"currency_neutral_ann_vol_pct":neutral,
            "usd_weight_pct":float(w@usd*100),"fx_only_1pct_pnl_twd":float(ex["model_nav_twd"]*(w@usd)*.01),
            "rows":rows,"assets":asset,"identity_error_pp":float((rc.sum()-vol)*100)}

def group_risk(cov,w,G):
    var=float(w@cov@w)
    if var<=1e-14 or not math.isfinite(var):raise ValueError("Invalid variance")
    vol=math.sqrt(var);parts=G@(w*(cov@w)/var)
    if not np.isclose(parts.sum(),1.,atol=1e-9):raise ValueError("Group risk identity")
    return vol,parts

def tail_loss(X,w):
    loss=-(X@w);mass=.05*len(loss)
    boundary=np.sort(loss)[::-1][math.ceil(mass)-1]
    above=loss>boundary
    return float(boundary),float((loss[above].sum()+(mass-above.sum())*boundary)/mass)

def rebalancing(ex,returns,scenarios,config=None,opt=None):
    """Same-sample comparison. No execution signals, no new securities."""
    config=config or json.loads(CONFIG.read_text())
    opt=opt or json.loads(OPT.read_text())
    hs=ex["holdings"];cols=[h["ticker"] for h in hs];n=len(cols)
    w0=np.array([h["weight"] for h in hs],dtype=float)
    X=np.array(returns[cols],dtype=np.float64,order="C",copy=True)
    if len(X)!=52 or not np.isfinite(X).all() or min(w0)<0 or not np.isclose(w0.sum(),1.,atol=1e-9):
        raise ValueError("Require exact 52 complete weekly observations")
    if n<2 or len(set(cols))!=n:raise ValueError("Invalid universe")
    buckets={h["ticker"]:h["bucket"] for h in hs}
    G=np.array([[buckets[t]==g for t in cols] for g in GROUPS],dtype=float)
    target=np.array([config["risk_budget"][g] for g in GROUPS],dtype=float)
    if min(target)<0 or not np.isclose(target.sum(),1.) or not np.isfinite(target).all():raise ValueError("Invalid risk budget")
    rates=np.array([0. if t==CASH else opt["cost_bps_per_side"][buckets[t]]/10000 for t in cols])
    cov=np.atleast_2d(np.cov(X,rowvar=False,ddof=1))*52
    A,b,bounds,names=constraint_matrix(cols,buckets,POLICY)
    usd=np.array([h["currency"]=="USD" for h in hs],dtype=float)
    nav=float(ex["model_nav_twd"])
    def evaluate(w,c):
        vol,shares=group_risk(cov,w,G)
        v,e=tail_loss(X,w)
        # Scenario returns fixed per instrument from v3.4. Compare post-cost
        # value against original model NAV, not against a smaller denominator.
        shock=[]
        for s in scenarios:
            if s.get("status")!="HYPOTHETICAL":continue
            r={x["ticker"]:x["return_pct"]/100 for x in s["rows"]}
            if set(r)!=set(cols):raise ValueError("Stress universe mismatch")
            gross=float(w@np.array([r[t] for t in cols]))
            net=(1-c)*(1+gross)-1
            shock.append({"id":s["id"],"label":s["label"],"return_pct":gross*100,"net_including_cost_pct":net*100,"pnl_twd":nav*net})
        return {"annualized_vol_pct":vol*100,"var95_loss_pct":v*100,"es95_loss_pct":e*100,
                "usd_weight_pct":float(w@usd*100),"budget_rmse_pp":float(np.sqrt(np.mean((shares-target)**2))*100),
                "groups":[{"bucket":g,"weight_pct":float((G@w)[i]*100),"risk_share_pct":float(shares[i]*100),"budget_pct":float(target[i]*100)} for i,g in enumerate(GROUPS)],
                "stress":shock}
    baseline=evaluate(w0,0.)
    out={"version":"v3.6","status":"RESEARCH_ONLY","execution_permission":False,"observations":52,
         "start":str((returns.index[0]-pd.Timedelta(days=7)).date()),"end":str(returns.index[-1].date()),
         "baseline":baseline,"budget":config["risk_budget"],"policy":POLICY,"current_policy_feasible":feasibility(w0,A,b,bounds),
         "current_policy_violations":[name for name,v in zip(names,A@w0-b) if v>1e-7]+[t+"_single_bound" for t,x,(lo,hi) in zip(cols,w0,bounds) if x<lo-1e-7 or x>hi+1e-7],
         "candidates":[],
         "notes":["Illustrative bucket risk targets, not approved investment policy. Fixed existing holdings plus TWD cash, long-only.",
                  "Sample covariance and stress comparison are in-sample, not walk-forward or expected-return forecasts. Same 52 observations for all candidates.",
                  "Existing sandbox allocation caps and nominal one-way turnover caps, no constraint relaxation. Minimum variance and squared risk-budget mismatch objectives; budget solution is local, not guaranteed exact.",
                  "Estimated one-time self-financing costs from existing bucket rates; zero for TWD cash, excludes FX spreads, taxes, minimum fees, lots and liquidity. Objective does not optimize costs or expected returns.",
                  "Net stress includes estimated one-time cost. Negative risk contributions remain signed. No live order or automatic rebalancing."]}
    I=np.eye(n);E=np.r_[np.ones(n),np.zeros(n)][None,:]
    bounds_z=bounds+[(0.,1.)]*n
    for cap in config["turnover_caps"]:
        if not math.isfinite(cap) or cap<=0 or cap>opt["turnover_cap_pct"]/100+1e-9:raise ValueError("Invalid turnover cap")
        C=np.vstack([np.c_[A,np.zeros_like(A)],np.c_[I,-I],np.c_[-I,-I],np.r_[np.zeros(n),np.ones(n)][None,:]])
        d=np.r_[b,w0,-w0,2*cap]
        lp=linprog(np.r_[np.zeros(n),np.ones(n)],A_ub=C,b_ub=d,A_eq=E,b_eq=[1.],bounds=bounds_z,method="highs")
        for kind in ("minimum_variance","risk_budget"):
            row={"objective":kind,"turnover_cap_pct":cap*100,"status":"INFEASIBLE" if lp.status==2 else "FAILED"}
            if not lp.success:out["candidates"].append(row);continue
            scale=max(float(np.max(np.abs(cov))),1e-12)
            def obj(z):
                w=z[:n]
                if kind=="minimum_variance":return float(w@cov@w/scale)
                try:_,parts=group_risk(cov,w,G);return float(np.sum((parts-target)**2))
                except ValueError:return 1e6
            con=[{"type":"eq","fun":lambda z:E@z-1,"jac":lambda z:E},
                 {"type":"ineq","fun":lambda z:d-C@z,"jac":lambda z:-C}]
            try:
                z=minimize(obj,lp.x,method="SLSQP",bounds=bounds_z,constraints=con,options={"maxiter":700,"ftol":1e-11})
                w=z.x[:n]
                turn=float(np.abs(w-w0).sum()/2)
                if not z.success or not feasibility(w,A,b,bounds) or turn>cap+1e-7 or obj(z.x)>=1e6:
                    out["candidates"].append(row);continue
                cost,_=trade_cost(w0,w,rates)
                amounts=((1-cost)*w-w0)*nav
                if abs(float(amounts.sum())+cost*nav)>.02:raise ValueError("Trade identity")
                result=evaluate(w,cost)
                row.update(status="RESEARCH_ONLY",**result,nominal_turnover_pct=turn*100,
                           estimated_cost_twd=cost*nav,estimated_cost_pct=cost*100,
                           post_cost_nav_twd=nav*(1-cost),
                           vol_change_pp=result["annualized_vol_pct"]-baseline["annualized_vol_pct"],
                           es_change_pp=result["es95_loss_pct"]-baseline["es95_loss_pct"],
                           trades=[{"ticker":t,"before_pct":float(w0[i]*100),"target_pct":float(w[i]*100),
                                    "weight_change_pp":float((w[i]-w0[i])*100),"signed_change_twd":float(amounts[i])}
                                   for i,t in enumerate(cols)])
            except Exception:row["status"]="FAILED"
            out["candidates"].append(row)
    if not any(r["status"]=="RESEARCH_ONLY" for r in out["candidates"]):
        out.update(status="NO_FEASIBLE_CANDIDATE",reason="No validated solution under the existing constraints")
    return out

def build_extensions(ex,market,latest,scenarios):
    fx={"version":"v3.5","status":"INSUFFICIENT_SAMPLE","execution_permission":False,"windows":{},
        "notes":["Fixed as-of holdings, weekly rebalanced price-risk decomposition, not realized historical P&L.",
                 "Local price + FX + multiplicative interaction reconcile exactly; covariance contributions may be negative.",
                 "FX-neutral volatility removes translation mathematically, not an implementable hedge. USD quotation exposure is not economic currency exposure."]}
    for n in (26,52,104):
        if len(latest)<n:fx["windows"][str(n)]={"status":"INSUFFICIENT_SAMPLE","available":len(latest),"required":n}
        else:
            try:fx["windows"][str(n)]=currency_risk(ex,market,latest.iloc[-n:])
            except Exception:fx["windows"][str(n)]={"status":"UNAVAILABLE","reason":"FX marks or risk identity unavailable"}
    if any(r["status"]=="RESEARCH_ONLY" for r in fx["windows"].values()):fx["status"]="RESEARCH_ONLY"
    rebal={"version":"v3.6","status":"INSUFFICIENT_SAMPLE","execution_permission":False,"available":len(latest),"required":52}
    if len(latest)>=52:
        # Keep risk estimates visible but do not suggest reallocation when
        # valuation disagrees materially with the recorded NAV or later trades exist.
        if abs(ex["nav_gap_pct"])>1 or ex["later_ledger_events"]:
            rebal.update(status="BLOCKED",reason="NAV_GAP_OR_LATER_LEDGER_EVENTS")
        else:
            try:rebal=rebalancing(ex,latest.iloc[-52:],scenarios)
            except Exception:rebal.update(status="BLOCKED",reason="Optimization inputs or solver validation failed")
    return fx,rebal
