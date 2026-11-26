"""Phase 3: hypothetical BL return scenarios and cost-aware constrained allocation.
No execution permission; no use of historical mean as forecast.
"""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import linprog, minimize

from run_constrained_optimizer import POLICY, TOL, constraint_matrix, feasibility

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/optimizer_phase3.json"
OUT = ROOT / "data/optimizer"


def snapshot_path():
    temp = os.getenv("RUNNER_TEMP")
    if not temp:
        raise RuntimeError("RUNNER_TEMP unavailable; phase 3 requires same-run common snapshot")
    return Path(temp) / "my-asset-optimizer-phase3.npz"


def save_snapshot(path, returns, weights, meta):
    np.savez_compressed(path, values=returns.to_numpy(dtype=float),
        dates=np.array([x.isoformat() for x in returns.index], dtype=str),
        tickers=np.array(returns.columns, dtype=str), weights=weights.reindex(returns.columns).to_numpy(dtype=float),
        metadata=np.array(json.dumps(meta, ensure_ascii=False)))


def load_snapshot(path):
    from run_skfolio_sandbox import optimizer_snapshot_id
    with np.load(path, allow_pickle=False) as f:
        tickers = f["tickers"].tolist()
        returns = pd.DataFrame(f["values"], columns=tickers, index=pd.to_datetime(f["dates"].tolist()))
        weights = pd.Series(f["weights"], index=tickers)
        meta = json.loads(str(f["metadata"].item()))
    digest = optimizer_snapshot_id(returns, weights, meta["fx_source"], meta["sources"])
    if digest != meta["snapshot_id"]:
        raise ValueError("Snapshot hash mismatch")
    return returns, weights, meta


def validate_config(c):
    for k in ("risk_aversion","tau","horizon_sessions"):
        if not math.isfinite(float(c[k])) or c[k] <= 0:
            raise ValueError("Invalid config: "+k)
    for k in ("covariance_diagonal_shrinkage","turnover_cap_pct"):
        limit = 1 if k == "covariance_diagonal_shrinkage" else 100
        if not 0 <= c[k] <= limit:
            raise ValueError("Invalid config: "+k)
    if not math.isfinite(float(c["view_pp_per_score"])) or c["view_pp_per_score"] < 0:
        raise ValueError("Invalid view scale")
    if not math.isfinite(float(c["return_floor_delta_pp"])):
        raise ValueError("Invalid return floor")
    if any(not math.isfinite(float(v)) or v < 0 for v in c["cost_bps_per_side"].values()):
        raise ValueError("Invalid cost rate")


