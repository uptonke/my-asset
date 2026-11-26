"""Research-only historical Brinson-Fachler; never modifies original NAV or ledger."""
import math
import json
import numpy as np
import pandas as pd
from performance_brinson import CONFIG, effects, benchmark_prices

EPS=1e-8
NAMES=("allocation","selection","interaction","execution_other","nav_bridge")


def active_link(rp,rb,components):
    """Carino active-return linking, including equal-return limits."""
    p,b,c=map(lambda x:np.asarray(x,dtype=float),(rp,rb,components))
    if p.ndim!=1 or p.shape!=b.shape or c.ndim!=2 or len(c)!=len(p) or not len(p):
        raise ValueError("Invalid linking shape")
    if not all(np.isfinite(v).all() for v in (p,b,c)) or np.any(p<=-1) or np.any(b<=-1):
        raise ValueError("Invalid return")
    if not np.allclose(c.sum(axis=1),p-b,atol=1e-10,rtol=1e-9):
        raise ValueError("Active period identity failed")
    def slope(a,z):
        delta=a-z
        return np.divide(np.log1p(delta/(1+z)),delta,out=1/(1+z),where=np.abs(delta)>1e-12)
    P=float(np.expm1(np.log1p(p).sum())); B=float(np.expm1(np.log1p(b).sum()))
    K=float(slope(np.array([P]),np.array([B]))[0])
    linked=(c*slope(p,b)[:,None]).sum(axis=0)/K
    if not np.isclose(linked.sum(),P-B,atol=1e-9,rtol=1e-9):
        raise ValueError("Active linking identity failed")
    return P,B,linked


def historical_interval(a,b,nav,tx,categories,market,config,bmarket):
    from build_performance_attribution import close
    groups=list(config["weights"]); idx={g:i for i,g in enumerate(groups)}
    wb=np.array([config["weights"][g] for g in groups],dtype=float)
    bp,bfx=bmarket
    def value(q,d):
        out=np.zeros(len(groups))
        for t,n in q.items():
            if abs(n)<EPS:continue
            if n<0:raise ValueError("Negative inventory: "+t)
            if t in market.get("quarantined",{}):raise ValueError("Quarantined holding: "+t)
            m=market["assets"].get(t,{})
            if m.get("error"):raise ValueError(m["error"])
            if m.get("splits") is None or any(s>d for s in m["splits"]):
                raise ValueError("Unverified split basis: "+t)
            g=m.get("bucket")
            if g not in idx:raise ValueError("Unsupported bucket: "+str(g))
            out[idx[g]]+=n*close(m["price"],d,7)*(close(market["fx"],d,4) if m["foreign"] else 1.)
        return out
    def bench(d):
        return np.array([close(bp[g],d,7)*(close(bfx,d,4) if config["currency"][g]=="USD" else 1.) for g in groups])
    q=dict.fromkeys(categories,0.)
    cash=0.
    for x in tx:
        if x["date"]>a:break
        cash+=x["flow"]
        if x["qty"]:q[x["ticker"]]+=x["qty"]
    def marks(q,d,cash):
        if cash<-.02:raise ValueError("Negative ledger-implied cash")
        v=value(q,d);v[idx["cash"]]+=max(0.,cash)
        if v.sum()<=0:raise ValueError("Nonpositive reconstructed NAV")
        return v
    start=marks(q,a,cash)
    opening_gap=nav[a]-float(start.sum())
    flows=[x for x in tx if a<x["date"]<=b]
    days=sorted({x["date"] for x in flows}|{b})
    ps=[];bs=[];cs=[];last=a
    for d in days:
        v0=marks(q,last,cash)
        vpre=marks(q,d,cash)
        rp=np.divide(vpre-v0,v0,out=np.zeros_like(v0),where=v0>EPS)
        p0,p1=bench(last),bench(d)
        rb=p1/p0-1
        rp=np.where(v0>EPS,rp,rb)
        Rpre,Rb,al,se,it=effects(v0/v0.sum(),rp,wb,rb)
        # Reference starts at policy weights on each observed NAV date;
        # drift between ledger-event dates, independent of portfolio turnover.
        wb=wb*(1+rb)/(1+Rb)
        events=[x for x in flows if x["date"]==d]
        ext=math.fsum(x["flow"] for x in events if x["type"] in ("deposit","withdraw"))
        for x in events:
            if x["qty"]:q[x["ticker"]]+=x["qty"]
            cash+=x["flow"]
        vpost=marks(q,d,cash)
        Rnet=(vpost.sum()-v0.sum()-ext)/v0.sum()
        parts=np.r_[al,se,it,Rnet-Rpre,0.]
        if not np.isclose(parts.sum(),Rnet-Rb,atol=1e-10):raise ValueError("Subperiod identity failed")
        ps.append(Rnet);bs.append(Rb);cs.append(parts);last=d
    P,B,linked=active_link(ps,bs,cs)
    external=math.fsum(x["flow"] for x in flows if x["type"] in ("deposit","withdraw"))
    denominator=nav[a]+math.fsum(x["flow"]*(b-x["date"]).days/(b-a).days for x in flows if x["type"] in ("deposit","withdraw"))
    if denominator<=0:raise ValueError("Invalid actual Dietz denominator")
    actual=(nav[b]-nav[a]-external)/denominator
    if actual<=-1:raise ValueError("Invalid actual return")
    linked[-1]+=actual-P
    if not np.isclose(linked.sum(),actual-B,atol=1e-9):raise ValueError("NAV bridge identity failed")
    n=len(groups)
    return {"start":str(a.date()),"end":str(b.date()),"status":"RECONSTRUCTED_RESEARCH_ONLY",
        "portfolio_return_pct":actual*100,"reconstructed_return_pct":P*100,"benchmark_return_pct":B*100,
        "active_return_pp":(actual-B)*100,"subperiod_count":len(days),"ledger_event_count":len(flows),
        "start_nav_gap_twd":opening_gap,"end_nav_gap_twd":nav[b]-float(vpost.sum()),
        "effects_pp":{k:float(v*100) for k,v in zip(NAMES,[linked[:n].sum(),linked[n:2*n].sum(),linked[2*n:3*n].sum(),linked[-2],linked[-1]])},
        "rows":[{"bucket":g,"allocation_pp":float(linked[i]*100),"selection_pp":float(linked[n+i]*100),"interaction_pp":float(linked[2*n+i]*100)} for i,g in enumerate(groups)]}


