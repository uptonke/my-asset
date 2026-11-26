"""Fixed-universe research models; never live weights or orders."""
import json
import math
import numpy as np
import pandas as pd
from scipy.optimize import linprog,minimize
from run_constrained_optimizer import POLICY,constraint_matrix,feasibility
from run_cost_aware_optimizer import solve

REGIME={"drawdown_risk_off":-.08,"vol_ratio_risk_off":1.35,"trend_risk_on":.03,
        "vol_ratio_risk_on":1.05,"short_observations":21,"long_observations":63}
FACTOR_NAMES=("global_market","taiwan_relative","value_relative","growth_relative","gold","crypto","residual")

def regime(train):
    """Fixed thresholds; no inference from future test or published macro lag."""
    x=train["VOO"].to_numpy(dtype=float)
    if len(x)<63 or not np.isfinite(x).all() or min(x)<=-1:raise ValueError("Regime history incomplete")
    short,long=x[-21:],x[-63:]
    curve=np.r_[1.,np.cumprod(1+long)]
    dd=float(curve[-1]/curve.max()-1)
    baseline=float(np.std(long,ddof=1))
    if baseline<=1e-12:raise ValueError("Regime volatility unavailable")
    ratio=float(np.std(short,ddof=1)/baseline)
    trend=float(np.prod(1+long)-1)
    name="RISK_OFF" if dd<=REGIME["drawdown_risk_off"] or ratio>=REGIME["vol_ratio_risk_off"] else (
        "RISK_ON" if trend>=REGIME["trend_risk_on"] and ratio<=REGIME["vol_ratio_risk_on"] else "NEUTRAL")
    return {"regime":name,"drawdown_pct":dd*100,"vol_ratio":ratio,"trend_pct":trend*100}

def regime_target(train,before,buckets,mu,cov,rates,cfg):
    signal=regime(train)
    # Risk-off uses empirical tail loss; risk-on/neutral uses reference-implied
    # mean-variance with lower/higher risk aversion. No expected-return fitting.
    c=dict(cfg)
    if signal["regime"]=="RISK_OFF":
        kind="cvar_cost"
    else:
        kind="mean_variance"
        c["risk_aversion"]=cfg["risk_aversion"]*(.75 if signal["regime"]=="RISK_ON" else 1.)
    floor=float(mu@before.to_numpy())+cfg["return_floor_delta_pp"]/100
    w,info=solve(train,before,buckets,mu,cov,rates,c,kind,floor)
    return w,{**info,**signal,"objective_mode":kind}

def proxy_model(train):
    # All observations are TWD returns over identical common-mark intervals.
    # These are tradable proxy spreads, not academic FF factor portfolios.
    x=train
    f=pd.DataFrame({"global_market":x["VOO"],"taiwan_relative":x["0050"]-x["VOO"],
        "value_relative":x["AVUV"]-x["VOO"],"growth_relative":x["QQQ"]-x["VOO"],
        "gold":x["GLDM"],"crypto":x["BTC-USD"]},index=x.index)
    X=f.to_numpy();Y=x.to_numpy()
    if len(X)<63 or not np.isfinite(X).all() or not np.isfinite(Y).all():raise ValueError("Insufficient factor data")
    X=X-X.mean(axis=0);Y=Y-Y.mean(axis=0)
    if np.linalg.matrix_rank(X)<X.shape[1]:raise ValueError("Rank-deficient proxy factors")
    B=np.linalg.lstsq(X,Y,rcond=None)[0]
    R=Y-X@B
    F=X.T@X/(len(X)-1);S=R.T@R/(len(X)-1)
    return B,F,S

def variance_shares(w,B,F,S):
    w=np.asarray(w,dtype=float);beta=B@w
    parts=np.r_[beta*(F@beta),w@S@w]
    total=float(parts.sum())
    if not np.isfinite(parts).all() or total<=1e-14:raise ValueError("Nonpositive risk variance")
    shares=parts/total
    return shares,total,beta

