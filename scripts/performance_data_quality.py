"""Attribution-only ledger reconciliation; never mutate source records."""
import math
import pandas as pd

EPS=1e-8


def inventory_trace(trades):
    q=0.; low=0.; first=None
    # Date-only ledger cannot establish intraday ordering: test end-of-day.
    for d in sorted({x["date"] for x in trades}):
        q+=math.fsum(x["qty"] for x in trades if x["date"]==d)
        low=min(low,q)
        if q < -EPS and first is None: first=str(d.date())
    return {"ending_shares":q,"minimum_shares":low,"first_negative_date":first,
            "status":"NEGATIVE_HISTORY" if first else "OK"}


def split_basis(trades, events, price, fx, foreign, close):
    """Yahoo Close is split-normalized. Infer only with clear trade-price evidence.
    Convert shares to common latest split basis; preserve all TWD cash flows.
    """
    if not isinstance(events,dict):
        raise ValueError("Split ratios unavailable")
    if any(not math.isfinite(float(v)) or v<=0 for v in events.values()):
        raise ValueError("Invalid corporate action ratio")
    pre=[x for x in trades if any(d>x["date"] for d in events)]
    if not pre:
        return trades,"no_pre_split_trade"
    # Trade-date split timing is unknown with a date-only ledger.
    if any(x["date"] in events for x in trades):
        raise ValueError("Trade on split date; share basis unverified")
    transformed=[]
    for x in trades:
        factor=math.prod(v for d,v in events.items() if d>x["date"])
        transformed.append({**x,"qty":x["qty"]*factor})
    scores=[]
    for candidate in (trades,transformed):
        errs=[]
        for x in candidate:
            if not any(d>x["date"] for d in events):continue
            mark=close(price,x["date"],4)*(close(fx,x["date"],4) if foreign else 1.)
            # Effective recorded TWD price (includes fees); not assumed exact.
            ratio=abs(x["flow"]/x["qty"])/mark
            if ratio<=0:raise ValueError("Invalid effective trade price")
            errs.append(abs(math.log(ratio)))
        scores.append(max(errs))
    # Every pre-split trade within 30%, alternative clearly worse.
    choice=min(range(2),key=lambda i:scores[i])
    chosen=(trades,transformed)[choice]
    if scores[choice]>math.log(1.30) or scores[1-choice]-scores[choice]<math.log(1.5) or inventory_trace(chosen)["status"]!="OK":
        raise ValueError("Split share basis ambiguous; broker confirmation required")
    return chosen,("inferred_already_split_normalized" if choice==0 else "inferred_as_traded_converted")


def reconcile_transactions(tx,categories,market,close):
    adjusted=[]; diagnostics=[]; excluded={}
    for ticker,cat in sorted(categories.items()):
        trades=[x for x in tx if x["ticker"]==ticker and x["qty"]!=0]
        raw=inventory_trace(trades)
        m=market["assets"].get(ticker,{})
        chosen=trades; basis="no_split_adjustment"
        try:
            if cat=="__AMBIGUOUS__":
                raise ValueError("Exchange/currency conflict; confirm TW vs ADR")
            events=m.get("split_ratios")
            if events:
                chosen,basis=split_basis(trades,events,m["price"],market["fx"],m["foreign"],close)
                # All chosen quantities are in the same split-normalized price basis.
                m["splits"]=[]
            elif m.get("splits"):
                raise ValueError("Split ratios or share basis unverified")
            final=inventory_trace(chosen)
            if final["status"]!="OK":
                raise ValueError("Negative historical inventory; missing or incorrect transaction")
        except Exception as exc:
            excluded[ticker]=str(exc)
            final=inventory_trace(chosen)
            basis="unverified"
        adjusted.extend(chosen)
        diagnostics.append({"ticker":ticker,"category":cat,"raw_inventory":raw,"normalized_inventory":final,
            "share_basis":basis,"corporate_actions":[{"date":str(d.date()),"ratio":float(v)} for d,v in (m.get("split_ratios") or {}).items()],
            "status":"QUARANTINED" if ticker in excluded else "OK",
            "reason":excluded.get(ticker),"last_trade":str(max(x["date"] for x in trades).date()) if trades else None,
            "instrument_id":m.get("instrument_id"),"currency":m.get("currency")})
    adjusted.extend(x for x in tx if x["qty"]==0)
    return sorted(adjusted,key=lambda x:x["date"]),diagnostics,excluded


def cash_reconciliation(nav,tx,windows):
    """Cash is cumulative recorded flows + unknown opening balance.
    Endpoint NAV less known marked assets is not an observed cash balance.
    """
    out={}
    for label,p in windows.items():
        a,b=pd.Timestamp(p["start"]),pd.Timestamp(p["end"])
        cash_a=math.fsum(x["flow"] for x in tx if x["date"]<=a)
        cash_b=math.fsum(x["flow"] for x in tx if x["date"]<=b)
        mv_a=math.fsum(r["opening_mv_twd"] for r in p["rows"])
        mv_b=math.fsum(r["closing_mv_twd"] for r in p["rows"])
        gap_a=nav[a]-mv_a-cash_a;gap_b=nav[b]-mv_b-cash_b
        excluded_trades=math.fsum(x["flow"] for x in tx if a<x["date"]<=b and x["qty"]!=0 and x["ticker"] not in {r["ticker"] for r in p["rows"]})
        out[label]={"start":p["start"],"end":p["end"],"excluded_trade_cashflow_twd":excluded_trades,"recorded_cumulative_cashflow_start_twd":cash_a,
            "recorded_cumulative_cashflow_end_twd":cash_b,"recorded_cash_change_twd":cash_b-cash_a,
            "known_assets_start_twd":mv_a,"known_assets_end_twd":mv_b,
            "nav_minus_known_assets_start_twd":nav[a]-mv_a,"nav_minus_known_assets_end_twd":nav[b]-mv_b,
            "unexplained_balance_start_twd":gap_a,"unexplained_balance_end_twd":gap_b,
            "unexplained_balance_change_twd":gap_b-gap_a,"pnl_residual_twd":p["unexplained_twd"],
            "bridge_error_twd":gap_b-gap_a-p["unexplained_twd"]+excluded_trades,
            "complete_asset_coverage":not p["missing"],"opening_cash_balance_verified":False,
            "status":"PARTIAL" if p["missing"] else "LEDGER_IMPLIED_ONLY"}
    return out
