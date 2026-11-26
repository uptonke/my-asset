"""Brinson-Fachler, research benchmark, captured marks only, no-flow periods."""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

CONFIG=Path(__file__).resolve().parents[1]/"config/attribution_benchmark.json"

def bucket(t,category):
    if t in ("BOXX","SHV","BIL","SGOV","CASH"):return "cash"
    if t in ("GLDM","GLD","IAU"):return "gold"
    if category=="加密貨幣":return "crypto"
    if category in ("台股","基金"):return "taiwan_equity"
    if category=="美股":return "global_equity"
    raise ValueError("Unknown instrument category: "+category)

def effects(wp,rp,wb,rb):
    if not all(np.isfinite(x).all() for x in (wp,rp,wb,rb)) or min(wp.min(),wb.min())<0 or not np.isclose(wp.sum(),1) or not np.isclose(wb.sum(),1):
        raise ValueError("Invalid weights or returns")
    Rb=float(wb@rb);Rp=float(wp@rp)
    allocation=(wp-wb)*(rb-Rb)
    selection=wb*(rp-rb)
    interaction=(wp-wb)*(rp-rb)
    if not np.isclose((allocation+selection+interaction).sum(),Rp-Rb,atol=1e-10):
        raise ValueError("BF identity mismatch")
    return Rp,Rb,allocation,selection,interaction

def benchmark_prices(config,earliest):
    from performance_market_data import yahoo_chart
    data={}
    for g,symbol in config["proxies"].items():
        px,_,currency=yahoo_chart(symbol,earliest)
        if currency!=config["currency"][g]:raise ValueError("Benchmark currency mismatch")
        data[g]=px
    fx,_,currency=yahoo_chart("TWD=X",earliest)
    if currency!="TWD":raise ValueError("Benchmark FX mismatch")
    return data,fx

def build_brinson(captured,tx,nav,config=None,market=None):
    config=config or json.loads(CONFIG.read_text())
    groups=list(config["weights"])
    out={"status":"NO_ELIGIBLE_CAPTURED_INTERVAL","benchmark":config,"periods":[],"skipped":[],
         "execution_permission":False,"notes":["Illustrative policy weights, not approved investment policy.",
         "Single-period BF only, no trades or external/other flows, unchanged captured holdings.",
         "Portfolio is recorded browser marks; benchmark is previous-calendar-day-or-earlier price close in TWD, not total return or timestamp-synchronized.",
         "No multi-period active linking; no fabricated historical holdings."]}
    if len(captured)<2:return out
    wb=np.array([config["weights"][g] for g in groups],dtype=float)
    if market is None:
        try:market=benchmark_prices(config,min(nav))
        except Exception as exc:
            out.update(status="BENCHMARK_UNAVAILABLE",reason=str(exc)[:180]);return out
    prices,fx=market
    from build_performance_attribution import close
    dates=list(nav)
    for a,b in zip(dates[:-1],dates[1:]):
        sa,sb=str(a.date()),str(b.date())
        if sa not in captured or sb not in captured:continue
        A,B=captured[sa],captured[sb]
        try:
            if any(a<x["date"]<=b for x in tx):raise ValueError("Interval contains ledger events")
            if A["fallback_count"] or B["fallback_count"]:raise ValueError("Cost-fallback marks")
            if set(A["holdings"])!=set(B["holdings"]):raise ValueError("Holdings changed")
            v0=dict.fromkeys(groups,0.);v1=dict.fromkeys(groups,0.)
            v0["cash"]=A["cash_twd"];v1["cash"]=B["cash_twd"]
            for t,h in A["holdings"].items():
                h1=B["holdings"][t]
                if abs(h["shares"]-h1["shares"])>1e-6 or h["category"]!=h1["category"]:
                    raise ValueError("Share or classification changed")
                g=bucket(t,h["category"]);v0[g]+=h["market_value_twd"];v1[g]+=h1["market_value_twd"]
            x=np.array([v0[g] for g in groups]);y=np.array([v1[g] for g in groups])
            if min(x.min(),y.min())<0 or x.sum()<=0 or not np.isclose(x.sum(),A["nav"],atol=.01) or not np.isclose(y.sum(),B["nav"],atol=.01):
                raise ValueError("Captured bucket NAV mismatch")
            # Strict prior calendar date: no same-day close from after capture.
            d0=a-pd.Timedelta(days=1);d1=b-pd.Timedelta(days=1)
            rates=[]
            for g in groups:
                p0,p1=close(prices[g],d0,7),close(prices[g],d1,7)
                f0,f1=(close(fx,d0,7),close(fx,d1,7)) if config["currency"][g]=="USD" else (1.,1.)
                rates.append(p1*f1/(p0*f0)-1)
            rb=np.array(rates);wp=x/x.sum()
            # Empty bucket: use benchmark return convention, selection + interaction cancel.
            rp=np.divide(y-x,x,out=rb.copy(),where=x>1e-8)
            if np.any((x<=1e-8)&(y>1e-8)):raise ValueError("New bucket without recorded flow")
            Rp,Rb,al,se,it=effects(wp,rp,wb,rb)
            if abs(Rp-(B["nav"]/A["nav"]-1))>1e-8:raise ValueError("Portfolio return mismatch")
            out["periods"].append({"start":sa,"end":sb,"portfolio_return_pct":Rp*100,"benchmark_return_pct":Rb*100,
                "active_return_pp":(Rp-Rb)*100,"allocation_pp":float(al.sum()*100),"selection_pp":float(se.sum()*100),
                "interaction_pp":float(it.sum()*100),"identity_error_pp":float(((al+se+it).sum()-(Rp-Rb))*100),
                "rows":[{"bucket":g,"portfolio_weight_pct":float(wp[i]*100),"benchmark_weight_pct":float(wb[i]*100),
                "portfolio_return_pct":float(rp[i]*100) if wp[i]>1e-8 else None,"benchmark_return_pct":float(rb[i]*100),
                "allocation_pp":float(al[i]*100),"selection_pp":float(se[i]*100),"interaction_pp":float(it[i]*100)} for i,g in enumerate(groups)]})
        except Exception as exc:out["skipped"].append({"start":sa,"end":sb,"reason":str(exc)[:180]})
    if out["periods"]:out.update(status="OK_RESEARCH_ONLY",latest=out["periods"][-1])
    return out
