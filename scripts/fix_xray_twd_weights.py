#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
from supabase import create_client

TAIPEI_TZ = timezone(timedelta(hours=8))
TODAY_TPE = datetime.now(TAIPEI_TZ).date()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_SECRET_KEY", "")
TABLE = os.getenv("SUPABASE_TABLE", "portfolio_db")
ROW_ID = int(os.getenv("PORTFOLIO_ROW_ID", "1"))

PROXY_TICKER_MAP = {
    "統一奔騰": "0052.TW",
    "安聯台灣科技": "0053.TW",
    "加密貨幣": "ETH-USD",
}


def normalize_ticker(raw: Any) -> str:
    return str(raw or "").strip().upper()


def is_tw_numeric_ticker(ticker: str) -> bool:
    return bool(re.match(r"^\d+[A-Z]*$", normalize_ticker(ticker)))


def is_chinese_label(ticker: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", str(ticker or "")))


def map_to_yf_ticker(ticker: str, tw_bench: str = "^TWII") -> str:
    raw = str(ticker or "").strip()
    t = normalize_ticker(raw)
    if not t:
        return ""
    if raw in PROXY_TICKER_MAP:
        return PROXY_TICKER_MAP[raw]
    if t in PROXY_TICKER_MAP:
        return PROXY_TICKER_MAP[t]
    if is_chinese_label(raw):
        return tw_bench
    if is_tw_numeric_ticker(t):
        return f"{t}.TW"
    return t


def is_usd_asset(ticker: str, meta: Dict[str, Any], yf_ticker: str = "") -> bool:
    t = normalize_ticker(ticker)
    y = normalize_ticker(yf_ticker)
    cat = str(meta.get("category", ""))
    return (
        "美股" in cat or
        "加密" in cat or
        t.endswith("-USD") or
        y.endswith("-USD") or
        (bool(re.match(r"^[A-Z]{1,5}$", t)) and not y.endswith(".TW") and t not in {"TWD", "NTD"})
    )


def fetch_yahoo_chart_close(symbol: str, days: int = 900) -> pd.Series:
    now = int(datetime.now(timezone.utc).timestamp())
    start = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"period1": start, "period2": now, "interval": "1d", "events": "history"}
    resp = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=25)
    resp.raise_for_status()
    result = (((resp.json().get("chart") or {}).get("result") or [])[:1])
    if not result:
        raise RuntimeError(f"YahooChart empty for {symbol}")
    r = result[0]
    ts = r.get("timestamp") or []
    quote = ((((r.get("indicators") or {}).get("quote") or [])[:1]) or [{}])[0]
    close = quote.get("close") or []
    if not ts or not close:
        raise RuntimeError(f"YahooChart malformed for {symbol}")
    s = pd.Series(pd.to_numeric(close, errors="coerce"), index=pd.to_datetime(ts, unit="s"), name=symbol)
    s = s.dropna().sort_index()
    if len(s) < 40:
        raise RuntimeError(f"YahooChart too few rows for {symbol}: {len(s)}")
    return s


def active_shares_from_ledger(ledger: List[Dict[str, Any]]) -> Dict[str, float]:
    shares: Dict[str, float] = {}
    for tx in ledger or []:
        t_raw = str(tx.get("ticker") or "").strip()
        if not t_raw:
            continue
        typ = str(tx.get("type") or "").strip().lower()
        if typ not in {"buy", "sell", "買入", "賣出"}:
            continue
        try:
            qty = float(tx.get("shares") or 0.0)
        except Exception:
            qty = 0.0
        if qty <= 0:
            continue
        sign = -1.0 if typ in {"sell", "賣出"} else 1.0
        # Keep original label for Chinese funds, uppercase for exchange tickers.
        key = t_raw if is_chinese_label(t_raw) else normalize_ticker(t_raw)
        shares[key] = shares.get(key, 0.0) + sign * qty
    return {t: s for t, s in shares.items() if s > 0.0001}


def price_for_asset(ticker: str, meta: Dict[str, Any], settings: Dict[str, Any], latest_prices: Dict[str, float], yf_ticker: str) -> Optional[float]:
    price_map = settings.get("priceMap") if isinstance(settings.get("priceMap"), dict) else {}
    candidates = [
        price_map.get(ticker),
        price_map.get(normalize_ticker(ticker)),
        meta.get("last_price"),
        meta.get("price"),
        latest_prices.get(yf_ticker),
        latest_prices.get(ticker),
    ]
    for x in candidates:
        try:
            v = float(x)
            if math.isfinite(v) and v > 0:
                return v
        except Exception:
            continue
    return None


