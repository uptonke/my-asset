"""v3.3/v3.4: private portfolio exposure risk, not live trade signals.

Weekly date-only price/NAV changes in TWD (no dividend adjustment).
All holdings required; no missing asset dropped or reweighted.
"""
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime
import numpy as np
import pandas as pd
from performance_coverage import quote,prepare_subscriptions
from performance_calendar import required_session,DOMESTIC_FUNDS

CONFIG=Path(__file__).resolve().parents[1]/"config/portfolio_risk_v34.json"
CASH="__TWD_CASH__"
BUCKETS={"global_equity","taiwan_equity","gold","cash","crypto"}
EPS=1e-8

class RiskBlocked(ValueError):
    pass

def mark(t,m,fx,d):
    """Strict scheduled session for known exchanges/funds; exact crypto day."""
    if m.get("error") or m.get("splits") is None or not m.get("instrument_id"):
        raise RiskBlocked("MARKET_IDENTITY_UNAVAILABLE")
    currency=m.get("currency");foreign=m.get("foreign")
    if (currency,foreign) not in (("USD",True),("TWD",False)):
        raise RiskBlocked("CURRENCY_UNVERIFIED")
    cal=m.get("calendar")
    if m.get("fund"):
        if t not in DOMESTIC_FUNDS or foreign:raise RiskBlocked("FUND_CALENDAR_UNVERIFIED")
        cal="XTAI"
    if cal not in ("XTAI","XNYS"):
        if cal is not None or m.get("bucket")!="crypto" or not foreign:
            raise RiskBlocked("UNSUPPORTED_MARKET_CALENDAR")
        cal=None
    if (cal=="XTAI" and foreign) or (cal=="XNYS" and not foreign):
        raise RiskBlocked("MARKET_CURRENCY_CONFLICT")
    p=quote(m.get("price"),d,0 if cal is None else 7,t,m.get("source","unknown"),calendar=cal)
    f=quote(fx,d,4,"USD/TWD","portfolio FX","FX") if foreign else 1.
    return p*f

def exposure(nav,tx,categories,market,captured,today=None):
    """Latest recorded NAV date, only completed prior-day marks.
    A valid automated record uses its original saved market values.
    Otherwise use a distinctly labelled ledger reconstruction; never fill NAV gap.
    """
    today=pd.Timestamp(datetime.now(ZoneInfo("Asia/Taipei")).date()) if today is None else pd.Timestamp(today)
    d=max(nav);cutoff=d-pd.Timedelta(days=1)
    if d>today:raise RiskBlocked("FUTURE_NAV")
    s=captured.get(str(d.date()))
    exact=bool(s and s.get("capture_mode")=="automated_completed_daily_marks" and
               s.get("quote_dates_verified") is True and not s.get("fallback_count"))
    earlier=[x for x in tx if x["date"]<=cutoff]
    if any(x["date"]==d for x in tx):raise RiskBlocked("SAME_DAY_LEDGER_NO_COMPLETED_MARK")
    lots,errors=prepare_subscriptions(earlier,market)
    vals={}
    for t,cat in categories.items():
        n=math.fsum(x["qty"] for x in earlier if x["ticker"]==t)
        if n< -EPS:raise RiskBlocked("NEGATIVE_INVENTORY")
        if n<=EPS:continue
        m=market["assets"].get(t,{})
        if t==CASH or t in market.get("quarantined",{}) or cat not in ("美股","台股","基金","加密貨幣"):
            raise RiskBlocked("UNVERIFIED_ACTIVE_INVENTORY")
        if t in errors or (t in lots and lots[t]["paid"]<=cutoff<lots[t]["switch"]):
            raise RiskBlocked("PENDING_OR_UNVERIFIED_SUBSCRIPTION")
        if m.get("error") or m.get("bucket") not in BUCKETS or m.get("splits") is None:
            raise RiskBlocked("ACTIVE_MARK_UNAVAILABLE")
        if any(x>cutoff for x in (m.get("split_ratios") or {})) or any(x>cutoff for x in m["splits"]):
            raise RiskBlocked("SPLIT_AFTER_CUTOFF")
        expected="USD" if cat in ("美股","加密貨幣") else "TWD"
        if m.get("currency")!=expected or m.get("foreign") is not (expected=="USD"):
            raise RiskBlocked("ACTIVE_CURRENCY_CONFLICT")
        if exact:
            h=s["holdings"].get(t)
            if not h or h["currency"]!=expected or abs(h["shares"]-n)>1e-5 or h.get("instrument_id")!=m.get("instrument_id"):
                raise RiskBlocked("CAPTURED_MARK_INVENTORY_MISMATCH")
            mv=float(h["market_value_twd"])
        else:mv=n*mark(t,m,market["fx"],cutoff)
        if not math.isfinite(mv) or mv<=0:raise RiskBlocked("INVALID_MARKET_VALUE")
        vals[t]={"ticker":t,"bucket":m["bucket"],"currency":expected,"market_value_twd":mv,
                 "source":"captured_daily_mark" if exact else m.get("source","unknown")}
    if exact and set(vals)!=set(s["holdings"]):raise RiskBlocked("CAPTURED_HOLDING_SET_MISMATCH")
    cash=float(s["cash_twd"]) if exact else math.fsum(x["flow"] for x in earlier)
    if cash<-.01 or not math.isfinite(cash):raise RiskBlocked("NEGATIVE_LEDGER_CASH")
    vals[CASH]={"ticker":CASH,"bucket":"cash","currency":"TWD","market_value_twd":max(0.,cash),"source":"ledger_cash"}
    total=math.fsum(v["market_value_twd"] for v in vals.values())
    if total<=0 or not math.isfinite(total):raise RiskBlocked("NONPOSITIVE_MODEL_NAV")
    for v in vals.values():v["weight"]=v["market_value_twd"]/total
    gap=float(nav[d]-total)
    warnings=["CASH_NOT_INDEPENDENTLY_VERIFIED","QUOTE_TIMESTAMPS_NOT_VERIFIED"]
    if not exact:warnings.append("RECONSTRUCTED_EXPOSURE")
    if abs(gap)/nav[d]>.01:warnings.append("NAV_GAP_ABOVE_1_PERCENT")
    if cash<0:warnings.append("MICRO_NEGATIVE_CASH_CLAMPED")
    later=sum(x["date"]>d for x in tx)
    if later:warnings.append("LATER_LEDGER_EVENTS_EXCLUDED")
    return {"as_of":str(d.date()),"cutoff":str(cutoff.date()),"basis":"VALID_AUTOMATED_CAPTURE" if exact else "RECONSTRUCTED_LEDGER",
            "model_nav_twd":total,"recorded_nav_twd":float(nav[d]),"nav_gap_twd":gap,"nav_gap_pct":gap/nav[d]*100,
            "later_ledger_events":later,"warnings":warnings,"holdings":list(vals.values())}

