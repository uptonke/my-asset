"""Historical quote providers; do not mix dividend-adjusted and actual marks."""
import io
import math
import re
import pandas as pd

FUND_CODES={
    "安聯台灣科技":("ACDD04-NTDEQ0004","安聯台灣科技基金"),
    "統一奔騰":("ACPS10-NTDEQ0030","統一奔騰基金"),
    "統一黑馬":("ACPS02-NTDEQ0040","統一黑馬基金"),
}


def series(s):
    s=pd.to_numeric(s,errors="coerce").dropna()
    s.index=pd.to_datetime(s.index).tz_localize(None).normalize()
    return s[~s.index.duplicated(keep="last")].sort_index()


def parse_fund_nav(html,name):
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(html,"html.parser")
    if name not in soup.get_text():
        raise ValueError("Fund identity mismatch")
    rows={}
    for tr in soup.find_all("tr"):
        cols=[td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols)<2 or not re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}",cols[0]):
            continue
        d=pd.Timestamp(cols[0]);v=float(cols[1].replace(",",""))
        if not math.isfinite(v) or v<=0 or (d in rows and rows[d]!=v):
            raise ValueError("Invalid or conflicting fund NAV")
        rows[d]=v
    if not rows:raise ValueError("No dated fund NAV rows")
    return pd.Series(rows,dtype=float).sort_index()


def merge_fund_archive(ticker, recent, path=None):
    from pathlib import Path
    path=Path(path) if path is not None else Path(__file__).resolve().parents[1]/"data/attribution/fund_nav_history.csv"
    if not path.exists():return recent
    df=pd.read_csv(path,dtype={"ticker":str,"fund_id":str,"currency":str,"source":str})
    required={"ticker","fund_id","currency","date","nav","source"}
    if not required.issubset(df.columns):raise ValueError("Fund archive schema mismatch")
    df=df[df["ticker"]==ticker].copy()
    if df.empty:return recent
    if not (df["fund_id"]==FUND_CODES[ticker][0]).all() or not (df["currency"]=="TWD").all() or df["source"].fillna("").str.strip().eq("").any():
        raise ValueError("Fund archive identity/currency/source mismatch")
    df["date"]=pd.to_datetime(df["date"],format="%Y-%m-%d",errors="raise")
    df["nav"]=pd.to_numeric(df["nav"],errors="raise")
    if df["date"].duplicated().any() or not df["nav"].map(lambda v:math.isfinite(v) and v>0).all():
        raise ValueError("Invalid archive NAV")
    archive=pd.Series(df["nav"].to_numpy(),index=df["date"]).sort_index()
    overlap=recent.index.intersection(archive.index)
    if len(overlap) and ((recent.loc[overlap]/archive.loc[overlap]-1).abs()>.005).any():
        raise ValueError("Fund archive conflicts with recent source")
    return recent.combine_first(archive).sort_index()


def fund_nav(ticker):
    import requests
    code,name=FUND_CODES[ticker]
    url="https://fglife.moneydj.com/w/wr/wr02.djhtm"
    r=requests.get(url,params={"a":code},timeout=20,headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    # Requests may assume ISO-8859-1 for Big5/UTF8 HTML without charset.
    from bs4 import BeautifulSoup
    html=BeautifulSoup(r.content,"html.parser").decode()
    return parse_fund_nav(html,name)


def yahoo_chart(symbol,earliest):
    import requests
    start=int((earliest-pd.Timedelta(days=10)).tz_localize("UTC").timestamp())
    stop=int(pd.Timestamp.now(tz="UTC").timestamp())+86400
    r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/"+symbol,
        params={"period1":start,"period2":stop,"interval":"1d","events":"div,splits","includePrePost":"false"},
        timeout=25,headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    p=r.json()["chart"]["result"][0];meta=p["meta"]
    if str(meta.get("symbol","")).upper()!=symbol.upper():raise ValueError("Quote symbol mismatch")
    tz=meta.get("exchangeTimezoneName")
    if not tz:raise ValueError("Missing quote timezone")
    def dates(x):return pd.to_datetime(x,unit="s",utc=True).tz_convert(tz).tz_localize(None).normalize()
    px=series(pd.Series(p["indicators"]["quote"][0]["close"],index=dates(p["timestamp"])))
    if px.empty:raise ValueError("No historical close")
    events={}
    for event in (p.get("events") or {}).get("splits",{}).values():
        ratio=float(event["numerator"])/float(event["denominator"])
        d=dates([event["date"]])[0]
        if ratio<=0 or not math.isfinite(ratio):raise ValueError("Invalid split")
        events[d]=ratio
    return px,events,str(meta.get("currency","")).upper()


def load_asset(t,cat,earliest,q):
    import yfinance as yf
    if t in FUND_CODES:
        if cat!="基金":raise ValueError("Fund category conflict")
        try: px=fund_nav(t);err=None
        except Exception as exc:
            px=pd.Series(dtype=float);err=str(exc)[:180]
        original=len(px);px=merge_fund_archive(t,px)
        source="MoneyDJ recent 90 NAV observations"+(" + supplied NAV archive" if len(px)>original else "")
        return {"price":px,"splits":[],"split_ratios":{},"foreign":False,"bucket":"taiwan_equity",
                "source":source,"instrument_id":FUND_CODES[t][0],"currency":"TWD",
                "fund_nav_error":err,"fund":True}
    if cat=="__AMBIGUOUS__":raise ValueError("Exchange/currency conflict; confirm TW vs ADR")
    sym=q.yfinance_symbol(t,cat)
    foreign=q.is_foreign_currency_asset(t,cat);expected="USD" if foreign else "TWD"
    # Explicit exchange suffixes must agree with recorded category.
    if (sym.endswith((".TW",".TWO")) and foreign) or (sym=="TSM" and not foreign):
        raise ValueError("Ticker exchange contradicts ledger currency")
    try:
        obj=yf.Ticker(sym)
        h=obj.history(start=(earliest-pd.Timedelta(days=10)).strftime("%Y-%m-%d"),
                      auto_adjust=False,actions=True,raise_errors=True)
        if h.empty or "Close" not in h or "Stock Splits" not in h:raise ValueError("Close/actions unavailable")
        px=series(h["Close"]);events=series(h["Stock Splits"])[lambda x:x!=0].to_dict()
        currency=str(obj.fast_info.currency or "").upper()
        if not currency:raise ValueError("Quote currency unavailable")
        source="yfinance Close (no dividend adjustment)"
    except Exception:
        px,events,currency=yahoo_chart(sym,earliest)
        source="Yahoo chart Close + split events"
    if currency!=expected:raise ValueError("Quote currency does not match ledger classification")
    # FinMind raw marks can fill missing TW dates only on a verified no-split
    # history. Never combine raw and split-normalized prices across a split.
    if not foreign and not events and (px.empty or px.index[0]>earliest+pd.Timedelta(days=7)):
        try:
            raw=q.finmind_request("TaiwanStockPrice",q.finmind_id(t),str(earliest.date()),str(pd.Timestamp.now().date()))
            fm=series(pd.Series(raw["close"].to_numpy(),index=pd.to_datetime(raw["date"])))
            overlap=px.index.intersection(fm.index)
            if len(overlap)>=5 and ((px.loc[overlap]/fm.loc[overlap]-1).abs()<.005).all():
                px=px.combine_first(fm).sort_index();source+=" + FinMind verified raw overlap"
        except Exception: pass
    return {"price":px,"splits":list(events),"split_ratios":events,"foreign":foreign,
            "bucket":q.classify_asset_bucket(t,cat),"source":source,"instrument_id":sym,"currency":currency}
