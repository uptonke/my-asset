"""Private v3.5 currency attribution and v3.6 constrained rebalance simulation.

Same completed-date marks and current holdings as v3.4. No dividend imputation,
new instruments, currency hedge orders, or formal policy approval.
"""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog,minimize
from performance_coverage import quote
from performance_portfolio_risk import CASH,BUCKETS,RiskBlocked,risk_contributions,hypothetical
from run_constrained_optimizer import POLICY,constraint_matrix,feasibility
from cost_walk_forward import trade_cost

CONFIG=Path(__file__).resolve().parents[1]/"config/risk_rebalance_v36.json"
OPT=Path(__file__).resolve().parents[1]/"config/optimizer_phase3.json"

def recorded_currency_pnl(pnl):
    """Preserve actual P&L identity; unknown decomposition stays unknown."""
    out={"version":"v3.5","status":"RESEARCH_ONLY","windows":{},"execution_permission":False}
    for label,p in pnl.items():
        try:
            keys=("price_twd","fx_twd","interaction_twd","execution_vs_close_twd","unallocated_pnl_twd",
                  "explicit_other_cashflow_twd","unexplained_twd")
            parts={k:float(p[k]) for k in keys}
            actual=float(p["actual_pnl_twd"])
            err=actual-math.fsum(parts.values())
            if not all(math.isfinite(v) for v in [actual,err,*parts.values()]) or abs(err)>.02:
                raise RiskBlocked("PNL_IDENTITY_FAILED")
            rows=[]
            for r in p["rows"]:
                rows.append({k:r.get(k) for k in ("ticker","bucket","pnl_twd","price_twd","fx_twd","interaction_twd","execution_vs_close_twd","decomposition_status")})
            partial=bool(p.get("missing") or p.get("partial_decomposition") or p.get("status")=="PARTIAL")
            out["windows"][label]={"status":"PARTIAL_RESEARCH_ONLY" if partial else "RESEARCH_ONLY",
                "start":p["start"],"end":p["end"],"actual_pnl_twd":actual,**parts,
                "known_fx_including_interaction_twd":parts["fx_twd"]+parts["interaction_twd"],
                "identity_error_twd":err,"rows":rows,"missing":p.get("missing",[]),
                "partial_decomposition":p.get("partial_decomposition",[])}
        except Exception:out["windows"][label]={"status":"UNAVAILABLE","reason":"Recorded P&L decomposition failed validation"}
    out["notes"]=["Historical mark-to-mark P&L from recorded holdings and trade dates; price, pure FX and price×FX interaction kept separate.",
                  "Execution vs close contains trading/FX execution and fees; not pure FX. Endpoint-only, missing and NAV residual amounts not assigned to FX. No added dividend cash."]
    return out

def currency_parts(returns,ex,fx):
    cols=[h["ticker"] for h in ex["holdings"]]
    X=returns[cols].to_numpy(dtype=float)
    if len(X)<26 or not np.isfinite(X).all() or (X<=-1).any():raise RiskBlocked("INVALID_COMMON_RETURNS")
    if not (returns.index.to_series().diff().dropna()==pd.Timedelta(days=7)).all():
        raise RiskBlocked("NONCONTIGUOUS_WEEKLY_SAMPLE")
    usd=np.array([h["currency"]=="USD" for h in ex["holdings"]],dtype=float)
    if usd.any():
        dates=[returns.index[0]-pd.Timedelta(days=7),*returns.index]
        vals=np.array([quote(fx,d,4,"USD/TWD","portfolio FX","FX") for d in dates])
        f=vals[1:]/vals[:-1]-1
    else:f=np.zeros(len(X))
    F=f[:,None]*usd
    L=(1+X)/(1+F)-1
    I=L*F
    if not np.allclose(L+F+I,X,atol=1e-12,rtol=1e-10):raise RiskBlocked("CURRENCY_RETURN_IDENTITY_FAILED")
    return X,L,F,I

