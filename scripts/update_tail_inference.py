#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import requests
from supabase import create_client

try:
    from scripts.tail_inference import compute_tail_bootstrap_ci
except ModuleNotFoundError:
    from tail_inference import compute_tail_bootstrap_ci

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_SECRET_KEY", "")
TABLE = os.getenv("SUPABASE_TABLE", "portfolio_db")
ROW_ID = int(os.getenv("PORTFOLIO_ROW_ID", "1"))
HORIZON_WEEKS = 13
HISTORY_DAYS = 3700


def _fetch_yahoo_adjusted_close(symbol: str, days: int = HISTORY_DAYS) -> pd.Series:
    now = int(datetime.now(timezone.utc).timestamp())
    start = int((datetime.now(timezone.utc) - timedelta(days=int(days))).timestamp())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"period1": start, "period2": now, "interval": "1d", "events": "div,splits"}
    resp = requests.get(
        url,
        params=params,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=25,
    )
    resp.raise_for_status()
    result = (((resp.json().get("chart") or {}).get("result") or [])[:1])
    if not result:
        raise RuntimeError(f"YahooChart empty for {symbol}")
    r = result[0]
    ts = r.get("timestamp") or []
    indicators = r.get("indicators") or {}
    adj_blocks = (indicators.get("adjclose") or [])[:1]
    adj = (adj_blocks[0].get("adjclose") or []) if adj_blocks else []
    if not adj:
        quote_blocks = (indicators.get("quote") or [])[:1]
        adj = (quote_blocks[0].get("close") or []) if quote_blocks else []
    if not ts or not adj:
        raise RuntimeError(f"YahooChart malformed for {symbol}")
    out = pd.Series(pd.to_numeric(adj, errors="coerce"), index=pd.to_datetime(ts, unit="s"), name=symbol)
    out = out.dropna().sort_index()
    if len(out) < 40:
        raise RuntimeError(f"YahooChart too few rows for {symbol}: {len(out)}")
    return out


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except (TypeError, ValueError):
        return default


def _safe_corr(a: pd.Series, b: pd.Series) -> float | None:
    pair = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(pair) < 3 or pair["a"].std() <= 1e-12 or pair["b"].std() <= 1e-12:
        return None
    out = float(pair["a"].corr(pair["b"]))
    return out if math.isfinite(out) else None


def _compute_cvar(series: pd.Series, q: float = 0.05) -> float | None:
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(s) < 3:
        return None
    threshold = float(s.quantile(q))
    tail = s[s <= threshold]
    if tail.empty:
        return None
    out = float(tail.mean())
    return out if math.isfinite(out) else None


def _compute_var_es(series: pd.Series, alpha: float = 0.95) -> Dict[str, Any]:
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    out = {"var": None, "es": None, "sample_count": int(len(s))}
    if len(s) < 3:
        return out
    q = max(0.0, min(1.0, 1.0 - float(alpha)))
    threshold = float(s.quantile(q))
    tail = s[s <= threshold]
    out["var"] = threshold
    out["es"] = float(tail.mean()) if not tail.empty else threshold
    return out


def _rolling_compounded_returns(series: pd.Series, window: int) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(s) < int(window):
        return pd.Series(dtype=float)
    return (1.0 + s).rolling(int(window)).apply(np.prod, raw=True).dropna() - 1.0