def bl_scenario(returns, current, priors, c):
    validate_config(c)
    cols = list(returns.columns)
    if len(returns) < 60 or not np.isfinite(returns.to_numpy()).all():
        raise ValueError("Insufficient common returns")
    if list(current.index) != cols or not np.isfinite(current).all() or current.min() < -TOL or abs(current.sum()-1) > TOL:
        raise ValueError("Invalid reference weights")
    rows = {p["ticker"]: p for p in priors}
    if set(rows) != set(cols) or len(rows) != len(priors):
        raise ValueError("Prior universe mismatch")
    for t in cols:
        row = rows[t]
        if not isinstance(row.get("bucket"), str) or not math.isfinite(float(row["relative_score"])) or not 0 < float(row["confidence"]) < 1:
            raise ValueError("Invalid relative prior: "+t)
        if abs(float(row["current_weight_pct"])-current[t]*100) > .002:
            raise ValueError("Prior reference weight mismatch: "+t)
    raw = returns.cov().to_numpy()*252.
    shrink = float(c["covariance_diagonal_shrinkage"])
    cov = (1-shrink)*raw + shrink*np.diag(np.diag(raw))
    cov = (cov+cov.T)/2
    # A tiny PSD ridge avoids numerical singularity, not a return signal.
    cov += np.eye(len(cols))*max(float(np.max(np.diag(cov)))*1e-10,1e-12)
    w0 = current.to_numpy()
    pi = float(c["risk_aversion"])*cov@w0  # reference-implied, not market equilibrium
    tau_cov = float(c["tau"])*cov
    groups = sorted({rows[t]["bucket"] for t in cols})
    scores = np.array([float(rows[t]["relative_score"]) for t in cols])
    ref_score = float(scores@w0)
    P, Q, O, views = [], [], [], []
    for group in groups:
        mask = np.array([rows[t]["bucket"] == group for t in cols], dtype=bool)
        member = w0*mask
        if member.sum() <= TOL:
            continue
        member /= member.sum()
        p = member-w0  # relative bucket vs current portfolio
        if np.linalg.norm(p) < TOL:
            continue
        confidence = min(.75, float(np.average([float(rows[t]["confidence"]) for t in cols if rows[t]["bucket"] == group], weights=member[mask])))
        shift = float(c["view_pp_per_score"])/100.*(float(member@scores)-ref_score)
        q = float(p@pi)+shift
        omega = max(float(p@tau_cov@p)*(1-confidence)/confidence,1e-12)
        P.append(p); Q.append(q); O.append(omega)
        views.append({"bucket":group,"confidence":confidence,"scenario_shift_pp":round(shift*100,5),
                      "relative_view_pct":round(q*100,5),"omega":omega})
    if P:
        P = np.stack(P); Q = np.array(Q); omega = np.diag(O)
        posterior = pi + tau_cov@P.T@np.linalg.solve(P@tau_cov@P.T+omega,Q-P@pi)
    else:
        posterior = pi.copy()
    if not np.isfinite(posterior).all():
        raise ValueError("Non-finite BL posterior")
    return posterior, cov, pi, views


