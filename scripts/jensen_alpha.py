#!/usr/bin/env python3
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm

DEFAULT_BENCHMARKS = ("SPY", "^TWII")
DEFAULT_RF_TICKER = "^IRX"


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except (TypeError, ValueError):
        return default


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_yahoo_chart_close(symbol: str, days: int = 1600, timeout: int = 25) -> pd.Series:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        "period1": int(start.timestamp()),
        "period2": int(now.timestamp()),
        "interval": "1d",
        "events": "history",
    }
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    result = (((response.json().get("chart") or {}).get("result") or [])[:1])
    if not result:
        raise RuntimeError(f"Yahoo chart returned no result for {symbol}")
    payload = result[0]
    timestamps = payload.get("timestamp") or []
    quote = ((((payload.get("indicators") or {}).get("quote") or [])[:1]) or [{}])[0]
    closes = quote.get("close") or []
    if not timestamps or not closes:
        raise RuntimeError(f"Yahoo chart malformed for {symbol}")
    series = pd.Series(
        pd.to_numeric(closes, errors="coerce"),
        index=pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None),
        name=symbol,
        dtype="float64",
    ).dropna().sort_index()
    if len(series) < 20:
        raise RuntimeError(f"Yahoo chart too few observations for {symbol}: {len(series)}")
    return series


def build_cash_flow_adjusted_period_returns(
    history_data: Sequence[Mapping[str, Any]],
    ledger_data: Sequence[Mapping[str, Any]],
) -> pd.DataFrame:
    history: List[Dict[str, Any]] = []
    for row in history_data or []:
        try:
            dt = pd.Timestamp(str(row.get("date") or "")).normalize()
        except Exception:
            continue
        assets = _num(row.get("assets"))
        if pd.isna(dt) or assets is None or assets <= 0:
            continue
        history.append({"date": dt, "assets": float(assets)})
    history.sort(key=lambda x: x["date"])

    flows: List[Dict[str, Any]] = []
    for tx in ledger_data or []:
        tx_type = str(tx.get("type") or "").strip()
        if tx_type not in {"Deposit", "Withdraw"}:
            continue
        try:
            dt = pd.Timestamp(str(tx.get("date") or "")).normalize()
        except Exception:
            continue
        flow = _num(tx.get("totalCashFlow"), 0.0) or 0.0
        if pd.isna(dt):
            continue
        flows.append({"date": dt, "flow": float(flow)})

    rows: List[Dict[str, Any]] = []
    for prev, curr in zip(history[:-1], history[1:]):
        prev_date = prev["date"]
        curr_date = curr["date"]
        days = int((curr_date - prev_date).days)
        if days <= 0:
            continue
        external_flow = sum(
            item["flow"] for item in flows
            if item["date"] > prev_date and item["date"] <= curr_date
        )
        period_return = ((curr["assets"] - external_flow) / prev["assets"]) - 1.0
        if not math.isfinite(period_return) or period_return <= -1.0:
            continue
        rows.append({
            "prev_date": prev_date,
            "date": curr_date,
            "period_days": days,
            "portfolio_return": float(period_return),
            "external_flow": float(external_flow),
        })

    return pd.DataFrame(rows)


def _close_on_or_before(series: pd.Series, when: pd.Timestamp) -> float | None:
    if series.empty:
        return None
    cutoff = pd.Timestamp(when).normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    subset = series.loc[:cutoff]
    if subset.empty:
        return None
    value = _num(subset.iloc[-1])
    return float(value) if value is not None and value > 0 else None