def currency_risk(returns,ex,fx):
    X,L,F,I=currency_parts(returns,ex,fx)
    w=np.array([h["weight"] for h in ex["holdings"]])
    y=X@w
    vol=float(y.std(ddof=1)*math.sqrt(52))
    if vol<=1e-12:raise RiskBlocked("ZERO_VOLATILITY")
    # Euler contribution of additive return components, preserving correlations.
    yc=y-y.mean()
    def component(Z):
        return (Z-Z.mean(axis=0)).T@yc/(len(y)-1)*52/vol
    c=[component(Z)*w for Z in (L,F,I)]
    total=math.fsum(float(v.sum()) for v in c)
    if not math.isclose(total,vol,abs_tol=1e-10):raise RiskBlocked("CURRENCY_EULER_IDENTITY_FAILED")
    rows=[]
    for j,h in enumerate(ex["holdings"]):
        row={"ticker":h["ticker"],"currency":h["currency"],"weight_pct":w[j]*100,
             **{k:float(v[j]*100) for k,v in zip(("local_pp","fx_pp","interaction_pp"),c)}}
        row["total_pp"]=row["local_pp"]+row["fx_pp"]+row["interaction_pp"]
        rows.append(row)
    parts={k:float(v.sum()*100) for k,v in zip(("local_pp","fx_pp","interaction_pp"),c)}
    return {"status":"RESEARCH_ONLY","observations":len(y),"start":str((returns.index[0]-pd.Timedelta(days=7)).date()),
            "end":str(returns.index[-1].date()),"annualized_vol_pct":vol*100,
            "constant_fx_ann_vol_pct":float((L@w).std(ddof=1)*math.sqrt(52)*100),
            "components_pp":parts,"fx_including_interaction_pp":parts["fx_pp"]+parts["interaction_pp"],
            "fx_including_interaction_risk_share_pct":(parts["fx_pp"]+parts["interaction_pp"])/vol,
            "identity_error_pp":(total-vol)*100,"rows":sorted(rows,key=lambda r:abs(r["fx_pp"]+r["interaction_pp"]),reverse=True)}

def currency_summary(ex,latest,market):
    usd=math.fsum(h["weight"] for h in ex["holdings"] if h["currency"]=="USD")
    out={"version":"v3.5","status":"PARTIAL_RESEARCH_ONLY","execution_permission":False,
         "as_of":ex["as_of"],"basis":ex["basis"],"usd_quote_weight_pct":usd*100,"twd_quote_weight_pct":(1-usd)*100,
         "usd_twd_1pct_sensitivity_twd":usd*ex["model_nav_twd"]*.01,
         "windows":{},"notes":["Quote-currency translation exposure, not underlying issuer economic currency exposure or hedge-adjusted beta.",
             "Frozen as-of weights; weekly local + pure FX + interaction returns add to TWD return. Signed covariance/Euler components add to annual volatility.",
             "Constant-FX risk is a counterfactual local-price model, not the cost or effectiveness of a currency hedge."]}
    for n in (26,52,104):
        if len(latest)<n:out["windows"][str(n)]={"status":"INSUFFICIENT_SAMPLE","available":len(latest)}
        else:
            try:out["windows"][str(n)]=currency_risk(latest.iloc[-n:],ex,market["fx"])
            except Exception:out["windows"][str(n)]={"status":"UNAVAILABLE","reason":"Common FX or return identity failed"}
    if any(r["status"]=="RESEARCH_ONLY" for r in out["windows"].values()):out["status"]="RESEARCH_ONLY"
    return out

def bucket_matrix(holdings):
    names=sorted(BUCKETS)
    return names,np.array([[h["bucket"]==g for h in holdings] for g in names],dtype=float)

def group_shares(w,cov,G):
    v=float(w@cov@w)
    if not math.isfinite(v) or v<=1e-14:raise RiskBlocked("ZERO_OR_INVALID_VARIANCE")
    return G@(w*(cov@w))/v

def policy_violations(w,A,b,bounds,names,cols):
    out=[{"constraint":name,"excess_pp":float((a@w-limit)*100)} for a,limit,name in zip(A,b,names) if a@w>limit+1e-7]
    for x,(lo,hi),t in zip(w,bounds,cols):
        if x>hi+1e-7:out.append({"constraint":"single_max:"+t,"excess_pp":float((x-hi)*100)})
        if x<lo-1e-7:out.append({"constraint":"minimum:"+t,"excess_pp":float((lo-x)*100)})
    return out

