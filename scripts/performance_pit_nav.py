"""Recorded browser marks, never manufactured historical snapshots."""
from datetime import datetime
from zoneinfo import ZoneInfo
import math
import hashlib
import json
from performance_calendar import required_session
import pandas as pd

EPS=1e-7

def numeric(x):
    if isinstance(x,bool):raise ValueError("Boolean numeric")
    v=float(x)
    if not math.isfinite(v):raise ValueError("Nonfinite number")
    return v

def ledger_fingerprint(tx):
    # Canonical normalized ledger fields, ordered by parser stable date order.
    rows=[{"date":str(x["date"].date()),"type":x["type"],"ticker":x["ticker"],
           "qty":float(x["qty"]),"flow":float(x["flow"]),"category":x.get("category",""),
           "subscription":x.get("subscription")} for x in tx]
    return hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(",",":")).encode()).hexdigest()

def validate_snapshot(record,tx):
    v=record.get("valuation")
    if not isinstance(v,dict) or v.get("version") not in ("v1","v2"):raise ValueError("Legacy NAV without captured marks")
    d=pd.Timestamp(record["date"]).normalize()
    stamp=datetime.fromisoformat(v["captured_at"].replace("Z","+00:00"))
    if stamp.tzinfo is None or stamp.astimezone(ZoneInfo("Asia/Taipei")).date()!=d.date() or v["date"]!=str(d.date()):
        raise ValueError("Capture date/time mismatch")
    prior=[x for x in tx if x["date"]<=d]
    if len(prior)!=v["ledger_count"]:raise ValueError("Historical ledger count changed")
    automated=v["version"]=="v2"
    if automated:
        cutoff=d-pd.Timedelta(days=1)
        if (v.get("capture_mode")!="automated_completed_daily_marks" or v.get("cutoff_date")!=str(cutoff.date())
            or stamp.astimezone(ZoneInfo("Asia/Taipei")).hour<10 or v.get("ledger_fingerprint")!=ledger_fingerprint(prior)
            or any(x["date"]>cutoff for x in prior) or v.get("quote_dates_verified") is not True
            or v.get("quote_timestamps_verified") is not False):
            raise ValueError("Automated capture provenance or ledger fingerprint mismatch")
        fxdate=pd.Timestamp(v["fx_quote_date"])
        if not 0<=(cutoff-fxdate).days<=4 or not v.get("fx_price_source"):
            raise ValueError("Automated FX quote date mismatch")
    cash=numeric(v["cash_twd"]);rawcash=math.fsum(x["flow"] for x in prior)
    if cash<-.01 or abs(rawcash-cash)>.02 or abs(numeric(v["nav_cash_twd"])-max(0,cash))>.01:
        raise ValueError("Cash inconsistent with ledger")
    balances={};categories={}
    for x in prior:
        if x["qty"]:
            balances[x["ticker"]]=balances.get(x["ticker"],0.)+x["qty"]
            categories.setdefault(x["ticker"],set()).add(x.get("category",""))
    if any(q< -EPS for q in balances.values()):raise ValueError("Negative historical inventory")
    holdings={}
    for h in v["holdings"]:
        t=h["ticker"]
        if t in holdings:raise ValueError("Duplicate instrument")
        q,p,fx,mv=map(numeric,[h["shares"],h["native_price"],h["fx_to_twd"],h["market_value_twd"]])
        if min(q,p,fx,mv)<=0 or abs(q*p*fx-mv)>.01 or abs(q-balances.get(t,0.))>1e-5:
            raise ValueError("Captured holding/ledger mismatch")
        if len(categories.get(t,set()))!=1 or h["category"] not in categories[t]:
            raise ValueError("Instrument category conflict")
        if h["currency"] not in ("USD","TWD") or abs(fx-(numeric(v["fx_usdtwd"]) if h["currency"]=="USD" else 1.))>EPS:
            raise ValueError("Currency/FX mismatch")
        if automated:
            kind=h.get("quote_kind");cal=h.get("calendar");cat=h["category"]
            if cat=="台股":expected=("market_close","XTAI","TWD")
            elif cat=="基金":expected=("fund_nav","XTAI","TWD")
            elif cat=="美股":expected=("market_close","XNYS","USD")
            elif cat=="加密貨幣":expected=("crypto_daily_close",None,"USD")
            else:raise ValueError("Automated unsupported category")
            if (kind,cal,h["currency"])!=expected or h["price_source"]!="verified_daily_mark" or not h.get("price_provider") or not h.get("instrument_id"):
                raise ValueError("Automated price provenance missing")
            expected_date=required_session(cal,cutoff) if cal else cutoff
            if h.get("quote_as_of")!=str(expected_date.date()):
                raise ValueError("Automated quote session mismatch")
        elif h["price_source"] not in ("manual","price_map","cost_fallback"):raise ValueError("Unknown price source")
        holdings[t]={**h,"market_value_twd":mv}
    if set(holdings)!={t for t,q in balances.items() if q>0.0001}:raise ValueError("Missing captured holding")
    invested=math.fsum(h["market_value_twd"] for h in holdings.values())
    nav=numeric(v["nav_unrounded_twd"])
    if abs(invested-numeric(v["invested_twd"]))>.01 or abs(nav-invested-max(0,cash))>.01 or abs(nav-numeric(record["assets"]))>.50001:
        raise ValueError("NAV identity mismatch")
    return {"date":str(d.date()),"captured_at":v["captured_at"],"cash_twd":cash,"nav":nav,"holdings":holdings,
            "fallback_count":sum(h["price_source"]=="cost_fallback" for h in holdings.values()),
            "quote_timestamps_verified":False,"quote_dates_verified":automated,
            "capture_mode":v.get("capture_mode","browser"),"cutoff_date":v.get("cutoff_date"),"fx_quote_date":v.get("fx_quote_date")}