def _interval_rf_return(irx_yield_pct: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float | None:
    days = int((pd.Timestamp(end).normalize() - pd.Timestamp(start).normalize()).days)
    if days <= 0:
        return None
    window = irx_yield_pct.loc[(irx_yield_pct.index > start) & (irx_yield_pct.index <= end)]
    if window.empty:
        cutoff = irx_yield_pct.loc[:end]
        if cutoff.empty:
            return None
        annual_pct = _num(cutoff.iloc[-1])
    else:
        annual_pct = _num(window.mean())
    if annual_pct is None:
        return None
    annual_rate = annual_pct / 100.0
    if annual_rate <= -0.99:
        return None
    return float((1.0 + annual_rate) ** (days / 365.25) - 1.0)


def _regress_one_benchmark(
    periods: pd.DataFrame,
    benchmark_close: pd.Series,
    irx_yield_pct: pd.Series,
    benchmark: str,
    hac_lags: int = 4,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for rec in periods.to_dict("records"):
        start = pd.Timestamp(rec["prev_date"])
        end = pd.Timestamp(rec["date"])
        start_px = _close_on_or_before(benchmark_close, start)
        end_px = _close_on_or_before(benchmark_close, end)
        rf_ret = _interval_rf_return(irx_yield_pct, start, end)
        if start_px is None or end_px is None or rf_ret is None:
            continue
        market_ret = (end_px / start_px) - 1.0
        port_ret = float(rec["portfolio_return"])
        if not all(math.isfinite(v) for v in (market_ret, port_ret, rf_ret)):
            continue
        rows.append({
            "date": end,
            "period_days": int(rec["period_days"]),
            "portfolio_excess": port_ret - rf_ret,
            "market_excess": market_ret - rf_ret,
            "portfolio_return": port_ret,
            "market_return": market_ret,
            "rf_return": rf_ret,
        })

    aligned = pd.DataFrame(rows).sort_values("date")
    n = len(aligned)
    if n < 26:
        return {
            "status": "insufficient_sample",
            "benchmark": benchmark,
            "n": n,
            "minimum_required": 26,
        }

    y = aligned["portfolio_excess"].astype(float)
    X = sm.add_constant(aligned[["market_excess"]].astype(float), has_constant="add")
    maxlags = max(0, min(int(hac_lags), max(0, n - 2)))
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags, "use_correction": True}, use_t=True)

    alpha_period = float(fit.params["const"])
    beta = float(fit.params["market_excess"])
    alpha_se_period = float(fit.bse["const"])
    beta_se = float(fit.bse["market_excess"])
    alpha_ci = fit.conf_int(alpha=0.05).loc["const"].tolist()
    beta_ci = fit.conf_int(alpha=0.05).loc["market_excess"].tolist()
    median_days = float(aligned["period_days"].median())
    periods_per_year = 365.25 / median_days if median_days > 0 else 52.0
    annualizer = periods_per_year * 100.0
    alpha_annual_pct = alpha_period * annualizer
    alpha_ci_low = float(alpha_ci[0]) * annualizer
    alpha_ci_high = float(alpha_ci[1]) * annualizer
    alpha_se_annual = alpha_se_period * annualizer
    p_value = float(fit.pvalues["const"])
    t_stat = float(fit.tvalues["const"])

    if p_value < 0.05 and alpha_ci_low > 0:
        evidence = "positive_alpha_distinguishable_from_zero_at_5pct_under_this_benchmark"
    elif p_value < 0.05 and alpha_ci_high < 0:
        evidence = "negative_alpha_distinguishable_from_zero_at_5pct_under_this_benchmark"
    else:
        evidence = "alpha_not_distinguishable_from_zero_at_5pct_under_this_benchmark"

    return {
        "status": "available",
        "benchmark": benchmark,
        "n": n,
        "sample_start": pd.Timestamp(aligned["date"].iloc[0]).date().isoformat(),
        "sample_end": pd.Timestamp(aligned["date"].iloc[-1]).date().isoformat(),
        "median_period_days": round(median_days, 2),
        "min_period_days": int(aligned["period_days"].min()),
        "max_period_days": int(aligned["period_days"].max()),
        "periods_per_year_for_alpha_annualization": round(periods_per_year, 4),
        "alpha_period_pct": round(alpha_period * 100.0, 4),
        "alpha_annualized_pct": round(alpha_annual_pct, 4),
        "alpha_hac_se_annualized_pct": round(alpha_se_annual, 4),
        "alpha_t_stat_hac": round(t_stat, 4),
        "alpha_p_value_hac": round(p_value, 6),
        "alpha_ci95_low_annualized_pct": round(alpha_ci_low, 4),
        "alpha_ci95_high_annualized_pct": round(alpha_ci_high, 4),
        "beta": round(beta, 4),
        "beta_hac_se": round(beta_se, 4),
        "beta_ci95_low": round(float(beta_ci[0]), 4),
        "beta_ci95_high": round(float(beta_ci[1]), 4),
        "r_squared": round(float(fit.rsquared), 4),
        "hac_lags": maxlags,
        "evidence_5pct": evidence,
    }