def common_marks(ex,market,d):
    result={}
    for h in ex["holdings"]:
        t=h["ticker"]
        result[t]=1. if t==CASH else mark(t,market["assets"][t],market["fx"],d)
    return result

def weekly_marks(ex,market,max_weeks=104):
    """Whole fixed seven-day observations. Record all holes; do not bridge."""
    end=pd.Timestamp(ex["cutoff"]);dates=pd.date_range(end-pd.Timedelta(weeks=max_weeks),end,freq="7D")
    rows=[];issues=[]
    for d in dates:
        try:rows.append({"date":d,**common_marks(ex,market,d)})
        except Exception:issues.append(str(d.date()))
    cols=[h["ticker"] for h in ex["holdings"]]
    frame=pd.DataFrame(rows).set_index("date").reindex(dates)[cols] if rows else pd.DataFrame(index=dates,columns=cols,dtype=float)
    # Missing row remains NaN on both adjacent returns.
    ret=frame.pct_change(fill_method=None).iloc[1:]
    valid=ret.dropna(how="any")
    if len(valid) and (not np.isfinite(valid.to_numpy()).all() or (valid<=-1).any().any()):
        raise RiskBlocked("INVALID_WEEKLY_RETURNS")
    start=len(ret)
    while start>0 and not ret.iloc[start-1].isna().any():start-=1
    latest=ret.iloc[start:]
    return frame,ret,latest,issues