def solve_candidates(returns,ex,cfg,opt):
    h=ex["holdings"];cols=[r["ticker"] for r in h];w0=np.array([r["weight"] for r in h])
    X=returns[cols].to_numpy(dtype=float);n=len(w0)
    if len(X)<52 or not np.isfinite(X).all() or not np.isfinite(w0).all() or min(w0)<0 or not np.isclose(w0.sum(),1,atol=1e-9):
        raise RiskBlocked("INSUFFICIENT_OR_INVALID_SAMPLE")
    cov=np.atleast_2d(np.cov(X,rowvar=False,ddof=1))*52.
    groups,G=bucket_matrix(h)
    budget=cfg["risk_budget"]
    if set(budget)!=BUCKETS or any(not math.isfinite(v) or v<0 for v in budget.values()) or abs(sum(budget.values())-1)>1e-9:
        raise RiskBlocked("INVALID_RISK_BUDGET")
    target=np.array([budget[g] for g in groups])
    # Existing sandbox limits, not user-approved policy. Keep actual cash
    # distinct from traded cash-like securities for cost accounting.
    A,b,bounds,names=constraint_matrix(cols,{r["ticker"]:r["bucket"] for r in h},POLICY)
    cap=float(opt["turnover_cap_pct"])/100
    rates=np.array([0. if r["ticker"]==CASH else opt["cost_bps_per_side"][r["bucket"]]/10000 for r in h])
    if not 0<=cap<=1 or not np.isfinite(rates).all() or min(rates)<0 or max(rates)>=.1:raise RiskBlocked("INVALID_COST_ASSUMPTIONS")
    I=np.eye(n);C=np.vstack([np.c_[A,np.zeros_like(A)],np.c_[I,-I],np.c_[-I,-I],np.r_[np.zeros(n),np.ones(n)][None,:]])
    d=np.r_[b,w0,-w0,2*cap];E=np.r_[np.ones(n),np.zeros(n)][None,:];limits=bounds+[(0.,1.)]*n
    lp=linprog(np.zeros(2*n),A_ub=C,b_ub=d,A_eq=E,b_eq=[1.],bounds=limits,method="highs")
    info={"policy":dict(POLICY),"nominal_turnover_cap_pct":cap*100,"risk_budget_pct":{k:v*100 for k,v in budget.items()},
          "current_policy_violations":policy_violations(w0,A,b,bounds,names,cols),"cost_bps_per_side":dict(opt["cost_bps_per_side"])}
    if not lp.success:return info,{},{"status":"INFEASIBLE" if lp.status==2 else "FAILED"}
    def valid(z):
        w=z[:n]
        return feasibility(w,A,b,bounds) and np.abs(w-w0).sum()/2<=cap+1e-7 and np.all(C@z<=d+1e-7)
    def budget_obj(z):
        try:return float(np.sum((group_shares(z[:n],cov,G)-target)**2))
        except RiskBlocked:return 1e6
    scale=max(float(np.max(np.abs(cov))),1e-12)
    def variance_obj(z):return float(z[:n]@cov@z[:n]/scale)
    constraints=[{"type":"eq","fun":lambda z:E@z-1},{"type":"ineq","fun":lambda z:d-C@z}]
    starts=[lp.x]
    z0=np.r_[w0,np.zeros(n)]
    if valid(z0):starts.append(z0)
    solved={};failures={}
    for name,obj in (("minimum_volatility",variance_obj),("risk_budget",budget_obj)):
        results=[]
        for seed in starts:
            r=minimize(obj,seed,method="SLSQP",bounds=limits,constraints=constraints,options={"ftol":1e-10,"maxiter":600})
            if r.success and valid(r.x) and math.isfinite(obj(r.x)) and obj(r.x)<1e6:results.append(r.x)
        if results:
            best=min(results,key=obj)
            solved[name]=best[:n].copy()
            starts.append(best)
        else:failures[name]="SOLVER_FAILED"
    return info,solved,{"status":"RESEARCH_ONLY" if solved else "FAILED","failures":failures,"rates":rates}

