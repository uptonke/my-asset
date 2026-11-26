"""Research interpretation quality gate, independent of order execution."""
import math
import pandas as pd

LIMITS={"max_endpoint_nav_gap_pct":1.0,"max_abs_nav_bridge_pp":0.5,"max_identity_error_pp":1e-6}

def interval_quality(r,nav,limits=LIMITS):
    reasons=[]
    a,b=pd.Timestamp(r["start"]),pd.Timestamp(r["end"])
    try:
        gap=max(abs(float(r["start_nav_gap_twd"]))/nav[a],abs(float(r["end_nav_gap_twd"]))/nav[b])*100
        bridge=abs(float(r["effects_pp"]["nav_bridge"]))
        identity=abs(math.fsum(float(x) for x in r["effects_pp"].values())-float(r["active_return_pp"]))
        if not all(math.isfinite(x) for x in (gap,bridge,identity)):raise ValueError("nonfinite")
    except (KeyError,ValueError,TypeError,ZeroDivisionError,OverflowError):
        return {"start":r["start"],"end":r["end"],"status":"BLOCKED","reasons":["INVALID_DIAGNOSTICS"]}
    if gap>limits["max_endpoint_nav_gap_pct"]:reasons.append("NAV_GAP")
    if bridge>limits["max_abs_nav_bridge_pp"]:reasons.append("METHOD_BRIDGE")
    if identity>limits["max_identity_error_pp"]:reasons.append("IDENTITY")
    q=r.get("data_quality") or {}
    if q.get("issues"):reasons.append("SOURCE_ISSUES")
    if q.get("micro_cash_tolerance_used"):reasons.append("MICRO_CASH")
    if q.get("pending_subscription_tickers"):reasons.append("SUBSCRIPTION_PROXY")
    return {"start":r["start"],"end":r["end"],"status":"REVIEW_REQUIRED" if reasons else "RESEARCH_SCREEN_PASS",
            "reasons":reasons,"max_nav_gap_pct":gap,"abs_nav_bridge_pp":bridge,"identity_error_pp":identity}

def quality_gate(nav,price,tr,pit,quarantined,limits=LIMITS):
    h=tr if tr.get("periods") else price
    records=[interval_quality(r,nav,limits) for r in h.get("periods",[])]
    expected=max(0,len(nav)-1)
    eligible=len(records)
    passed=sum(r["status"]=="RESEARCH_SCREEN_PASS" for r in records)
    counts={}
    for r in records:
        for k in r["reasons"]:counts[k]=counts.get(k,0)+1
    invalid=sum(x.get("status")=="INVALID" for x in pit.get("snapshots",[]))
    auto_pairs=pit.get("adjacent_pairs",[])
    reasons=[]
    if not tr.get("periods"):reasons.append("ADJUSTED_BENCHMARK_UNAVAILABLE")
    if not tr.get("benchmark",{}).get("approved"):reasons.append("POLICY_NOT_APPROVED")
    if eligible!=expected:reasons.append("HISTORICAL_GAPS_OR_POLICY_SCOPE")
    if passed!=eligible:reasons.append("HISTORICAL_QUALITY_WARNINGS")
    if invalid:reasons.append("INVALID_CAPTURED_SNAPSHOT")
    if quarantined:reasons.append("QUARANTINED_INSTRUMENTS")
    if not auto_pairs or auto_pairs[-1].get("end")!=str(max(nav).date()) or auto_pairs[-1].get("status")!="OK":
        reasons.append("NO_CURRENT_ADJACENT_AUTOMATED_PAIR")
    # Exact quote times and independently verified cash are not available.
    reasons.extend(["CASH_NOT_INDEPENDENTLY_VERIFIED","QUOTE_TIMESTAMPS_NOT_VERIFIED","HISTORICAL_NAV_PROVENANCE_NOT_CERTIFIED"])
    status="BLOCKED" if not eligible else "RESEARCH_ONLY"
    return {"version":"v2.6","status":status,"execution_permission":False,"formal_attribution_permission":False,
            "limits":limits,"basis":"distribution_adjusted_comparison" if h is tr else "price_comparison_only",
            "eligible_intervals":eligible,"expected_intervals":expected,"screen_pass_intervals":passed,
            "review_intervals":eligible-passed,"invalid_snapshots":invalid,"reasons":reasons,
            "reason_counts":counts,"periods":records,
            "notes":["Screen pass does not certify actual returns. Thresholds are engineering defaults, not user policy.",
                     "The report remains visible for diagnosis; no formal or execution permission is granted."]}
