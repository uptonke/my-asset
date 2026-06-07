#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Supabase secret compatibility.
if not os.getenv("SUPABASE_SECRET_KEY") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SECRET_KEY"] = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

from run_skfolio_sandbox import (  # type: ignore
    load_strict_returns_and_weights,
    portfolio_metrics,
    weight_table,
    turnover,
    inverse_vol_weights,
    scipy_min_variance_weights,
    skfolio_meanrisk_weights,
)
from run_riskfolio_sandbox import run_riskfolio_optimization  # type: ignore


def normalize_weight_series(weights: pd.Series, columns: List[str]) -> pd.Series:
    w = weights.reindex(columns).fillna(0.0).astype(float)
    w = w.clip(lower=0.0)
    if float(w.sum()) <= 0:
        return pd.Series(1.0 / max(len(columns), 1), index=columns)
    return w / float(w.sum())


def method_result(
    returns: pd.DataFrame,
    current_weights: pd.Series,
    key: str,
    weights: Optional[pd.Series],
    method: Dict[str, Any],
) -> Dict[str, Any]:
    if weights is None:
        return {
            "status": method.get("status", "FAILED"),
            "method": method,
            "metrics": {},
            "turnover_vs_current_pct": None,
            "weights": [],
        }

    w = normalize_weight_series(weights, list(returns.columns))
    cw = normalize_weight_series(current_weights, list(returns.columns))

    return {
        "status": "OK",
        "method": method,
        "metrics": portfolio_metrics(returns, w, key),
        "turnover_vs_current_pct": round(turnover(w, cw) * 100.0, 2),
        "weights": weight_table(w, cw, top_n=25),
        "weight_vector": {t: round(float(w.get(t, 0.0)), 8) for t in returns.columns},
    }


def compute_window_portfolios(returns: pd.DataFrame, current_weights: pd.Series) -> Dict[str, Dict[str, Any]]:
    portfolios: Dict[str, Dict[str, Any]] = {}

    cw = normalize_weight_series(current_weights, list(returns.columns))
    portfolios["current_weight"] = method_result(
        returns, cw, "current_weight", cw,
        {"status": "OK", "method": "current weights"},
    )

    inv_w = inverse_vol_weights(returns)
    portfolios["inverse_vol_baseline"] = method_result(
        returns, cw, "inverse_vol_baseline", inv_w,
        {"status": "OK", "method": "inverse daily volatility"},
    )

    try:
        scipy_w, scipy_info = scipy_min_variance_weights(returns)
        portfolios["scipy_min_variance_fallback"] = method_result(
            returns, cw, "scipy_min_variance_fallback", scipy_w, scipy_info
        )
    except Exception as exc:
        portfolios["scipy_min_variance_fallback"] = {
            "status": "FAILED",
            "method": {"status": "FAILED", "error": str(exc)[:500]},
            "metrics": {},
            "weights": [],
        }

    sk_w, sk_info = skfolio_meanrisk_weights(returns, risk="VARIANCE")
    portfolios["skfolio_min_variance"] = method_result(
        returns, cw, "skfolio_min_variance", sk_w, sk_info
    )

    sk_cvar_w, sk_cvar_info = skfolio_meanrisk_weights(returns, risk="CVAR")
    portfolios["skfolio_cvar_minimize"] = method_result(
        returns, cw, "skfolio_cvar_minimize", sk_cvar_w, sk_cvar_info
    )

    for key, kind in [
        ("riskfolio_min_variance", "min_variance"),
        ("riskfolio_cvar_minimize", "cvar_minimize"),
        ("riskfolio_risk_parity_mv", "risk_parity_mv"),
        ("riskfolio_hrp_mv", "hrp_mv"),
    ]:
        w, info = run_riskfolio_optimization(returns, kind=kind)
        portfolios[key] = method_result(returns, cw, key, w, info)

    return portfolios


