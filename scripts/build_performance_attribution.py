"""Private actual performance attribution. No public portfolio artifacts."""
from __future__ import annotations
import io
import json
import math
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

FACTORS = ["Mkt-RF","SMB","HML","RMW","CMA","Mom","TW_Mkt_RF","Crypto_RF"]
WINDOWS = {"1W":7,"1M":30,"3M":91,"YTD":None,"12M":365,"SI":None}
EPS=1e-8
ENGINE_VERSION='v2.2-historical-bf'


def number(x):
    if isinstance(x,bool):
        raise ValueError("Boolean numeric value")
    v=float(x)
    if not math.isfinite(v):
        raise ValueError("Nonfinite value")
    return v


def day(x):
    t=pd.Timestamp(x)
    if pd.isna(t):
        raise ValueError("Invalid date")
    return t.tz_localize(None).normalize()


def parse_inputs(row):
    nav={}
    for h in row.get("history_data") or []:
        d=day(h["date"]); v=number(h["assets"])
        if v<=0 or d in nav:
            raise ValueError("Nonpositive NAV or duplicate snapshot date")
        nav[d]=v
    if len(nav)<2:
        raise ValueError("Need two valid NAV snapshots")
    tx=[]
    categories={}
    for x in row.get("ledger_data") or []:
        t=str(x["type"]).strip().lower()
        d=day(x["date"])
        flow=number(x["totalCashFlow"])
        ticker=str(x.get("ticker") or "").strip().upper()
        q=0.
        if t in ("buy","sell"):
            q=number(x["shares"])
            if not ticker or q<=0 or (t=="buy" and flow>=0) or (t=="sell" and flow<=0):
                raise ValueError("Invalid trade quantity or cash-flow sign")
            q=q if t=="buy" else -q
            cat=str(x.get("category") or "")
            if ticker in categories and categories[ticker]!=cat:
                categories[ticker]="__AMBIGUOUS__"
            else:
                categories[ticker]=cat
        elif t in ("deposit","withdraw"):
            if (t=="deposit" and flow<0) or (t=="withdraw" and flow>0):
                raise ValueError("Invalid external flow sign")
        tx.append({"date":d,"type":t,"ticker":ticker,"qty":q,"flow":flow,"category":str(x.get("category") or "")})
    return dict(sorted(nav.items())),sorted(tx,key=lambda x:x["date"]),categories


def close(series,d,max_age=7):
    if series is None or series.empty:
        raise ValueError("Missing price or FX series")
    x=series.loc[:d]
    if x.empty or (d-x.index[-1]).days>max_age:
        raise ValueError("Missing or stale valuation")
    v=number(x.iloc[-1])
    if v<=0: raise ValueError("Nonpositive valuation")
    return v


def split_leg(q,p0,f0,p1,f1):
    # Exact algebra for each signed holding / trade leg.
    return np.array([q*(p1-p0)*f0,q*p0*(f1-f0),q*(p1-p0)*(f1-f0)],dtype=float)


