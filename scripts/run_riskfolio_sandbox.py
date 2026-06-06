#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Compatibility with repos that store the service role key under either name.
if not os.getenv("SUPABASE_SECRET_KEY") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SECRET_KEY"] = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def finite_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def normalize_weights(weights: Dict[str, float], tickers: List[str]) -> pd.Series:
    s = pd.Series({t: max(0.0, finite_float(weights.get(t), 0.0) or 0.0) for t in tickers}, dtype=float)
    if float(s.sum()) <= 0:
        return pd.Series(1.0 / max(len(tickers), 1), index=tickers)
    return s / float(s.sum())


def portfolio_metrics(returns: pd.DataFrame, weights: pd.Series, label: str) -> Dict[str, Any]:
    cols = [c for c in returns.columns if c in weights.index]
    if not cols:
        return {"label": label, "status": "NO_COMMON_ASSETS"}

    w = weights.reindex(cols).fillna(0.0)
    if float(w.sum()) <= 0:
        return {"label": label, "status": "ZERO_WEIGHT"}
    w = w / float(w.sum())

    r = returns[cols].dropna(how="any").dot(w)
    r = pd.to_numeric(r, errors="coerce").dropna()
    if len(r) < 40:
        return {"label": label, "status": "INSUFFICIENT_SAMPLE", "sample_count": int(len(r))}

    q05 = float(r.quantile(0.05))
    q01 = float(r.quantile(0.01))
    tail95 = r[r <= q05]
    tail99 = r[r <= q01]
    curve = (1.0 + r).cumprod()
    dd = curve / curve.cummax() - 1.0

    ann_return = float(((1.0 + r.mean()) ** 252) - 1.0)
    ann_vol = float(r.std(ddof=1) * math.sqrt(252))
    sharpe = ann_return / ann_vol if ann_vol > 0 else None

    return {
        "label": label,
        "status": "OK",
        "sample_count": int(len(r)),
        "start_date": str(r.index.min().date()),
        "end_date": str(r.index.max().date()),
        "annual_return_pct": round(ann_return * 100.0, 2),
        "annual_vol_pct": round(ann_vol * 100.0, 2),
        "sharpe": round(float(sharpe), 3) if sharpe is not None and math.isfinite(float(sharpe)) else None,
        "var95_pct": round(max(0.0, -q05) * 100.0, 3),
        "es95_pct": round(max(0.0, -float(tail95.mean())) * 100.0, 3) if len(tail95) else None,
        "var99_pct": round(max(0.0, -q01) * 100.0, 3),
        "es99_pct": round(max(0.0, -float(tail99.mean())) * 100.0, 3) if len(tail99) else None,
        "max_drawdown_pct": round(float(dd.min()) * 100.0, 2),
        "worst_day_pct": round(float(r.min()) * 100.0, 2),
        "best_day_pct": round(float(r.max()) * 100.0, 2),
    }


def weight_table(weights: pd.Series, current: pd.Series, top_n: int = 25) -> List[Dict[str, Any]]:
    all_idx = sorted(set(weights.index) | set(current.index))
    rows = []
    for t in all_idx:
        w = float(weights.get(t, 0.0))
        cw = float(current.get(t, 0.0))
        rows.append({
            "ticker": t,
            "weight_pct": round(w * 100.0, 3),
            "current_weight_pct": round(cw * 100.0, 3),
            "turnover_contribution_pct": round(abs(w - cw) * 100.0, 3),
            "delta_vs_current_pct": round((w - cw) * 100.0, 3),
        })
    rows.sort(key=lambda x: abs(x["delta_vs_current_pct"]), reverse=True)
    return rows[:top_n]


def turnover(weights: pd.Series, current: pd.Series) -> float:
    idx = sorted(set(weights.index) | set(current.index))
    w = weights.reindex(idx).fillna(0.0)
    c = current.reindex(idx).fillna(0.0)
    return float(0.5 * np.abs(w - c).sum())


def inverse_vol_weights(returns: pd.DataFrame) -> pd.Series:
    vol = returns.std(ddof=1).replace(0, np.nan)
    inv = 1.0 / vol
    inv = inv.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if float(inv.sum()) <= 0:
        return pd.Series(1.0 / len(returns.columns), index=returns.columns)
    return inv / float(inv.sum())