def solve(returns, current, buckets, mu, cov, costs, c, kind, floor=None):
    """Daily historical ES LP with explicit absolute weight-change auxiliaries.
    Annual excess-return proxy is separate from historical ES. Cost is one-off,
    amortized over configured sessions for daily ES or charged once for annual utility.
    """
    X = returns.to_numpy(dtype=float)
    n, T = len(current), len(returns)
    w0 = current.to_numpy(dtype=float)
    A,b,bounds,_ = constraint_matrix(list(current.index),buckets,POLICY)
    costs = np.asarray(costs,dtype=float)
    mu = np.asarray(mu,dtype=float)
    if (len(costs)!=n or len(mu)!=n or not np.isfinite(costs).all() or
        not np.isfinite(mu).all() or np.any(costs<0)):
        raise ValueError("Invalid model inputs")
    # z=(w,d); d>=|w-w0|. Turnover=0.5*sum(d).
    I=np.eye(n)
    C=np.vstack([np.c_[A,np.zeros_like(A)],np.c_[I,-I],np.c_[-I,-I],
                 np.r_[np.zeros(n),np.ones(n)][None,:]])
    B=np.r_[b,w0,-w0,2*c["turnover_cap_pct"]/100.]
    if floor is not None:
        C=np.vstack([C,np.r_[-mu,costs]])
        B=np.r_[B,-floor]
    E=np.r_[np.ones(n),np.zeros(n)][None,:]
    z_bounds=bounds+[(0.,1.)]*n
    feasible=linprog(np.zeros(2*n),A_ub=C,b_ub=B,A_eq=E,b_eq=[1.],bounds=z_bounds,method="highs")
    if not feasible.success:
        return None, {"status":"INFEASIBLE" if feasible.status==2 else "FAILED","message":str(feasible.message)}
    if kind in ("cvar","cvar_cost"):
        # target-return-only case is cost-free in the objective, but floor is net.
        coefficient=costs/float(c["horizon_sessions"]) if kind=="cvar_cost" else np.zeros(n)
        # z=(w,d,eta,u)
        tail=sparse.hstack([-sparse.csr_matrix(X),sparse.csr_matrix((T,n)),-np.ones((T,1)),-sparse.eye(T)],format="csr")
        C2=sparse.hstack([sparse.csr_matrix(C),sparse.csr_matrix((len(B),T+1))],format="csr")
        E2=sparse.hstack([sparse.csr_matrix(E),sparse.csr_matrix((1,T+1))],format="csr")
        res=linprog(np.r_[np.zeros(n),coefficient,1.,np.full(T,1/(.05*T))],
                    A_ub=sparse.vstack([C2,tail],format="csr"),b_ub=np.r_[B,np.zeros(T)],
                    A_eq=E2,b_eq=[1.],bounds=z_bounds+[(None,None)]+[(0.,None)]*T,method="highs")
        w=res.x[:n] if res.success else None
    elif kind=="mean_variance":
        # Annual utility: risk aversion/2 variance - annual excess return + one-off cost.
        delta=float(c["risk_aversion"])
        def obj(z):
            w=z[:n]
            return float(delta/2*w@cov@w-mu@w+costs@z[n:])
        def jac(z):
            return np.r_[delta*cov@z[:n]-mu,costs]
        res=minimize(obj,feasible.x,jac=jac,bounds=z_bounds,method="SLSQP",
            constraints=[{"type":"eq","fun":lambda z:E@z-1.,"jac":lambda z:E},
                         {"type":"ineq","fun":lambda z:B-C@z,"jac":lambda z:-C}],
            options={"maxiter":1000,"ftol":1e-12})
        w=res.x[:n] if res.success else None
    else:
        raise ValueError("Unknown solver")
    if w is None:
        return None, {"status":"FAILED","message":str(res.message)}
    d=np.abs(w-w0); cost=float(costs@d); turn=float(d.sum()/2)
    gross=float(mu@w); net=gross-cost
    if not feasibility(w,A,b,bounds) or turn>c["turnover_cap_pct"]/100.+TOL or (floor is not None and net<floor-TOL):
        return None, {"status":"FAILED","message":"Post-solve hard-constraint validation failed"}
    return pd.Series(w,index=current.index), {"status":"OK","constraint_validated":True,
        "gross_scenario_excess_return_pct":gross*100,"net_scenario_excess_return_pct":net*100,
        "estimated_oneoff_cost_pct":cost*100,"turnover_pct":turn*100,
        "return_floor_pct":None if floor is None else floor*100,
        "solver":"SLSQP" if kind=="mean_variance" else "HiGHS"}


