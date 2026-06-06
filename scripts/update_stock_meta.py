#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from supabase import create_client

TAIPEI_TZ = timezone(timedelta(hours=8))
TODAY_TPE = datetime.now(TAIPEI_TZ).date()
START_DATE = TODAY_TPE - timedelta(days=760)
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

def env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    return default if value is None or value == "" else value

FINMIND_TOKEN = env("FINMIND_TOKEN")
TWELVE_DATA_API_KEY = env("TWELVE_DATA_API_KEY")
SUPABASE_URL = env("SUPABASE_URL")
SUPABASE_SECRET_KEY = env("SUPABASE_SECRET_KEY")
SUPABASE_TABLE = env("SUPABASE_TABLE", "portfolio_db")
PORTFOLIO_ROW_ID = env("PORTFOLIO_ROW_ID", "1")
DRY_RUN = str(env("DRY_RUN", "false")).lower() in {"1", "true", "yes", "y"}
SYNTHETIC_RISK_KEY = "__synthetic_portfolio_risk__"
SYNTHETIC_EWMA_LAMBDA = 0.94

def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)

def finite_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default

def clamp(x: Any, low: float = 0.0, high: float = 10.0) -> float:
    n = finite_float(x, 0.0) or 0.0
    return round(max(low, min(high, n)), 3)

def pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b - 1.0

def safe_last(series: pd.Series) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return None if s.empty else float(s.iloc[-1])

def to_iso_date(value: Any) -> str:
    return str(value).split("T")[0] if value is not None else str(TODAY_TPE)

def read_ticker_map() -> Dict[str, Dict[str, Any]]:
    path = Path("data/quant_ticker_map.json")
    if not path.exists():
        path = Path("data/quant_ticker_map.sample.json")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(k).upper(): v for k, v in data.items() if isinstance(v, dict)} if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"WARN: failed to read ticker map: {exc}")
        return {}

TICKER_MAP = read_ticker_map()

def connect_supabase():
    if not SUPABASE_URL:
        fail("SUPABASE_URL missing.")
    if not SUPABASE_SECRET_KEY:
        fail("SUPABASE_SECRET_KEY missing.")
    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

def fetch_portfolio_row(client) -> Dict[str, Any]:
    try:
        response = client.table(SUPABASE_TABLE).select("*").eq("id", int(PORTFOLIO_ROW_ID)).single().execute()
        if not response.data:
            fail(f"No row found in {SUPABASE_TABLE} where id={PORTFOLIO_ROW_ID}.")
        return response.data
    except Exception as exc:
        fail(f"Failed to read Supabase row: {exc}")