def _drawdown_series(return_series: pd.Series) -> pd.Series:
    s = pd.to_numeric(return_series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return pd.Series(dtype=float)
    wealth = (1.0 + s).cumprod()
    peak = wealth.cummax()
    return wealth / peak - 1.0


def _extract_model_weights(chaos_meta: Dict[str, Any]) -> Tuple[Dict[str, float], float]:
    xray = chaos_meta.get("xray_meta") if isinstance(chaos_meta.get("xray_meta"), dict) else {}
    rows = xray.get("mrc_table") if isinstance(xray.get("mrc_table"), list) else []
    weights: Dict[str, float] = {}
    coverage = 0.0
    for row in rows:
        if not isinstance(row, dict):
            continue
        yf_ticker = str(row.get("yf_ticker") or "").strip()
        weight_pct = _num(row.get("weight_pct"), 0.0) or 0.0
        if not yf_ticker or weight_pct <= 0:
            continue
        weights[yf_ticker] = weights.get(yf_ticker, 0.0) + weight_pct / 100.0
        coverage += weight_pct
    return weights, coverage


def _choose_benchmark(weights: Dict[str, float]) -> str:
    tw_weight = sum(w for ticker, w in weights.items() if str(ticker).upper().endswith(".TW"))
    non_tw_weight = sum(w for ticker, w in weights.items() if not str(ticker).upper().endswith(".TW"))
    return "^TWII" if tw_weight > non_tw_weight else "SPY"


def _build_weekly_series(weights: Dict[str, float], benchmark: str) -> Tuple[pd.Series, pd.Series, Dict[str, Any]]:
    prices: Dict[str, pd.Series] = {}
    failures: Dict[str, str] = {}

    for ticker in list(weights) + [benchmark]:
        if ticker in prices:
            continue
        try:
            prices[ticker] = _fetch_yahoo_adjusted_close(ticker, days=HISTORY_DAYS)
            time.sleep(0.08)
        except Exception as exc:
            failures[ticker] = f"{type(exc).__name__}: {exc}"
            print(f"WARN tail price history failed {ticker}: {exc}")

    if benchmark not in prices:
        raise RuntimeError(f"benchmark history unavailable: {benchmark}")

    available_weights = {ticker: weight for ticker, weight in weights.items() if ticker in prices}
    if not available_weights:
        raise RuntimeError("no portfolio assets with usable history")

    raw_weight_sum = float(sum(available_weights.values()))
    if raw_weight_sum <= 0:
        raise RuntimeError("available portfolio weight <= 0")
    norm_weights = {ticker: weight / raw_weight_sum for ticker, weight in available_weights.items()}

    frame = pd.concat(
        [prices[t].rename(t) for t in list(available_weights) + [benchmark]],
        axis=1,
    ).sort_index()
    weekly_prices = frame.resample("W-FRI").last().dropna(how="all")
    weekly_returns = weekly_prices.pct_change(fill_method=None).dropna(how="any")
    if len(weekly_returns) < 24:
        raise RuntimeError(f"not enough aligned weekly returns: {len(weekly_returns)}")

    port = weekly_returns[list(available_weights)].mul(pd.Series(norm_weights), axis=1).sum(axis=1)
    bench = weekly_returns[benchmark]
    aligned = pd.concat([port.rename("port"), bench.rename("bench")], axis=1).dropna()
    if len(aligned) < 24:
        raise RuntimeError(f"not enough aligned portfolio/benchmark weeks: {len(aligned)}")

    diagnostics = {
        "requested_asset_count": len(weights),
        "available_asset_count": len(available_weights),
        "requested_weight_pct": round(float(sum(weights.values())) * 100.0, 4),
        "available_weight_pct": round(raw_weight_sum * 100.0, 4),
        "missing_price_tickers": sorted(set(weights) - set(available_weights)),
        "price_errors": failures,
        "return_price_basis": "yahoo_adjusted_close_with_raw_close_fallback",
    }
    return aligned["port"], aligned["bench"], diagnostics


def _compute_empirical_tail(port: pd.Series, bench: pd.Series, benchmark: str) -> Dict[str, Any]:
    historical_1w = _compute_var_es(port, alpha=0.95)
    port_horizon = _rolling_compounded_returns(port, HORIZON_WEEKS)
    historical_horizon = _compute_var_es(port_horizon, alpha=0.95)

    q20_b = float(bench.quantile(0.20))
    q10_b = float(bench.quantile(0.10))
    q05_b = float(bench.quantile(0.05))
    q20_p = float(port.quantile(0.20))
    q05_p = float(port.quantile(0.05))

    cond_mask = bench <= q20_b
    crisis_mask = bench <= q10_b
    downside_mask = bench < 0
    tail_b_mask = bench <= q05_b

    conditional_corr = _safe_corr(port[cond_mask], bench[cond_mask])
    crisis_corr = _safe_corr(port[crisis_mask], bench[crisis_mask])

    downside_beta = None
    if int(downside_mask.sum()) >= 3:
        bench_down = bench[downside_mask]
        port_down = port[downside_mask]
        bench_var = float(bench_down.var())
        if math.isfinite(bench_var) and bench_var > 1e-12:
            downside_beta = float(port_down.cov(bench_down) / bench_var)

    joint_hit = float((((bench <= q20_b) & (port <= q20_p)).mean()) * 100.0)
    dd_port = _drawdown_series(port)
    dd_bench = _drawdown_series(bench)
    co_dd = float((((dd_port <= -0.10) & (dd_bench <= -0.10)).mean()) * 100.0)

    rolling_26 = _compute_cvar(port.tail(26), q=0.05)
    rolling_52 = _compute_cvar(port.tail(52), q=0.05)
    stressed = _compute_cvar(port[crisis_mask], q=0.05) if int(crisis_mask.sum()) >= 3 else _compute_cvar(port.tail(52), q=0.05)
    tail_dependence = float(((port[tail_b_mask] <= q05_p).mean()) * 100.0) if int(tail_b_mask.sum()) else None

    inference = compute_tail_bootstrap_ci(
        port_returns=port,
        benchmark_returns=bench,
        n_boot=2000,
        block_weeks=4,
        seed=42,
    )

    return {
        "benchmark": benchmark,
        "sample_weeks": int(len(port)),
        "conditional_correlation": round(conditional_corr, 4) if conditional_corr is not None else None,
        "crisis_window_correlation": round(crisis_corr, 4) if crisis_corr is not None else None,
        "downside_beta": round(downside_beta, 4) if downside_beta is not None else None,
        "joint_downside_hit_rate": round(joint_hit, 2),
        "co_drawdown_frequency": round(co_dd, 2),
        "rolling_cvar_26w": round(rolling_26 * 100.0, 2) if rolling_26 is not None else None,
        "rolling_cvar_52w": round(rolling_52 * 100.0, 2) if rolling_52 is not None else None,
        "stressed_cvar": round(stressed * 100.0, 2) if stressed is not None else None,
        "tail_dependence_lite": round(tail_dependence, 2) if tail_dependence is not None else None,
        "crisis_window_label": f"{benchmark} <= P10 weekly return",
        "tail_sample_count": int(tail_b_mask.sum()),
        "crisis_sample_count": int(crisis_mask.sum()),
        "downside_sample_count": int(downside_mask.sum()),
        "co_drawdown_threshold": -10.0,
        "tail_threshold_quantile": 0.05,
        "historical_var95_1w": round(historical_1w["var"] * 100.0, 2) if historical_1w["var"] is not None else None,
        "historical_es95_1w": round(historical_1w["es"] * 100.0, 2) if historical_1w["es"] is not None else None,
        "historical_sample_count_1w": historical_1w["sample_count"],
        "historical_var95_horizon": round(historical_horizon["var"] * 100.0, 2) if historical_horizon["var"] is not None else None,
        "historical_es95_horizon": round(historical_horizon["es"] * 100.0, 2) if historical_horizon["es"] is not None else None,
        "historical_horizon_weeks": HORIZON_WEEKS,
        "historical_horizon_sample_count": historical_horizon["sample_count"],
        "historical_horizon_method": "overlapping_compounded_current_weight_returns",
        "tail_inference": inference,
    }


def update_tail_meta(row: Dict[str, Any]) -> Dict[str, Any]:
    chaos_meta = row.get("chaos_meta") if isinstance(row.get("chaos_meta"), dict) else {}
    weights, xray_coverage_pct = _extract_model_weights(chaos_meta)
    if not weights:
        raise RuntimeError("xray_meta.mrc_table has no usable yf_ticker weights")

    benchmark = _choose_benchmark(weights)
    port, bench, diagnostics = _build_weekly_series(weights, benchmark)
    empirical = _compute_empirical_tail(port, bench, benchmark)

    current_tail = chaos_meta.get("tail_meta") if isinstance(chaos_meta.get("tail_meta"), dict) else {}
    current_tail.update(empirical)
    current_tail["empirical_refresh"] = {
        "status": "available",
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "scheduled_current_weight_yahoo_chart",
        "xray_weight_coverage_pct": round(xray_coverage_pct, 4),
        **diagnostics,
    }
    chaos_meta["tail_meta"] = current_tail
    return chaos_meta


def main() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    row = client.table(TABLE).select("chaos_meta").eq("id", ROW_ID).single().execute().data
    if not row:
        raise SystemExit("ERROR: portfolio row not found")

    chaos_meta = update_tail_meta(row)
    client.table(TABLE).update({"chaos_meta": chaos_meta}).eq("id", ROW_ID).execute()

    tail = chaos_meta.get("tail_meta") or {}
    inference = tail.get("tail_inference") or {}
    print(
        "OK tail inference refreshed "
        f"bench={tail.get('benchmark')} n={tail.get('sample_weeks')} "
        f"crisis_corr={tail.get('crisis_window_correlation')} "
        f"CI=[{inference.get('crisis_corr_ci95_low')}, {inference.get('crisis_corr_ci95_high')}] "
        f"down_beta={tail.get('downside_beta')} "
        f"CI=[{inference.get('downside_beta_ci95_low')}, {inference.get('downside_beta_ci95_high')}]"
    )


if __name__ == "__main__":
    main()
