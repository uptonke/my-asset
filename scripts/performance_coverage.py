"""Private historical coverage diagnostics. Never impute missing market prices."""
import math
import pandas as pd
from performance_calendar import required_session, benchmark_calendar

CASH_TOLERANCE_TWD=1.
EPS=1e-8

class CoverageIssue(ValueError):
    def __init__(self,code,ticker,date,reason,**extra):
        super().__init__(reason)
        self.detail={"code":code,"ticker":ticker,"date":str(date.date()),"reason":reason,**extra}

def quote(s,d,age,t,source,kind="PRICE",calendar=None):
    s=s if s is not None else pd.Series(dtype=float)
    before=s.loc[:d] if len(s) else s
    extra={"source":source,"first_available":str(s.index[0].date()) if len(s) else None,
           "last_available":str(s.index[-1].date()) if len(s) else None,
           "last_on_or_before":str(before.index[-1].date()) if len(before) else None,"max_age_days":age}
    if calendar:
        try:expected=required_session(calendar,d)
        except Exception as e:
            raise CoverageIssue("CALENDAR_UNAVAILABLE",t,d,"Exchange calendar unavailable: "+t,calendar=calendar,source=source) from e
        extra.update(calendar=calendar,expected_session=str(expected.date()))
        if expected not in s.index:
            code="BEFORE_FIRST_QUOTE" if kind=="PRICE" and len(s) and expected<s.index[0] else "MISSING_SESSION_"+kind
            raise CoverageIssue(code,t,d,"Missing required session: "+t+" @ "+str(expected.date()),**extra)
        if len(before) and before.index[-1]!=expected:
            raise CoverageIssue("CALENDAR_QUOTE_CONFLICT",t,d,"Quote conflicts with exchange calendar: "+t,**extra)
        before=s.loc[:expected]
    if before.empty or (not calendar and (d-before.index[-1]).days>age):
        code="BEFORE_FIRST_QUOTE" if kind=="PRICE" and len(s) and d<s.index[0] else "MISSING_"+kind
        raise CoverageIssue(code,t,d,"Missing or stale valuation: "+t+" @ "+str(d.date()),**extra)
    v=float(before.iloc[-1])
    if not math.isfinite(v) or v<=0:raise CoverageIssue("INVALID_"+kind,t,d,"Invalid valuation: "+t,**extra)
    return v

def prepare_subscriptions(tx,market):
    """User-verified private paid subscription metadata, never inferred dates."""
    lots={};errors={}
    for x in tx:
        s=x.get("subscription")
        if s is None:continue
        t=x["ticker"]
        try:
            if not isinstance(s,dict) or s.get("verified") is not True or not str(s.get("evidence_ref") or "").strip():
                raise ValueError("Verified evidence required")
            if x["type"]!="buy" or x["qty"]<=0 or x["flow"]>=0 or x.get("category")!="台股":
                raise ValueError("Expected paid TWD equity subscription")
            paid=pd.Timestamp(s["paid_date"]).normalize();switch=pd.Timestamp(s["first_valuation_date"]).normalize()
            if paid!=x["date"] or switch<=paid or t in lots:raise ValueError("Debit date mismatch or multiple lots")
            m=market["assets"].get(t,{})
            if m.get("foreign") is not False or m.get("bucket")!="taiwan_equity" or m.get("splits")!=[] or m.get("split_ratios"):
                raise ValueError("Unverified identity or split basis")
            px=m.get("price")
            if px is None or switch not in px.index or not math.isfinite(float(px.loc[switch])) or float(px.loc[switch])<=0:
                raise ValueError("Exact first valuation date quote required")
            if any(y is not x and y["ticker"]==t and y["qty"] and y["date"]<switch for y in tx):
                raise ValueError("Other trades before conversion")
            lots[t]={"paid":paid,"switch":switch,"qty":x["qty"],"amount":-x["flow"]}
        except Exception as e:errors[t]=str(e)[:180]
    for t in errors:lots.pop(t,None)
    return lots,errors