def pairwise_weight_turnover(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = sorted(set(a) | set(b))
    av = np.array([float(a.get(k, 0.0)) for k in keys], dtype=float)
    bv = np.array([float(b.get(k, 0.0)) for k in keys], dtype=float)
    return float(0.5 * np.abs(av - bv).sum())


def summarize_method_stability(window_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    # window_results: window_label -> portfolio_result
    ok_items = {
        label: result for label, result in window_results.items()
        if isinstance(result, dict) and result.get("status") == "OK" and result.get("weight_vector")
    }

    if len(ok_items) < 2:
        return {
            "status": "INSUFFICIENT_WINDOWS",
            "available_windows": len(ok_items),
            "avg_pairwise_weight_turnover_pct": None,
            "max_pairwise_weight_turnover_pct": None,
            "max_asset_weight_range_pct": None,
            "es95_range_pct": None,
            "annual_vol_range_pct": None,
            "verdict": "樣本不足",
        }

    pair_turnovers = []
    for left, right in combinations(ok_items.keys(), 2):
        pair_turnovers.append(pairwise_weight_turnover(ok_items[left]["weight_vector"], ok_items[right]["weight_vector"]))

    all_tickers = sorted(set().union(*[set(v["weight_vector"].keys()) for v in ok_items.values()]))
    max_range = 0.0
    max_range_ticker = None
    for t in all_tickers:
        vals = [float(v["weight_vector"].get(t, 0.0)) for v in ok_items.values()]
        rng = max(vals) - min(vals)
        if rng > max_range:
            max_range = rng
            max_range_ticker = t

    es_vals = [
        float(v.get("metrics", {}).get("es95_pct"))
        for v in ok_items.values()
        if v.get("metrics", {}).get("es95_pct") is not None
    ]
    vol_vals = [
        float(v.get("metrics", {}).get("annual_vol_pct"))
        for v in ok_items.values()
        if v.get("metrics", {}).get("annual_vol_pct") is not None
    ]

    avg_to = float(np.mean(pair_turnovers)) if pair_turnovers else None
    max_to = float(np.max(pair_turnovers)) if pair_turnovers else None

    if avg_to is None:
        verdict = "樣本不足"
    elif avg_to <= 0.15 and max_range <= 0.10:
        verdict = "穩定"
    elif avg_to <= 0.35 and max_range <= 0.25:
        verdict = "可觀察"
    else:
        verdict = "不穩定"

    return {
        "status": "OK",
        "available_windows": len(ok_items),
        "avg_pairwise_weight_turnover_pct": round((avg_to or 0.0) * 100.0, 2),
        "max_pairwise_weight_turnover_pct": round((max_to or 0.0) * 100.0, 2),
        "max_asset_weight_range_pct": round(max_range * 100.0, 2),
        "max_asset_weight_range_ticker": max_range_ticker,
        "es95_range_pct": round(max(es_vals) - min(es_vals), 3) if len(es_vals) >= 2 else None,
        "annual_vol_range_pct": round(max(vol_vals) - min(vol_vals), 2) if len(vol_vals) >= 2 else None,
        "verdict": verdict,
    }


def main() -> None:
    out_dir = Path("data/optimizer")
    out_dir.mkdir(parents=True, exist_ok=True)

    full_returns, current_weights, meta = load_strict_returns_and_weights()

    # Strict sample is currently about 375 days, so 2Y/3Y are expected to be unavailable.
    window_specs = [
        {"label": "6M", "days": 126, "min_days": 80},
        {"label": "1Y", "days": 252, "min_days": 160},
        {"label": "FULL_STRICT", "days": None, "min_days": 160},
        {"label": "2Y", "days": 504, "min_days": 360},
        {"label": "3Y", "days": 756, "min_days": 540},
    ]

    windows: List[Dict[str, Any]] = []
    window_results: Dict[str, Dict[str, Any]] = {}

    for spec in window_specs:
        label = spec["label"]
        days = spec["days"]
        min_days = int(spec["min_days"])

        if days is None:
            r = full_returns.copy()
        else:
            r = full_returns.tail(int(days)).copy()

        if len(r) < min_days:
            windows.append({
                "label": label,
                "status": "UNAVAILABLE",
                "sample_count": int(len(r)),
                "required_min_days": min_days,
                "reason": "strict sample too short for this window",
            })
            continue

        windows.append({
            "label": label,
            "status": "OK",
            "sample_count": int(len(r)),
            "start_date": str(r.index.min().date()),
            "end_date": str(r.index.max().date()),
        })
        window_results[label] = compute_window_portfolios(r, current_weights)

    method_keys = sorted(set().union(*[set(v.keys()) for v in window_results.values()])) if window_results else []
    method_stability = {}
    for method in method_keys:
        method_stability[method] = summarize_method_stability({
            win: results.get(method, {}) for win, results in window_results.items()
        })

    stable_candidates = [
        {"method": k, **v}
        for k, v in method_stability.items()
        if v.get("status") == "OK"
    ]
    stable_candidates.sort(key=lambda x: (
        {"穩定": 0, "可觀察": 1, "不穩定": 2}.get(x.get("verdict"), 9),
        x.get("avg_pairwise_weight_turnover_pct") if x.get("avg_pairwise_weight_turnover_pct") is not None else 999,
    ))

    result = {
        "version": "v1.4",
        "status": "OK" if window_results else "NO_AVAILABLE_WINDOWS",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "optimizer_robustness_sandbox",
        "safe_mode": True,
        "safe_mode_note": "This robustness check does not write Supabase, does not alter holdings, and does not create trade signals.",
        "sample": {
            "strict_sample": meta["strict_sample"],
            "strict_start": meta["strict_start"],
            "strict_end": meta["strict_end"],
            "asset_count": int(len(full_returns.columns)),
            "fx_source": meta["fx_source"],
        },
        "windows": windows,
        "method_stability": method_stability,
        "stable_rank": stable_candidates,
        "window_results": window_results,
        "warnings": [
            "2Y / 3Y robustness may be unavailable when strict sample is shorter than required.",
            "Stability is based on weight sensitivity across windows, not realized future performance.",
            "Low turnover between windows is not sufficient; ES, MDD, and implementation turnover still matter.",
            "This is a sandbox diagnostic, not a rebalance instruction.",
        ],
    }

    latest_path = out_dir / "optimizer_robustness_latest.json"
    latest_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_lines = [
        "# Optimizer Robustness v1.4",
        "",
        f"- Status: `{result['status']}`",
        f"- Strict sample: `{result['sample']['strict_sample']}`",
        f"- Period: `{result['sample']['strict_start']} → {result['sample']['strict_end']}`",
        f"- Asset count: `{result['sample']['asset_count']}`",
        "",
        "## Windows",
        "",
        "| Window | Status | Sample | Period / Reason |",
        "|---|---:|---:|---|",
    ]

    for w in windows:
        period = f"{w.get('start_date', '')} → {w.get('end_date', '')}" if w.get("status") == "OK" else w.get("reason", "")
        summary_lines.append(f"| {w['label']} | {w['status']} | {w.get('sample_count', 'N/A')} | {period} |")

    summary_lines.extend([
        "",
        "## Method stability",
        "",
        "| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])

    for method, s in sorted(method_stability.items()):
        summary_lines.append(
            f"| {method} | {s.get('verdict', 'N/A')} | {s.get('available_windows', 'N/A')} | "
            f"{s.get('avg_pairwise_weight_turnover_pct', 'N/A')}% | "
            f"{s.get('max_asset_weight_range_pct', 'N/A')}% | "
            f"{s.get('es95_range_pct', 'N/A')}% | "
            f"{s.get('annual_vol_range_pct', 'N/A')}% |"
        )

    summary_path = out_dir / "optimizer_robustness_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    github_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if github_summary:
        Path(github_summary).write_text("\n".join(summary_lines), encoding="utf-8")

    print(json.dumps({
        "version": result["version"],
        "status": result["status"],
        "strict_sample": result["sample"]["strict_sample"],
        "available_windows": [w["label"] for w in windows if w.get("status") == "OK"],
        "unavailable_windows": [w["label"] for w in windows if w.get("status") != "OK"],
        "method_count": len(method_stability),
        "output": str(latest_path),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
