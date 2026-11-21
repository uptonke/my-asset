#!/usr/bin/env python3
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd
import requests
import statsmodels.api as sm

DEFAULT_BENCHMARKS = ("SPY", "^TWII")
DEFAULT_RF_TICKER = "^IRX"
DEFAULT_FX_TICKER = "TWD=X"


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
    """Build Modified Dietz returns from weekly NAV snapshots and dated external cash flows."""
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

        period_flows = [
            item for item in flows
            if item["date"] > prev_date and item["date"] <= curr_date
        ]
        external_flow = float(sum(item["flow"] for item in period_flows))
        weighted_flow = 0.0
        for item in period_flows:
            remaining_days = max(0, int((curr_date - item["date"]).days))
            weight = min(1.0, max(0.0, remaining_days / days))
            weighted_flow += item["flow"] * weight

        denominator = float(prev["assets"]) + weighted_flow
        if not math.isfinite(denominator) or denominator <= 0:
            continue
        period_return = (
            float(curr["assets"]) - float(prev["assets"]) - external_flow
        ) / denominator
        if not math.isfinite(period_return) or period_return <= -1.0:
            continue

        rows.append({
            "prev_date": prev_date,
            "date": curr_date,
            "period_days": days,
            "portfolio_return_twd": float(period_return),
            "external_flow": external_flow,
            "weighted_external_flow": float(weighted_flow),
            "dietz_denominator": denominator,
            "external_flow_count": len(period_flows),
            "return_method": "modified_dietz",
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


def _interval_price_return(series: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float | None:
    start_px = _close_on_or_before(series, start)
    end_px = _close_on_or_before(series, end)
    if start_px is None or end_px is None or start_px <= 0:
        return None
    out = end_px / start_px - 1.0
    return float(out) if math.isfinite(out) and out > -1.0 else None


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


def _combine_returns(asset_return: float, fx_return: float) -> float:
    return float((1.0 + asset_return) * (1.0 + fx_return) - 1.0)


def _remove_fx_from_twd_return(twd_return: float, fx_return: float) -> float | None:
    denom = 1.0 + fx_return
    if denom <= 0:
        return None
    out = (1.0 + twd_return) / denom - 1.0
    return float(out) if math.isfinite(out) and out > -1.0 else None


def _twd_opportunity_cost_return(
    irx_yield_pct: pd.Series,
    fx_close: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> float | None:
    """Unhedged USD T-bill proxy translated to TWD; not a domestic TWD risk-free rate."""
    rf_usd = _interval_rf_return(irx_yield_pct, start, end)
    fx_ret = _interval_price_return(fx_close, start, end)
    if rf_usd is None or fx_ret is None:
        return None
    out = _combine_returns(rf_usd, fx_ret)
    return out if math.isfinite(out) and out > -1.0 else None


def _benchmark_return_usd(
    benchmark_close: pd.Series,
    fx_close: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
    benchmark_currency: str,
) -> float | None:
    market_local = _interval_price_return(benchmark_close, start, end)
    if market_local is None:
        return None
    if benchmark_currency.upper() == "USD":
        return market_local
    fx_ret = _interval_price_return(fx_close, start, end)
    if fx_ret is None:
        return None
    return _remove_fx_from_twd_return(market_local, fx_ret)


def _build_rolling_12m_excess(
    periods: pd.DataFrame,
    irx_yield_pct: pd.Series,
    fx_close: pd.Series,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for rec in periods.to_dict("records"):
        start = pd.Timestamp(rec["prev_date"])
        end = pd.Timestamp(rec["date"])
        opportunity_twd = _twd_opportunity_cost_return(irx_yield_pct, fx_close, start, end)
        port_ret = _num(rec.get("portfolio_return_twd"))
        if opportunity_twd is None or port_ret is None:
            continue
        rows.append({
            "prev_date": start,
            "date": end,
            "portfolio_return_twd": float(port_ret),
            "opportunity_cost_return_twd": float(opportunity_twd),
        })

    if not rows:
        return []

    aligned = pd.DataFrame(rows).sort_values("date")
    output: List[Dict[str, Any]] = []
    for _, endpoint in aligned.iterrows():
        end = pd.Timestamp(endpoint["date"])
        cutoff = end - pd.Timedelta(days=365)
        window = aligned[(aligned["date"] > cutoff) & (aligned["date"] <= end)].copy()
        if window.empty:
            continue
        window_days = int((end - pd.Timestamp(window["prev_date"].iloc[0])).days)
        if len(window) < 40 or window_days < 330:
            continue
        portfolio_growth = float((1.0 + window["portfolio_return_twd"].astype(float)).prod())
        opportunity_growth = float((1.0 + window["opportunity_cost_return_twd"].astype(float)).prod())
        if portfolio_growth <= 0 or opportunity_growth <= 0:
            continue
        portfolio_12m = portfolio_growth - 1.0
        opportunity_12m = opportunity_growth - 1.0
        output.append({
            "date": end.date().isoformat(),
            "portfolio_12m_pct": round(portfolio_12m * 100.0, 4),
            "opportunity_cost_12m_pct": round(opportunity_12m * 100.0, 4),
            "excess_12m_pct": round((portfolio_12m - opportunity_12m) * 100.0, 4),
            "n": int(len(window)),
            "window_days": window_days,
        })
    return output


def _regress_one_benchmark(
    periods: pd.DataFrame,
    benchmark_close: pd.Series,
    irx_yield_pct: pd.Series,
    fx_close: pd.Series,
    benchmark: str,
    benchmark_currency: str,
    hac_lags: int = 4,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for rec in periods.to_dict("records"):
        start = pd.Timestamp(rec["prev_date"])
        end = pd.Timestamp(rec["date"])
        fx_ret = _interval_price_return(fx_close, start, end)
        rf_usd = _interval_rf_return(irx_yield_pct, start, end)
        market_usd = _benchmark_return_usd(
            benchmark_close, fx_close, start, end, benchmark_currency
        )
        port_twd = float(rec["portfolio_return_twd"])
        if fx_ret is None or rf_usd is None or market_usd is None:
            continue
        port_usd = _remove_fx_from_twd_return(port_twd, fx_ret)
        if port_usd is None:
            continue
        rows.append({
            "date": end,
            "period_days": int(rec["period_days"]),
            "portfolio_excess": port_usd - rf_usd,
            "market_excess": market_usd - rf_usd,
        })

    aligned = pd.DataFrame(rows).sort_values("date")
    n = len(aligned)
    if n < 26:
        return {
            "status": "insufficient_sample",
            "benchmark": benchmark,
            "benchmark_currency_original": benchmark_currency,
            "analysis_currency": "USD",
            "n": n,
            "minimum_required": 26,
        }

    y = aligned["portfolio_excess"].astype(float)
    X = sm.add_constant(aligned[["market_excess"]].astype(float), has_constant="add")
    maxlags = max(0, min(int(hac_lags), max(0, n - 2)))
    fit = sm.OLS(y, X).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": maxlags, "use_correction": True},
        use_t=True,
    )

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
        "benchmark_currency_original": benchmark_currency,
        "analysis_currency": "USD",
        "benchmark_fx_translation": "none" if benchmark_currency.upper() == "USD" else "TWD_return_deflated_by_USDTWD_return",
        "portfolio_fx_translation": "TWD_Modified_Dietz_return_deflated_by_USDTWD_return",
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
    fx_ticker: str = DEFAULT_FX_TICKER,
    fetch_days: int = 1600,
    hac_lags: int = 4,
) -> Dict[str, Any]:
    """CAPM Jensen alpha using common USD returns plus TWD rolling opportunity cost."""
    base: Dict[str, Any] = {
        "schema_version": 2,
        "status": "unavailable",
        "generated_at": _utc_now(),
        "method": "realized_modified_dietz_common_USD_CAPM_OLS_with_HAC_Newey_West",
        "portfolio_return_source": "weekly_NAV_modified_dietz_period_returns_TWD_converted_to_USD_for_CAPM",
        "portfolio_return_method": "Modified Dietz; strict TWR unavailable without valuation at each external cash-flow timestamp",
        "analysis_currency": "USD",
        "benchmark_policy": "report_multiple_benchmarks_after_common_currency_alignment_no_single_benchmark_skill_claim",
        "fx_source": f"YahooChart:{fx_ticker}",
        "risk_free_source": rf_ticker,
        "risk_free_method": "USD_^IRX_interval_compounding_for_CAPM",
        "opportunity_cost_label": "USD 3M T-bill proxy translated to TWD with unhedged USD/TWD FX; opportunity-cost proxy, not domestic TWD risk-free",
        "rolling_12m_method": "compounded Modified Dietz TWD return minus compounded TWD-translated USD T-bill opportunity-cost proxy over trailing ~12 months",
        "hac_lags_requested": int(hac_lags),
        "benchmarks": {},
        "rolling_12m_excess_return_twd": [],
        "rolling_12m_latest": None,
        "limitations": [
            "Weekly NAV snapshots cannot produce strict TWR; Modified Dietz is used instead.",
            "Jensen CAPM uses a common USD numeraire: TWD portfolio returns and ^TWII returns are translated to USD using USD/TWD, while SPY and ^IRX remain USD.",
            "Rolling 12M Excess Return is separately shown in TWD against an unhedged USD T-bill opportunity-cost proxy translated through USD/TWD; that proxy contains FX risk and is not a domestic TWD risk-free asset.",
            "Single-factor CAPM alpha is benchmark-dependent for a mixed cross-asset portfolio.",
            "Alpha does not isolate security-selection skill from allocation, timing, or other effects.",
            "HAC/Newey-West does not fix benchmark misspecification.",
            "^IRX is an annualized yield proxy rather than an exact realized total-return series.",
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
        fx_series = fetch_yahoo_chart_close(fx_ticker, days=fetch_days)
    except Exception as exc:
        base["status"] = "risk_free_or_fx_source_unavailable"
        base["error"] = f"{type(exc).__name__}: {exc}"
        return base

    rolling = _build_rolling_12m_excess(periods, rf_series, fx_series)
    base["rolling_12m_excess_return_twd"] = rolling
    base["rolling_12m_latest"] = rolling[-1] if rolling else None

    errors: Dict[str, str] = {}
    results: Dict[str, Dict[str, Any]] = {}
    for benchmark in symbols:
        benchmark_currency = "TWD" if benchmark == "^TWII" else "USD"
        try:
            bench_series = fetch_yahoo_chart_close(benchmark, days=fetch_days)
            results[benchmark] = _regress_one_benchmark(
                periods, bench_series, rf_series, fx_series,
                benchmark, benchmark_currency, hac_lags
            )
        except Exception as exc:
            errors[benchmark] = f"{type(exc).__name__}: {exc}"
            results[benchmark] = {
                "status": "fetch_or_regression_failed",
                "benchmark": benchmark,
                "benchmark_currency_original": benchmark_currency,
                "analysis_currency": "USD",
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