def compute_xray_twd(row: Dict[str, Any]) -> Dict[str, Any]:
    ledger = row.get("ledger_data") or []
    stock_meta = row.get("stock_meta") if isinstance(row.get("stock_meta"), dict) else {}
    settings = row.get("settings") if isinstance(row.get("settings"), dict) else {}
    exchange_rate = float(settings.get("exchangeRate") or 31.5)

    shares = active_shares_from_ledger(ledger)
    if not shares:
        raise RuntimeError("no active holdings")

    yf_map: Dict[str, str] = {t: map_to_yf_ticker(t) for t in shares}
    price_series: Dict[str, pd.Series] = {}
    latest_prices: Dict[str, float] = {}

    for yf_t in sorted(set(yf_map.values())):
        if not yf_t:
            continue
        try:
            s = fetch_yahoo_chart_close(yf_t)
            price_series[yf_t] = s
            latest_prices[yf_t] = float(s.iloc[-1])
            time.sleep(0.15)
        except Exception as exc:
            print(f"WARN xray price history failed {yf_t}: {exc}")

    values_twd: Dict[str, float] = {}
    usd_value_twd = 0.0
    total_value_twd = 0.0

    for t, qty in shares.items():
        meta = stock_meta.get(t, {}) if isinstance(stock_meta.get(t, {}), dict) else {}
        yf_t = yf_map.get(t, "")
        p = price_for_asset(t, meta, settings, latest_prices, yf_t)
        if p is None:
            print(f"WARN xray no price for {t}; skipped valuation")
            continue
        multiplier = exchange_rate if is_usd_asset(t, meta, yf_t) else 1.0
        v = max(0.0, float(qty) * float(p) * multiplier)
        values_twd[t] = v
        total_value_twd += v
        if multiplier != 1.0:
            usd_value_twd += v

    if total_value_twd <= 0:
        raise RuntimeError("total TWD holding value <= 0")

    grouped_values: Dict[str, float] = {}
    label_map: Dict[str, List[str]] = {}
    for t, v in values_twd.items():
        yf_t = yf_map.get(t, "")
        if yf_t not in price_series:
            continue
        grouped_values[yf_t] = grouped_values.get(yf_t, 0.0) + v
        label_map.setdefault(yf_t, []).append(t)

    if len(grouped_values) < 2:
        raise RuntimeError("not enough assets with return series for xray")

    prices = pd.concat([price_series[yf_t].rename(yf_t) for yf_t in grouped_values], axis=1).sort_index()
    returns = prices.pct_change().dropna(how="any")
    if len(returns) < 40:
        raise RuntimeError(f"not enough aligned return rows: {len(returns)}")

    cov = returns.cov().values * 252.0
    columns = list(returns.columns)
    model_values = np.array([grouped_values[c] for c in columns], dtype=float)
    model_total = float(model_values.sum())
    weights = model_values / model_total

    sigma_w = cov.dot(weights)
    port_var = float(weights.T.dot(sigma_w))
    port_vol = math.sqrt(port_var) if port_var > 0 else 0.0

    mrc_table = []
    if port_vol > 0:
        for i, yf_t in enumerate(columns):
            mrc = float(sigma_w[i] / port_vol)
            rc = float(weights[i] * mrc)
            risk_pct = float((rc / port_vol) * 100.0) if port_vol > 0 else None
            display_name = "/".join(label_map.get(yf_t, [yf_t]))
            actual_value = float(grouped_values[yf_t])
            mrc_table.append({
                "ticker": display_name,
                "yf_ticker": yf_t,
                "weight_pct": round((actual_value / total_value_twd) * 100.0, 2),
                "model_weight_pct": round((actual_value / model_total) * 100.0, 2),
                "risk_pct": round(risk_pct, 2) if risk_pct is not None else None,
                "mrc": round(mrc * 100.0, 4),
                "rc": round(rc * 100.0, 4),
                "value_twd": round(actual_value, 2),
            })
        mrc_table = sorted(mrc_table, key=lambda x: x.get("risk_pct") or 0.0, reverse=True)

    corr = returns.corr().replace([np.inf, -np.inf], np.nan).fillna(0.0).values
    eigvals = np.linalg.eigvalsh(corr)
    eigvals = np.array(sorted([float(v) for v in eigvals if not np.isnan(v)], reverse=True))
    if len(eigvals) > 0 and eigvals.sum() > 0:
        pc1 = float(eigvals[0] / eigvals.sum() * 100.0)
        pc3 = float(eigvals[: min(3, len(eigvals))].sum() / eigvals.sum() * 100.0)
    else:
        pc1 = pc3 = None

    return {
        "mrc_table": mrc_table,
        "pca": {
            "pc1_explained": round(pc1, 2) if pc1 is not None else None,
            "pc3_cum_explained": round(pc3, 2) if pc3 is not None else None,
        },
        "fx": {
            "net_fx_exposure_pct": round((usd_value_twd / total_value_twd) * 100.0, 2),
            "usd_nav_impact_1pct_twd": round(usd_value_twd * 0.01, 2),
            "usd_exposure_value_twd": round(usd_value_twd, 2),
        },
        "lookthrough_overlap": {
            "status": "missing_holdings_source",
            "note": "ETF constituent holdings source not connected yet. X-Ray weights corrected to TWD valuation.",
        },
        "basis": {
            "currency": "TWD",
            "exchange_rate": exchange_rate,
            "total_holding_value_twd": round(total_value_twd, 2),
            "model_total_value_twd": round(model_total, 2),
            "updated_at": str(TODAY_TPE),
        },
    }


def main() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    row = client.table(TABLE).select("ledger_data,stock_meta,settings,chaos_meta").eq("id", ROW_ID).single().execute().data
    if not row:
        raise SystemExit("ERROR: portfolio row not found")

    xray = compute_xray_twd(row)
    chaos_meta = row.get("chaos_meta") if isinstance(row.get("chaos_meta"), dict) else {}
    chaos_meta["xray_meta"] = xray
    client.table(TABLE).update({"chaos_meta": chaos_meta}).eq("id", ROW_ID).execute()

    print("OK xray TWD weights fixed")
    for r in xray.get("mrc_table", [])[:10]:
        print(f"{r['ticker']}: capital={r['weight_pct']}% model={r['model_weight_pct']}% risk={r['risk_pct']}%")


if __name__ == "__main__":
    main()
