"""Exchange-session-aware date-only research marks; not point-in-time prices."""
from functools import lru_cache
import pandas as pd

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
    return pd.Timestamp(session).tz_localize(None).normalize()

def benchmark_calendar(config,group):
    symbol=config.get("proxies",{}).get(group,"")
    if symbol.endswith((".TW",".TWO")):return "XTAI"
    if symbol in {"VT","BOXX","GLDM","VOO","VTI","SPY","BIL","SGOV","SHV","GLD","IAU"}:return "XNYS"
    return None