def pair(a,b,tx,nav):
    start,end=pd.Timestamp(a["date"]),pd.Timestamp(b["date"])
    flows=[x for x in tx if start<x["date"]<=end]
    ext=math.fsum(x["flow"] for x in flows if x["type"] in ("deposit","withdraw"))
    rows=[]
    for t in sorted(set(a["holdings"])|set(b["holdings"])|{x["ticker"] for x in flows if x["qty"]}):
        v0=a["holdings"].get(t,{}).get("market_value_twd",0.)
        v1=b["holdings"].get(t,{}).get("market_value_twd",0.)
        trades=math.fsum(x["flow"] for x in flows if x["ticker"]==t and x["qty"])
        rows.append({"ticker":t,"start_mv_twd":v0,"end_mv_twd":v1,"trade_cashflow_twd":trades,"pnl_twd":v1-v0+trades})
    asset=math.fsum(r["pnl_twd"] for r in rows)
    trade=math.fsum(r["trade_cashflow_twd"] for r in rows)
    other=math.fsum(x["flow"] for x in flows if x["type"] not in ("deposit","withdraw","buy","sell"))
    cash=b["cash_twd"]-a["cash_twd"]-trade-ext-other
    rounding=nav[end]-nav[start]-(b["nav"]-a["nav"])
    total=nav[end]-nav[start]-ext
    err=total-asset-other-cash-rounding
    return {"status":"OK" if abs(err)<.02 else "FAILED","start":a["date"],"end":b["date"],
        "actual_pnl_twd":total,"asset_pnl_twd":asset,"external_flow_twd":ext,"other_cashflow_twd":other,
        "cash_bridge_twd":cash,"rounding_bridge_twd":rounding,"identity_error_twd":err,"rows":rows,
        "captured_marks_not_independent_market_validation":True}

def build_pit(history,tx,nav,windows):
    valid={};diagnostics=[]
    for r in sorted(history,key=lambda r:r["date"]):
        d=str(r["date"])[:10]
        try:
            a=validate_snapshot(r,tx);valid[d]=a
            diagnostics.append({"date":d,"status":"CAPTURED","captured_at":a["captured_at"],"fallback_count":a["fallback_count"],"capture_mode":a["capture_mode"],"quote_dates_verified":a["quote_dates_verified"],"cutoff_date":a["cutoff_date"],"fx_quote_date":a["fx_quote_date"]})
        except Exception as exc:
            diagnostics.append({"date":d,"status":"LEGACY" if not r.get("valuation") else "INVALID","reason":str(exc)})
    out={}
    for k,w in windows.items():
        s,e=w["start"],w["end"]
        out[k]=pair(valid[s],valid[e],tx,nav) if s in valid and e in valid else {"status":"NO_CAPTURED_PAIR","start":s,"end":e,"reason":"Both endpoint marks required; historical reconstruction remains separate"}
    adjacent=[]
    for a,b in zip(sorted(nav)[:-1],sorted(nav)[1:]):
        s,e=str(a.date()),str(b.date())
        if s not in valid or e not in valid:continue
        if any(valid[d].get("capture_mode")!="automated_completed_daily_marks" for d in (s,e)):continue
        try:
            r=pair(valid[s],valid[e],tx,nav)
            if abs(r["cash_bridge_twd"])>.02 or abs(r["rounding_bridge_twd"])>1.00002:
                r["status"]="REVIEW_REQUIRED"
            adjacent.append(r)
        except Exception:
            adjacent.append({"start":s,"end":e,"status":"FAILED"})
    return {"version":"v2.4","adjacent_pairs":adjacent,"adjacent_pair_count":sum(r["status"]=="OK" for r in adjacent),"valid_count":len(valid),"pair_count":sum(p["status"]=="OK" for p in out.values()),
            "snapshots":diagnostics,"windows":out},valid
