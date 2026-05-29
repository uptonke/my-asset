#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests
from supabase import create_client

TAIPEI_TZ = timezone(timedelta(hours=8))
TODAY_TPE = datetime.now(TAIPEI_TZ).date()
START_DATE = TODAY_TPE - timedelta(days=560)
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

FINMIND_TOKEN = os.getenv("FINMIND_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "portfolio_db")
PORTFOLIO_ROW_ID = os.getenv("PORTFOLIO_ROW_ID", "1")
DRY_RUN = str(os.getenv("DRY_RUN", "false")).lower() in {"1", "true", "yes", "y"}

VALID_TW_TICKER_RE = re.compile(r"^\d{4,6}[A-Z]?$")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def fnum(x: Any) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) and v > 0 else None
    except Exception:
        return None


def active_tickers(ledger: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for tx in ledger or []:
        ticker = str(tx.get("ticker") or "").strip().upper()
        if not ticker:
            continue
        typ = str(tx.get("type") or "")
        if typ not in {"Buy", "Sell"}:
            continue
        shares = float(tx.get("shares") or 0)
        cat = str(tx.get("category") or "")
        row = out.setdefault(ticker, {"shares": 0.0, "category": cat})
        row["shares"] += shares if typ == "Buy" else -shares
        if cat:
            row["category"] = cat
    return {k: v for k, v in out.items() if v["shares"] > 0.0001}


def normalized_tw_code(ticker: str) -> str:
    return ticker.upper().replace(".TW", "").replace(".TWO", "")


def is_tw_ticker(ticker: str) -> bool:
    return bool(VALID_TW_TICKER_RE.match(normalized_tw_code(ticker)))


def should_skip_ticker(ticker: str) -> bool:
    # Chinese fund names such as 安聯台灣科技 are not exchange tickers.
    return bool(CJK_RE.search(ticker)) and not is_tw_ticker(ticker)


def yf_symbol(ticker: str) -> str:
    t = ticker.upper()
    return f"{normalized_tw_code(t)}.TW" if is_tw_ticker(t) else t


def fetch_finmind_ohlc(ticker: str) -> pd.DataFrame:
    if not FINMIND_TOKEN:
        raise RuntimeError("FINMIND_TOKEN missing")
    data_id = normalized_tw_code(ticker)
    resp = requests.get(
        FINMIND_URL,
        params={"dataset": "TaiwanStockPrice", "data_id": data_id, "start_date": str(START_DATE), "end_date": str(TODAY_TPE)},
        headers={"Authorization": f"Bearer {FINMIND_TOKEN}"},
        timeout=25,
    )
    resp.raise_for_status()
    data = resp.json().get("data") or []
    if not data:
        raise RuntimeError(f"FinMind empty for {ticker}")
    df = pd.DataFrame(data)
    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["date"])
    out["open"] = pd.to_numeric(df.get("open"), errors="coerce")
    out["high"] = pd.to_numeric(df["max"] if "max" in df.columns else df.get("high"), errors="coerce")
    out["low"] = pd.to_numeric(df["min"] if "min" in df.columns else df.get("low"), errors="coerce")
    out["close"] = pd.to_numeric(df.get("close"), errors="coerce")
    return out.dropna(subset=["date", "high", "low", "close"]).sort_values("date")


def fetch_yahoo_ohlc(symbol: str) -> pd.DataFrame:
    resp = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"range": "18mo", "interval": "1d", "events": "history"},
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=25,
    )
    resp.raise_for_status()
    result = (((resp.json().get("chart") or {}).get("result") or [])[:1])
    if not result:
        raise RuntimeError(f"YahooChart empty for {symbol}")
    r = result[0]
    ts = r.get("timestamp") or []
    q = ((((r.get("indicators") or {}).get("quote") or [])[:1]) or [{}])[0]
    if not ts or not q:
        raise RuntimeError(f"YahooChart malformed for {symbol}")
    out = pd.DataFrame({
        "date": pd.to_datetime(ts, unit="s"),
        "open": pd.to_numeric(q.get("open"), errors="coerce"),
        "high": pd.to_numeric(q.get("high"), errors="coerce"),
        "low": pd.to_numeric(q.get("low"), errors="coerce"),
        "close": pd.to_numeric(q.get("close"), errors="coerce"),
    })
    return out.dropna(subset=["date", "high", "low", "close"]).sort_values("date")


def fetch_ohlc(ticker: str) -> tuple[pd.DataFrame, str]:
    if is_tw_ticker(ticker):
        try:
            return fetch_finmind_ohlc(ticker), "FinMind"
        except Exception as exc:
            print(f"WARN {ticker}: FinMind monthly pivot failed: {exc}; trying YahooChart")
    symbol = yf_symbol(ticker)
    return fetch_yahoo_ohlc(symbol), f"YahooChart:{symbol}"


