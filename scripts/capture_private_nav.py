"""Scheduled forward-only, private close-based NAV capture. No historical backfill."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib
import json
import math
import os
import pandas as pd
from build_performance_attribution import parse_inputs, close
from performance_calendar import required_session
from performance_market_data import load_asset, yahoo_chart, FUND_CODES
from performance_data_quality import reconcile_transactions
from performance_coverage import quote
from performance_pit_nav import validate_snapshot, ledger_fingerprint

TAIPEI=ZoneInfo("Asia/Taipei")
EPS=1e-7

class CaptureBlocked(ValueError):
    pass

def capture_dates(now):
    if now.tzinfo is None:raise CaptureBlocked("TIMEZONE_REQUIRED")
    local=now.astimezone(TAIPEI)
    if local.hour<10:raise CaptureBlocked("BEFORE_COMPLETED_CLOSE_WINDOW")
    today=pd.Timestamp(local.date())
    return today,today-pd.Timedelta(days=1)

def inputs(row,now):
    today,cutoff=capture_dates(now)
    nav,tx,categories=parse_inputs(row)
    if any(d>today for d in nav):raise CaptureBlocked("FUTURE_NAV")
    if today in nav:return None
    if any(x["date"]>cutoff for x in tx):raise CaptureBlocked("SAME_DAY_OR_FUTURE_LEDGER")
    if any(x["type"] not in {"buy","sell","deposit","withdraw","income","expense"} or
           (x["type"]=="expense" and x["flow"]>0) or (x["type"]=="income" and x["flow"]<0) for x in tx):
        raise CaptureBlocked("LEDGER_TYPE_OR_SIGN")
    rawcash=math.fsum(x["flow"] for x in tx)
    if rawcash<-.01:raise CaptureBlocked("NEGATIVE_CASH")
    balances={t:math.fsum(x["qty"] for x in tx if x["ticker"]==t) for t in categories}
    if any(n< -EPS for n in balances.values()):raise CaptureBlocked("NEGATIVE_INVENTORY")
    active={t:categories[t] for t,n in balances.items() if n>0.0001}
    if any(c not in {"台股","美股","基金","加密貨幣"} for c in active.values()):raise CaptureBlocked("UNVERIFIED_CATEGORY")
    if any(EPS<n<=.0001 for n in balances.values()):raise CaptureBlocked("BELOW_DISPLAY_QUANTITY_THRESHOLD")
    return today,cutoff,tx,active,balances,rawcash

def price_kind(t,cat,m):
    if cat=="基金":
        if t not in FUND_CODES or not m.get("fund") or m.get("foreign") is not False or m.get("instrument_id")!=FUND_CODES[t][0]:
            raise CaptureBlocked("FUND_IDENTITY")
        return "XTAI","fund_nav"
    if cat=="台股" and m.get("calendar")=="XTAI" and m.get("foreign") is False:return "XTAI","market_close"
    if cat=="美股" and m.get("calendar")=="XNYS" and m.get("foreign") is True:return "XNYS","market_close"
    if cat=="加密貨幣" and m.get("foreign") is True and str(m.get("instrument_id","")).endswith("-USD"):
        return None,"crypto_daily_close"
    raise CaptureBlocked("UNSUPPORTED_MARKET")

def cost_basis(row,active):
    # Match the existing browser average-cost calculation and stored order.
    # This is display cost, not cumulative deposits or audited broker basis.
    amounts={t:[0.,0.] for t in active}
    for x in row["ledger_data"]:
        t=str(x.get("ticker") or "").strip().upper()
        if t not in amounts or x["type"] not in ("Buy","Sell"):continue
        q=float(x["shares"]);flow=float(x["totalCashFlow"])
        shares,cost=amounts[t]
        if x["type"]=="Buy":amounts[t]=[shares+q,cost+abs(flow)]
        else:amounts[t]=[shares-q,cost-(cost/shares if shares else 0.)*q]
    total=math.fsum(c for _,c in amounts.values())
    if not math.isfinite(total) or total<0:raise CaptureBlocked("INVALID_DISPLAY_COST")
    return math.floor(total+.5)

def make_snapshot(row,now,market,parsed=None):
    parsed=inputs(row,now) if parsed is None else parsed
    if parsed is None:return None
    today,cutoff,tx,active,balances,cash=parsed
    # Reconcile only active instruments. Closed historic lots cannot poison
    # a current quote, but active share basis must agree with the raw ledger.
    filtered=[x for x in tx if not x["qty"] or x["ticker"] in active]
    copied={**market,"assets":{t:dict(m) for t,m in market["assets"].items()}}
    adjusted,_,quarantine=reconcile_transactions(filtered,active,copied,close)
    if quarantine:raise CaptureBlocked("ACTIVE_INVENTORY_OR_SPLIT_BASIS")
    fx_series=market["fx"]
    fx=quote(fx_series,cutoff,4,"USD/TWD","Yahoo chart Close","FX")
    fx_date=fx_series.loc[:cutoff].index[-1]
    holdings=[]
    for t,cat in sorted(active.items()):
        m=copied["assets"].get(t,{})
        if m.get("error") or not m.get("source") or not m.get("instrument_id") or m.get("splits") is None:
            raise CaptureBlocked("MARKET_IDENTITY_UNAVAILABLE")
        if any(d>cutoff for d in (m.get("split_ratios") or {})):raise CaptureBlocked("SPLIT_AFTER_CUTOFF")
        q=math.fsum(x["qty"] for x in adjusted if x["ticker"]==t)
        if abs(q-balances[t])>1e-5:raise CaptureBlocked("RAW_NORMALIZED_QUANTITY_CONFLICT")
        calendar,kind=price_kind(t,cat,m)
        px=m["price"]
        # Restrict to completed dates. No cost, manual or forward fill on
        # a missing scheduled exchange session or crypto UTC day.
        p=quote(px,cutoff,0 if calendar is None else 7,t,m["source"],calendar=calendar)
        mark_date=px.loc[:cutoff].index[-1]
        rate=fx if m["foreign"] else 1.
        holdings.append({"ticker":t,"category":cat,"currency":"USD" if m["foreign"] else "TWD",
            "shares":balances[t],"native_price":p,"fx_to_twd":rate,"market_value_twd":balances[t]*p*rate,
            "price_source":"verified_daily_mark","price_provider":m["source"],"instrument_id":m["instrument_id"],
            "quote_as_of":str(mark_date.date()),"quote_kind":kind,"calendar":calendar})
    invested=math.fsum(h["market_value_twd"] for h in holdings)
    nav=invested+max(0.,cash)
    if not math.isfinite(nav) or nav<=0:raise CaptureBlocked("NONPOSITIVE_NAV")
    d=str(today.date())
    record={"date":d,"assets":math.floor(nav+.5),"cost":cost_basis(row,active),
        "valuation":{"version":"v2","capture_mode":"automated_completed_daily_marks","captured_at":now.isoformat(),
          "timezone":"Asia/Taipei","date":d,"cutoff_date":str(cutoff.date()),"holdings":holdings,
          "cash_twd":cash,"nav_cash_twd":max(0.,cash),"fx_usdtwd":fx,
          "fx_quote_date":str(fx_date.date()),"fx_price_source":"Yahoo chart Close (TWD=X)",
          "invested_twd":invested,"nav_unrounded_twd":nav,"ledger_count":len(tx),
          "ledger_fingerprint":ledger_fingerprint(tx),"quote_dates_verified":True,"quote_timestamps_verified":False}}
    validate_snapshot(record,tx)
    return record

def load_capture_market(parsed):
    import update_stock_meta as q
    _,cutoff,tx,active,_,_=parsed
    assets={}
    for t,cat in active.items():
        earliest=min([x["date"] for x in tx if x["ticker"]==t]+[cutoff])
        assets[t]=load_asset(t,cat,earliest,q)
    fx,_,currency=yahoo_chart("TWD=X",cutoff-pd.Timedelta(days=10))
    if currency!="TWD":raise CaptureBlocked("FX_IDENTITY")
    return {"assets":assets,"fx":fx}

def main():
    if not os.getenv("SUPABASE_SECRET_KEY") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        os.environ["SUPABASE_SECRET_KEY"]=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    import update_stock_meta as q
    now=datetime.now(timezone.utc)
    if os.getenv("CAPTURE_SCHEDULED")=="true" and now.astimezone(TAIPEI).weekday()!=5:
        print("NAV_CAPTURE_SKIPPED schedule day elapsed")
        return
    client=q.connect_supabase()
    row=q.fetch_portfolio_row(client)
    parsed=inputs(row,now)
    if parsed is None:
        print("NAV_CAPTURE_SKIPPED existing date")
        return
    market=load_capture_market(parsed)
    # Use actual completion time, not job start, while refusing a date rollover.
    finished=datetime.now(timezone.utc)
    if capture_dates(finished)!=capture_dates(now):raise CaptureBlocked("DATE_ROLLOVER")
    record=make_snapshot(row,finished,market,parsed)
    json.dumps(record,allow_nan=False)
    result=client.rpc("append_automated_nav",{"p_row_id":int(q.PORTFOLIO_ROW_ID),"p_ledger":row["ledger_data"],
        "p_history":row["history_data"],"p_record":record}).execute()
    if result.data is not True:raise CaptureBlocked("CAS_REFUSED")
    data=client.table(q.SUPABASE_TABLE).select("history_data").eq("id",int(q.PORTFOLIO_ROW_ID)).single().execute().data
    if record not in data["history_data"]:raise CaptureBlocked("READBACK_FAILED")
    print("NAV_CAPTURE_OK")

if __name__=="__main__":
    try:main()
    except CaptureBlocked as e:
        # Codes are static and contain no holdings or balances.
        print("NAV_CAPTURE_BLOCKED",str(e));raise SystemExit(1)
    except Exception:
        # Provider/DB exceptions can expose private identifiers or payloads.
        print("NAV_CAPTURE_BLOCKED provider, validation or database error");raise SystemExit(1)