def budget_target(train,before,buckets,cfg):
    B,F,S=proxy_model(train)
    w0=before.to_numpy(dtype=float);n=len(w0)
    A,b,bounds,_=constraint_matrix(list(before.index),buckets,POLICY)
    I=np.eye(n);cap=cfg["turnover_cap_pct"]/100
    C=np.vstack([np.c_[A,np.zeros_like(A)],np.c_[I,-I],np.c_[-I,-I],np.r_[np.zeros(n),np.ones(n)][None,:]])
    d=np.r_[b,w0,-w0,2*cap]
    E=np.r_[np.ones(n),np.zeros(n)][None,:]
    limits=bounds+[(0.,1.)]*n
    feasible=linprog(np.zeros(2*n),A_ub=C,b_ub=d,A_eq=E,b_eq=[1.],bounds=limits,method="highs")
    if not feasible.success:return None,{"status":"INFEASIBLE","reason":"Policy and turnover constraints"}
    target=np.ones(len(FACTOR_NAMES))/len(FACTOR_NAMES)
    def objective(z):
        try:
            r,_,_=variance_shares(z[:n],B,F,S)
            return float(np.sum((r-target)**2))
        except ValueError:return 1e6
    result=minimize(objective,feasible.x,method="SLSQP",bounds=limits,
        constraints=[{"type":"eq","fun":lambda z:E@z-1},{"type":"ineq","fun":lambda z:d-C@z}],
        options={"maxiter":500,"ftol":1e-10})
    w=result.x[:n]
    if not result.success or not feasibility(w,A,b,bounds) or np.abs(w-w0).sum()/2>cap+1e-7 or objective(result.x)>=1e6:
        return None,{"status":"FAILED","reason":"Budget solver failed feasibility or convergence"}
    old,_,_=variance_shares(w0,B,F,S);new,var,beta=variance_shares(w,B,F,S)
    return pd.Series(w,index=before.index),{"status":"OK","budget_match_rmse_pp":float(np.sqrt(np.mean((new-target)**2))*100),
        "risk_shares":[{"factor":k,"before_pct":float(o*100),"candidate_pct":float(v*100),"target_pct":float(t*100)}
            for k,o,v,t in zip(FACTOR_NAMES,old,new,target)],"variance_per_observation":var,
        "budget_is_illustrative":True,"constraint_validated":True}

def actual_factor_budget(periods,factors):
    """Retrospective actual USD excess-return variance, equal-duration periods."""
    out={"status":"INSUFFICIENT_SAMPLE","execution_permission":False,"basis":"actual_NAV_USD_excess_weekly_in_sample"}
    if periods is None or periods.empty:return out
    p=periods.loc[(periods["end"]-periods["start"]).dt.days==7].sort_values("end")
    out["observations"]=len(p)
    if len(p)<52:return out
    X=p[factors].to_numpy(dtype=float);y=(p["usd"]-p["RF"]).to_numpy(dtype=float)
    if not np.isfinite(X).all() or not np.isfinite(y).all():return out
    X=X-X.mean(axis=0);y=y-y.mean()
    if np.linalg.matrix_rank(X)<len(factors):out["status"]="RANK_DEFICIENT";return out
    beta=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@beta
    F=X.T@X/(len(X)-1);parts=np.r_[beta*(F@beta),res@res/(len(X)-1)]
    var=float(y@y/(len(X)-1))
    if var<=1e-14 or not np.isclose(parts.sum(),var,rtol=1e-8,atol=1e-12):
        out["status"]="VARIANCE_IDENTITY_FAILED";return out
    budget=100/len(parts)
    out.update(status="RESEARCH_ONLY",start=str(p.iloc[0]["start"].date()),end=str(p.iloc[-1]["end"].date()),
        annualized_excess_vol_pct=math.sqrt(var*52)*100,
        rows=[{"factor":k,"risk_pct":float(v/var*100),"illustrative_budget_pct":budget,"gap_pp":float(v/var*100-budget)}
              for k,v in zip(list(factors)+["Residual"],parts)],
        identity_error_pct=float((parts.sum()/var-1)*100),
        notes=["Signed correlated-factor Euler variance shares; negative contributions are possible. Equal budgets are illustrative, not approved.",
               "Only exact seven-day observed intervals, with gaps allowed for covariance estimation; no return linking. Retrospective USD excess-return risk, not TWD total portfolio risk."])
    return out

def run_research(prices=None,config=None,opt=None):
    from cost_walk_forward import CONFIG,OPT,load_prices,simulate
    config=config or json.loads(CONFIG.read_text());opt=opt or json.loads(OPT.read_text())
    out={"version":"v3.1/v3.2","status":"BLOCKED","execution_permission":False,"regime_thresholds":REGIME,
         "notes":["Fixed illustrative universe, revised adjusted closes, common marks; not actual portfolio or historical investable universe.",
                  "Identical dates, training, initial weights, costs and turnover caps for static and adaptive strategies; no training on test returns.",
                  "Regime uses trailing VOO TWD return/drawdown/volatility only. Thresholds fixed, not optimized.",
                  "Factor budget uses correlated tradable TWD proxy factors, not FF exposures. Equal signed variance shares incl residual are illustrative; constrained minimum error is not exact risk parity.",
                  "Failed solve holds drifted weights; constraints may remain violated. Cost model excludes taxes/minimum fees; no trade permission."]}
    try:
        prices=load_prices(config) if prices is None else prices
        # Same scenario, dates and cost treatment; no second independent data fetch.
        out["comparison"]=simulate(prices,config,opt,1.,methods=("buy_hold","strategic_rebalance","cost_aware_mean_variance","regime_aware","factor_budget"))
        out["status"]="OK_RESEARCH_ONLY"
        out["latest_fold"]=out["comparison"]["folds"][-1]
        out["regime_counts"]={}
        for fold in out["comparison"]["folds"]:
            name=fold["methods"]["regime_aware"].get("model",{}).get("regime","UNAVAILABLE")
            out["regime_counts"][name]=out["regime_counts"].get(name,0)+1
    except Exception:
        out.update(status="BLOCKED",reason="Common marks, model or optimization failed; no fallback signal")
    return out
