"""Explicit cash-flow taxonomy and security-linked dividend attribution.

Never infer an income category from a price move or provider distribution.
Net receipts are included once; no synthetic cash or historical ledger edits.
"""
from collections import defaultdict
import math
import pandas as pd

KINDS={"income":{"dividend","interest","other_income"},
       "expense":{"fee","tax","other_expense","correction"}}

def classify(x,categories):
    t=x["type"];v=x["flow"]
    if t in ("buy","sell","deposit","withdraw"):return t,None,"RECORDED_TYPE"
    meta=x.get("cashflow_detail")
    if not isinstance(meta,dict):
        return ("unclassified_income" if t=="income" else "unclassified_expense" if t=="expense" else "unclassified_other"),None,"UNCLASSIFIED"
    k=meta.get("kind");s=str(meta.get("ticker") or "").strip().upper()
    if k not in KINDS.get(t,set()) or (t=="income" and v<=0) or (t=="expense" and v>=0):
        return "unclassified_other",None,"INVALID_METADATA"
    if k=="dividend":
        if not s or s not in categories or categories[s]=="__AMBIGUOUS__":
            return "dividend_unlinked",None,"UNKNOWN_SECURITY"
        return k,s,"EXPLICIT_LEDGER_LINK"
    return k,None,"EXPLICIT_LEDGER_CLASS"

def interval(nav,tx,categories,pnl):
    a,b=pd.Timestamp(pnl["start"]),pd.Timestamp(pnl["end"])
    events=[x for x in tx if a<x["date"]<=b]
    sums=defaultdict(float);counts=defaultdict(int);unclassified=[];dividends=defaultdict(float)
    external=0.;weighted=0.
    for x in events:
        k,t,status=classify(x,categories)
        sums[k]+=x["flow"];counts[k]+=1
        if k in ("deposit","withdraw"):
            external+=x["flow"];weighted+=x["flow"]*(b-x["date"]).days/(b-a).days
        if k=="dividend":dividends[t]+=x["flow"]
        if status in ("UNCLASSIFIED","INVALID_METADATA","UNKNOWN_SECURITY"):
            unclassified.append({"date":str(x["date"].date()),"type":x["type"],"amount_twd":x["flow"],"status":status})
    other={k:v for k,v in sums.items() if k not in ("buy","sell","deposit","withdraw")}
    den=nav[a]+weighted
    if abs(math.fsum(other.values())-pnl["explicit_other_cashflow_twd"])>.01:raise ValueError("Cash taxonomy identity")
    # These are additive Dietz-period components, NOT the linked BF effects.
    assets={r["ticker"]:r["pnl_twd"] for r in pnl["rows"]}
    securities=[{"ticker":t,"recorded_net_dividend_twd":dividends.get(t,0.),
                  "price_trade_pnl_twd":assets.get(t),
                  "pnl_including_dividend_twd":assets[t]+dividends.get(t,0.) if t in assets else None}
                 for t in sorted(set(assets)|set(dividends))]
    linked=math.fsum(dividends.values())
    adjusted_asset=pnl["asset_pnl_twd"]+linked
    remaining=pnl["explicit_other_cashflow_twd"]-linked
    err=pnl["actual_pnl_twd"]-adjusted_asset-remaining-pnl["unexplained_twd"]
    if abs(err)>.01:raise ValueError("Dividend reconciliation identity")
    return {"start":pnl["start"],"end":pnl["end"],"totals_twd":dict(sums),"counts":dict(counts),
        "other_dietz_pp":{k:v/den*100 for k,v in other.items()} if den>0 else {},
        "unclassified":unclassified,"security_rows":securities,"linked_dividend_twd":linked,
        "unlinked_dividend_twd":sums.get("dividend_unlinked",0.),"unclassified_income_twd":sums.get("unclassified_income",0.),
        "asset_including_linked_dividend_twd":adjusted_asset,"other_after_dividend_twd":remaining,
        "unexplained_twd":pnl["unexplained_twd"],"identity_error_twd":err}

def cashflow_report(nav,tx,categories,pnl):
    out={"version":"v2.8/v2.9","status":"RESEARCH_ONLY","execution_permission":False,"windows":{},
         "notes":["Explicit cashflow_detail metadata only; no inferred or accrued dividends. Security P&L includes net received dividends only, excludes unlinked and missing receipts.",
                  "No double counting: linked dividends moved from other cash to security P&L in this view only. No change to NAV, original P&L or Brinson.",
                  "Embedded trade fees/taxes remain in execution vs close; explicit separately booked fees/taxes only. Dietz pp are single-window additive, not linked BF contributions.",
                  "Zero recorded dividends does not certify zero distributions. Unclassified historical income requires user evidence."]}
    for k,w in pnl.items():
        try:out["windows"][k]=interval(nav,tx,categories,w)
        except Exception:out["windows"][k]={"status":"UNAVAILABLE","reason":"Cash flow reconciliation failed"}
    return out