def risk_contributions(returns,ex):
    cols=[h["ticker"] for h in ex["holdings"]]
    w=np.array([h["weight"] for h in ex["holdings"]],dtype=float)
    X=returns[cols].to_numpy(dtype=float);n=len(X)
    if n<26 or not np.isfinite(X).all() or not np.isclose(w.sum(),1.,atol=1e-10) or min(w)<0:
        raise RiskBlocked("INSUFFICIENT_OR_INVALID_SAMPLE")
    cov=np.atleast_2d(np.cov(X,rowvar=False,ddof=1))*52.
    var=float(w@cov@w)
    if not math.isfinite(var) or var<=1e-14:raise RiskBlocked("ZERO_OR_INVALID_VOLATILITY")
    vol=math.sqrt(var);marg=cov@w/vol;component=w*marg
    if not np.isclose(component.sum(),vol,atol=1e-10):raise RiskBlocked("EULER_IDENTITY_FAILED")
    standalone=np.sqrt(np.maximum(0.,np.diag(cov)))
    # Exact fractional empirical 5% lower tail; share boundary ties equally.
    tail=None
    if n>=52:
        losses=-(X@w);mass=.05*n
        boundary=np.sort(losses)[::-1][math.ceil(mass)-1]
        coeff=np.where(losses>boundary,1.,0.)
        ties=losses==boundary
        coeff[ties]=(mass-coeff.sum())/ties.sum()
        if not np.isclose(coeff.sum(),mass):raise RiskBlocked("TAIL_MASS_IDENTITY_FAILED")
        tail_asset=-(coeff@X)/mass
        tail_components=w*tail_asset;es=float(coeff@losses/mass)
        if not np.isclose(tail_components.sum(),es,atol=1e-10):raise RiskBlocked("ES_IDENTITY_FAILED")
        tail={"var95_loss_pct":float(boundary*100),"es95_loss_pct":es*100,"effective_tail_observations":mass,
              "components":tail_components,"marginal":tail_asset}
    rows=[];groups={}
    for i,h in enumerate(ex["holdings"]):
        r={"ticker":h["ticker"],"bucket":h["bucket"],"weight_pct":w[i]*100,"standalone_ann_vol_pct":standalone[i]*100,
           "marginal_vol_pp_per_1pp_weight":marg[i],"component_ann_vol_pp":component[i]*100,"risk_share_pct":component[i]/vol*100,
           "es95_component_loss_pp":float(tail["components"][i]*100) if tail else None,
           "es95_marginal_loss_pp_per_1pp_weight":float(tail["marginal"][i]) if tail else None}
        rows.append(r)
        g=groups.setdefault(h["bucket"],{"bucket":h["bucket"],"weight_pct":0.,"component_ann_vol_pp":0.,"risk_share_pct":0.,"es95_component_loss_pp":0. if tail else None})
        for k in ("weight_pct","component_ann_vol_pp","risk_share_pct"):g[k]+=r[k]
        if tail:g["es95_component_loss_pp"]+=r["es95_component_loss_pp"]
    return {"status":"RESEARCH_ONLY","start":str((returns.index[0]-pd.Timedelta(days=7)).date()),"end":str(returns.index[-1].date()),
            "observations":n,"asset_count":len(cols),"annualized_vol_pct":vol*100,"diversification_ratio":float(w@standalone/vol),
            "identity_error_pp":float((component.sum()-vol)*100),"rows":sorted(rows,key=lambda r:r["risk_share_pct"],reverse=True),
            "groups":sorted(groups.values(),key=lambda r:r["risk_share_pct"],reverse=True),
            "tail":{k:v for k,v in tail.items() if k not in ("components","marginal")} if tail else None,
            "warnings":["SMALL_SAMPLE_COVARIANCE"] if n<52 or n<=2*len(cols) else []}

def result_for_returns(ex,returns):
    """Unlevered accounting identity; returns are shocked instrument prices."""
    rows=[]
    for h in ex["holdings"]:
        r=float(returns[h["ticker"]])
        if not math.isfinite(r) or r< -1:raise RiskBlocked("INVALID_SCENARIO_RETURN")
        rows.append({"ticker":h["ticker"],"bucket":h["bucket"],"weight_pct":h["weight"]*100,
                     "return_pct":r*100,"contribution_pp":h["weight"]*r*100,"pnl_twd":h["market_value_twd"]*r})
    pnl=math.fsum(r["pnl_twd"] for r in rows)
    pct=pnl/ex["model_nav_twd"]*100
    if not math.isclose(pct,math.fsum(r["contribution_pp"] for r in rows),abs_tol=1e-9):raise RiskBlocked("STRESS_IDENTITY_FAILED")
    return {"return_pct":pct,"pnl_twd":pnl,"stressed_model_nav_twd":ex["model_nav_twd"]+pnl,
            "rows":sorted(rows,key=lambda r:r["pnl_twd"])}

def hypothetical(ex,scenario):
    shocks=scenario["local_price_shocks"];overrides=scenario.get("ticker_overrides",{})
    if set(shocks)!=BUCKETS or any(not math.isfinite(float(v)) or float(v)<-1 for v in [*shocks.values(),*overrides.values()]):
        raise RiskBlocked("INVALID_SHOCK_CONFIGURATION")
    fx=float(scenario["usd_twd_shock"])
    if not math.isfinite(fx) or fx<=-1:raise RiskBlocked("INVALID_FX_SHOCK")
    returns={}
    for h in ex["holdings"]:
        t=h["ticker"]
        p=0. if t==CASH else float(overrides.get(t,shocks[h["bucket"]]))
        f=fx if h["currency"]=="USD" else 0.
        returns[t]=(1+p)*(1+f)-1
    return {"id":scenario["id"],"label":scenario["label"],"status":"HYPOTHETICAL",
            "local_price_shocks":shocks,"usd_twd_shock":fx,"ticker_overrides":overrides,**result_for_returns(ex,returns)}