def build(returns,current,meta,prior,bl,c):
    from run_skfolio_sandbox import portfolio_metrics,weight_table
    validate_config(c)
    sid=meta["snapshot_id"]
    result={"version":"v3.0","snapshot_id":sid,"status":"BLOCKED","execution_permission":False,
            "scope":"sandbox_hypothetical_scenarios_only","config":c,"portfolios":{},"sensitivity":[],
            "notes":["Returns are hypothetical annual TWD excess-return scenarios, not absolute forecasts.",
                     "Existing v3.2 relative scores already include v3.1 BL tilt views; no double counting.",
                     "Reference-implied prior uses current weights, not market equilibrium weights.",
                     "Costs are assumed per side on gross buys plus sells; not live brokerage quotes.",
                     "One-time costs are charged once against annual scenario return and amortized for daily ES objective.",
                     "Hard turnover cap and policy constraints never relax automatically. No formal trade or Supabase write."]}
    if meta.get("skipped"):
        result["reason"]="Incomplete or stale asset universe";return result
    if prior.get("snapshot_id")!=sid or bl.get("snapshot_id")!=sid or prior.get("status")!="OK" or bl.get("status")!="OK":
        result["reason"]="Expected-return / BL source snapshot mismatch or unavailable";return result
    rows=prior.get("asset_expected_return_priors",[])
    buckets=meta["asset_buckets"]
    costs=np.array([float(c["cost_bps_per_side"][buckets[t]])/10000 for t in current.index])
    mu,cov,pi,views=bl_scenario(returns,current,rows,c)
    floor=float(mu@current.to_numpy())+float(c["return_floor_delta_pp"])/100
    result.update(status="OK",reference_scenario_excess_return_pct=float(mu@current.to_numpy())*100,
        views=views,return_scenarios=[{"ticker":t,"prior_excess_pct":float(pi[i])*100,
                                     "posterior_excess_pct":float(mu[i])*100,"cost_bps_per_side":float(costs[i])*10000}
                                    for i,t in enumerate(current.index)])
    def candidate(kind, mu_, cov_, costs_, cfg, floor_):
        w,info=solve(returns,current,buckets,mu_,cov_,costs_,cfg,kind,floor_)
        p={"status":info["status"],"method":info,"diagnostic_only":True}
        if w is not None:
            p.update(metrics=portfolio_metrics(returns,w,kind),weights=weight_table(w,current,top_n=len(w)))
        return p
    for key,kind,f in (("target_return_cvar","cvar",floor),("cost_aware_cvar","cvar_cost",floor),
                       ("cost_aware_mean_variance","mean_variance",floor)):
        result["portfolios"][key]=candidate(kind,mu,cov,costs,c,f)
    # One-at-a-time sensitivity, never silently change the base candidate.
    scenarios=[]
    for mult in c["sensitivity"]["cost_multipliers"]:
        scenarios.append(("cost_multiplier",mult,mu,cov,costs*mult,c,floor))
    for scale in c["sensitivity"]["view_pp_per_score"]:
        cfg={**c,"view_pp_per_score":scale}
        m,v,_,_=bl_scenario(returns,current,rows,cfg)
        scenarios.append(("view_pp_per_score",scale,m,v,costs,cfg,float(m@current.to_numpy())+cfg["return_floor_delta_pp"]/100))
    for delta in c["sensitivity"]["return_floor_delta_pp"]:
        scenarios.append(("return_floor_delta_pp",delta,mu,cov,costs,c,float(mu@current.to_numpy())+delta/100))
    for horizon in c["sensitivity"]["horizon_sessions"]:
        scenarios.append(("horizon_sessions",horizon,mu,cov,costs,{**c,"horizon_sessions":horizon},floor))
    for axis,value,m,v,cs,cfg,f in scenarios:
        p=candidate("cvar_cost",m,v,cs,cfg,f)
        result["sensitivity"].append({"axis":axis,"value":value,"status":p["status"],"method":p["method"],"metrics":p.get("metrics",{}),"weights":p.get("weights",[])})
    if not any(p["status"]=="OK" for p in result["portfolios"].values()):
        result["status"]="NO_FEASIBLE_BASE_CANDIDATE"
    return result


def main():
    report_path=OUT/"skfolio_sandbox_latest.json"
    report=json.loads(report_path.read_text(encoding="utf-8"))
    sid=report.get("sample",{}).get("snapshot_id")
    try:
        r,w,meta=load_snapshot(snapshot_path())
        if meta["snapshot_id"]!=sid:
            raise ValueError("Published report snapshot mismatch")
        prior=json.loads((OUT/"expected_return_model_latest.json").read_text(encoding="utf-8"))
        bl=json.loads((OUT/"black_litterman_sandbox_latest.json").read_text(encoding="utf-8"))
        cfg=json.loads(CONFIG.read_text(encoding="utf-8"))
        phase=build(r,w,meta,prior,bl,cfg)
    except Exception as exc:
        phase={"version":"v3.0","status":"BLOCKED","snapshot_id":sid,"execution_permission":False,
               "reason":str(exc)[:400],"portfolios":{},"sensitivity":[]}
    report["phase3"]=phase
    tmp=report_path.with_suffix(".phase3.tmp")
    tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    tmp.replace(report_path)
    print("Phase 3:",phase["status"],phase.get("reason",""),{k:v["status"] for k,v in phase["portfolios"].items()})
    if phase["status"]=="BLOCKED":
        raise RuntimeError("Phase 3 inputs failed validation")


if __name__=="__main__":
    main()
