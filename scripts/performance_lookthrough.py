"""Extend the existing ETF snapshot pipeline with all-NAV equity exposure.

Only evidence-backed security joins; missing weights are not redistributed.
"""
from collections import defaultdict
from datetime import date
import math
import re
from enrich_xray_lookthrough import (SUPPORTED_FUNDS,SPECIAL_EXPOSURE_MODES,
    load_holdings_set,_snapshot_stale_limit_days)

UNKNOWN="Unknown"

# Explicit security identifiers only: no name-based or bare-ticker merges.
# Alphabet Class A/C and Berkshire Hathaway Class A/B.
ISSUER_GROUPS = {
    "ALPHABET": ("Alphabet Inc.", ("US02079K3059", "US02079K1079")),
    "BERKSHIRE": ("Berkshire Hathaway Inc.", ("US0846701086", "US0846707026")),
}
ISSUER_KEYS = {key: (issuer, name) for issuer, (name, ids) in ISSUER_GROUPS.items()
               for i in ids for key in ("ISIN:"+i, "CUSIP:"+i[2:11])}

def issuer_concentration(rows):
    groups = {}
    confirmed = 0.
    total = sum(r["total_pct"] for r in rows)
    for r in rows:
        match = ISSUER_KEYS.get(r["key"])
        key, name = match if match else ("PROXY:"+r["key"], r["name"] or r["ticker"])
        if match:
            confirmed += r["total_pct"]
        row = groups.setdefault(key, {"key":key,"name":name,"direct_pct":0.,"indirect_pct":0.,"total_pct":0.,
                                      "confirmed":bool(match),"securities":[],"source_funds":[]})
        for field in ("direct_pct","indirect_pct","total_pct"):
            row[field] += r[field]
        row["securities"].append(r["key"])
        row["source_funds"] = sorted(set(row["source_funds"]) | set(r["source_funds"]))
    ranked = sorted(groups.values(),key=lambda r:-r["total_pct"])
    hhi = sum((r["total_pct"]/total)**2 for r in ranked) if total else None
    return {"status":"PARTIAL_RESEARCH_ONLY" if total else "UNAVAILABLE",
            "method":"CURATED_IDENTIFIER_GROUPS_PLUS_UNVERIFIED_SECURITY_PROXIES",
            "confirmed_mapping_pct":confirmed/total*100 if total else None,
            "confirmed_mapping_nav_pct":confirmed,
            "proxy_nav_pct":total-confirmed,
            "hhi":hhi*10000 if hhi is not None else None,
            "effective_issuers":1/hhi if hhi else None,
            "top5_pct":sum(r["total_pct"] for r in ranked[:5]),
            "top10_pct":sum(r["total_pct"] for r in ranked[:10]),
            "issuer_proxy_count":len(ranked),"rows":ranked[:50],
            "note":"Provisional issuer proxy concentration on mapped equity; unverified securities remain separate. Not certified issuer-level coverage."}

def text(v):
    return str(v or "").strip()
def symbol(v):
    return re.sub(r"[ .-]+","-",text(v).upper())
def isin(h):
    v=text(h.get("id")).upper()
    return v if text(h.get("id_type")).upper()=="ISIN" and re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]",v) else ""
def cusip(h):
    i=isin(h)
    if i.startswith(("US","CA")):return i[2:11]
    v=text(h.get("id")).upper()
    return v if text(h.get("id_type")).upper()=="CUSIP" and re.fullmatch(r"[A-Z0-9]{9}",v) else ""
def alias(h):
    t=symbol(h.get("ticker"));c=text(h.get("country")).casefold();e=text(h.get("exchange")).upper()
    i=isin(h)
    if re.fullmatch(r"\d{4,6}",t) and (c in ("taiwan","台灣") or i.startswith("TW") or e in ("TWSE","TPEX")):return "TW:"+t
    if t and (e in ("NASDAQ","NYSE","NYSE ARCA","NYSE AMERICAN","NASDAQ GS","NASDAQ GLOBAL SELECT") or i.startswith("US")):
        return "US:"+t
    return ""
def country(v):
    s=text(v)
    return {"us":"United States","usa":"United States","united states of america":"United States","united states":"United States","united kingdom":"United Kingdom","taiwan":"Taiwan","uk":"United Kingdom","taiwan, province of china":"Taiwan","台灣":"Taiwan"}.get(s.casefold(),s.title() if s else UNKNOWN)