def asset_pnl(ticker,transactions,start,end,price,fx,foreign,splits):
    relevant=[x for x in transactions if x["ticker"]==ticker and x["qty"]!=0 and x["date"]<=end]
    opening=sum(x["qty"] for x in relevant if x["date"]<=start)
    trades=[x for x in relevant if start<x["date"]<=end]
    closing=opening+sum(x["qty"] for x in trades)
    if abs(opening)<EPS and not trades: return None
    if opening < -EPS or closing < -EPS:
        raise ValueError("Negative reconstructed holding")
    trades=[{"date":d,"qty":math.fsum(x["qty"] for x in trades if x["date"]==d),
             "flow":math.fsum(x["flow"] for x in trades if x["date"]==d)} for d in sorted({x["date"] for x in trades})]
    running=opening
    for x in trades:
        running+=x["qty"]
        if running < -EPS: raise ValueError("Negative reconstructed holding during period")
    # Yahoo historical Close is split-normalized. Without ledger split basis
    # metadata, decline any valuation before a subsequent split.
    if splits is None:
        raise ValueError("Corporate-action history unavailable")
    if any(d>start for d in splits):
        raise ValueError("Split-adjusted quantity basis unverified")
    def rate(d): return close(fx,d) if foreign else 1.
    p0=close(price,start) if abs(opening)>=EPS else None
    f0=rate(start) if abs(opening)>=EPS else 1.
    # Fully sold assets still need no closing quote: each held segment ends
    # at its trade-date mark. Use mark-to-market between consecutive trades.
    q=opening; mark_date=start; mark=p0; fmark=f0
    parts=np.zeros(3); execution=0.
    for x in trades:
        d=x["date"]; p=close(price,d); f=rate(d)
        if abs(q)>=EPS:
            parts+=split_leg(q,mark,fmark,p,f)
        # Actual TWD cash flow minus change in marked asset value.
        execution+=x["flow"]+x["qty"]*p*f
        q+=x["qty"]; mark_date=d; mark=p; fmark=f
    if abs(q)>=EPS:
        p1=close(price,end); f1=rate(end)
        parts+=split_leg(q,mark,fmark,p1,f1)
    else:
        p1=0.; f1=1.
    start_mv=opening*(p0 or 0.)*f0
    end_mv=q*p1*f1
    exact=end_mv-start_mv+sum(x["flow"] for x in trades)
    error=float(parts.sum()+execution-exact)
    if abs(error)>max(1e-5,abs(exact)*1e-10):
        raise ValueError("Asset P&L identity failed")
    return {"ticker":ticker,"opening_mv_twd":start_mv,"closing_mv_twd":end_mv,
            "opening_shares":opening,"closing_shares":q,"price_twd":float(parts[0]),
            "fx_twd":float(parts[1]),"interaction_twd":float(parts[2]),
            "execution_vs_close_twd":execution,"pnl_twd":exact,"identity_error_twd":error}