def asset_mark(t,n,d,market):
    if n<0:raise CoverageIssue("NEGATIVE_INVENTORY",t,d,"Negative inventory: "+t)
    if t in market.get("quarantined",{}):
        raise CoverageIssue("QUARANTINED",t,d,"Quarantined holding: "+t,source=market["quarantined"][t])
    if t in market.get("subscription_errors",{}):
        raise CoverageIssue("SUBSCRIPTION_UNVERIFIED",t,d,"Unverified subscription: "+t,source=market["subscription_errors"][t])
    m=market["assets"].get(t,{})
    if m.get("error"):raise CoverageIssue("PROVIDER_ERROR",t,d,"Market provider error: "+t,source=m["error"])
    if m.get("splits") is None or any(s>d for s in m["splits"]):
        raise CoverageIssue("SPLIT_BASIS",t,d,"Unverified split basis: "+t)
    lot=market.get("subscriptions",{}).get(t)
    if lot and lot["paid"]<=d<lot["switch"]:
        if abs(n-lot["qty"])>EPS:raise CoverageIssue("SUBSCRIPTION_QUANTITY",t,d,"Subscription quantity mismatch: "+t)
        return lot["amount"],True
    p=quote(m.get("price"),d,7,t,m.get("source","unknown"),calendar=m.get("calendar"))
    f=quote(market.get("fx"),d,4,"USD/TWD","portfolio FX","FX") if m.get("foreign") else 1.
    return n*p*f,False

def interval_diagnostics(a,b,tx,categories,market,config,bmarket):
    q=dict.fromkeys(categories,0.);cash=0.
    for x in tx:
        if x["date"]>a:break
        cash+=x["flow"]
        if x["qty"]:q[x["ticker"]]+=x["qty"]
    flows=[x for x in tx if a<x["date"]<=b]
    days=sorted({x["date"] for x in flows}|{b}|{v["switch"] for v in market.get("subscriptions",{}).values() if a<v["switch"]<=b})
    problems={};minimum=cash;pending=set()
    bp,bfx=bmarket
    def record(e):
        z=e.detail;problems[(z["code"],z["ticker"],z["date"])]=z
    def check(d,benchmark=True):
        nonlocal minimum
        minimum=min(minimum,cash)
        if cash < -CASH_TOLERANCE_TWD:
            record(CoverageIssue("NEGATIVE_CASH","CASH",d,"Negative ledger-implied cash",cash_twd=cash))
        for t,n in q.items():
            if abs(n)<EPS:continue
            try:
                _,is_pending=asset_mark(t,n,d,market)
                if market["assets"][t].get("bucket") not in config["weights"]:
                    raise CoverageIssue("UNSUPPORTED_BUCKET",t,d,"Unsupported bucket: "+t)
                if is_pending:pending.add(t)
            except CoverageIssue as e:record(e)
        if benchmark:
            for g in config["weights"]:
                try:quote(bp.get(g),d,7,"BENCHMARK:"+g,"benchmark close","BENCHMARK",benchmark_calendar(config,g))
                except CoverageIssue as e:record(e)
                if config["currency"][g]=="USD":
                    try:quote(bfx,d,4,"BENCHMARK:USD/TWD","benchmark FX","FX")
                    except CoverageIssue as e:record(e)
    check(a)
    for d in days:
        check(d)
        for x in flows:
            if x["date"]==d:
                if x["qty"]:q[x["ticker"]]+=x["qty"]
                cash+=x["flow"]
        check(d,False)
    return {"issues":list(problems.values()),"minimum_ledger_cash_twd":float(minimum),
            "micro_cash_tolerance_used":-CASH_TOLERANCE_TWD<=minimum<0,
            "pending_subscription_tickers":sorted(pending)}


def cash_trace(tx):
    daily={}
    for x in tx:daily.setdefault(x["date"],[]).append(x["flow"])
    balance=0.;minimum=0.;negative=[]
    for d,flows in sorted(daily.items()):
        flow=math.fsum(flows)
        balance=math.fsum([balance,flow]);minimum=min(minimum,balance)
        if balance < -EPS:
            negative.append({"date":str(d.date()),"daily_flow_twd":flow,"cash_twd":balance,
                             "status":"MATERIAL" if balance < -CASH_TOLERANCE_TWD else "MICRO"})
    return {"opening_cash_verified":False,"minimum_cash_twd":minimum,"material_negative_days":sum(r["status"]=="MATERIAL" for r in negative),"negative_days":negative}

def fund_coverage(market):
    rows=[]
    for t,m in market["assets"].items():
        if not m.get("fund"):continue
        s=m.get("price")
        rows.append({"ticker":t,"status":m.get("historical_recovery_status","UNKNOWN"),
                     "source":m.get("source","unknown"),"observations":len(s) if s is not None else 0,
                     "first_available":str(s.index[0].date()) if s is not None and len(s) else None,
                     "last_available":str(s.index[-1].date()) if s is not None and len(s) else None})
    return rows
