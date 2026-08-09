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


def split_material_values(
    values_twd: Dict[str, float],
    *,
    absolute_floor_twd: float = 100.0,
    nav_fraction: float = 0.0002,
) -> Tuple[Dict[str, float], Dict[str, float], float, float]:
    """Split economically material positions from tiny ledger remnants.

    Share counts are deliberately NOT used because fractional crypto/US shares can
    be economically large. Threshold = max(absolute floor, NAV fraction).
    """
    clean = {
        str(t): float(v)
        for t, v in (values_twd or {}).items()
        if math.isfinite(float(v)) and float(v) > 0
    }
    raw_total = float(sum(clean.values()))
    threshold = max(float(absolute_floor_twd), raw_total * float(nav_fraction)) if raw_total > 0 else float(absolute_floor_twd)
    material = {t: v for t, v in clean.items() if v >= threshold}
    dust = {t: v for t, v in clean.items() if 0 < v < threshold}

    # Fail-safe for synthetic/tiny portfolios: never erase every position.
    if clean and not material:
        material = dict(clean)
        dust = {}
    return material, dust, threshold, raw_total


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

    raw_values_twd: Dict[str, float] = {}
    usd_flags: Dict[str, bool] = {}

    for t, qty in shares.items():
        meta = stock_meta.get(t, {}) if isinstance(stock_meta.get(t, {}), dict) else {}
        yf_t = yf_map.get(t, "")
        p = price_for_asset(t, meta, settings, latest_prices, yf_t)
        if p is None:
            print(f"WARN xray no price for {t}; skipped valuation")
            continue
        usd_asset = is_usd_asset(t, meta, yf_t)
        multiplier = exchange_rate if usd_asset else 1.0
        raw_values_twd[t] = max(0.0, float(qty) * float(p) * multiplier)
        usd_flags[t] = usd_asset

    values_twd, dust_values_twd, dust_threshold_twd, raw_total_value_twd = split_material_values(raw_values_twd)
    total_value_twd = float(sum(values_twd.values()))
    usd_value_twd = float(sum(v for t, v in values_twd.items() if usd_flags.get(t, False)))

    if dust_values_twd:
        print(
            f"INFO xray economic dust excluded (< NT${dust_threshold_twd:,.2f}): "
            + ", ".join(f"{t}=NT${v:,.2f}" for t, v in sorted(dust_values_twd.items()))
        )

    if total_value_twd <= 0:
        raise RuntimeError("total material TWD holding value <= 0")

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
            "raw_total_holding_value_twd": round(raw_total_value_twd, 2),
            "total_holding_value_twd": round(total_value_twd, 2),
            "model_total_value_twd": round(model_total, 2),
            "economic_dust_policy": "exclude_if_value_below_max_100_twd_or_0.02pct_raw_nav",
            "economic_dust_threshold_twd": round(dust_threshold_twd, 2),
            "economic_dust_value_twd": round(sum(dust_values_twd.values()), 2),
            "economic_dust_weight_pct": round(
                (sum(dust_values_twd.values()) / raw_total_value_twd * 100.0) if raw_total_value_twd > 0 else 0.0,
                4
            ),
            "economic_dust_tickers_excluded": sorted(dust_values_twd),
            "material_position_values_twd": {t: round(v, 2) for t, v in sorted(values_twd.items())},
            "updated_at": str(TODAY_TPE),
        },
    }