def window_pnl(nav,tx,categories,market,start,end):
    flows=[x for x in tx if start<x["date"]<=end]
    external=sum(x["flow"] for x in flows if x["type"] in ("deposit","withdraw"))
    total=nav[end]-nav[start]-external
    rows=[]; missing=[]; historical_issues=[]
    for t,cat in sorted(categories.items()):
        rel=[x for x in tx if x["ticker"]==t and x["qty"]!=0 and x["date"]<=end]
        opening=sum(x["qty"] for x in rel if x["date"]<=start)
        if t in market.get("quarantined",{}):
            active=any(x["date"]>start for x in rel)
            if abs(opening)>=EPS or active:
                missing.append({"ticker":t,"reason":market["quarantined"][t],"historical_only_no_window_trades":not active})
                if not active: historical_issues.append(t)
            continue
        if abs(opening)<EPS and not any(x["date"]>start for x in rel): continue
        try:
            m=market["assets"][t]
            if m.get("error"): raise ValueError(m["error"])
            try:
                r=asset_pnl(t,tx,start,end,m["price"],market["fx"],m["foreign"],m["splits"])
            except ValueError as exc:
                if "Missing" not in str(exc) and "stale" not in str(exc):raise
                # Endpoint-only total P&L remains mathematically identifiable
                # even when intra-period marks are missing (e.g. fund NAV).
                if m["splits"] is None or any(d>start for d in m["splits"]):raise
                trades=[x for x in rel if x["date"]>start]
                closing=opening+sum(x["qty"] for x in trades)
                if min(opening,closing)<-EPS:raise
                def mv(q,d):
                    return q*close(m["price"],d)*(close(market["fx"],d) if m["foreign"] else 1.) if abs(q)>=EPS else 0.
                v0,v1=mv(opening,start),mv(closing,end)
                exact=v1-v0+math.fsum(x["flow"] for x in trades)
                r={"ticker":t,"opening_mv_twd":v0,"closing_mv_twd":v1,"opening_shares":opening,"closing_shares":closing,
                   "pnl_twd":exact,"price_twd":None,"fx_twd":None,"interaction_twd":None,"execution_vs_close_twd":None,
                   "unallocated_pnl_twd":exact,"identity_error_twd":0.,"decomposition_status":"ENDPOINT_ONLY","reason":str(exc)}
            if r is not None:
                r["bucket"]=m["bucket"];r["source"]=m["source"];rows.append(r)
        except Exception as exc:
            missing.append({"ticker":t,"reason":str(exc)[:180]})
    # Explicit non-trade, non-external ledger flows only. Do not infer
    # dividends or fees from unexplained NAV changes.
    explicit=sum(x["flow"] for x in flows if x["type"] not in ("deposit","withdraw","buy","sell"))
    asset_total=math.fsum(r["pnl_twd"] for r in rows)
    residual=total-asset_total-explicit
    denom=nav[start]+sum(x["flow"]*(end-x["date"]).days/(end-start).days for x in flows if x["type"] in ("deposit","withdraw"))
    groups={}
    for r in rows: groups[r["bucket"]]=groups.get(r["bucket"],0.)+r["pnl_twd"]
    partial_decomposition=[r["ticker"] for r in rows if r.get("decomposition_status")=="ENDPOINT_ONLY"]
    return {"status":"PARTIAL" if missing or abs(residual)>max(10.,abs(nav[start])*.001) else "RECONCILED_WITH_RESIDUAL",
        "historical_issues_no_window_trades":historical_issues,"partial_decomposition":partial_decomposition,
        "unallocated_pnl_twd":math.fsum(r.get("unallocated_pnl_twd",0.) for r in rows),
        "start":str(start.date()),"end":str(end.date()),"start_nav_twd":nav[start],"end_nav_twd":nav[end],
        "external_flow_twd":external,"actual_pnl_twd":total,"asset_pnl_twd":asset_total,
        "explicit_other_cashflow_twd":explicit,"unexplained_twd":residual,
        "dietz_return_pct":total/denom*100 if denom>0 else None,
        "price_twd":math.fsum(r["price_twd"] for r in rows if r["price_twd"] is not None),
        "fx_twd":math.fsum(r["fx_twd"] for r in rows if r["fx_twd"] is not None),
        "interaction_twd":math.fsum(r["interaction_twd"] for r in rows if r["interaction_twd"] is not None),
        "execution_vs_close_twd":math.fsum(r["execution_vs_close_twd"] for r in rows if r["execution_vs_close_twd"] is not None),
        "bucket_pnl_twd":groups,"rows":sorted(rows,key=lambda x:x["pnl_twd"]),
        "missing":missing,"reconciliation_error_twd":total-asset_total-explicit-residual}


def windows_for(dates):
    end=dates[-1]
    for label,n in WINDOWS.items():
        target=(pd.Timestamp(end.year,1,1) if label=="YTD" else
                dates[0] if label=="SI" else end-pd.Timedelta(days=n))
        candidates=[d for d in dates[:-1] if d<=target]
        if candidates:
            yield label,candidates[-1],end


def load_market(categories,earliest):
    import update_stock_meta as q
    from jensen_alpha import fetch_yahoo_chart_close
    from performance_market_data import series,load_asset,yahoo_chart
    days=max(60,(pd.Timestamp.now().normalize()-earliest).days+15)
    try: fx=series(fetch_yahoo_chart_close("TWD=X",days=days))
    except Exception:
        try:
            fx,_,currency=yahoo_chart("TWD=X",earliest)
            if currency!="TWD":raise ValueError("FX currency mismatch")
        except Exception:fx=pd.Series(dtype=float)
    out={}
    for t,cat in categories.items():
        try:out[t]=load_asset(t,cat,earliest,q)
        except Exception as exc:out[t]={"error":str(exc)[:180]}
    return {"assets":out,"fx":fx}