def sector(v):
    s=text(v)
    return {"information technology":"Information Technology","industrials":"Industrials","financials":"Financials","health care":"Health Care","consumer discretionary":"Consumer Discretionary","consumer staples":"Consumer Staples","energy":"Energy","materials":"Materials","utilities":"Utilities","real estate":"Real Estate","technology":"Information Technology","healthcare":"Health Care","consumer cyclical":"Consumer Discretionary","consumer defensive":"Consumer Staples","financial services":"Financials","basic materials":"Materials","communication services":"Communication Services"}.get(s.casefold(),s.title() if s else UNKNOWN)

def combined_exposure(ex,snapshots=None,as_of=None):
    if snapshots is None:snapshots,_=load_holdings_set()
    as_of=as_of or date.fromisoformat(ex["as_of"])
    # All available snapshots may supply identity/classification evidence.
    # Future-dated snapshots are never used; stale metadata remains flagged.
    valid={};warnings=[]
    for f,s in snapshots.items():
        try:
            d=date.fromisoformat(s["as_of"])
            if d>as_of or s.get("fund")!=f or s.get("lookthrough_mode")!="EQUITY_LOOKTHROUGH":continue
            if not isinstance(s["holdings"],list):continue
            valid[f]=s
        except Exception:continue
    aliases=defaultdict(set);cusips=defaultdict(set)
    for s in valid.values():
        for h in s["holdings"]:
            if h.get("asset_class")!="equity":continue
            if alias(h) and isin(h):aliases[alias(h)].add(isin(h))
            if cusip(h) and isin(h):cusips[cusip(h)].add(isin(h))
    def key(h,f,j):
        i=isin(h);a=alias(h);c=cusip(h)
        if i:return "ISIN:"+i
        if c and len(cusips[c])==1:return "ISIN:"+next(iter(cusips[c]))
        if c and not cusips[c] and not a:return "CUSIP:"+c
        if a and len(aliases[a])==1:return "ISIN:"+next(iter(aliases[a]))
        if a and not aliases[a]:return a
        # Exchange-qualified local identifier, not bare ambiguous ticker.
        e=text(h.get("exchange")).upper();t=symbol(h.get("ticker"))
        if e and t and not a:return "EX:"+e+":"+t
        return "UNMATCHED:"+f+":"+str(j)
    metadata=defaultdict(lambda:{"sector":set(),"country":set()})
    direct_evidence=defaultdict(set)
    for f,s in valid.items():
        for j,h in enumerate(s["holdings"]):
            if h.get("asset_class")!="equity":continue
            k=key(h,f,j)
            if alias(h):direct_evidence[alias(h)].add(k)
            # Stale classifications are not used to fill another snapshot.
            if (as_of-date.fromisoformat(s["as_of"])).days<=_snapshot_stale_limit_days(s):
                for field,fn in (("sector",sector),("country",country)):
                    v=fn(h.get(field))
                    if v!=UNKNOWN:metadata[k][field].add(v)
    hs=ex["holdings"]
    if not math.isclose(sum(float(h["weight"]) for h in hs),1.,abs_tol=1e-8) or any(float(h["weight"])<0 or not math.isfinite(float(h["weight"])) for h in hs):
        raise ValueError("Invalid NAV weight basis")
    rows={};unmapped=[];non_equity=[];funds=[]
    def add(k,t,name,w,f=None,h=None):
        r=rows.setdefault(k,{"key":k,"ticker":t,"name":name,"direct":0.,"indirect":0.,"funds":set(),"sector":set(),"country":set()})
        r["indirect" if f else "direct"]+=w
        if f:r["funds"].add(f)
        if h:
            for field,fn in (("sector",sector),("country",country)):
                v=fn(h.get(field))
                if v!=UNKNOWN:r[field].add(v)
    for h in hs:
        t=h["ticker"];w=float(h["weight"])
        if w<=0:continue
        if t in SUPPORTED_FUNDS:
            s=valid.get(t)
            if not s:
                unmapped.append({"ticker":t,"weight_pct":w*100,"reason":"MISSING_OR_FUTURE_SNAPSHOT"});continue
            try:
                entries=[(j,x,float(x["weight"])) for j,x in enumerate(s["holdings"]) if x.get("asset_class")=="equity"]
                if any(not math.isfinite(v) or v<0 for _,_,v in entries) or sum(v for _,_,v in entries)>1.0000001:raise ValueError()
            except Exception:
                unmapped.append({"ticker":t,"weight_pct":w*100,"reason":"INVALID_EQUITY_WEIGHTS"});continue
            covered=sum(v for _,_,v in entries)
            age=(as_of-date.fromisoformat(s["as_of"])).days
            stale=age>_snapshot_stale_limit_days(s)
            if stale:warnings.append("STALE:"+t)
            if not text(s.get("source_quality")).startswith("OFFICIAL"):warnings.append("NONOFFICIAL:"+t)
            funds.append({"ticker":t,"as_of":s["as_of"],"age_days":age,"stale":stale,"source_quality":s.get("source_quality"),"mapped_pct":w*covered*100})
            for j,x,v in entries:
                if v:add(key(x,t,j),text(x.get("ticker")),text(x.get("name")),w*v,t,x)
            if covered<1:unmapped.append({"ticker":t,"weight_pct":w*(1-covered)*100,"reason":"NON_EQUITY_OR_UNREPORTED_FUND_WEIGHT"})
        elif t== "__TWD_CASH__" or t in SPECIAL_EXPOSURE_MODES or h["bucket"] in ("crypto","gold","cash"):
            non_equity.append({"ticker":t,"weight_pct":w*100})
        else:
            a=("US:" if h["currency"]=="USD" else "TW:")+symbol(t)
            ks=direct_evidence.get(a,set())
            # A known constituent on the same market is evidence for a direct equity.
            # Unknown funds/stocks are not silently treated as single companies.
            if len(ks)==1:add(next(iter(ks)),t,t,w)
            else:unmapped.append({"ticker":t,"weight_pct":w*100,"reason":"DIRECT_EQUITY_IDENTITY_UNVERIFIED"})
    total=sum(r["direct"]+r["indirect"] for r in rows.values())
    unknown=sum(x["weight_pct"] for x in unmapped);other=sum(x["weight_pct"] for x in non_equity)
    if not math.isclose(total*100+unknown+other,100.,abs_tol=1e-6):raise ValueError("Exposure mass identity")
    dist={f:defaultdict(float) for f in ("sector","country")};out=[]
    for k,r in rows.items():
        v=r["direct"]+r["indirect"]
        fields={}
        for f in dist:
            values=r[f]|metadata[k][f]
            label=next(iter(values)) if len(values)==1 else UNKNOWN
            fields[f]=label;dist[f][label]+=v*100
        out.append({"key":k,"ticker":r["ticker"],"name":r["name"],"direct_pct":r["direct"]*100,"indirect_pct":r["indirect"]*100,
                    "total_pct":v*100,"source_funds":sorted(r["funds"]),**fields})
    out.sort(key=lambda r:r["total_pct"],reverse=True)
    hhi=sum((r["total_pct"]/100/total)**2 for r in out) if total else None
    if any(r["key"].startswith("UNMATCHED:") for r in out):warnings.append("UNRESOLVED_SECURITY_IDENTITIES")
    issuer=issuer_concentration(out)
    return {"version":"v3.8.5","status":"PARTIAL_RESEARCH_ONLY" if unknown>1e-8 or warnings or any(UNKNOWN in d for d in dist.values()) else "RESEARCH_ONLY",
            "execution_permission":False,"as_of":ex["as_of"],"snapshot_reference_date":str(as_of),"basis":ex["basis"],
            "mapped_equity_pct":total*100,"unmapped_pct":unknown,"non_equity_pct":other,
            "direct_pct":sum(r["direct_pct"] for r in out),"indirect_pct":sum(r["indirect_pct"] for r in out),
            "top5_pct":sum(r["total_pct"] for r in out[:5]),"top10_pct":sum(r["total_pct"] for r in out[:10]),
            "mapped_equity_hhi":hhi*10000 if hhi else None,"effective_names":1/hhi if hhi else None,
            "issuer_concentration":issuer,
            "mapped_equity_count":len(out),"rows":out[:50],"unmapped":unmapped,"non_equity":non_equity,"funds":funds,"warnings":warnings,
            "sector":[{"label":k,"portfolio_pct":v} for k,v in sorted(dist["sector"].items(),key=lambda x:-x[1])],
            "country":[{"label":k,"portfolio_pct":v} for k,v in sorted(dist["country"].items(),key=lambda x:-x[1])],
            "notes":["All weights relative to model NAV including TWD cash. HHI conditional on mapped equity only, not whole portfolio; unresolved identities may understate concentration.",
                     "Current holdings snapshot dates may differ; stale holdings retained as provisional. Sector/country from supplied records only, conflicts unknown; fresh matched records may fill absent labels. No fund domicile or ISIN prefix used as country classification.",
                     "Direct equity requires matching market-qualified constituent evidence; unknown assets and fund residuals stay unmapped. No derivative notional or nested fund inference. Original security HHI retained; issuer proxy HHI merges curated identifiers only."]}