def candidate_report(w,ex,returns,rates,scenarios,budget):
    h=ex["holdings"];w0=np.array([r["weight"] for r in h]);nav=ex["model_nav_twd"]
    c,actual_turn=trade_cost(w0,w,rates)
    after_nav=nav*(1-c);amounts=((1-c)*w-w0)*nav
    if not math.isclose(float(amounts.sum()),-nav*c,abs_tol=1e-5):raise RiskBlocked("SELF_FINANCING_IDENTITY_FAILED")
    candidate={**ex,"model_nav_twd":after_nav,"holdings":[{**r,"weight":float(x),"market_value_twd":float(after_nav*x)} for r,x in zip(h,w)]}
    risk=risk_contributions(returns,candidate)
    short=risk_contributions(returns.iloc[-26:],candidate)
    by={g["bucket"]:g["risk_share_pct"] for g in risk["groups"]}
    errors=[by.get(k,0.)-v*100 for k,v in budget.items()]
    stress=[]
    for s in scenarios:
        r=hypothetical(candidate,s)
        stress.append({"id":s["id"],"label":s["label"],"return_pct_before_cost":r["return_pct"],
            "net_pnl_twd":r["stressed_model_nav_twd"]-nav,"net_return_pct":(r["stressed_model_nav_twd"]/nav-1)*100,
            "stressed_model_nav_twd":r["stressed_model_nav_twd"]})
    return {"annualized_vol_pct":risk["annualized_vol_pct"],"ann_vol_26w_pct":short["annualized_vol_pct"],
            "es95_loss_pct":risk["tail"]["es95_loss_pct"],"diversification_ratio":risk["diversification_ratio"],
            "risk_budget_rmse_pp":float(np.sqrt(np.mean(np.square(errors)))),"groups":risk["groups"],
            "usd_quote_weight_pct":float(sum(x for r,x in zip(h,w) if r["currency"]=="USD")*100),
            "nominal_turnover_pct":float(np.abs(w-w0).sum()/2*100),"actual_half_gross_traded_pct":actual_turn*100,
            "estimated_cost_twd":nav*c,"estimated_cost_pct":c*100,"post_cost_nav_twd":after_nav,
            "cashflow_identity_error_twd":float(amounts.sum()+nav*c),
            "cost_sensitivity_twd":{str(m):nav*trade_cost(w0,w,rates*m)[0] for m in (.5,2.)},
            "weights":[{"ticker":r["ticker"],"bucket":r["bucket"],"before_pct":float(o*100),"after_pct":float(x*100),
                        "change_pp":float((x-o)*100),"modeled_value_change_twd":float(a)} for r,o,x,a in zip(h,w0,w,amounts)],
            "stress":stress}

def rebalance_report(ex,latest,scenarios,cfg=None,opt=None):
    out={"version":"v3.6","status":"BLOCKED","execution_permission":False,"candidates":{},
         "notes":["Existing instruments and TWD cash only. No new holdings, shorting, leverage, expected-return forecast or order creation.",
                  "Illustrative group risk budgets and existing sandbox constraints; not approved personal allocation policy. Baseline may violate limits.",
                  "52 common weeks fit and evaluate in sample; 26-week overlap sensitivity is not out-of-sample validation.",
                  "Min volatility and risk-budget mismatch objectives do not optimize fees; exact self-financing costs applied after solve and all stress returns shown net of modeled costs. Cash funding leg has zero cost.",
                  "No minimum commissions, lots, taxes, separate FX conversion spread or liquidity impact; risk budget objective is nonconvex, local solver only."]}
    if abs(ex["nav_gap_pct"])>1 or ex.get("later_ledger_events",0) or "MICRO_NEGATIVE_CASH_CLAMPED" in ex.get("warnings",[]):
        out["reason"]="EXPOSURE_QUALITY_GATE";return out
    if len(latest)<52:
        out.update(status="INSUFFICIENT_SAMPLE",available=len(latest),required=52);return out
    cfg=cfg or json.loads(CONFIG.read_text());opt=opt or json.loads(OPT.read_text())
    returns=latest.iloc[-52:]
    try:
        info,solved,result=solve_candidates(returns,ex,cfg,opt)
        out.update(info,status=result["status"],failures=result.get("failures",{}),
                   as_of=ex["as_of"],basis=ex["basis"],start=str((returns.index[0]-pd.Timedelta(days=7)).date()),end=str(returns.index[-1].date()))
        w0=np.array([h["weight"] for h in ex["holdings"]])
        # Baseline remains visible even if no feasible candidate.
        baseline_rates=np.zeros(len(w0))
        out["baseline"]=candidate_report(w0,ex,returns,baseline_rates,scenarios,cfg["risk_budget"])
        for name,w in solved.items():
            try:out["candidates"][name]=candidate_report(w,ex,returns,result["rates"],scenarios,cfg["risk_budget"])
            except Exception:out["failures"][name]="CANDIDATE_ACCOUNTING_FAILED"
        if not out["candidates"] and out["status"]=="RESEARCH_ONLY":out["status"]="FAILED"
    except Exception:out.update(status="BLOCKED",reason="Risk sample, constraints or accounting validation failed",candidates={})
    return out
