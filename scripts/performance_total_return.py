"""Research benchmark calibration and dividend-adjusted proxy comparison.

Recorded portfolio NAV is not reconstructed using adjusted stock prices:
that would double-count dividends already present in ledger cash.
"""
from datetime import datetime, timezone
import json
import math
import pandas as pd
from performance_brinson import CONFIG
from performance_brinson_historical import build_historical
from performance_market_data import yahoo_chart
from performance_calendar import benchmark_calendar
from performance_coverage import quote

# These proxies are retained for comparability, not optimized to past returns.
# BOXX is USD cash-like exposure, not a TWD risk-free rate.
def policy_config(settings, now=None):
    config=json.loads(CONFIG.read_text())
    config.update(description="Research benchmark, provider distribution-adjusted proxy returns in TWD",
                  return_basis="provider_distribution_adjusted_proxy",rebalance="observed_NAV_boundaries",
                  approved=False,policy_source="illustrative",effective_date=None)
    p=(settings or {}).get("attributionBenchmarkPolicy")
    if p is None:return config
    if not isinstance(p,dict) or p.get("approved") is not True:raise ValueError("Explicit benchmark approval required")
    w=p.get("weights")
    if not isinstance(w,dict) or set(w)!=set(config["weights"]):raise ValueError("Policy bucket mismatch")
    if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not 0<=v<=1 for v in w.values()):
        raise ValueError("Invalid benchmark weight")
    if abs(math.fsum(w.values())-1)>1e-9:raise ValueError("Benchmark weights must sum to one")
    stamp=datetime.fromisoformat(p["approved_at"].replace("Z","+00:00"))
    now=now or datetime.now(timezone.utc)
    if stamp.tzinfo is None or stamp>now:raise ValueError("Invalid approval timestamp")
    local=pd.Timestamp(stamp).tz_convert("Asia/Taipei").date()
    effective=pd.Timestamp(p["effective_date"])
    if effective.tzinfo is not None or effective!=effective.normalize() or effective.date()<local:
        raise ValueError("Policy cannot precede approval")
    config.update(weights={g:float(w[g]) for g in config["weights"]},approved=True,
                  policy_source="user_private_settings",effective_date=str(effective.date()),approved_at=stamp.isoformat())
    return config

def adjusted_benchmark_prices(config,earliest):
    data={}
    for g,symbol in config["proxies"].items():
        # BTC has no distributions; the spot price is its unlevered return proxy.
        px,_,currency=yahoo_chart(symbol,earliest,adjusted=(g!="crypto"))
        if currency!=config["currency"][g]:raise ValueError("Benchmark currency mismatch")
        data[g]=px
    fx,_,currency=yahoo_chart("TWD=X",earliest)
    if currency!="TWD":raise ValueError("Benchmark FX mismatch")
    return data,fx

def trim_policy_history(nav,config):
    if not config.get("effective_date"):return nav
    effective=pd.Timestamp(config["effective_date"])
    return {d:v for d,v in nav.items() if d>=effective}

def calibration(config,historical):
    # Benchmark target weights are ex ante; never fit on portfolio performance.
    # Opening exposures are computed in the historical engine, same dates.
    periods=historical.get("periods",[])
    if not periods:return None
    rows=periods[-1].get("opening_weights",{})
    if set(rows)!=set(config["weights"]):return None
    return {"date":periods[-1]["start"],"weights":[
        {"bucket":g,"portfolio_pct":rows[g]*100,"target_pct":w*100,"gap_pp":(rows[g]-w)*100}
        for g,w in config["weights"].items()],
        "one_way_distance_pct":.5*math.fsum(abs(rows[g]-w) for g,w in config["weights"].items())*100}

def matched_price_comparison(tr,price):
    # No comparisons across holes or mismatched calendar ranges. Both
    # branches use the same illustrative policy only.
    from performance_brinson_historical import link_segment
    if tr.get("benchmark",{}).get("weights")!=price.get("benchmark",{}).get("weights"):return []
    p={(r["start"],r["end"]):r for r in price.get("periods",[])}
    result=[]
    for seg in tr.get("segments",[]):
        rows=[r for r in tr["periods"] if seg["start"]<=r["start"] and r["end"]<=seg["end"]]
        if not rows or any((r["start"],r["end"]) not in p for r in rows):continue
        other=link_segment([p[(r["start"],r["end"])] for r in rows],list(tr["benchmark"]["weights"]))
        result.append({"start":seg["start"],"end":seg["end"],"period_count":len(rows),
            "price_benchmark_return_pct":other["benchmark_return_pct"],"adjusted_benchmark_return_pct":seg["benchmark_return_pct"],
            "distribution_adjustment_pp":seg["benchmark_return_pct"]-other["benchmark_return_pct"],
            "price_active_pp":other["active_return_pp"],"adjusted_active_pp":seg["active_return_pp"]})
    return result

def build_total_return(nav,tx,categories,market,settings,price,bmarket=None):
    out={"version":"v2.5","status":"UNAVAILABLE","execution_permission":False,
         "notes":["Provider adjusted-close ETF proxy returns in TWD, before investor-specific taxes and costs; BTC spot return.",
                  "Portfolio uses recorded NAV Modified Dietz. Holdings use unadjusted market marks and actual ledger cash, never adjusted prices for valuation.",
                  "Allocation/selection/interaction compare price-mark exposures against adjusted benchmark. Recorded income stays in execution/other; missing distributions and methodology remain in NAV bridge.",
                  "Not complete security-level dividend attribution or an official index total return. No policy inferred from historical returns.",
                  "Benchmark resets at observed NAV boundaries; no linking across missing intervals. USD BOXX is not TWD cash."]}
    try:
        config=policy_config(settings)
        out["benchmark"]=config
        dates=trim_policy_history(nav,config)
        if len(dates)<2:
            out["status"]="WAITING_POLICY_EFFECTIVE_HISTORY";return out
        bmarket=bmarket if bmarket is not None else adjusted_benchmark_prices(config,min(dates))
        h=build_historical(dates,tx,categories,market,config,bmarket)
        out.update(status=h["status"],coverage_pct=h.get("coverage_pct"),eligible_intervals=h.get("eligible_intervals",0),
                   expected_intervals=h.get("expected_intervals",0),segments=h.get("segments",[]),periods=h.get("periods",[]),
                   skipped=h.get("skipped",[]),latest_segment=h.get("latest_segment"),calibration=calibration(config,h))
        out["matched_price_comparison"]=matched_price_comparison(h,price)
        return out
    except Exception:
        out.update(status="UNAVAILABLE",reason="Policy or adjusted benchmark source failed validation; no price fallback")
        return out