def previous_month_ohlc(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["period"] = df["date"].dt.to_period("M")
    monthly = df.groupby("period").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        last_date=("date", "max"),
    ).dropna(subset=["high", "low", "close"]).reset_index()
    if monthly.empty:
        return None
    current_period = pd.Timestamp(TODAY_TPE).to_period("M")
    completed = monthly[monthly["period"] < current_period]
    row = completed.iloc[-1] if not completed.empty else monthly.iloc[-1]
    h, l, c = fnum(row["high"]), fnum(row["low"]), fnum(row["close"])
    o = fnum(row["open"]) or c
    if h is None or l is None or c is None or h <= l:
        return None
    return {"open": o, "high": h, "low": l, "close": c, "period": str(row["period"]), "last_date": str(pd.to_datetime(row["last_date"]).date())}


def add(cands: list[dict], method: str, level: str, price: float, current: float) -> None:
    p = fnum(price)
    if p is None or p == current:
        return
    cands.append({"method": method, "level": level, "price": round(p, 6), "side": "support" if p < current else "resistance"})


def candidates(ohlc: Dict[str, Any], current: float) -> list[dict]:
    h, l, c, o = ohlc["high"], ohlc["low"], ohlc["close"], ohlc["open"]
    rng = h - l
    out: list[dict] = []
    if rng <= 0:
        return out

    p = (h + l + c) / 3
    classic = {"P": p, "R1": 2*p-l, "S1": 2*p-h, "R2": p+rng, "S2": p-rng, "R3": h+2*(p-l), "S3": l-2*(h-p)}
    fib = {"P": p, "R1": p+0.382*rng, "S1": p-0.382*rng, "R2": p+0.618*rng, "S2": p-0.618*rng, "R3": p+rng, "S3": p-rng}
    cam = {"R1": c+rng*1.1/12, "S1": c-rng*1.1/12, "R2": c+rng*1.1/6, "S2": c-rng*1.1/6, "R3": c+rng*1.1/4, "S3": c-rng*1.1/4, "R4": c+rng*1.1/2, "S4": c-rng*1.1/2}
    wp = (h + l + 2*c) / 4
    woodie = {"P": wp, "R1": 2*wp-l, "S1": 2*wp-h, "R2": wp+rng, "S2": wp-rng}
    x = h + 2*l + c if c < o else 2*h + l + c if c > o else h + l + 2*c
    demark = {"R1": x/2-l, "S1": x/2-h}

    for method, levels in [("Classic", classic), ("Fibonacci", fib), ("Camarilla", cam), ("Woodie", woodie), ("DeMark", demark)]:
        for level, price in levels.items():
            add(out, method, level, price, current)
    return out


def cluster(cands: list[dict], current: float, side: str) -> Optional[dict]:
    pts = sorted([x for x in cands if x["side"] == side], key=lambda x: x["price"])
    if not pts:
        return None
    # Monthly pivot uses a wider clustering band than weekly to avoid fake precision.
    tol = max(current * 0.01, 1e-9)
    clusters: list[list[dict]] = []
    for p in pts:
        if not clusters:
            clusters.append([p])
        elif abs(p["price"] - float(np.median([x["price"] for x in clusters[-1]]))) <= tol:
            clusters[-1].append(p)
        else:
            clusters.append([p])

    ranked = []
    for group in clusters:
        prices = [x["price"] for x in group]
        low, high, mid = min(prices), max(prices), float(np.median(prices))
        methods = sorted(set(x["method"] for x in group))
        levels = sorted(set(f'{x["method"]}:{x["level"]}' for x in group))
        near = abs(current - high) if side == "support" else abs(low - current)
        ranked.append({
            "zone_low": round(low, 4),
            "zone_high": round(high, 4),
            "zone_mid": round(mid, 4),
            "distance_pct": round((mid / current - 1) * 100, 2),
            "confluence": f"{len(methods)}/5",
            "method_count": len(methods),
            "methods": methods,
            "levels": levels[:10],
            "_near": near,
            "_n": len(methods),
        })
    ranked.sort(key=lambda x: (x["_near"], -x["_n"]))
    best = ranked[0]
    best.pop("_near", None)
    best.pop("_n", None)
    return best


