"""Exchange-session-aware date-only research marks; not point-in-time prices."""
from functools import lru_cache
import pandas as pd

# TWSE emergency closure, announced 2026-07-09: https://www.cna.com.tw/news/afe/202607090360.aspx
# Exchange-calendar packages do not necessarily include unscheduled closures.
CLOSURE_OVERRIDES={"XTAI":frozenset({pd.Timestamp("2026-07-10")})}
# Verified domestic stock fund holiday: https://wealth.firstbank.com.tw/promotion/announcement/latest-news/fund/20260130-1?articleId=%7B05E3FEA9-FA64-4A3D-8DAA-84A0B5F5F111%7D
DOMESTIC_FUNDS=frozenset({"安聯台灣科技","統一奔騰","統一黑馬"})
FUND_HOLIDAY_START=pd.Timestamp("2026-02-12")
FUND_HOLIDAY_END=pd.Timestamp("2026-02-22")

def fund_holiday_calendar(ticker,date):
    # Apply the specific verified holiday only; do not assume every fund
    # follows every exchange session on all dates.
    return "XTAI" if ticker in DOMESTIC_FUNDS and FUND_HOLIDAY_START<=date<=FUND_HOLIDAY_END else None

@lru_cache(maxsize=2)
def exchange(name):
    import exchange_calendars as xcals
    return xcals.get_calendar(name)

@lru_cache(maxsize=4096)
def required_session(name,date):
    d=pd.Timestamp(date).normalize()
    if d.tzinfo is not None:raise ValueError("Expected local calendar date")
    if name not in ("XTAI","XNYS"):raise ValueError("Unsupported exchange calendar")
    session=exchange(name).date_to_session(d,direction="previous")
    session=pd.Timestamp(session).tz_localize(None).normalize()
    while session in CLOSURE_OVERRIDES.get(name,()):
        session=pd.Timestamp(exchange(name).date_to_session(session-pd.Timedelta(days=1),direction="previous")).tz_localize(None).normalize()
    return session

def benchmark_calendar(config,group):
    symbol=config.get("proxies",{}).get(group,"")
    if symbol.endswith((".TW",".TWO")):return "XTAI"
    if symbol in {"VT","BOXX","GLDM","VOO","VTI","SPY","BIL","SGOV","SHV","GLD","IAU"}:return "XNYS"
    return None
