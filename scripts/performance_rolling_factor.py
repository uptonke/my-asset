"""Prior-only rolling factor attribution, retrospective revised-data experiment."""
import numpy as np
import pandas as pd

TRAIN=52
EMBARGO=60


def rolling_report(periods,nav,factors,carino,windows_for,train_count=TRAIN,embargo_days=EMBARGO):
    out={"status":"INSUFFICIENT_SAMPLE","training_intervals":train_count,"assumed_publication_lag_days":embargo_days,
         "method":"prior_only_rolling_OLS_revised_data","point_in_time_vintages_verified":False,
         "eligible_intervals":len(periods),"evaluated_intervals":0,"rows":[],"windows":{},
         "notes":["Training interval ends at least 60 calendar days before evaluation start by default.",
                  "Publication embargo is an assumption, not a verified historical publication timestamp.",
                  "Current-vintage revised factor data and realized evaluation factors: retrospective pseudo-out-of-sample attribution, not a trading forecast.",
                  "52 valid observations, not necessarily 52 consecutive weeks. Alpha scaled by interval duration."]}
    if len(periods)<=train_count:return out
    p=periods.sort_values("end").reset_index(drop=True).copy()
    p["duration_weeks"]=(p["end"]-p["start"]).dt.days/7.
    columns=["duration_weeks"]+factors
    names=["RF","Alpha"]+factors+["Residual","FX","Dietz_currency_bridge"]
    rows=[];components=[];returns=[];skip=0
    for _,cur in p.iterrows():
        cutoff=cur["start"]-pd.Timedelta(days=embargo_days)
        train=p[p["end"]<=cutoff].tail(train_count)
        if len(train)<train_count:
            skip+=1;continue
        X=train[columns].to_numpy(dtype=float)
        y=(train["usd"]-train["RF"]).to_numpy(dtype=float)
        if np.linalg.matrix_rank(X)<len(columns):
            skip+=1;continue
        beta=np.linalg.lstsq(X,y,rcond=None)[0]
        if not np.isfinite(beta).all():
            skip+=1;continue
        factor_parts=cur[factors].to_numpy(dtype=float)*beta[1:]
        alpha=float(cur["duration_weeks"]*beta[0])
        rf=float(cur["RF"]);ru=float(cur["usd"]);rt=float(cur["twd"]);fx=float(cur["fx"])
        residual=ru-rf-alpha-float(factor_parts.sum())
        usd=np.r_[rf,alpha,factor_parts,residual]
        c=np.r_[usd*(1+fx),fx,rt-((1+ru)*(1+fx)-1)]
        if not np.isclose(c.sum(),rt,rtol=1e-9,atol=1e-10):raise ValueError("Rolling attribution identity failed")
        rows.append({"start":str(cur["start"].date()),"end":str(cur["end"].date()),
            "train_start":str(train.iloc[0]["start"].date()),"train_end":str(train.iloc[-1]["end"].date()),
            "train_count":len(train),"alpha_weekly_pct":float(beta[0]*100),
            "beta":dict(zip(factors,beta[1:].tolist())),"actual_return_pct":rt*100,
            "contributions_pp":dict(zip(names,(c*100).tolist()))})
        components.append(c);returns.append(rt)
    out.update(evaluated_intervals=len(rows),skipped_intervals=skip,rows=rows,
        evaluation_coverage_pct=len(rows)/max(1,len(nav)-1)*100)
    if not rows:return out
    out["status"]="OK";out["latest"]=rows[-1];out["beta_change_from_first"]={k:rows[-1]["beta"][k]-rows[0]["beta"][k] for k in factors}
    j=len(rows)-1
    while j>0 and rows[j]["start"]==rows[j-1]["end"]:j-=1
    dates=[pd.Timestamp(rows[j]["start"])]+[pd.Timestamp(r["end"]) for r in rows[j:]]
    for label,start,end in windows_for(dates):
        if label=="SI" and start!=min(nav):continue
        ids=[k for k,r in enumerate(rows) if pd.Timestamp(r["start"])>=start and pd.Timestamp(r["end"])<=end]
        total,linked=carino(np.array(returns)[ids],np.array(components)[ids])
        out["windows"][label]={"start":str(start.date()),"end":str(end.date()),"period_count":len(ids),
             "total_return_pct":total*100,"contributions_pp":dict(zip(names,(linked*100).tolist())),
             "reconciliation_error_pp":float((linked.sum()-total)*100)}
    return out