def pivot_meta(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {"pivot_status": "資料不足", "pivot_data_quality": "empty"}
    current = fnum(df["close"].iloc[-1])
    ohlc = previous_month_ohlc(df)
    if current is None or ohlc is None:
        return {"pivot_status": "資料不足", "pivot_data_quality": "insufficient_ohlc"}

    cands = candidates(ohlc, current)
    support = cluster(cands, current, "support")
    resistance = cluster(cands, current, "resistance")

    out: Dict[str, Any] = {
        "pivot_timeframe": "monthly",
        "pivot_methods_used": ["Classic", "Fibonacci", "Camarilla", "Woodie", "DeMark"],
        "pivot_source_period": ohlc["period"],
        "pivot_source_last_date": ohlc["last_date"],
        "pivot_current_price": round(current, 4),
        "pivot_data_quality": "ok" if support or resistance else "no_nearby_levels",
    }

    if support:
        out.update({
            "pivot_support_zone_low": support["zone_low"],
            "pivot_support_zone_high": support["zone_high"],
            "pivot_support_zone_mid": support["zone_mid"],
            "pivot_support_distance_pct": support["distance_pct"],
            "pivot_support_confluence": support["confluence"],
            "pivot_support_method_count": support["method_count"],
            "pivot_support_methods": support["methods"],
            "pivot_support_levels": support["levels"],
        })
    if resistance:
        out.update({
            "pivot_resistance_zone_low": resistance["zone_low"],
            "pivot_resistance_zone_high": resistance["zone_high"],
            "pivot_resistance_zone_mid": resistance["zone_mid"],
            "pivot_resistance_distance_pct": resistance["distance_pct"],
            "pivot_resistance_confluence": resistance["confluence"],
            "pivot_resistance_method_count": resistance["method_count"],
            "pivot_resistance_methods": resistance["methods"],
            "pivot_resistance_levels": resistance["levels"],
        })

    sd = abs(support["distance_pct"]) if support else None
    rd = abs(resistance["distance_pct"]) if resistance else None
    sc = support["method_count"] if support else 0
    rc = resistance["method_count"] if resistance else 0

    if support and not resistance:
        status = "突破月壓力區"
    elif resistance and not support:
        status = "跌破月支撐區"
    elif sd is not None and rd is not None and sd <= 2.0 and rd <= 2.0:
        status = "月線樞軸壓縮"
    elif rd is not None and rd <= 1.5 and rc >= 3:
        status = "接近月壓力"
    elif sd is not None and sd <= 1.5 and sc >= 3:
        status = "接近月支撐"
    elif support and resistance:
        status = "月線區間中段"
    else:
        status = "N/A"
    out["pivot_status"] = status
    return out


def main() -> None:
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        fail("SUPABASE_URL or SUPABASE_SECRET_KEY missing")
    client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    row = client.table(SUPABASE_TABLE).select("ledger_data,stock_meta").eq("id", int(PORTFOLIO_ROW_ID)).single().execute().data
    if not row:
        fail("portfolio row not found")

    holdings = active_tickers(row.get("ledger_data") or [])
    stock_meta = row.get("stock_meta") if isinstance(row.get("stock_meta"), dict) else {}
    updated, skipped, failed = [], [], []

    for ticker, h in sorted(holdings.items()):
        if should_skip_ticker(ticker):
            stock_meta[ticker] = {**(stock_meta.get(ticker) or {}), "pivot_status": "不適用", "pivot_data_quality": "skipped_non_ticker", "pivot_timeframe": "monthly", "pivot_updated_at": str(TODAY_TPE)}
            skipped.append(ticker)
            print(f"SKIP pivot {ticker}: non-tradable text ticker")
            continue
        try:
            df, source = fetch_ohlc(ticker)
            meta = pivot_meta(df)
            meta["pivot_source"] = source
            meta["pivot_updated_at"] = str(TODAY_TPE)
            stock_meta[ticker] = {**(stock_meta.get(ticker) or {}), **meta}
            updated.append(ticker)
            print(f"OK monthly pivot {ticker}: {meta.get('pivot_status')} support={meta.get('pivot_support_confluence')} resistance={meta.get('pivot_resistance_confluence')}")
            time.sleep(0.25)
        except Exception as exc:
            failed.append((ticker, str(exc)))
            print(f"FAIL monthly pivot {ticker}: {exc}")

    if DRY_RUN:
        print("DRY_RUN=true, not writing monthly pivot metadata.")
    else:
        client.table(SUPABASE_TABLE).upsert({"id": int(PORTFOLIO_ROW_ID), "stock_meta": stock_meta}, on_conflict="id").execute()
        print(f"Wrote monthly pivot metadata for {len(updated)} tickers; skipped {len(skipped)}.")

    if failed:
        print("Failed:", failed)


if __name__ == "__main__":
    main()