def scipy_min_variance_weights(returns: pd.DataFrame) -> Tuple[pd.Series, Dict[str, Any]]:
    from scipy.optimize import minimize

    cols = list(returns.columns)
    cov = returns[cols].cov().values * 252.0
    n = len(cols)
    x0 = np.ones(n) / n

    bounds = [(0.0, 1.0) for _ in range(n)]
    constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]

    def objective(x: np.ndarray) -> float:
        return float(x @ cov @ x.T)

    res = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints, options={"maxiter": 500})
    if not res.success:
        raise RuntimeError(f"scipy min variance failed: {res.message}")

    w = pd.Series(res.x, index=cols)
    w = w.clip(lower=0.0)
    w = w / float(w.sum())
    return w, {"optimizer": "scipy_slsqp_min_variance", "success": bool(res.success), "message": str(res.message)}


def extract_riskfolio_weights(raw: Any, tickers: List[str]) -> Optional[pd.Series]:
    if raw is None:
        return None

    try:
        if isinstance(raw, pd.DataFrame):
            if "weights" in raw.columns:
                s = raw["weights"]
            elif raw.shape[1] >= 1:
                s = raw.iloc[:, 0]
            else:
                return None
        elif isinstance(raw, pd.Series):
            s = raw
        else:
            arr = np.asarray(raw, dtype=float).reshape(-1)
            if arr.size != len(tickers):
                return None
            s = pd.Series(arr, index=tickers)

        s = pd.to_numeric(s, errors="coerce")
        # Riskfolio usually returns index = asset names.
        s = s.reindex(tickers).fillna(0.0)
        s = s.clip(lower=0.0)
        if float(s.sum()) <= 0:
            return None
        return s / float(s.sum())
    except Exception:
        return None


def riskfolio_portfolio_setup(returns: pd.DataFrame) -> Any:
    import riskfolio as rp

    port = rp.Portfolio(returns=returns)

    # Historical estimates. Different versions may accept slightly different args.
    try:
        port.assets_stats(method_mu="hist", method_cov="hist", d=0.94)
    except TypeError:
        try:
            port.assets_stats(method_mu="hist", method_cov="hist")
        except Exception:
            pass
    except Exception:
        pass

    return port


def run_riskfolio_optimization(returns: pd.DataFrame, kind: str) -> Tuple[Optional[pd.Series], Dict[str, Any]]:
    import riskfolio as rp

    tickers = list(returns.columns)
    tried: List[Dict[str, Any]] = []

    try:
        if kind == "min_variance":
            port = riskfolio_portfolio_setup(returns)
            configs = [
                {"model": "Classic", "rm": "MV", "obj": "MinRisk", "rf": 0, "l": 0, "hist": True},
                {"model": "Classic", "rm": "MV", "obj": "MinRisk", "rf": 0, "hist": True},
            ]
            for kwargs in configs:
                try:
                    raw = port.optimization(**kwargs)
                    w = extract_riskfolio_weights(raw, tickers)
                    if w is not None:
                        return w, {"status": "OK", "library": "Riskfolio-Lib", "method": "Portfolio.optimization", "kind": kind, "kwargs": kwargs}
                    tried.append({"kwargs": kwargs, "error": "weights extraction failed"})
                except Exception as exc:
                    tried.append({"kwargs": kwargs, "error": str(exc)[:500]})

        if kind == "cvar_minimize":
            port = riskfolio_portfolio_setup(returns)
            configs = [
                {"model": "Classic", "rm": "CVaR", "obj": "MinRisk", "rf": 0, "l": 0, "hist": True},
                {"model": "Classic", "rm": "CVaR", "obj": "MinRisk", "rf": 0, "hist": True},
            ]
            for kwargs in configs:
                try:
                    raw = port.optimization(**kwargs)
                    w = extract_riskfolio_weights(raw, tickers)
                    if w is not None:
                        return w, {"status": "OK", "library": "Riskfolio-Lib", "method": "Portfolio.optimization", "kind": kind, "kwargs": kwargs}
                    tried.append({"kwargs": kwargs, "error": "weights extraction failed"})
                except Exception as exc:
                    tried.append({"kwargs": kwargs, "error": str(exc)[:500]})

        if kind == "risk_parity_mv":
            port = riskfolio_portfolio_setup(returns)
            configs = [
                {"model": "Classic", "rm": "MV", "rf": 0, "b": None, "hist": True},
                {"model": "Classic", "rm": "MV", "rf": 0, "hist": True},
            ]
            for kwargs in configs:
                try:
                    raw = port.rp_optimization(**kwargs)
                    w = extract_riskfolio_weights(raw, tickers)
                    if w is not None:
                        return w, {"status": "OK", "library": "Riskfolio-Lib", "method": "Portfolio.rp_optimization", "kind": kind, "kwargs": kwargs}
                    tried.append({"kwargs": kwargs, "error": "weights extraction failed"})
                except Exception as exc:
                    tried.append({"kwargs": kwargs, "error": str(exc)[:500]})

        if kind == "hrp_mv":
            configs = [
                {"model": "HRP", "codependence": "pearson", "rm": "MV", "rf": 0, "linkage": "single", "max_k": 10, "leaf_order": True},
                {"model": "HRP", "codependence": "pearson", "rm": "MV", "rf": 0, "linkage": "ward", "max_k": 10, "leaf_order": True},
                {"codependence": "pearson", "rm": "MV", "rf": 0, "linkage": "single", "max_k": 10, "leaf_order": True},
            ]
            for kwargs in configs:
                try:
                    hc = rp.HCPortfolio(returns=returns)
                    raw = hc.optimization(**kwargs)
                    w = extract_riskfolio_weights(raw, tickers)
                    if w is not None:
                        return w, {"status": "OK", "library": "Riskfolio-Lib", "method": "HCPortfolio.optimization", "kind": kind, "kwargs": kwargs}
                    tried.append({"kwargs": kwargs, "error": "weights extraction failed"})
                except Exception as exc:
                    tried.append({"kwargs": kwargs, "error": str(exc)[:500]})

    except Exception as exc:
        tried.append({"kwargs": {"kind": kind}, "error": str(exc)[:500]})

    return None, {"status": "FAILED", "library": "Riskfolio-Lib", "kind": kind, "tried": tried}


