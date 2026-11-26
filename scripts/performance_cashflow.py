"""Explicit recorded cash-flow taxonomy; no security-level dividend attribution."""
from collections import defaultdict
import math
import pandas as pd

KINDS={"income":{"interest","other_income"},
       "expense":{"fee","tax","other_expense","correction"}}

def classify(x,categories):
    t=x["type"];v=x["flow"]
    if t in ("buy","sell","deposit","withdraw"):return t,None,"RECORDED_TYPE"
    meta=x.get("cashflow_detail")
    fallback="unclassified_income" if t=="income" else "unclassified_expense" if t=="expense" else "unclassified_other"
    if not isinstance(meta,dict):return fallback,None,"UNCLASSIFIED"
    k=meta.get("kind")
    # Preserve existing recorded money, but do not attribute dividends to securities.
    if t=="income" and k=="dividend" and v>0:return fallback,None,"UNCLASSIFIED"
    if k not in KINDS.get(t,set()) or (t=="income" and v<=0) or (t=="expense" and v>=0):
        return fallback,None,"INVALID_METADATA"
    return k,None,"EXPLICIT_LEDGER_CLASS"

def interval(nav,tx,categories,pnl):
    a,b=pd.Timestamp(pnl["start"]),pd.Timestamp(pnl["end"])
    events=[x for x in tx if a<x["date"]<=b]
    sums=defaultdict(float);counts=defaultdict(int);unclassified=[]
    weighted=0.
    for x in events:
        k,_,status=classify(x,categories)
        sums[k]+=x["flow"];counts[k]+=1
        if k in ("deposit","withdraw"):
            weighted+=x["flow"]*(b-x["date"]).days/(b-a).days
        if status in ("UNCLASSIFIED","INVALID_METADATA"):
            unclassified.append({"date":str(x["date"].date()),"type":x["type"],"amount_twd":x["flow"],"status":status})
    other={k:v for k,v in sums.items() if k not in ("buy","sell","deposit","withdraw")}
    den=nav[a]+weighted
    total=math.fsum(other.values())
    if abs(total-pnl["explicit_other_cashflow_twd"])>.01:raise ValueError("Cash taxonomy identity")
    err=pnl["actual_pnl_twd"]-pnl["asset_pnl_twd"]-total-pnl["unexplained_twd"]
    if abs(err)>.01:raise ValueError("Cash reconciliation identity")
    return {"start":pnl["start"],"end":pnl["end"],"totals_twd":dict(sums),"counts":dict(counts),
        "other_dietz_pp":{k:v/den*100 for k,v in other.items()} if den>0 else {},
        "unclassified":unclassified,"unclassified_income_twd":sums.get("unclassified_income",0.),
        "asset_pnl_twd":pnl["asset_pnl_twd"],"explicit_other_cashflow_twd":total,
        "unexplained_twd":pnl["unexplained_twd"],"identity_error_twd":err}

def cashflow_report(nav,tx,categories,pnl):
    out={"version":"v2.9.1","status":"RESEARCH_ONLY","execution_permission":False,"windows":{},
         "notes":["Recorded cash flows only. No security-level dividend attribution, inferred dividends, or synthetic cash.",
                  "Previously recorded income remains in cash, including any legacy dividend metadata treated as unclassified income. No changes to NAV or asset P&L.",
                  "Embedded trade fees/taxes remain in execution vs close; explicit separately booked fees/taxes only. Dietz pp are single-window additive, not linked BF contributions."]}
    for k,w in pnl.items():
        try:out["windows"][k]=interval(nav,tx,categories,w)
        except Exception:out["windows"][k]={"status":"UNAVAILABLE","reason":"Cash flow reconciliation failed"}
    return out