def compute_jensen_alpha_regression(
    history_data: Sequence[Mapping[str, Any]],
    ledger_data: Sequence[Mapping[str, Any]],
    benchmarks: Iterable[str] = DEFAULT_BENCHMARKS,
    rf_ticker: str = DEFAULT_RF_TICKER,
    fetch_days: int = 1600,
    hac_lags: int = 4,
) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "schema_version": 1,
        "status": "unavailable",
        "generated_at": _utc_now(),
        "method": "realized_cash_flow_adjusted_NAV_CAPM_OLS_with_HAC_Newey_West",
        "portfolio_return_source": "history_data_cash_flow_adjusted_TWR_periods",
        "benchmark_policy": "report_multiple_benchmarks_no_single_benchmark_skill_claim",
        "risk_free_source": rf_ticker,
        "risk_free_method": "interval_compounding_from_average_annualized_^IRX_yield_proxy",
        "hac_lags_requested": int(hac_lags),
        "benchmarks": {},
        "limitations": [
            "Single-factor CAPM alpha is benchmark-dependent for a mixed cross-asset portfolio.",
            "Alpha captures the realized portfolio outcome after cash-flow adjustment; it does not isolate security-selection skill from allocation, timing, or other factors.",
            "HAC/Newey-West adjusts standard errors for heteroskedasticity/autocorrelation but does not fix benchmark misspecification.",
            "^IRX is used as an annualized short-rate proxy rather than an exact realized risk-free total-return series.",
        ],
    }

    periods = build_cash_flow_adjusted_period_returns(history_data, ledger_data)
    base["portfolio_period_count"] = int(len(periods))
    if len(periods) < 26:
        base["status"] = "insufficient_portfolio_history"
        base["minimum_required"] = 26
        return base

    symbols = list(dict.fromkeys([str(x) for x in benchmarks if str(x).strip()]))
    try:
        rf_series = fetch_yahoo_chart_close(rf_ticker, days=fetch_days)
    except Exception as exc:
        base["status"] = "risk_free_source_unavailable"
        base["error"] = f"{type(exc).__name__}: {exc}"
        return base

    errors: Dict[str, str] = {}
    results: Dict[str, Dict[str, Any]] = {}
    for benchmark in symbols:
        try:
            bench_series = fetch_yahoo_chart_close(benchmark, days=fetch_days)
            results[benchmark] = _regress_one_benchmark(
                periods=periods,
                benchmark_close=bench_series,
                irx_yield_pct=rf_series,
                benchmark=benchmark,
                hac_lags=hac_lags,
            )
        except Exception as exc:
            errors[benchmark] = f"{type(exc).__name__}: {exc}"
            results[benchmark] = {
                "status": "fetch_or_regression_failed",
                "benchmark": benchmark,
                "error": errors[benchmark],
            }

    available = [row for row in results.values() if row.get("status") == "available"]
    base["benchmarks"] = results
    base["errors"] = errors
    base["available_benchmark_count"] = len(available)
    if available:
        base["status"] = "available" if len(available) == len(symbols) else "partial"
    else:
        base["status"] = "unavailable"

    if len(available) >= 2:
        alphas = [float(row["alpha_annualized_pct"]) for row in available]
        base["benchmark_alpha_range_pct"] = [round(min(alphas), 4), round(max(alphas), 4)]
        base["benchmark_alpha_spread_pp"] = round(max(alphas) - min(alphas), 4)
    else:
        base["benchmark_alpha_range_pct"] = None
        base["benchmark_alpha_spread_pp"] = None

    return base