def load_strict_returns_and_weights() -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
    import update_stock_meta as q

    client = q.connect_supabase()
    row = q.fetch_portfolio_row(client)
    ledger = row.get("ledger_data") or []
    holdings = q.active_holdings_from_ledger(ledger)

    if not holdings:
        raise RuntimeError("No active holdings found.")

    settings = row.get("settings") if isinstance(row.get("settings"), dict) else {}
    static_fx = finite_float(settings.get("exchangeRate"), 31.5) or 31.5
    fx_series, fx_source = q.fetch_usdtwd_series(static_fx)

    asset_prices_twd: Dict[str, pd.Series] = {}
    asset_values: Dict[str, float] = {}
    sources: Dict[str, str] = {}
    skipped: List[Dict[str, Any]] = []

    for ticker, h in sorted(holdings.items()):
        shares = finite_float(h.get("shares"), 0.0) or 0.0
        if shares <= 0:
            continue

        category = str(h.get("category") or "")

        try:
            df, source, extras = q.fetch_history(ticker, category)
            price = q.clean_price_series(df)
            if len(price) < 40:
                skipped.append({"ticker": ticker, "reason": f"insufficient_price_rows:{len(price)}"})
                continue

            if q.is_foreign_currency_asset(ticker, category):
                if not fx_series.empty:
                    aligned_fx = fx_series.reindex(price.index).ffill().bfill()
                    price_twd = price * aligned_fx
                else:
                    price_twd = price * static_fx
            else:
                price_twd = price

            price_twd = pd.to_numeric(price_twd, errors="coerce").dropna()
            if len(price_twd) < 40:
                skipped.append({"ticker": ticker, "reason": f"insufficient_twd_rows:{len(price_twd)}"})
                continue

            market_value = float(price_twd.iloc[-1]) * shares
            if market_value <= 0:
                skipped.append({"ticker": ticker, "reason": "non_positive_market_value"})
                continue

            asset_prices_twd[ticker] = price_twd
            asset_values[ticker] = market_value
            sources[ticker] = source
        except Exception as exc:
            skipped.append({"ticker": ticker, "reason": str(exc)[:300]})

    if len(asset_prices_twd) < 2:
        raise RuntimeError("Less than 2 assets with usable price history.")

    total_mv = sum(asset_values.values())
    current_weights = normalize_weights({t: v / total_mv for t, v in asset_values.items()}, list(asset_prices_twd.keys()))

    prices = pd.concat(asset_prices_twd, axis=1).sort_index().ffill()
    strict_prices = prices.dropna(how="any")
    returns = strict_prices.pct_change().dropna(how="any")

    if len(returns) < 60:
        raise RuntimeError(f"Strict returns sample too short: {len(returns)}")

    current_weights = current_weights.reindex(returns.columns).fillna(0.0)
    current_weights = current_weights / float(current_weights.sum())

    meta = {
        "sources": sources,
        "skipped": skipped,
        "fx_source": fx_source,
        "strict_sample": int(len(returns)),
        "strict_start": str(returns.index.min().date()),
        "strict_end": str(returns.index.max().date()),
    }

    return returns, current_weights, meta


