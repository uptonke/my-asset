#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

OUT_DIR = Path("data/optimizer")
SKFOLIO = OUT_DIR / "skfolio_sandbox_latest.json"
RISKFOLIO = OUT_DIR / "riskfolio_sandbox_latest.json"
ROBUSTNESS = OUT_DIR / "optimizer_robustness_latest.json"
STRESS = OUT_DIR / "optimizer_stress_latest.json"
EXPECTED_RETURN = OUT_DIR / "expected_return_model_latest.json"
JSON_OUT = OUT_DIR / "walk_forward_backtest_latest.json"
MD_OUT = OUT_DIR / "walk_forward_backtest_summary.md"
VERSION = "v3.3"

SAFE_MODE_NOTE = (
    "v3.3 Walk-forward Backtest 用於檢查 optimizer 是否在樣本外風險/報酬表現上優於 current portfolio；"
    "輸出僅供模型驗證，不產生 BUY / SELL 指令，不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。"
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> Dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "READ_ERROR", "error": str(exc)[:500]}


def finite(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def mean(xs: List[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None and math.isfinite(float(x))]
    return sum(xs) / len(xs) if xs else None


def try_true_walk_forward() -> Tuple[Optional[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    try:
        import numpy as np
        import pandas as pd
        repo_root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repo_root / "scripts"))
        if not os.getenv("SUPABASE_SECRET_KEY") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
            os.environ["SUPABASE_SECRET_KEY"] = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        from run_skfolio_sandbox import load_strict_returns_and_weights, inverse_vol_weights, scipy_min_variance_weights, portfolio_metrics, turnover

        returns, current, meta = load_strict_returns_and_weights()
        returns = returns.dropna(how="any").sort_index()
        if len(returns) < 220:
            warnings.append(f"True walk-forward skipped: insufficient return sample ({len(returns)}).")
            return None, warnings

        train_days = 126
        test_days = 21
        step_days = 21
        methods = ["current_weight", "inverse_vol_baseline", "scipy_min_variance_fallback"]
        folds = []
        method_rows: Dict[str, List[Dict[str, Any]]] = {m: [] for m in methods}

        for start in range(0, len(returns) - train_days - test_days + 1, step_days):
            train = returns.iloc[start:start + train_days]
            test = returns.iloc[start + train_days:start + train_days + test_days]
            if len(test) < 15:
                continue
            fold_id = f"wf_{len(folds)+1:02d}"
            fold_info = {
                "fold_id": fold_id,
                "train_start": str(train.index.min().date()),
                "train_end": str(train.index.max().date()),
                "test_start": str(test.index.min().date()),
                "test_end": str(test.index.max().date()),
                "methods": {},
            }
            weights_map = {"current_weight": current}
            try:
                weights_map["inverse_vol_baseline"] = inverse_vol_weights(train)
            except Exception as exc:
                warnings.append(f"inverse_vol failed in {fold_id}: {str(exc)[:120]}")
            try:
                w, _ = scipy_min_variance_weights(train)
                weights_map["scipy_min_variance_fallback"] = w
            except Exception as exc:
                warnings.append(f"scipy_min_variance failed in {fold_id}: {str(exc)[:120]}")

            for method, w in weights_map.items():
                m = portfolio_metrics(test, w, method)
                m["turnover_vs_current_pct"] = round(float(turnover(w, current)) * 100.0, 3)
                m["fold_id"] = fold_id
                fold_info["methods"][method] = m
                method_rows.setdefault(method, []).append(m)
            folds.append(fold_info)

        if not folds:
            warnings.append("True walk-forward skipped: no valid folds.")
            return None, warnings

        current_rows = method_rows.get("current_weight", [])
        current_by_fold = {r.get("fold_id"): r for r in current_rows}
        aggregate = []
        for method, rows in method_rows.items():
            if not rows:
                continue
            ann_ret = [finite(r.get("annual_return_pct"), None) for r in rows]
            ann_vol = [finite(r.get("annual_vol_pct"), None) for r in rows]
            es = [finite(r.get("es95_pct"), None) for r in rows]
            mdd = [finite(r.get("max_drawdown_pct"), None) for r in rows]
            sharpe = [finite(r.get("sharpe"), None) for r in rows]
            turn = [finite(r.get("turnover_vs_current_pct"), None) for r in rows]
            risk_wins = 0
            return_wins = 0
            comparable = 0
            for r in rows:
                c = current_by_fold.get(r.get("fold_id"))
                if not c or method == "current_weight":
                    continue
                comparable += 1
                if (finite(r.get("es95_pct"), 999) or 999) <= (finite(c.get("es95_pct"), -999) or -999):
                    risk_wins += 1
                if (finite(r.get("annual_return_pct"), -999) or -999) >= (finite(c.get("annual_return_pct"), 999) or 999):
                    return_wins += 1
            aggregate.append({
                "method": method,
                "fold_count": len(rows),
                "avg_annual_return_pct": round(mean([x for x in ann_ret if x is not None]) or 0.0, 3),
                "avg_annual_vol_pct": round(mean([x for x in ann_vol if x is not None]) or 0.0, 3),
                "avg_es95_pct": round(mean([x for x in es if x is not None]) or 0.0, 3),
                "avg_max_drawdown_pct": round(mean([x for x in mdd if x is not None]) or 0.0, 3),
                "avg_sharpe": round(mean([x for x in sharpe if x is not None]) or 0.0, 3),
                "avg_turnover_vs_current_pct": round(mean([x for x in turn if x is not None]) or 0.0, 3),
                "risk_win_rate_vs_current": round(risk_wins / comparable, 3) if comparable else None,
                "return_win_rate_vs_current": round(return_wins / comparable, 3) if comparable else None,
                "decision": "baseline" if method == "current_weight" else "watch_only_validation",
            })
        aggregate.sort(key=lambda x: ((x.get("risk_win_rate_vs_current") or 0), -(x.get("avg_turnover_vs_current_pct") or 999)), reverse=True)
        return {
            "mode_detail": "true_walk_forward_from_price_returns",
            "sample": {
                "return_sample_count": int(len(returns)),
                "train_days": train_days,
                "test_days": test_days,
                "step_days": step_days,
                **(meta if isinstance(meta, dict) else {}),
            },
            "folds": folds,
            "aggregate_results": aggregate,
        }, warnings
    except Exception as exc:
        warnings.append(f"True walk-forward unavailable; fallback proxy used. Reason: {str(exc)[:500]}")
        return None, warnings


def proxy_walk_forward_from_robustness() -> Dict[str, Any]:
    robustness = load_json(ROBUSTNESS)
    stress = load_json(STRESS)
    window_results = robustness.get("window_results") or {}
    method_stability = robustness.get("method_stability") or {}
    comparison_rows = stress.get("comparison_rows") or []
    worst_by_method = {}
    for r in comparison_rows if isinstance(comparison_rows, list) else []:
        name = str(r.get("candidate") or r.get("method") or "")
        worst = finite(r.get("worst_scenario_pct") or r.get("worst_scenario_return_pct"), None)
        if name:
            worst_by_method[name] = worst

    aggregate = []
    for method, stability in method_stability.items() if isinstance(method_stability, dict) else []:
        vals = []
        turns = []
        es_vals = []
        vol_vals = []
        for win, rows in window_results.items():
            row = (rows or {}).get(method) if isinstance(rows, dict) else None
            if not row:
                continue
            metrics = row.get("metrics") or {}
            vals.append(win)
            turns.append(finite(row.get("turnover_vs_current_pct"), None))
            es_vals.append(finite(metrics.get("es95_pct"), None))
            vol_vals.append(finite(metrics.get("annual_vol_pct"), None))
        aggregate.append({
            "method": method,
            "fold_count": len(vals),
            "window_labels": vals,
            "avg_es95_pct": round(mean([x for x in es_vals if x is not None]) or 0.0, 3),
            "avg_annual_vol_pct": round(mean([x for x in vol_vals if x is not None]) or 0.0, 3),
            "avg_turnover_vs_current_pct": round(mean([x for x in turns if x is not None]) or 0.0, 3),
            "stability_verdict": stability.get("verdict"),
            "avg_pairwise_weight_turnover_pct": stability.get("avg_pairwise_weight_turnover_pct"),
            "worst_stress_pct": worst_by_method.get(method),
            "decision": "baseline" if method == "current_weight" else "proxy_only_no_out_of_sample_claim",
        })
    aggregate.sort(key=lambda x: ((x.get("avg_es95_pct") or 999), (x.get("avg_turnover_vs_current_pct") or 999)))
    return {
        "mode_detail": "proxy_from_robustness_windows_not_true_walk_forward",
        "sample": robustness.get("sample") or {},
        "folds": [],
        "aggregate_results": aggregate,
    }


def build() -> Dict[str, Any]:
    warnings: List[str] = []
    true_wf, wf_warnings = try_true_walk_forward()
    warnings.extend(wf_warnings)
    if true_wf is None:
        wf = proxy_walk_forward_from_robustness()
        status = "PROXY_ONLY"
        warnings.append("This is not a true out-of-sample walk-forward backtest; it uses robustness windows as proxy.")
    else:
        wf = true_wf
        status = "OK"
    agg = wf.get("aggregate_results") or []
    non_baseline = [r for r in agg if r.get("method") != "current_weight"]
    likely_better = []
    for r in non_baseline:
        risk_win = finite(r.get("risk_win_rate_vs_current"), None)
        turn = finite(r.get("avg_turnover_vs_current_pct"), 999) or 999
        if risk_win is not None and risk_win >= 0.6 and turn <= 35:
            likely_better.append(r.get("method"))
    return {
        "version": VERSION,
        "status": status,
        "generated_at": now_utc(),
        "mode": "walk_forward_backtest",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "source_files": {
            "skfolio": str(SKFOLIO),
            "riskfolio": str(RISKFOLIO),
            "optimizer_robustness": str(ROBUSTNESS),
            "optimizer_stress": str(STRESS),
            "expected_return_model": str(EXPECTED_RETURN),
        },
        "backtest_policy": {
            "auto_promotion_to_candidate": False,
            "requires_manual_review": True,
            "return_forecast_used": False,
            "transaction_cost_model": "not_included_yet",
            "lookahead_guard": "train_window_weights_applied_to_next_test_window_when_true_walk_forward_available",
        },
        **wf,
        "summary": {
            "method_count": len(agg),
            "fold_count": max([r.get("fold_count", 0) or 0 for r in agg], default=0),
            "likely_better_than_current_count": len(likely_better),
            "likely_better_than_current": likely_better,
            "verdict": "needs_more_out_of_sample_evidence" if status == "OK" else "proxy_only_insufficient_for_model_promotion",
        },
        "warnings": warnings,
        "execution_permission": False,
        "not_trade_order": True,
        "requires_manual_approval": True,
    }


def write_md(result: Dict[str, Any]) -> str:
    s = result.get("summary", {})
    lines = [
        "# Walk-forward Backtest v3.3",
        "",
        f"Generated: `{result.get('generated_at')}`",
        "",
        "## Safety boundary",
        "",
        "- 用於模型驗證，不是交易指令。",
        "- 不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。",
        "",
        "## Summary",
        "",
        f"- Status: `{result.get('status')}`",
        f"- Mode detail: `{result.get('mode_detail')}`",
        f"- Method count: `{s.get('method_count', 0)}`",
        f"- Fold count: `{s.get('fold_count', 0)}`",
        f"- Likely better than current: `{', '.join(s.get('likely_better_than_current') or []) or '-'}`",
        f"- Verdict: `{s.get('verdict')}`",
        "",
        "## Aggregate results",
        "",
        "| Method | Folds | Avg ES95 | Avg Vol | Avg Turnover | Risk win rate | Decision |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in result.get("aggregate_results", [])[:12]:
        lines.append(f"| `{r.get('method')}` | {r.get('fold_count')} | {r.get('avg_es95_pct', '-')} | {r.get('avg_annual_vol_pct', '-')} | {r.get('avg_turnover_vs_current_pct', '-')} | {r.get('risk_win_rate_vs_current', '-')} | `{r.get('decision')}` |")
    lines += ["", "## Warnings", ""]
    for w in result.get("warnings", []):
        lines.append(f"- {w}")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = build()
    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(write_md(result), encoding="utf-8")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Status: {result['status']}")
    print(f"Fold count: {result['summary']['fold_count']}")


if __name__ == "__main__":
    main()