def french_csv(content):
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        lines=z.read(z.namelist()[0]).decode("utf-8",errors="replace").splitlines()
    first=next(i for i,l in enumerate(lines) if l.split(",")[0].strip().isdigit() and len(l.split(",")[0].strip())==8)
    header=lines[first-1].strip()
    data=[]
    for l in lines[first:]:
        if not l.split(",")[0].strip().isdigit() or len(l.split(",")[0].strip())!=8: break
        data.append(l)
    df=pd.read_csv(io.StringIO("\n".join([header]+data)),index_col=0)
    df.index=pd.to_datetime(df.index.astype(str).str.strip(),format="%Y%m%d")
    df.columns=df.columns.str.strip()
    df=df.apply(pd.to_numeric,errors="coerce").replace([-99.99,-999.,-999.99],np.nan)/100.
    return df.sort_index()


def load_factors(earliest):
    import requests
    from jensen_alpha import fetch_yahoo_chart_close
    base="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    def fetch(name):
        r=requests.get(base+name,timeout=40,headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status();return french_csv(r.content)
    ff=fetch("F-F_Research_Data_5_Factors_2x3_daily_CSV.zip")
    mom=fetch("F-F_Momentum_Factor_daily_CSV.zip")
    factors=ff.join(mom[["Mom"]],how="inner").dropna()
    days=max(60,(pd.Timestamp.now().normalize()-earliest).days+15)
    def px(symbol):
        s=fetch_yahoo_chart_close(symbol,days=days)
        s.index=s.index.normalize()
        return s[~s.index.duplicated(keep="last")].sort_index()
    return factors,px("^TWII"),px("BTC-USD")


def factor_periods(nav,tx,fx,ff,tw,btc):
    rows=[]; skipped=[]
    for start,end in zip(list(nav)[:-1],list(nav)[1:]):
        try:
            days=(end-start).days
            if not 1<=days<=31: raise ValueError("NAV interval outside 1–31 day model limit")
            # Do not fill unpublished French observations with zero. Weekly
            # source must cover end, allowing weekend/holiday lag only.
            if end>ff.index[-1]+pd.Timedelta(days=3) or start<ff.index[0]:
                raise ValueError("French factors not published for full interval")
            f=ff.loc[(ff.index>start)&(ff.index<=end)]
            weekdays=len(pd.bdate_range(start+pd.Timedelta(days=1),end))
            # Holiday-aware proxy: published observations must span the interval.
            # No zero imputation; exclude weekend-only / insufficient coverage.
            if f.empty or len(f)<max(1,math.ceil(.60*weekdays)) or (end-f.index[-1]).days>3 or (f.index[0]-start).days>4:
                raise ValueError("Factor interval incomplete")
            if len(f)>1 and f.index.to_series().diff().dropna().dt.days.max()>4:
                raise ValueError("Internal factor date gap")
            vals=(1+f).prod()-1
            x0=close(fx,start,4);x1=close(fx,end,4);fxr=x1/x0-1
            twr=(close(tw,end,5)/x1)/(close(tw,start,5)/x0)-1
            br=close(btc,end,2)/close(btc,start,2)-1
            ext=[x for x in tx if x["type"] in ("deposit","withdraw") and start<x["date"]<=end]
            weights=[(end-x["date"]).days/days for x in ext]
            usd=[x["flow"]/close(fx,x["date"],4) for x in ext]
            td=nav[start]+sum(x["flow"]*w for x,w in zip(ext,weights))
            ud=nav[start]/x0+sum(v*w for v,w in zip(usd,weights))
            if td<=0 or ud<=0: raise ValueError("Invalid Dietz denominator")
            rt=(nav[end]-nav[start]-sum(x["flow"] for x in ext))/td
            ru=(nav[end]/x1-nav[start]/x0-sum(usd))/ud
            if min(rt,ru)<=-1: raise ValueError("Return <= -100%")
            row={"start":start,"end":end,"duration_weeks":days/7.,"twd":rt,"usd":ru,"fx":fxr,"RF":float(vals["RF"]),
                 **{k:float(vals[k]) for k in FACTORS[:6]},
                 "TW_Mkt_RF":twr-float(vals["RF"]),"Crypto_RF":br-float(vals["RF"])}
            if not all(math.isfinite(v) for k,v in row.items() if k not in ("start","end")):
                raise ValueError("Nonfinite factor")
            rows.append(row)
        except Exception as exc:
            skipped.append({"start":str(start.date()),"end":str(end.date()),"reason":str(exc)[:180]})
    return pd.DataFrame(rows),skipped


def carino(returns,contributions):
    r=np.asarray(returns,dtype=float); c=np.asarray(contributions,dtype=float)
    if r.ndim!=1 or c.ndim!=2 or len(r)!=len(c) or not len(r) or np.any(r<=-1) or not np.isfinite(r).all() or not np.isfinite(c).all():
        raise ValueError("Invalid linking inputs")
    if not np.allclose(c.sum(axis=1),r,rtol=1e-9,atol=1e-10):
        raise ValueError("Period contributions do not reconcile")
    log=np.log1p(r); total=float(np.expm1(log.sum()))
    k=np.divide(log,r,out=np.ones_like(r),where=np.abs(r)>1e-12)
    K=float(np.log1p(total)/total) if abs(total)>1e-12 else 1.
    linked=(c*k[:,None]).sum(axis=0)/K
    if not np.isclose(linked.sum(),total,rtol=1e-9,atol=1e-10):
        raise ValueError("Carino reconciliation failed")
    return total,linked


def factor_report(periods,skipped,nav):
    import statsmodels.api as sm
    out={"status":"INSUFFICIENT_SAMPLE","sample_count":len(periods),"skipped":skipped,
         "model":"FF5 + Momentum + TW USD excess + Crypto USD excess","method":"actual_NAV_Modified_Dietz_USD_in_sample_HAC",
         "windows":{},"coverage":{"expected_intervals":len(nav)-1,"available_intervals":len(periods),
             "coverage_pct":len(periods)/max(1,len(nav)-1)*100,
             "nav_latest":str(max(nav).date()),"latest_factor_interval":str(periods["end"].max().date()) if len(periods) else None,
             "lag_days":int((max(nav)-periods["end"].max()).days) if len(periods) else None,
             "irregular_intervals":int(((periods["end"]-periods["start"]).dt.days!=7).sum()) if len(periods) else 0}}
    # 8 factors plus intercept: minimum 52 intervals, full rank required.
    if len(periods)<52:return out
    p=periods.sort_values("end").reset_index(drop=True)
    p["duration_weeks"]=(p["end"]-p["start"]).dt.days/7.
    X=p[["duration_weeks"]+FACTORS]
    if np.linalg.matrix_rank(X.to_numpy())<len(FACTORS)+1:
        out["status"]="RANK_DEFICIENT";return out
    fit=sm.OLS(p["usd"]-p["RF"],X).fit(cov_type="HAC",cov_kwds={"maxlags":4,"use_correction":True})
    names=["RF","Alpha"]+FACTORS+["Residual","FX","Dietz_currency_bridge"]
    # Translate each USD contribution to TWD including FX interaction.
    usd=np.column_stack([p["RF"],p["duration_weeks"].to_numpy()*fit.params["duration_weeks"],
                         p[FACTORS].to_numpy()*fit.params[FACTORS].to_numpy(),fit.resid])
    fx=p["fx"].to_numpy();ru=p["usd"].to_numpy();rt=p["twd"].to_numpy()
    c=np.column_stack([usd*(1+fx[:,None]),fx,rt-((1+ru)*(1+fx)-1)])
    # Use only latest contiguous covered periods; never bridge skipped weeks.
    j=len(p)-1
    while j>0 and p.loc[j,"start"]==p.loc[j-1,"end"]:j-=1
    suffix=p.iloc[j:]
    dates=[suffix.iloc[0]["start"]]+list(suffix["end"])
    for label,start,end in windows_for(dates):
        if label=="SI" and start!=next(iter(nav)):continue
        ids=np.flatnonzero((p["start"]>=start)&(p["end"]<=end))
        total,linked=carino(rt[ids],c[ids])
        out["windows"][label]={"start":str(start.date()),"end":str(end.date()),"period_count":len(ids),
            "total_return_pct":total*100,"contributions_pp":dict(zip(names,(linked*100).tolist())),
            "reconciliation_error_pp":float((linked.sum()-total)*100)}
    out.update(status="OK",start=str(p.iloc[0]["start"].date()),end=str(p.iloc[-1]["end"].date()),
               nav_latest=str(list(nav)[-1].date()),r_squared=float(fit.rsquared),
               alpha_weekly_pct=float(fit.params["duration_weeks"]*100),alpha_hac_pvalue=float(fit.pvalues["duration_weeks"]),
               beta={k:float(fit.params[k]) for k in FACTORS},
               notes=["Retrospective in-sample fit; not an investable or out-of-sample alpha estimate.",
                      "Daily French factor spreads compounded to actual NAV intervals (approximation); intercept scaled by duration in weeks; HAC lags are observation-based.",
                      "USD Dietz converts external flows on their own dates; FX interaction allocated proportionately to USD components.",
                      "Dietz currency bridge retained explicitly; latest factor period may lag latest NAV.",
                      "Carino links only contiguous covered periods."])
    return out


def clean_json(x):
    if isinstance(x,dict): return {k:clean_json(v) for k,v in x.items()}
    if isinstance(x,list): return [clean_json(v) for v in x]
    if isinstance(x,(np.floating,float)):return float(x) if math.isfinite(float(x)) else None
    if isinstance(x,np.integer):return int(x)
    return x


def build(row,market=None,factor_data=None):
    nav,tx,categories=parse_inputs(row)
    from performance_data_quality import reconcile_transactions,cash_reconciliation
    earliest=min(nav)
    earliest_trade=min([x["date"] for x in tx]+[earliest])
    market=load_market(categories,earliest_trade) if market is None else market
    # Copy metadata only; no mutation of raw ledger, NAV or source prices.
    market={**market,"assets":{t:dict(m) for t,m in market["assets"].items()}}
    adjusted,diagnostics,quarantined=reconcile_transactions(tx,categories,market,close)
    market["quarantined"]=quarantined
    pnl={label:window_pnl(nav,adjusted,categories,market,start,end) for label,start,end in windows_for(list(nav))}
    from performance_pit_nav import build_pit
    pit, captured=build_pit(row.get("history_data") or [],tx,nav,pnl)
    from performance_brinson import build_brinson
    try:brinson=build_brinson(captured,tx,nav)
    except Exception as exc:brinson={"status":"UNAVAILABLE","reason":str(exc)[:180],"periods":[]}
    from performance_brinson_historical import build_historical
    try:historical_brinson=build_historical(nav,adjusted,categories,market)
    except Exception as exc:historical_brinson={"status":"UNAVAILABLE","reason":str(exc)[:180],"periods":[]}
    quality={"version":"v1.1","inventory":diagnostics,"quarantined_count":len(quarantined),
             "cash_reconciliation":cash_reconciliation(nav,tx,pnl),
             "notes":["Unknown opening cash balance; cumulative ledger flows are not an independently observed bank balance.",
                      "Split normalization is an inferred diagnostic, never a ledger edit. Ambiguous cases remain quarantined.",
                      "Negative historical inventory with no current-period trades is flagged separately, not silently assigned zero exposure."]}
    try:
        ff,tw,btc=load_factors(earliest) if factor_data is None else factor_data
        periods,skipped=factor_periods(nav,tx,market["fx"],ff,tw,btc)
        factor=factor_report(periods,skipped,nav)
        factor["coverage"]["french_latest"]=str(ff.index.max().date())
        factor["coverage"]["lag_warning"]=factor["coverage"]["lag_days"] is None or factor["coverage"]["lag_days"]>7
        from performance_rolling_factor import rolling_report
        try:rolling=rolling_report(periods,nav,FACTORS,carino,windows_for)
        except Exception as exc:rolling={"status":"UNAVAILABLE","reason":str(exc)[:200],"rows":[],"windows":{}}
    except Exception as exc:
        factor={"status":"UNAVAILABLE","reason":str(exc)[:200],"windows":{}}
        rolling={"status":"UNAVAILABLE","reason":str(exc)[:200],"rows":[],"windows":{}}
    return clean_json({"version":"v1.0","engine_version":ENGINE_VERSION,"quality":quality,"point_in_time":pit,"brinson":brinson,"historical_brinson":historical_brinson,"generated_at":datetime.now(timezone.utc).isoformat(),
        "nav_as_of":str(list(nav)[-1].date()),"ledger_count":len(tx),"history_count":len(nav),
        "pnl":pnl,"factor":factor,"rolling_factor":rolling,"execution_permission":False,
        "notes":["NAV and external flows are recorded data; per-asset P&L is reconstructed, not broker-certified.",
                 "Date-only ledger uses end-of-date marks and (start,end] trade convention. Local closing dates may not match NAV timestamp.",
                 "Prices exclude dividend adjustment; unrecorded dividends, fees, split basis, valuation and data gaps remain unexplained.",
                 "Execution vs close includes intraday movement, fees and FX execution differences; not a pure fee estimate.",
                 "Deposits and withdrawals follow the recorded classification. No inferred dividend or spending reclassification."]})


def refresh_reason(row, now=None):
    """Skip intact fresh reports; trigger clears them on any source edit."""
    now = now or datetime.now(timezone.utc)
    report = row.get("performance_attribution")
    if not isinstance(report, dict) or report.get("version") != "v1.0" or report.get("engine_version") != ENGINE_VERSION:
        return "missing_or_invalidated"
    try:
        nav, tx, _ = parse_inputs(row)
        if (report.get("nav_as_of") != str(max(nav).date())
                or report.get("ledger_count") != len(tx)
                or report.get("history_count") != len(nav)
                or not isinstance(report.get("pnl"), dict) or not report["pnl"]):
            return "source_mismatch"
        stamp = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return "invalid_report_timestamp"
        age = (now - stamp).total_seconds()
        if age < 0:
            return "invalid_report_timestamp"
        # A weekly refresh catches delayed/revised factors and prices even
        # without a new NAV. Failed factor downloads retry on the next check.
        factor = report.get("factor")
        if not isinstance(factor, dict) or factor.get("status") == "UNAVAILABLE":
            if age >= 86400:
                return "retry_factor_source"
        if age >= 7 * 86400:
            return "weekly_source_refresh"
        return None
    except (KeyError, TypeError, ValueError, OverflowError):
        return "invalid_report_metadata"


def main():
    if not os.getenv("SUPABASE_SECRET_KEY") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        os.environ["SUPABASE_SECRET_KEY"]=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    import update_stock_meta as q
    client=q.connect_supabase()
    row=q.fetch_portfolio_row(client)
    if os.getenv("ATTRIBUTION_IF_STALE", "false").lower() == "true":
        reason = refresh_reason(row)
        if reason is None:
            print("PERFORMANCE_ATTRIBUTION_SKIPPED current report is fresh")
            return
        print("PERFORMANCE_ATTRIBUTION_REFRESH", reason)
    report=build(row)
    json.dumps(report,allow_nan=False)
    result=client.rpc("publish_performance_attribution",{"p_row_id":int(q.PORTFOLIO_ROW_ID),
        "p_ledger":row["ledger_data"],"p_history":row["history_data"],"p_report":report}).execute()
    if result.data is not True:
        raise RuntimeError("Publish refused: source data changed or row unavailable")
    # Verify status without printing private financial values.
    v=client.table(q.SUPABASE_TABLE).select("performance_attribution").eq("id",int(q.PORTFOLIO_ROW_ID)).single().execute()
    if v.data.get("performance_attribution")!=report:
        raise RuntimeError("Read-back differs from published report")
    print("PERFORMANCE_ATTRIBUTION_OK",report["nav_as_of"],len(report["pnl"]),report["factor"]["status"])


if __name__=="__main__":
    main()