def link_segment(rows,groups):
    vectors=[]
    for r in rows:
        by={x["bucket"]:x for x in r["rows"]}
        vectors.append([by[g][k+"_pp"]/100 for k in NAMES[:3] for g in groups]+[r["effects_pp"][k]/100 for k in NAMES[3:]])
    P,B,c=active_link([r["portfolio_return_pct"]/100 for r in rows],[r["benchmark_return_pct"]/100 for r in rows],vectors)
    n=len(groups)
    return {"start":rows[0]["start"],"end":rows[-1]["end"],"period_count":len(rows),
        "portfolio_return_pct":P*100,"benchmark_return_pct":B*100,"active_return_pp":(P-B)*100,
        "effects_pp":{k:float(v*100) for k,v in zip(NAMES,[c[:n].sum(),c[n:2*n].sum(),c[2*n:3*n].sum(),c[-2],c[-1]])},
        "rows":[{"bucket":g,"allocation_pp":float(c[i]*100),"selection_pp":float(c[n+i]*100),"interaction_pp":float(c[2*n+i]*100)} for i,g in enumerate(groups)],
        "identity_error_pp":float((c.sum()-(P-B))*100)}


def build_historical(nav,tx,categories,market,config=None,bmarket=None):
    config=config or json.loads(CONFIG.read_text())
    groups=list(config["weights"])
    out={"version":"v2.2","status":"NO_ELIGIBLE_INTERVAL","benchmark":config,"execution_permission":False,
        "expected_intervals":max(0,len(nav)-1),"periods":[],"skipped":[],"segments":[],
        "notes":["Historical reconstruction only; recorded NAV remains unchanged. Ledger-implied cash is not independently verified.",
                 "Same-date or earlier unadjusted closes, current-vintage data, asynchronous markets; not total returns or point-in-time marks.",
                 "End-of-day ledger events; trade execution and other recorded cash flow effects separate from allocation, selection and interaction.",
                 "Reference policy reset at each NAV boundary, drift within interval. Actual portfolio uses Modified Dietz; NAV bridge also includes methodology differences.",
                 "No linking across skipped intervals. No formal trade permission."]}
    if bmarket is None:
        try:bmarket=benchmark_prices(config,min(nav))
        except Exception as e:out.update(status="BENCHMARK_UNAVAILABLE",reason=str(e)[:180]);return out
    current=[]
    dates=sorted(nav)
    for a,b in zip(dates[:-1],dates[1:]):
        try:
            r=historical_interval(a,b,nav,tx,categories,market,config,bmarket)
            out["periods"].append(r);current.append(r)
        except Exception as e:
            if current:out["segments"].append(link_segment(current,groups));current=[]
            out["skipped"].append({"start":str(a.date()),"end":str(b.date()),"reason":str(e)[:180]})
    if current:out["segments"].append(link_segment(current,groups))
    out["eligible_intervals"]=len(out["periods"])
    out["coverage_pct"]=len(out["periods"])/max(1,len(nav)-1)*100
    if out["segments"]:
        out.update(status="OK_RESEARCH_ONLY" if not out["skipped"] else "PARTIAL_RESEARCH_ONLY",
                   latest=out["periods"][-1],latest_segment=out["segments"][-1])
    return out
