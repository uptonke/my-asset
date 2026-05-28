#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests
from supabase import create_client

TAIPEI_TZ = timezone(timedelta(hours=8))
TODAY_TPE = datetime.now(TAIPEI_TZ).date()
START_DATE = TODAY_TPE - timedelta(days=120)
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

FINMIND_TOKEN = os.getenv("FINMIND_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "portfolio_db")
PORTFOLIO_ROW_ID = os.getenv("PORTFOLIO_ROW_ID", "1")
DRY_RUN = str(os.getenv("DRY_RUN", "false")).lower() in {"1", "true", "yes", "y"}


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


def is_tw(ticker: str, category: str) -> bool:
    clean = ticker.replace(".TW", "").replace(".TWO", "")
    return clean.isdigit() or "台" in str(category)


def yf_symbol(ticker: str, category: str) -> str:
    t = ticker.upper()
    if is_tw(t, category):
        return f"{t.replace('.TW', '').replace('.TWO', '')}.TW"
    return t


def fetch_finmind_ohlc(ticker: str) -> pd.DataFrame:
    if not FINMIND_TOKEN:
        raise RuntimeError("FINMIND_TOKEN missing")
    data_id = ticker.replace(".TW", "").replace(".TWO", "")
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
        params={"range": "6mo", "interval": "1d", "events": "history"},
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


def fetch_ohlc(ticker: str, category: str) -> tuple[pd.DataFrame, str]:
    if is_tw(ticker, category):
        try:
            return fetch_finmind_ohlc(ticker), "FinMind"
        except Exception as exc:
            print(f"WARN {ticker}: FinMind pivot failed: {exc}")
    symbol = yf_symbol(ticker, category)
    return fetch_yahoo_ohlc(symbol), f"YahooChart:{symbol}"


def previous_week_ohlc(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W-FRI")
    weekly = df.groupby("week").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        last_date=("date", "max"),
    ).dropna(subset=["high", "low", "close"]).reset_index()
    if weekly.empty:
        return None
    current = pd.Timestamp(TODAY_TPE).to_period("W-FRI")
    completed = weekly[weekly["week"] < current]
    row = completed.iloc[-1] if not completed.empty else weekly.iloc[-1]
    h, l, c = fnum(row["high"]), fnum(row["low"]), fnum(row["close"])
    o = fnum(row["open"]) or c
    if h is None or l is None or c is None or h <= l:
        return None
    return {"open": o, "high": h, "low": l, "close": c, "week": str(row["week"]), "last_date": str(pd.to_datetime(row["last_date"]).date())}


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
    tol = max(current * 0.005, 1e-9)
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
    ohlc = previous_week_ohlc(df)
    if current is None or ohlc is None:
        return {"pivot_status": "資料不足", "pivot_data_quality": "insufficient_ohlc"}

    cands = candidates(ohlc, current)
    support = cluster(cands, current, "support")
    resistance = cluster(cands, current, "resistance")

    out: Dict[str, Any] = {
        "pivot_timeframe": "weekly",
        "pivot_methods_used": ["Classic", "Fibonacci", "Camarilla", "Woodie", "DeMark"],
        "pivot_source_period": ohlc["week"],
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
            "pivot_resistance_methods": resistance["methods"],
            "pivot_resistance_levels": resistance["levels"],
        })

    sd = abs(support["distance_pct"]) if support else None
    rd = abs(resistance["distance_pct"]) if resistance else None
    if support and not resistance:
        status = "突破上方樞軸"
    elif resistance and not support:
        status = "跌破下方樞軸"
    elif rd is not None and rd <= 1:
        status = "接近壓力"
    elif sd is not None and sd <= 1:
        status = "接近支撐"
    elif support and resistance:
        status = "區間中段"
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
    updated, failed = [], []

    for ticker, h in sorted(holdings.items()):
        try:
            df, source = fetch_ohlc(ticker, h.get("category", ""))
            meta = pivot_meta(df)
            meta["pivot_source"] = source
            meta["pivot_updated_at"] = str(TODAY_TPE)
            stock_meta[ticker] = {**(stock_meta.get(ticker) or {}), **meta}
            updated.append(ticker)
            print(f"OK pivot {ticker}: {meta.get('pivot_status')} support={meta.get('pivot_support_confluence')} resistance={meta.get('pivot_resistance_confluence')}")
            time.sleep(0.25)
        except Exception as exc:
            failed.append((ticker, str(exc)))
            print(f"FAIL pivot {ticker}: {exc}")

    if DRY_RUN:
        print("DRY_RUN=true, not writing pivot metadata.")
    else:
        client.table(SUPABASE_TABLE).upsert({"id": int(PORTFOLIO_ROW_ID), "stock_meta": stock_meta}, on_conflict="id").execute()
        print(f"Wrote pivot metadata for {len(updated)} tickers.")

    if failed:
        print("Failed:", failed)


if __name__ == "__main__":
    main()