def historical(ex,frame,weeks):
    # Fixed current shares and cash, compounded instrument endpoint ratios.
    # Require every weekly mark inside the shock window; no gap stitching.
    worst=None;count=0
    for i in range(weeks,len(frame)):
        block=frame.iloc[i-weeks:i+1]
        if block.isna().any().any():continue
        rets=(block.iloc[-1]/block.iloc[0]-1).to_dict()
        r=result_for_returns(ex,rets);count+=1
        if worst is None or r["return_pct"]<worst["return_pct"]:
            worst={"start":str(block.index[0].date()),"end":str(block.index[-1].date()),**r}
    return {"weeks":weeks,"candidate_windows":count,"status":"REPLAY" if worst else "UNAVAILABLE","worst":worst}

def event_replay(ex,market,event):
    a,b=pd.Timestamp(event["start"]),pd.Timestamp(event["end"])
    out={**event,"status":"UNAVAILABLE"}
    if a>=b or b>pd.Timestamp(ex["cutoff"]):return out
    try:
        first=common_marks(ex,market,a);last=common_marks(ex,market,b)
        r=result_for_returns(ex,{t:last[t]/first[t]-1 for t in first})
        out.update(status="REPLAY",**r)
    except Exception:out["reason"]="Required endpoint marks unavailable; no proxy substitution"
    return out

def build_portfolio_risk(nav,tx,categories,market,captured,config=None,today=None):
    out={"version":"v3.3/v3.4","status":"BLOCKED","execution_permission":False,"risk_windows":{},"hypothetical":[],"historical":[],"events":[],
         "notes":["Exposure as of latest recorded NAV with completed prior-day marks; not live prices. Reconstructed NAV gap remains unexplained, never assigned to cash.",
                  "All holding weights use model NAV including recorded TWD cash. No renormalization of surviving subset, no dividend additions.",
                  "Weekly unadjusted price/NAV proxy returns translated to TWD; known exchange sessions, supported domestic funds assume XTAI schedule, crypto exact UTC date, FX last <=4 days. Not synchronized quotes.",
                  "Volatility annualized by sqrt(52), Euler marginal and component contributions; signed components may be negative. Marginal is local derivative for +1pp weight before funding, not trade advice.",
                  "Historical ES/VaR 95% use weekly empirical losses, not forecasts; at least 52 observations with a small tail. Cash is held constant in TWD.",
                  "Stress tests apply illustrative local instrument price shocks and USD/TWD shock multiplicatively; not underlying-index beta, leverage, duration or liquidity model. No implied scenario probability.",
                  "Historical replay applies today's as-of weights to past instrument marks, not actual historical holdings or realized portfolio returns. No proxy fills, no cross-gap rolling windows."]}
    try:
        config=config or json.loads(CONFIG.read_text())
        ex=exposure(nav,tx,categories,market,captured,today)
        out["exposure"]=ex
    except Exception as e:
        out["reason"]=str(e)[:160] if isinstance(e,RiskBlocked) else "EXPOSURE_MARK_OR_SOURCE_VALIDATION_FAILED"
        return out
    # Keep scenarios useful even when weekly covariance history is insufficient.
    for s in config["scenarios"]:
        try:out["hypothetical"].append(hypothetical(ex,s))
        except Exception:out["hypothetical"].append({"id":s.get("id"),"label":s.get("label"),"status":"UNAVAILABLE"})
    for e in config["events"]:out["events"].append(event_replay(ex,market,e))
    try:
        frame,ret,latest,issues=weekly_marks(ex,market,int(config["history_weeks"]))
        out["coverage"]={"expected_weeks":len(ret),"valid_weeks":len(ret.dropna()),"latest_contiguous_weeks":len(latest),
                         "missing_mark_dates":issues}
        for n in (26,52,104):
            if len(latest)<n:out["risk_windows"][str(n)]={"status":"INSUFFICIENT_SAMPLE","available":len(latest),"required":n}
            else:
                try:out["risk_windows"][str(n)]=risk_contributions(latest.iloc[-n:],ex)
                except RiskBlocked as e:out["risk_windows"][str(n)]={"status":"UNAVAILABLE","reason":str(e)}
        out["historical"]=[historical(ex,frame,n) for n in (1,4)]
    except Exception:out["coverage"]={"status":"UNAVAILABLE","reason":"Common weekly marks failed"}
    out["status"]="RESEARCH_ONLY" if any(r["status"]=="RESEARCH_ONLY" for r in out["risk_windows"].values()) else "PARTIAL_RESEARCH_ONLY"
    return out
