"""Diagnostics on the same eligible-period basis as the quality gate."""
from collections import Counter,defaultdict
import pandas as pd
from performance_brinson_historical import link_segment

def diagnostics(nav,tx,price,tr,gate):
    h=tr if gate["basis"]=="distribution_adjusted_comparison" else price
    periods={(r["start"],r["end"]):r for r in h.get("periods",[])}
    checks={(r["start"],r["end"]):r for r in gate["periods"]}
    skipped={(r["start"],r["end"]):r for r in h.get("skipped",[])}
    groups=list(h.get("benchmark",{}).get("weights",{}))
    dates=sorted(nav); rows=[]; reasons=Counter(); cohorts=defaultdict(lambda:{"intervals":0,"review_or_excluded":0})
    for a,b in zip(dates[:-1],dates[1:]):
        key=(str(a.date()),str(b.date()));q=checks.get(key);p=periods.get(key);skip=skipped.get(key,{})
        if q is None:
            codes=sorted({x["code"] for x in (skip.get("diagnostics") or {}).get("issues",[])}) or ["OUTSIDE_SCOPE_OR_UNAVAILABLE"]
            r={"start":key[0],"end":key[1],"status":"EXCLUDED","reasons":codes,"severity":None}
        else:
            r=dict(q)
            r["severity"]=max(q.get("max_nav_gap_pct",0)/gate["limits"]["max_endpoint_nav_gap_pct"],
                q.get("abs_nav_bridge_pp",0)/gate["limits"]["max_abs_nav_bridge_pp"],
                q.get("identity_error_pp",0)/gate["limits"]["max_identity_error_pp"])
        ev=[x for x in tx if a<x["date"]<=b]
        r["event_types"]=sorted({x["type"] for x in ev})
        r["traded_tickers"]=sorted({x["ticker"] for x in ev if x["qty"] and x["ticker"]})
        if p:
            r["start_nav_gap_twd"]=p["start_nav_gap_twd"];r["end_nav_gap_twd"]=p["end_nav_gap_twd"]
            r["signed_bridge_pp"]=p["effects_pp"]["nav_bridge"]
        bad=r["status"]!="RESEARCH_SCREEN_PASS"
        reasons.update(r["reasons"])
        for k in ["month:"+key[1][:7]]+["type:"+x for x in r["event_types"]]+["trade:"+x for x in r["traded_tickers"]]:
            cohorts[k]["intervals"]+=1;cohorts[k]["review_or_excluded"]+=int(bad)
        rows.append(r)
    windows={}
    for n in (4,13,26,52):
        start=dates[-1]-pd.Timedelta(weeks=n)
        rr=[r for r in rows if pd.Timestamp(r["start"])>=start]
        eligible=sum(r["status"]!="EXCLUDED" for r in rr);passed=sum(r["status"]=="RESEARCH_SCREEN_PASS" for r in rr)
        windows[str(n)]={"start":str(start.date()),"end":str(dates[-1].date()),"expected":len(rr),"eligible":eligible,"passed":passed,
                         "pass_pct_all":100*passed/len(rr) if rr else None,"pass_pct_eligible":100*passed/eligible if eligible else None}
    segments=[];run=[]
    def flush():
        if run:segments.append(link_segment(run,groups));run.clear()
    for r in rows:
        if r["status"]=="RESEARCH_SCREEN_PASS" and (r["start"],r["end"]) in periods:
            run.append(periods[(r["start"],r["end"])])
        else:flush()
    flush()
    priority=sorted([r for r in rows if r["status"]!="RESEARCH_SCREEN_PASS"],
                    key=lambda r:(r["status"] in ("EXCLUDED","BLOCKED"),r.get("severity") or 0,r["end"]),reverse=True)
    return {"version":"v2.6.1","status":"RESEARCH_ONLY","basis":gate["basis"],"execution_permission":False,
            "windows":windows,"reason_counts":dict(reasons),"priority":priority,"cohorts":[{"group":k,**v} for k,v in sorted(cohorts.items())],
            "all_segments":h.get("segments",[]),"quality_segments":segments,
            "notes":["Whole observed intervals within calendar windows only. Excluded intervals rank before review; severity is max threshold multiple, not financial loss.",
                     "Quality segments never cross a rejected interval. Segment results have different dates; not directly comparable performance.",
                     "Trade/type/month cohorts are associations, not causal attribution; intervals can overlap multiple cohorts."]}