def active_holdings_from_ledger(ledger_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    holdings: Dict[str, Dict[str, Any]] = {}
    for tx in ledger_data or []:
        ticker = str(tx.get("ticker") or "").strip().upper()
        if not ticker:
            continue
        mapped = TICKER_MAP.get(ticker, {})
        if mapped.get("skip") is True:
            continue
        tx_type = str(tx.get("type") or "").strip()
        if tx_type not in {"Buy", "Sell"}:
            continue
        shares = finite_float(tx.get("shares"), 0.0) or 0.0
        category = str(tx.get("category") or "").strip() or "未知"
        if ticker not in holdings:
            holdings[ticker] = {"ticker": ticker, "category": category, "shares": 0.0, "last_tx_date": to_iso_date(tx.get("date"))}
        holdings[ticker]["shares"] += shares if tx_type == "Buy" else -shares
        holdings[ticker]["category"] = category
        holdings[ticker]["last_tx_date"] = to_iso_date(tx.get("date"))
    return {k: v for k, v in holdings.items() if v["shares"] > 0.0001}

def is_taiwan_asset(ticker: str, category: str) -> bool:
    mapped = TICKER_MAP.get(ticker.upper(), {})
    if mapped.get("source") == "finmind":
        return True
    if mapped.get("source") in {"yfinance", "stooq", "coingecko"}:
        return False
    clean = ticker.upper().replace(".TW", "").replace(".TWO", "")
    return ("台" in str(category or "")) or clean.isdigit()

def finmind_id(ticker: str) -> str:
    mapped = TICKER_MAP.get(ticker.upper(), {})
    return str(mapped.get("finmind_id") or ticker.upper().replace(".TW", "").replace(".TWO", ""))

def yfinance_symbol(ticker: str, category: str) -> str:
    mapped = TICKER_MAP.get(ticker.upper(), {})
    if mapped.get("yf_symbol"):
        return str(mapped["yf_symbol"])
    t = ticker.upper().strip()
    if is_taiwan_asset(t, category):
        return f"{t.replace('.TW', '').replace('.TWO', '')}.TW"
    if "加密" in str(category or "") or t in {"BTC", "ETH", "BTC-USD", "ETH-USD", "SOL"}:
        if t.endswith("-USD"):
            return t
        return f"{t}-USD"
    if t in {"USD/TWD", "USDTWD", "TWD=X"}:
        return "TWD=X"
    return t

def stooq_symbol(ticker: str) -> str:
    mapped = TICKER_MAP.get(ticker.upper(), {})
    if mapped.get("stooq_symbol"):
        return str(mapped["stooq_symbol"]).lower()
    t = yfinance_symbol(ticker, "").upper().replace("-", ".")
    if "." not in t:
        t = f"{t}.US"
    return t.lower()

def coingecko_id(symbol: str) -> Optional[str]:
    t = symbol.upper().replace("-USD", "").replace("USDT", "")
    mapped = TICKER_MAP.get(symbol.upper(), {})
    if mapped.get("coingecko_id"):
        return str(mapped["coingecko_id"])
    return {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}.get(t)

def is_cash_like_asset(ticker: str, category: str) -> bool:
    t = str(ticker or "").upper().strip()
    cat = str(category or "")
    return (
        t in {"BOXX", "BIL", "SHV", "SGOV", "TBIL", "CASH", "TWD", "NTD", "USD"}
        or "現金" in cat
        or "貨幣" in cat
        or "短債" in cat
        or "CASH" in cat.upper()
    )

def is_gold_like_asset(ticker: str, category: str) -> bool:
    t = str(ticker or "").upper().strip()
    cat = str(category or "")
    return (
        t in {"GLD", "GLDM", "IAU", "SGOL", "SGLN", "PHYS"}
        or "黃金" in cat
        or "GOLD" in cat.upper()
    )

def is_crypto_asset(ticker: str, category: str) -> bool:
    t = str(ticker or "").upper().strip()
    cat = str(category or "")
    return (
        t in {"BTC", "ETH", "BTC-USD", "ETH-USD", "SOL", "SOL-USD"}
        or t.endswith("-USD") and t.replace("-USD", "") in {"BTC", "ETH", "SOL"}
        or "加密" in cat
        or "CRYPTO" in cat.upper()
    )

def benchmark_override_symbol(ticker: str) -> str:
    """
    Explicit benchmark override.

    New rule:
    - data/quant_ticker_map.json is mainly for data-source mapping.
    - Benchmark should be inferred automatically.
    - Only these explicit fields override inference:
      beta_benchmark_override / benchmark_override
    - Old `benchmark` fields are ignored to avoid stale manual mappings such as Taiwan assets vs SPY.
    """
    mapped = TICKER_MAP.get(str(ticker or "").upper().strip(), {})
    return str(mapped.get("beta_benchmark_override") or mapped.get("benchmark_override") or "").strip()

def infer_primary_benchmark(ticker: str, category: str) -> str:
    """
    Infer the official dashboard beta benchmark from ticker/category.

    Official beta is a consistent risk model input:
    - Taiwan assets: local equity market beta (^TWII)
    - US/global equities and ETFs: SPY risk-on beta
    - Crypto: SPY risk-on beta, not BTC beta, so BTC/ETH can be compared to equity risk appetite
    - Gold ETFs: GLD
    - Cash-like assets: CASH override
    """
    t = str(ticker or "").upper().strip()

    override = benchmark_override_symbol(t)
    if override:
        return override

    if is_cash_like_asset(t, category):
        return "CASH"
    if is_taiwan_asset(t, category):
        return "^TWII"
    if is_gold_like_asset(t, category):
        return "GLD"
    if is_crypto_asset(t, category):
        return "SPY"
    return "SPY"

def benchmark_symbol(ticker: str, category: str) -> str:
    return infer_primary_benchmark(ticker, category)

def benchmark_candidates(ticker: str, category: str) -> List[str]:
    primary = infer_primary_benchmark(ticker, category)
    if primary == "CASH":
        return ["CASH"]

    candidates = [primary]

    if is_taiwan_asset(ticker, category):
        # Do not fall back to SPY for Taiwan beta. Better to return beta=None than mix regimes.
        candidates += ["^TWII", "0050.TW", "006208.TW"]
    elif is_gold_like_asset(ticker, category):
        candidates += ["GLD", "IAU", "SGOL"]
    elif is_crypto_asset(ticker, category):
        # Official crypto beta is risk-on beta vs equity market.
        # Do NOT fall back to BTC-USD here; BTC vs BTC mechanically becomes beta=1
        # and ETH vs BTC is a different diagnostic metric, not the dashboard beta.
        candidates += ["SPY", "QQQ"]
    else:
        candidates += ["SPY"]

    out: List[str] = []
    seen = set()
    for c in candidates:
        c = str(c or "").strip()
        if c and c not in seen:
            out.append(c)
            seen.add(c)
    return out

def compute_beta_with_benchmark_candidates(asset: pd.DataFrame, candidates: List[str]) -> Tuple[Optional[float], Optional[float], str]:
    for bench_symbol in candidates:
        if bench_symbol == "CASH":
            return 0.0, 0.0, "CASH"
        beta, corr = compute_beta_and_corr(asset, get_benchmark(bench_symbol))
        if beta is not None:
            return beta, corr, bench_symbol
    return None, None, candidates[0] if candidates else ""


def finmind_request(dataset: str, data_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    if not FINMIND_TOKEN:
        raise RuntimeError("FINMIND_TOKEN missing")
    params = {"dataset": dataset, "data_id": data_id, "start_date": start_date, "end_date": end_date}
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    resp = requests.get(FINMIND_URL, params=params, headers=headers, timeout=25)
    if resp.status_code == 402:
        raise RuntimeError("FinMind quota exceeded")
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("data") or []
    return pd.DataFrame(data) if data else pd.DataFrame()

def fetch_finmind_price(ticker: str) -> pd.DataFrame:
    df = finmind_request("TaiwanStockPrice", finmind_id(ticker), str(START_DATE), str(TODAY_TPE))
    if df.empty or "date" not in df.columns or "close" not in df.columns:
        raise RuntimeError(f"FinMind TaiwanStockPrice empty for {ticker}")
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["date"])
    out["close"] = pd.to_numeric(df["close"], errors="coerce")
    out["volume"] = pd.to_numeric(df["Trading_Volume"] if "Trading_Volume" in df.columns else df.get("volume", np.nan), errors="coerce")
    return out.dropna(subset=["date", "close"]).sort_values("date")

def fetch_finmind_valuation(ticker: str) -> Dict[str, Any]:
    try:
        df = finmind_request("TaiwanStockPER", finmind_id(ticker), str(START_DATE), str(TODAY_TPE))
        if df.empty:
            return {}
        latest = df.sort_values("date").iloc[-1].to_dict()
        result: Dict[str, Any] = {}
        for src, dst in [("PER", "pe"), ("PBR", "pb"), ("dividend_yield", "dividend_yield"), ("DividendYield", "dividend_yield")]:
            if src in latest:
                result[dst] = finite_float(latest.get(src))
        return {k: v for k, v in result.items() if v is not None}
    except Exception as exc:
        print(f"WARN: FinMind valuation skipped for {ticker}: {exc}")
        return {}

def fetch_finmind_chip(ticker: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        df = finmind_request("TaiwanStockInstitutionalInvestorsBuySell", finmind_id(ticker), str(TODAY_TPE - timedelta(days=60)), str(TODAY_TPE))
        if not df.empty and {"date", "buy", "sell"}.issubset(df.columns):
            df["date"] = pd.to_datetime(df["date"])
            df["net_buy"] = pd.to_numeric(df["buy"], errors="coerce") - pd.to_numeric(df["sell"], errors="coerce")
            daily = df.groupby("date")["net_buy"].sum().sort_index()
            out["institutional_5d_net_buy"] = float(daily.tail(5).sum())
            out["institutional_20d_net_buy"] = float(daily.tail(20).sum())
    except Exception as exc:
        print(f"WARN: FinMind institutional skipped for {ticker}: {exc}")
    return out

def normalize_yf_download(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    close_col = "Close" if "Close" in df.columns else "Adj Close" if "Adj Close" in df.columns else None
    if not close_col:
        return pd.DataFrame()
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df.index).tz_localize(None)
    out["close"] = pd.to_numeric(df[close_col], errors="coerce")
    out["volume"] = pd.to_numeric(df["Volume"], errors="coerce") if "Volume" in df.columns else np.nan
    return out.dropna(subset=["date", "close"]).sort_values("date")

def fetch_yfinance_price(symbol: str) -> pd.DataFrame:
    df = yf.download(symbol, period="2y", interval="1d", auto_adjust=True, progress=False, threads=False)
    out = normalize_yf_download(df)
    if out.empty:
        raise RuntimeError(f"yfinance empty for {symbol}")
    return out


def fetch_yahoo_chart_price(symbol: str) -> pd.DataFrame:
    """
    Direct Yahoo chart fallback. This avoids some yfinance crumb/session failures.
    It is still an unofficial Yahoo endpoint, so it is only a fallback for personal dashboard use.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        "range": "2y",
        "interval": "1d",
        "includePrePost": "false",
        "events": "history",
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
    }
    resp = requests.get(url, params=params, headers=headers, timeout=25)
    resp.raise_for_status()
    payload = resp.json()
    result = (((payload.get("chart") or {}).get("result") or [])[:1])
    if not result:
        raise RuntimeError(f"YahooChart empty for {symbol}")

    r = result[0]
    timestamps = r.get("timestamp") or []
    quote = (((r.get("indicators") or {}).get("quote") or [])[:1])
    adj = (((r.get("indicators") or {}).get("adjclose") or [])[:1])

    if not timestamps or not quote:
        raise RuntimeError(f"YahooChart malformed for {symbol}")

    q = quote[0]
    close_values = None
    if adj and isinstance(adj[0], dict) and adj[0].get("adjclose"):
        close_values = adj[0].get("adjclose")
    if close_values is None:
        close_values = q.get("close")

    if not close_values:
        raise RuntimeError(f"YahooChart missing close for {symbol}")

    out = pd.DataFrame({
        "date": pd.to_datetime(timestamps, unit="s"),
        "close": pd.to_numeric(close_values, errors="coerce"),
        "volume": pd.to_numeric(q.get("volume", [np.nan] * len(timestamps)), errors="coerce"),
    })
    out = out.dropna(subset=["date", "close"]).sort_values("date")
    out = out[out["date"] >= pd.Timestamp(START_DATE)]
    if len(out) < 40:
        raise RuntimeError(f"YahooChart too few rows for {symbol}: {len(out)}")
    return out


def fetch_coinbase_price(symbol: str) -> pd.DataFrame:
    """
    Coinbase Exchange candles fallback for major crypto pairs.
    Coinbase only returns limited candles per request, so this paginates in 250-day chunks.
    """
    t = symbol.upper().replace("USDT", "-USD")
    if t in {"BTC", "ETH", "SOL"}:
        product_id = f"{t}-USD"
    elif t in {"BTC-USD", "ETH-USD", "SOL-USD"}:
        product_id = t
    else:
        raise RuntimeError(f"Coinbase product unsupported for {symbol}")

    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=730)
    rows = []

    cursor = start_dt
    while cursor < end_dt:
        chunk_end = min(cursor + timedelta(days=250), end_dt)
        url = f"https://api.exchange.coinbase.com/products/{product_id}/candles"
        params = {
            "granularity": 86400,
            "start": cursor.isoformat(),
            "end": chunk_end.isoformat(),
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            rows.extend(data)
        cursor = chunk_end + timedelta(seconds=1)
        time.sleep(0.15)

    if len(rows) < 40:
        raise RuntimeError(f"Coinbase empty for {product_id}")

    # Coinbase candle row: [time, low, high, open, close, volume]
    df = pd.DataFrame(rows, columns=["ts", "low", "high", "open", "close", "volume"])
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["ts"], unit="s")
    out["close"] = pd.to_numeric(df["close"], errors="coerce")
    out["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    out = out.dropna(subset=["date", "close"]).drop_duplicates(subset=["date"]).sort_values("date")
    out = out[out["date"] >= pd.Timestamp(START_DATE)]
    if len(out) < 40:
        raise RuntimeError(f"Coinbase too few rows for {product_id}: {len(out)}")
    return out

def fetch_stooq_price(symbol: str) -> pd.DataFrame:
    stooq = stooq_symbol(symbol)
    url = f"https://stooq.com/q/d/l/?s={stooq}&i=d"
    resp = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    text = resp.text.strip()
    if not text or "No data" in text or len(text.splitlines()) < 40:
        raise RuntimeError(f"Stooq empty for {stooq}")
    from io import StringIO
    df = pd.read_csv(StringIO(text))
    if "Date" not in df.columns or "Close" not in df.columns:
        raise RuntimeError(f"Stooq malformed for {stooq}")
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["Date"])
    out["close"] = pd.to_numeric(df["Close"], errors="coerce")
    out["volume"] = pd.to_numeric(df["Volume"], errors="coerce") if "Volume" in df.columns else np.nan
    out = out[out["date"] >= pd.Timestamp(START_DATE)]
    return out.dropna(subset=["date", "close"]).sort_values("date")

def fetch_coingecko_price(symbol: str) -> pd.DataFrame:
    gid = coingecko_id(symbol)
    if not gid:
        raise RuntimeError(f"CoinGecko id missing for {symbol}")
    url = f"https://api.coingecko.com/api/v3/coins/{gid}/market_chart"
    resp = requests.get(url, params={"vs_currency": "usd", "days": "730", "interval": "daily"}, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    data = resp.json()
    prices = data.get("prices") or []
    vols = data.get("total_volumes") or []
    if len(prices) < 40:
        raise RuntimeError(f"CoinGecko empty for {symbol}")
    df = pd.DataFrame(prices, columns=["ts", "close"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms")
    if vols:
        vdf = pd.DataFrame(vols, columns=["ts", "volume"])
        vdf["date"] = pd.to_datetime(vdf["ts"], unit="ms")
        df = df.merge(vdf[["date", "volume"]], on="date", how="left")
    else:
        df["volume"] = np.nan
    return df[["date", "close", "volume"]].dropna(subset=["date", "close"]).sort_values("date")

def fetch_twelve_data_price(symbol: str) -> pd.DataFrame:
    if not TWELVE_DATA_API_KEY:
        raise RuntimeError("Twelve Data key not configured")
    resp = requests.get("https://api.twelvedata.com/time_series", params={"symbol": symbol, "interval": "1day", "outputsize": 520, "apikey": TWELVE_DATA_API_KEY, "format": "JSON"}, timeout=25)
    resp.raise_for_status()
    data = resp.json()
    values = data.get("values") or []
    if not values:
        raise RuntimeError(f"Twelve Data empty for {symbol}")
    df = pd.DataFrame(values)
    df["date"] = pd.to_datetime(df["datetime"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce") if "volume" in df.columns else np.nan
    return df[["date", "close", "volume"]].dropna(subset=["date", "close"]).sort_values("date")

def fetch_history(ticker: str, category: str) -> Tuple[pd.DataFrame, str, Dict[str, Any]]:
    extras: Dict[str, Any] = {}
    mapped = TICKER_MAP.get(ticker.upper(), {})
    if mapped.get("skip") is True:
        raise RuntimeError("ticker marked skip in data/quant_ticker_map.json")

    if is_taiwan_asset(ticker, category):
        try:
            df = fetch_finmind_price(ticker)
            extras.update(fetch_finmind_valuation(ticker))
            extras.update(fetch_finmind_chip(ticker))
            time.sleep(0.35)
            return df, "FinMind", extras
        except Exception as exc:
            print(f"WARN: FinMind price failed for {ticker}: {exc}; trying yfinance fallback")

    symbol = yfinance_symbol(ticker, category)
    errors = []

    for name, fn in [
        ("YahooChart", lambda: fetch_yahoo_chart_price(symbol)),
        ("yfinance", lambda: fetch_yfinance_price(symbol)),
        ("Coinbase", lambda: fetch_coinbase_price(symbol)),
        ("Stooq", lambda: fetch_stooq_price(symbol)),
    ]:
        try:
            df = fn()
            return df, f"{name}:{symbol}", extras
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            print(f"WARN: {name} failed for {ticker} ({symbol}): {exc}")

    if TWELVE_DATA_API_KEY:
        try:
            return fetch_twelve_data_price(symbol), f"TwelveData:{symbol}", extras
        except Exception as exc:
            errors.append(f"TwelveData: {exc}")

    raise RuntimeError("all free sources failed; " + " | ".join(errors))

_BENCHMARK_CACHE: Dict[str, pd.DataFrame] = {}

def get_benchmark(symbol: str) -> pd.DataFrame:
    if symbol not in _BENCHMARK_CACHE:
        for name, fn in [
            ("YahooChart", lambda: fetch_yahoo_chart_price(symbol)),
            ("yfinance", lambda: fetch_yfinance_price(symbol)),
            ("Stooq", lambda: fetch_stooq_price(symbol)),
        ]:
            try:
                _BENCHMARK_CACHE[symbol] = fn()
                break
            except Exception as exc:
                print(f"WARN: benchmark {symbol} {name} unavailable: {exc}")
        else:
            _BENCHMARK_CACHE[symbol] = pd.DataFrame()
    return _BENCHMARK_CACHE[symbol]

def rsi(close: pd.Series, period: int = 14) -> Optional[float]:
    close = pd.to_numeric(close, errors="coerce").dropna()
    if len(close) < period + 2:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    value = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
    return safe_last(value)

def macd_hist(close: pd.Series) -> Optional[float]:
    close = pd.to_numeric(close, errors="coerce").dropna()
    if len(close) < 35:
        return None
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return safe_last(macd - signal)

def max_drawdown(close: pd.Series) -> Optional[float]:
    close = pd.to_numeric(close, errors="coerce").dropna()
    if close.empty:
        return None
    return safe_last((close / close.cummax() - 1).cummin())

def compute_beta_and_corr(asset: pd.DataFrame, bench: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    if asset.empty or bench.empty:
        return None, None
    a = asset[["date", "close"]].copy()
    b = bench[["date", "close"]].copy()
    a["date"] = pd.to_datetime(a["date"]).dt.date
    b["date"] = pd.to_datetime(b["date"]).dt.date
    merged = pd.merge(a, b, on="date", suffixes=("_asset", "_bench")).sort_values("date")
    if len(merged) < 80:
        return None, None
    aligned = pd.concat([merged["close_asset"].pct_change(), merged["close_bench"].pct_change()], axis=1).dropna()
    aligned.columns = ["asset", "bench"]
    if len(aligned) < 60:
        return None, None
    var = float(np.var(aligned["bench"], ddof=1))
    if var == 0 or not math.isfinite(var):
        return None, None
    beta = float(np.cov(aligned["asset"], aligned["bench"], ddof=1)[0, 1] / var)
    corr = float(aligned["asset"].corr(aligned["bench"]))
    return beta, corr

def score_trend(m1, m3, m6, m12, ma60, ma200) -> float:
    score = 5.0
    for val, weight in [(m1, 10.0), (m3, 8.0), (m6, 5.0), (m12, 3.5), (ma60, 7.0), (ma200, 5.0)]:
        if val is not None:
            score += max(-1.6, min(1.6, val * weight))
    return clamp(score)

def score_risk(vol60, vol252, mdd, beta, corr) -> float:
    score = 3.0
    v = vol252 if vol252 is not None else vol60
    if v is not None:
        score += max(0.0, min(3.0, v * 10.0))
    if mdd is not None:
        score += max(0.0, min(2.2, abs(mdd) * 6.0))
    if beta is not None:
        score += max(-1.0, min(1.8, (beta - 1.0) * 1.2))
    if corr is not None:
        score += max(0.0, min(1.0, abs(corr) * 0.8))
    return clamp(score)

def score_technical(rsi_val, macd_h, ma20, ma60, ma200) -> float:
    score = 5.0
    if rsi_val is not None:
        if 52 <= rsi_val <= 68:
            score += 1.8
        elif 45 <= rsi_val < 52:
            score += 0.6
        elif 68 < rsi_val <= 75:
            score += 0.3
        elif rsi_val > 75:
            score -= 1.5
        elif rsi_val < 35:
            score -= 1.2
    if macd_h is not None:
        score += 1.0 if macd_h > 0 else -0.8
    for gap, weight in [(ma20, 0.8), (ma60, 1.0), (ma200, 1.0)]:
        if gap is not None:
            score += max(-weight, min(weight, gap * 12.0))
    return clamp(score)

def score_chip(extras: Dict[str, Any]) -> Optional[float]:
    if not any(k in extras for k in ["institutional_5d_net_buy", "institutional_20d_net_buy"]):
        return None
    score = 5.0
    for key, weight in [("institutional_5d_net_buy", 0.7), ("institutional_20d_net_buy", 1.2)]:
        val = finite_float(extras.get(key))
        if val is not None:
            score += weight if val > 0 else -weight
    return clamp(score)

def score_valuation(extras: Dict[str, Any]) -> Tuple[float, float]:
    score = 5.0
    pe = finite_float(extras.get("pe"))
    pb = finite_float(extras.get("pb"))
    if pe is not None:
        if pe <= 0:
            score -= 2.0
        elif pe < 12:
            score += 1.5
        elif pe < 22:
            score += 0.7
        elif pe > 45:
            score -= 2.0
        elif pe > 30:
            score -= 1.0
    if pb is not None:
        if pb < 1.5:
            score += 1.0
        elif pb > 8:
            score -= 1.5
        elif pb > 4:
            score -= 0.7
    attractiveness = clamp(score)
    return attractiveness, clamp(10.0 - attractiveness)

def score_liquidity(df: pd.DataFrame) -> Optional[float]:
    if "volume" not in df.columns or df["volume"].dropna().empty:
        return None
    adv = pd.to_numeric(df.tail(60)["volume"], errors="coerce").dropna().mean()
    if not math.isfinite(adv) or adv <= 0:
        return None
    return clamp(2.5 + math.log10(max(adv, 1)) * 1.15)

def compute_meta(ticker: str, category: str, df: pd.DataFrame, source: str, extras: Dict[str, Any]) -> Dict[str, Any]:
    df = df.dropna(subset=["close"]).sort_values("date").copy()
    close = pd.to_numeric(df["close"], errors="coerce").dropna()
    returns = close.pct_change().dropna()
    if len(close) < 40:
        raise RuntimeError(f"insufficient price history for {ticker}: {len(close)} rows")
    last_price = safe_last(close)
    p21 = float(close.iloc[-22]) if len(close) >= 22 else None
    p63 = float(close.iloc[-64]) if len(close) >= 64 else None
    p126 = float(close.iloc[-127]) if len(close) >= 127 else None
    p252 = float(close.iloc[-253]) if len(close) >= 253 else None
    mom1, mom3, mom6, mom12 = pct(last_price, p21), pct(last_price, p63), pct(last_price, p126), pct(last_price, p252)
    vol20 = float(returns.tail(20).std(ddof=1) * math.sqrt(252)) if len(returns) >= 20 else None
    vol60 = float(returns.tail(60).std(ddof=1) * math.sqrt(252)) if len(returns) >= 60 else None
    vol252 = float(returns.tail(252).std(ddof=1) * math.sqrt(252)) if len(returns) >= 252 else None
    rsi_val, macd_h = rsi(close), macd_hist(close)
    ma20, ma60, ma200 = safe_last(close.rolling(20).mean()), safe_last(close.rolling(60).mean()), safe_last(close.rolling(200).mean())
    ma20_gap, ma60_gap, ma200_gap = pct(last_price, ma20), pct(last_price, ma60), pct(last_price, ma200)
    mdd_1y = max_drawdown(close.tail(min(len(close), 252)))
    beta, corr, bench_symbol = compute_beta_with_benchmark_candidates(df, benchmark_candidates(ticker, category))
    trend = score_trend(mom1, mom3, mom6, mom12, ma60_gap, ma200_gap)
    risk_s = score_risk(vol60, vol252, mdd_1y, beta, corr)
    tech = score_technical(rsi_val, macd_h, ma20_gap, ma60_gap, ma200_gap)
    chip = score_chip(extras)
    valuation, valuation_pressure = score_valuation(extras)
    liquidity = score_liquidity(df)
    beta_for_risk = beta if beta is not None else 1.0
    corr_for_risk = corr if corr is not None else 0.0
    contagion = clamp((abs(beta_for_risk) * 3.0) + (abs(corr_for_risk) * 4.0))
    quant_health = clamp(0.30 * trend + 0.20 * tech + 0.15 * (chip if chip is not None else 5.0) + 0.15 * valuation + 0.20 * (10.0 - risk_s))
    last_date = pd.to_datetime(df["date"].iloc[-1]).date()
    days_stale = (TODAY_TPE - last_date).days
    coverage_score = clamp(len(df) / 252.0, 0, 1)

    meta = {
        "beta": round(beta, 2) if beta is not None else None,
        "std": round((vol252 if vol252 is not None else vol60 or 0) * 100, 3),
        "vol_20d": round(vol20, 6) if vol20 is not None else None,
        "vol_60d": round(vol60, 6) if vol60 is not None else None,
        "vol_252d": round(vol252, 6) if vol252 is not None else None,
        "rsi": round(rsi_val, 3) if rsi_val is not None else None,
        "macd_h": round(macd_h, 6) if macd_h is not None else None,
        "mom_1m": round(mom1, 6) if mom1 is not None else None,
        "mom_3m": round(mom3, 6) if mom3 is not None else None,
        "mom_6m": round(mom6, 6) if mom6 is not None else None,
        "mom_12m": round(mom12, 6) if mom12 is not None else None,
        "ma20_gap": round(ma20_gap, 6) if ma20_gap is not None else None,
        "ma60_gap": round(ma60_gap, 6) if ma60_gap is not None else None,
        "ma200_gap": round(ma200_gap, 6) if ma200_gap is not None else None,
        "max_drawdown_1y": round(mdd_1y, 6) if mdd_1y is not None else None,
        "trend_score": trend,
        "momentum_score": trend,
        "risk_score": risk_s,
        "technical_score": tech,
        "chip_score": chip,
        "valuation_score": valuation,
        "valuation_pressure": valuation_pressure,
        "valuation_risk_score": valuation_pressure,
        "liquidity_score": liquidity,
        "contagion_score": contagion,
        "quant_health_score": quant_health,
        "benchmark": bench_symbol,
        "beta_benchmark": bench_symbol,
        "beta_method": "cash_like_override" if bench_symbol == "CASH" else "auto_inferred_benchmark_daily_return_covariance",
        "beta_inference_rule": "auto_infer_from_ticker_category_with_optional_override",
        "source": source,
        "lookback_days": int(len(df)),
        "coverage_score": round(coverage_score, 3),
        "data_quality": "stale" if days_stale > 10 else ("thin" if len(df) < 120 else "ok"),
        "stale": bool(days_stale > 10),
        "last_market_date": str(last_date),
        "updated_at": str(TODAY_TPE),
    }
    for key, value in extras.items():
        if value is None:
            continue
        meta[key] = round(float(value), 6) if isinstance(value, (int, float, np.integer, np.floating)) else value
    return {k: v for k, v in meta.items() if v is not None}


def is_foreign_currency_asset(ticker: str, category: str) -> bool:
    """Return True if the asset should be converted from USD to TWD for synthetic risk."""
    t = str(ticker or "").upper()
    cat = str(category or "")
    if t in {"TWD", "CASH", "NTD"}:
        return False
    if is_taiwan_asset(t, cat):
        return False
    if "美" in cat or "加密" in cat or "美元" in cat:
        return True
    # Most non-TW tickers in this dashboard are USD quoted ETFs/stocks/crypto.
    return True


def clean_price_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty or "date" not in df.columns or "close" not in df.columns:
        return pd.Series(dtype=float)
    out = df[["date", "close"]].copy()
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None).dt.normalize()
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna(subset=["date", "close"]).drop_duplicates(subset=["date"]).sort_values("date")
    if out.empty:
        return pd.Series(dtype=float)
    return pd.Series(out["close"].values, index=out["date"], dtype=float)


def fetch_usdtwd_series(static_fx: float) -> Tuple[pd.Series, str]:
    """Fetch USD/TWD history. If unavailable, return an empty series and use static FX later."""
    try:
        fx_df = fetch_yahoo_chart_price("TWD=X")
        fx = clean_price_series(fx_df)
        if len(fx) >= 40:
            return fx, "YahooChart:TWD=X"
    except Exception as exc:
        print(f"WARN: USD/TWD historical FX unavailable, using static exchange rate: {exc}")
    return pd.Series(dtype=float), f"static_exchange_rate:{static_fx}"


def max_drawdown_from_returns(returns: pd.Series) -> Optional[float]:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    if r.empty:
        return None
    curve = (1.0 + r).cumprod()
    peak = curve.cummax()
    dd = curve / peak - 1.0
    return float(dd.min())


def ewma_annual_vol(returns: pd.Series, lam: float = SYNTHETIC_EWMA_LAMBDA) -> Optional[float]:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    if len(r) < 20:
        return None
    alpha = 1.0 - lam
    vol = r.ewm(alpha=alpha, adjust=False).std(bias=False).iloc[-1]
    if not math.isfinite(vol):
        return None
    return float(vol * math.sqrt(252))


def confidence_from_sample(sample_count: int, included_weight_pct: float, asset_count: int) -> Tuple[str, str]:
    if asset_count < 2:
        return "INVALID", "可用標的少於 2 檔，無法形成有意義的合成投組。"
    if sample_count < 252:
        return "INVALID", "日資料樣本少於 252 筆，僅能作為除錯參考。"
    if included_weight_pct < 80:
        return "LOW", "可納入合成模型的持倉權重低於 80%，結果可能偏誤。"
    if sample_count >= 1250 and included_weight_pct >= 90:
        return "HIGH", "樣本約 5 年以上且涵蓋主要持倉。"
    if sample_count >= 750 and included_weight_pct >= 85:
        return "MEDIUM", "樣本約 3 年以上，適合作為主要風控參考。"
    return "LOW", "樣本約 1–3 年或資料涵蓋度有限，適合作為 v0.2 監控，不適合直接作為交易引擎。"


def compute_synthetic_portfolio_risk(
    holdings: Dict[str, Dict[str, Any]],
    history_frames: Dict[str, Tuple[pd.DataFrame, str]],
    row: Dict[str, Any],
) -> Dict[str, Any]:
    """
    v0.2 Synthetic Portfolio Risk Engine.

    Method:
    - Use current active holding weights.
    - Convert foreign/USD assets to TWD with USD/TWD history when available.
    - Build current-weight synthetic daily portfolio returns.
    - Estimate volatility, VaR, ES, MDD, EWMA volatility, and component risk.
    """
    settings = row.get("settings") if isinstance(row.get("settings"), dict) else {}
    static_fx = finite_float(settings.get("exchangeRate"), 31.5) or 31.5
    fx_series, fx_source = fetch_usdtwd_series(static_fx)

    asset_prices_twd: Dict[str, pd.Series] = {}
    asset_sources: Dict[str, str] = {}
    asset_weights_value: Dict[str, float] = {}
    asset_meta: Dict[str, Any] = {}

    for ticker, h in sorted((holdings or {}).items()):
        if ticker not in history_frames:
            continue

        df, source = history_frames[ticker]
        price = clean_price_series(df)
        if len(price) < 40:
            continue

        category = str(h.get("category") or "")
        is_foreign = is_foreign_currency_asset(ticker, category)

        if is_foreign:
            if not fx_series.empty:
                aligned_fx = fx_series.reindex(price.index).ffill().bfill()
                price_twd = price * aligned_fx
                fx_mode = fx_source
            else:
                price_twd = price * static_fx
                fx_mode = f"static_exchange_rate:{static_fx}"
        else:
            price_twd = price
            fx_mode = "native_twd"

        price_twd = pd.to_numeric(price_twd, errors="coerce").dropna()
        if len(price_twd) < 40:
            continue

        shares = finite_float(h.get("shares"), 0.0) or 0.0
        latest_price_twd = float(price_twd.iloc[-1])
        market_value_twd = max(0.0, shares * latest_price_twd)

        if market_value_twd <= 0:
            continue

        asset_prices_twd[ticker] = price_twd
        asset_sources[ticker] = source
        asset_weights_value[ticker] = market_value_twd
        asset_meta[ticker] = {
            "ticker": ticker,
            "category": category,
            "source": source,
            "fx_mode": fx_mode,
            "rows": int(len(price_twd)),
            "start_date": str(price_twd.index.min().date()),
            "end_date": str(price_twd.index.max().date()),
            "market_value_twd": round(market_value_twd, 0),
        }

    if len(asset_prices_twd) < 2:
        return {
            "version": "v0.2",
            "status": "INVALID",
            "confidence": "INVALID",
            "confidence_reason": "可用持倉歷史資料少於 2 檔。",
            "updated_at": str(TODAY_TPE),
            "method": "current_weight_synthetic_daily_returns",
            "currency": "TWD",
            "fx_source": fx_source,
            "metrics": {},
            "components": [],
            "assets": list(asset_meta.values()),
        }

    total_mv = sum(asset_weights_value.values())
    weights = {t: v / total_mv for t, v in asset_weights_value.items() if total_mv > 0}

    prices = pd.concat(asset_prices_twd, axis=1).sort_index().ffill().dropna()
    returns = prices.pct_change().dropna(how="any")

    if len(returns) < 40:
        return {
            "version": "v0.2",
            "status": "INVALID",
            "confidence": "INVALID",
            "confidence_reason": "合成後共同日報酬樣本少於 40 筆。",
            "updated_at": str(TODAY_TPE),
            "method": "current_weight_synthetic_daily_returns",
            "currency": "TWD",
            "fx_source": fx_source,
            "metrics": {"sample_count": int(len(returns))},
            "components": [],
            "assets": list(asset_meta.values()),
        }

    tickers = list(returns.columns)
    w = np.array([weights[t] for t in tickers], dtype=float)
    w = w / w.sum()

    port = returns.dot(w)
    port = pd.to_numeric(port, errors="coerce").dropna()

    q05 = float(port.quantile(0.05))
    q01 = float(port.quantile(0.01))
    tail95 = port[port <= q05]
    tail99 = port[port <= q01]

    ann_return = float(((1.0 + port.mean()) ** 252) - 1.0) if len(port) else None
    ann_vol = float(port.std(ddof=1) * math.sqrt(252)) if len(port) > 1 else None
    ewma_vol = ewma_annual_vol(port)
    mdd = max_drawdown_from_returns(port)

    included_weight_pct = 100.0  # weights are normalized across all usable active holdings.
    confidence, confidence_reason = confidence_from_sample(len(port), included_weight_pct, len(tickers))

    cov = returns[tickers].cov() * 252
    port_var = float(w @ cov.values @ w.T) if len(tickers) else 0.0
    marginal = cov.values @ w.T if port_var > 0 else np.zeros(len(tickers))
    rc = w * marginal / port_var if port_var > 0 else np.zeros(len(tickers))

    components = []
    tail_returns = returns.loc[tail95.index, tickers] if not tail95.empty else pd.DataFrame(columns=tickers)

    for i, ticker in enumerate(tickers):
        r = pd.to_numeric(returns[ticker], errors="coerce").dropna()
        asset_tail_contrib = None
        if not tail_returns.empty:
            asset_tail_contrib = float(-(tail_returns[ticker] * w[i]).mean())

        components.append({
            "ticker": ticker,
            "weight_pct": round(float(w[i] * 100.0), 2),
            "variance_risk_contribution_pct": round(float(rc[i] * 100.0), 2) if math.isfinite(float(rc[i])) else None,
            "tail_loss_contribution_pct": round((asset_tail_contrib or 0.0) * 100.0, 3),
            "ann_vol_pct": round(float(r.std(ddof=1) * math.sqrt(252) * 100.0), 2) if len(r) > 1 else None,
            "sample_days": int(len(r)),
            "source": asset_sources.get(ticker, "unknown"),
        })

    components.sort(key=lambda x: (x.get("variance_risk_contribution_pct") or 0), reverse=True)

    q95_pos = float(port.quantile(0.95))
    tail_ratio = q95_pos / abs(q05) if q05 < 0 else None

    metrics = {
        "sample_count": int(len(port)),
        "start_date": str(port.index.min().date()),
        "end_date": str(port.index.max().date()),
        "asset_count": int(len(tickers)),
        "included_weight_pct": round(included_weight_pct, 1),
        "ann_return_pct": round((ann_return or 0.0) * 100.0, 2),
        "ann_vol_pct": round((ann_vol or 0.0) * 100.0, 2),
        "ewma_vol_pct": round((ewma_vol or 0.0) * 100.0, 2) if ewma_vol is not None else None,
        "var95_pct": round(max(0.0, -q05) * 100.0, 2),
        "es95_pct": round(max(0.0, -float(tail95.mean())) * 100.0, 2) if not tail95.empty else None,
        "var99_pct": round(max(0.0, -q01) * 100.0, 2),
        "es99_pct": round(max(0.0, -float(tail99.mean())) * 100.0, 2) if not tail99.empty else None,
        "max_drawdown_pct": round((mdd or 0.0) * 100.0, 2),
        "worst_day_pct": round(float(port.min()) * 100.0, 2),
        "best_day_pct": round(float(port.max()) * 100.0, 2),
        "tail_ratio": round(float(tail_ratio), 2) if tail_ratio is not None and math.isfinite(float(tail_ratio)) else None,
    }

    return {
        "version": "v0.2",
        "status": "OK" if confidence != "INVALID" else "INVALID",
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "updated_at": str(TODAY_TPE),
        "method": "current_weight_synthetic_daily_returns",
        "currency": "TWD",
        "fx_source": fx_source,
        "metrics": metrics,
        "components": components[:10],
        "assets": list(asset_meta.values()),
        "assumptions": [
            "使用目前持倉權重回套歷史日報酬，不代表真實歷史投組績效。",
            "外幣資產盡量用 USD/TWD 歷史匯率轉成 TWD；若匯率資料失敗，改用目前 exchangeRate 靜態轉換。",
            "v0.2 是風控監控引擎，不是自動交易或最佳化引擎。",
        ],
    }


def merge_stock_meta(existing: Dict[str, Any], new_meta: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    merged = dict(existing or {})
    for ticker, meta in new_meta.items():
        old = merged.get(ticker, {})
        if not isinstance(old, dict):
            old = {}
        merged[ticker] = {**old, **meta}
    return merged

def write_supabase_stock_meta(client, merged_stock_meta: Dict[str, Any]) -> None:
    if DRY_RUN:
        print("DRY_RUN=true, not writing to Supabase.")
        return
    try:
        client.table(SUPABASE_TABLE).upsert({"id": int(PORTFOLIO_ROW_ID), "stock_meta": merged_stock_meta}, on_conflict="id").execute()
    except Exception as exc:
        fail(f"Failed to write Supabase stock_meta: {exc}")

def write_github_summary(results: Dict[str, Any]) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [
        "# Stock Meta Quant Pipeline",
        "",
        f"- Date: `{TODAY_TPE}`",
        f"- Dry run: `{DRY_RUN}`",
        f"- Updated tickers: `{len(results.get('updated', []))}`",
        f"- Failed tickers: `{len(results.get('failed', []))}`",
        f"- Skipped tickers: `{len(results.get('skipped', []))}`",
        "",
    ]
    if results.get("updated"):
        lines.append("| Ticker | Source | Health | Trend | Risk | Technical | Data Quality |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for item in results["updated"]:
            lines.append(f"| {item['ticker']} | {item['source']} | {item.get('quant_health_score', 'N/A')} | {item.get('trend_score', 'N/A')} | {item.get('risk_score', 'N/A')} | {item.get('technical_score', 'N/A')} | {item.get('data_quality', 'N/A')} |")
    if results.get("synthetic_risk"):
        sr = results["synthetic_risk"]
        lines.extend(["", "## Synthetic Portfolio Risk v0.2", ""])
        lines.append(f"- Status: `{sr.get('status', 'N/A')}`")
        lines.append(f"- Confidence: `{sr.get('confidence', 'N/A')}`")
        lines.append(f"- Sample count: `{sr.get('sample_count', 'N/A')}`")
        lines.append(f"- Ann Vol: `{sr.get('ann_vol_pct', 'N/A')}%`")
        lines.append(f"- VaR 95: `{sr.get('var95_pct', 'N/A')}%`")
        lines.append(f"- ES 95: `{sr.get('es95_pct', 'N/A')}%`")
    lines.extend(["", "## Failed", ""])
    if results.get("failed"):
        lines.append("| Ticker | Error |")
        lines.append("|---|---|")
        for item in results["failed"]:
            lines.append(f"| {item['ticker']} | {item['error']} |")
    else:
        lines.append("N/A")
    if results.get("skipped"):
        lines.extend(["", "## Skipped", ""])
        lines.append("| Ticker | Reason |")
        lines.append("|---|---|")
        for item in results["skipped"]:
            lines.append(f"| {item['ticker']} | {item['reason']} |")
    Path(path).write_text("\n".join(lines), encoding="utf-8")

def main() -> None:
    print("Starting stock_meta quant update...")
    print(f"Target table={SUPABASE_TABLE}, row_id={PORTFOLIO_ROW_ID}, dry_run={DRY_RUN}")
    client = connect_supabase()
    row = fetch_portfolio_row(client)
    ledger = row.get("ledger_data") or []
    if not isinstance(ledger, list):
        fail("ledger_data is not a list.")
    holdings = active_holdings_from_ledger(ledger)
    if not holdings:
        fail("No active holdings found from ledger_data.")
    print(f"Active holdings: {', '.join(sorted(holdings.keys()))}")

    existing_meta = row.get("stock_meta") if isinstance(row.get("stock_meta"), dict) else {}
    new_meta: Dict[str, Dict[str, Any]] = {}
    history_frames: Dict[str, Tuple[pd.DataFrame, str]] = {}
    results = {"updated": [], "failed": [], "skipped": []}

    for ticker, h in sorted(holdings.items()):
        mapped = TICKER_MAP.get(ticker.upper(), {})
        if mapped.get("skip") is True:
            results["skipped"].append({"ticker": ticker, "reason": mapped.get("note", "skip=true")})
            continue
        category = h.get("category") or ""
        try:
            df, source, extras = fetch_history(ticker, category)
            history_frames[ticker] = (df.copy(), source)
            meta = compute_meta(ticker, category, df, source, extras)
            new_meta[ticker] = meta
            results["updated"].append({"ticker": ticker, "source": source, "quant_health_score": meta.get("quant_health_score"), "trend_score": meta.get("trend_score"), "risk_score": meta.get("risk_score"), "technical_score": meta.get("technical_score"), "data_quality": meta.get("data_quality")})
            print(f"OK {ticker}: source={source}, health={meta.get('quant_health_score')}, trend={meta.get('trend_score')}, risk={meta.get('risk_score')}")
        except Exception as exc:
            results["failed"].append({"ticker": ticker, "error": str(exc)})
            print(f"FAIL {ticker}: {exc}", file=sys.stderr)

    if not new_meta:
        fail("No stock_meta was produced. Nothing to write.")

    merged_meta = merge_stock_meta(existing_meta, new_meta)

    try:
        synthetic_risk = compute_synthetic_portfolio_risk(holdings, history_frames, row)
        merged_meta[SYNTHETIC_RISK_KEY] = synthetic_risk
        results["synthetic_risk"] = {
            "status": synthetic_risk.get("status"),
            "confidence": synthetic_risk.get("confidence"),
            "sample_count": synthetic_risk.get("metrics", {}).get("sample_count"),
            "ann_vol_pct": synthetic_risk.get("metrics", {}).get("ann_vol_pct"),
            "var95_pct": synthetic_risk.get("metrics", {}).get("var95_pct"),
            "es95_pct": synthetic_risk.get("metrics", {}).get("es95_pct"),
        }
        print(
            "OK synthetic risk: "
            f"status={synthetic_risk.get('status')}, "
            f"confidence={synthetic_risk.get('confidence')}, "
            f"sample={synthetic_risk.get('metrics', {}).get('sample_count')}"
        )
    except Exception as exc:
        merged_meta[SYNTHETIC_RISK_KEY] = {
            "version": "v0.2",
            "status": "FAILED",
            "confidence": "INVALID",
            "confidence_reason": str(exc),
            "updated_at": str(TODAY_TPE),
            "method": "current_weight_synthetic_daily_returns",
            "metrics": {},
            "components": [],
        }
        results["synthetic_risk"] = {"status": "FAILED", "error": str(exc)}
        print(f"FAIL synthetic risk: {exc}", file=sys.stderr)

    write_supabase_stock_meta(client, merged_meta)
    write_github_summary(results)
    print("Done.")
    if results["failed"]:
        print("Some tickers failed. Existing stock_meta values were left untouched for those tickers.")

if __name__ == "__main__":
    main()