def add_portfolio(portfolios: Dict[str, Dict[str, Any]], key: str, weights: Optional[pd.Series], current_weights: pd.Series, returns: pd.DataFrame, method: Dict[str, Any]) -> None:
    if weights is None:
        portfolios[key] = {"status": method.get("status", "FAILED"), "method": method}
        return

    portfolios[key] = {
        "status": "OK",
        "weights": weight_table(weights, current_weights, top_n=25),
        "metrics": portfolio_metrics(returns, weights, key),
        "turnover_vs_current_pct": round(turnover(weights, current_weights) * 100.0, 2),
        "method": method,
    }


def main() -> None:
    out_dir = Path("data/optimizer")
    out_dir.mkdir(parents=True, exist_ok=True)

    returns, current_weights, meta = load_strict_returns_and_weights()

    portfolios: Dict[str, Dict[str, Any]] = {}

    add_portfolio(
        portfolios,
        "current_weight",
        current_weights,
        current_weights,
        returns,
        {"status": "OK", "method": "current portfolio weights"},
    )

    inv_w = inverse_vol_weights(returns)
    add_portfolio(
        portfolios,
        "inverse_vol_baseline",
        inv_w,
        current_weights,
        returns,
        {"status": "OK", "method": "inverse daily volatility"},
    )

    try:
        scipy_w, scipy_info = scipy_min_variance_weights(returns)
        add_portfolio(portfolios, "scipy_min_variance_fallback", scipy_w, current_weights, returns, scipy_info)
    except Exception as exc:
        portfolios["scipy_min_variance_fallback"] = {"status": "FAILED", "error": str(exc)[:500]}

    for key, kind in [
        ("riskfolio_min_variance", "min_variance"),
        ("riskfolio_cvar_minimize", "cvar_minimize"),
        ("riskfolio_risk_parity_mv", "risk_parity_mv"),
        ("riskfolio_hrp_mv", "hrp_mv"),
    ]:
        w, info = run_riskfolio_optimization(returns, kind=kind)
        add_portfolio(portfolios, key, w, current_weights, returns, info)

    riskfolio_statuses = {k: v.get("status") for k, v in portfolios.items() if k.startswith("riskfolio_")}
    any_riskfolio_ok = any(v == "OK" for v in riskfolio_statuses.values())

    result = {
        "version": "v1.2",
        "status": "OK" if any_riskfolio_ok else "DEGRADED",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "sandbox_only",
        "safe_mode": True,
        "safe_mode_note": "This sandbox does not write Supabase, does not alter holdings, and does not create trade signals.",
        "sample": {
            "strict_sample": meta["strict_sample"],
            "strict_start": meta["strict_start"],
            "strict_end": meta["strict_end"],
            "asset_count": int(len(returns.columns)),
            "fx_source": meta["fx_source"],
        },
        "portfolios": portfolios,
        "riskfolio_statuses": riskfolio_statuses,
        "skipped": meta.get("skipped", []),
        "warnings": [
            "Riskfolio-Lib output is sandbox diagnostics only.",
            "No expected-return model is used; return-seeking optimization is intentionally excluded.",
            "High turnover vs current indicates implementation friction and tax/fee/slippage risk.",
            "If one Riskfolio method fails but others succeed, inspect method.tried for API/solver details.",
        ],
    }

    latest_path = out_dir / "riskfolio_sandbox_latest.json"
    latest_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_lines = [
        "# Riskfolio-Lib Sandbox v1.2",
        "",
        f"- Status: `{result['status']}`",
        f"- Mode: `{result['mode']}`",
        f"- Strict sample: `{result['sample']['strict_sample']}`",
        f"- Period: `{result['sample']['strict_start']} → {result['sample']['strict_end']}`",
        f"- Asset count: `{result['sample']['asset_count']}`",
        "",
        "| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for name, p in portfolios.items():
        m = p.get("metrics", {}) if isinstance(p, dict) else {}
        summary_lines.append(
            f"| {name} | {p.get('status', 'N/A')} | "
            f"{m.get('annual_vol_pct', 'N/A')}% | {m.get('var95_pct', 'N/A')}% | "
            f"{m.get('es95_pct', 'N/A')}% | {m.get('max_drawdown_pct', 'N/A')}% | "
            f"{p.get('turnover_vs_current_pct', 'N/A')}% |"
        )

    (out_dir / "riskfolio_sandbox_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")

    github_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if github_summary:
        Path(github_summary).write_text("\n".join(summary_lines), encoding="utf-8")

    print(json.dumps({
        "version": result["version"],
        "status": result["status"],
        "strict_sample": result["sample"]["strict_sample"],
        "asset_count": result["sample"]["asset_count"],
        "riskfolio_statuses": riskfolio_statuses,
        "output": str(latest_path),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