def compute_rebalance_semantics(row: Dict[str, Any], xray: Dict[str, Any]) -> Dict[str, Any]:
    """Build an actionable rebalance packet from material ledger positions only."""
    stock_meta = row.get("stock_meta") if isinstance(row.get("stock_meta"), dict) else {}
    settings = row.get("settings") if isinstance(row.get("settings"), dict) else {}
    basis = xray.get("basis") if isinstance(xray.get("basis"), dict) else {}
    values = basis.get("material_position_values_twd") if isinstance(basis.get("material_position_values_twd"), dict) else {}
    values = {str(t): float(v) for t, v in values.items() if float(v) >= 0}
    portfolio_value = float(sum(values.values()))

    buffer_floor_wt = max(0.0, min(float(settings.get("liquidityBufferRatio") or 0.0) / 100.0, 0.80))
    hard_buffers = ["SHY", "BOXX"]
    current_buffer_value = float(sum(values.get(t, 0.0) for t in hard_buffers))
    current_buffer_wt = current_buffer_value / portfolio_value if portfolio_value > 0 else 0.0
    buffer_gap_wt = max(0.0, buffer_floor_wt - current_buffer_wt)
    per_buffer_fill_wt = buffer_gap_wt / len(hard_buffers) if hard_buffers else 0.0

    active = set(values)
    excluded_nonheld_targets = sorted([
        str(t)
        for t, meta in stock_meta.items()
        if isinstance(meta, dict)
        and str(t) not in active
        and normalize_ticker(t) not in set(hard_buffers)
        and float(meta.get("target_weight") or 0.0) > 0
    ])

    signals: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []
    universe = sorted(active | set(hard_buffers))
    for t in universe:
        meta = stock_meta.get(t, {}) if isinstance(stock_meta.get(t, {}), dict) else {}
        cw = values.get(t, 0.0) / portfolio_value if portfolio_value > 0 else 0.0
        base_tw = float(meta.get("target_weight") or 0.0)
        effective_tw = base_tw
        if t in hard_buffers and buffer_gap_wt > 0.0001:
            effective_tw = max(base_tw, cw + per_buffer_fill_wt)

        delta_w = effective_tw - cw
        if abs(delta_w) <= 0.01:
            continue

        direction = "ADD" if delta_w > 0 else "TRIM"
        signal_type = "BUFFER_REPLENISHMENT" if t in hard_buffers and delta_w > 0 and buffer_gap_wt > 0.0001 else "TARGET_DRIFT"
        signal = {
            "ticker": t,
            "direction": direction,
            "signal_type": signal_type,
            "execution_status": "ACTIONABLE",
            "action": "BUY (加碼)" if direction == "ADD" else "SELL (減碼)",
            "current_weight": f"{cw * 100:.2f}%",
            "target_weight": f"{effective_tw * 100:.2f}%",
            "delta_weight": f"{delta_w * 100:.2f}%",
            "current_weight_pct": round(cw * 100, 4),
            "target_weight_pct": round(effective_tw * 100, 4),
            "signed_drift_pp": round((cw - effective_tw) * 100, 4),
            "delta_to_target_pp": round(delta_w * 100, 4),
            "rule_threshold_pp": 1.0,
            "trade_amount": round(portfolio_value * delta_w, 2),
        }

        if direction == "TRIM":
            signal["reason"] = "目前權重高於目標超過規則門檻，候選動作為 TRIM"
            signals.append(signal)
        elif buffer_gap_wt > 0.0001 and t not in hard_buffers:
            signal["execution_status"] = "BLOCKED_BY_BUFFER"
            signal["reason"] = "目標低配但硬緩衝缺口尚未補足；ADD 暫不可執行"
            blocked.append(signal)
        else:
            signal["reason"] = (
                "補足硬緩衝至最低安全邊際"
                if signal_type == "BUFFER_REPLENISHMENT"
                else "目前權重低於目標超過規則門檻，候選動作為 ADD"
            )
            signals.append(signal)

    return {
        "buffer_floor_pct": round(buffer_floor_wt * 100.0, 2),
        "current_buffer_pct": round(current_buffer_wt * 100.0, 2),
        "buffer_gap_pct": round(buffer_gap_wt * 100.0, 2),
        "buffer_gap_value": round(portfolio_value * buffer_gap_wt, 2),
        "buffer_blocking_risk_buys": bool(buffer_gap_wt > 0.0001),
        "hard_buffer_tickers": hard_buffers,
        "universe_policy": "material_ledger_holdings_plus_hard_buffer_only",
        "sheet_only_tickers_excluded": excluded_nonheld_targets,
        "nonheld_target_tickers_excluded": excluded_nonheld_targets,
        "economic_dust_threshold_twd": basis.get("economic_dust_threshold_twd"),
        "economic_dust_tickers_excluded": basis.get("economic_dust_tickers_excluded") or [],
        "rule_threshold_pp": 1.0,
        "signals": signals,
        "blocked_signals": blocked,
        "signal_count": len(signals),
        "blocked_signal_count": len(blocked),
        "generated_by": "fix_xray_twd_weights.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    row = client.table(TABLE).select("ledger_data,stock_meta,settings,chaos_meta").eq("id", ROW_ID).single().execute().data
    if not row:
        raise SystemExit("ERROR: portfolio row not found")

    xray = compute_xray_twd(row)
    rebalance_meta = compute_rebalance_semantics(row, xray)
    chaos_meta = row.get("chaos_meta") if isinstance(row.get("chaos_meta"), dict) else {}
    chaos_meta["xray_meta"] = xray
    client.table(TABLE).update({
        "chaos_meta": chaos_meta,
        "rebalance_meta": rebalance_meta,
    }).eq("id", ROW_ID).execute()

    print("OK xray TWD weights + rebalance semantics refreshed")
    print(
        f"rebalance actionable={rebalance_meta['signal_count']} "
        f"blocked={rebalance_meta['blocked_signal_count']} "
        f"dust={rebalance_meta['economic_dust_tickers_excluded']}"
    )
    for r in xray.get("mrc_table", [])[:10]:
        print(f"{r['ticker']}: capital={r['weight_pct']}% model={r['model_weight_pct']}% risk={r['risk_pct']}%")


if __name__ == "__main__":
    main()
