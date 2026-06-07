#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

OUT_DIR = Path("data/optimizer")
JSON_OUT = OUT_DIR / "model_governance_dashboard_latest.json"
MD_OUT = OUT_DIR / "model_governance_dashboard_summary.md"
VERSION = "v3.4"

REGISTRY = [
    ("v1.0", "skfolio Sandbox", "skfolio_sandbox_latest.json"),
    ("v1.1", "Riskfolio Dependency Sandbox", "riskfolio_dependency_status.json"),
    ("v1.2", "Riskfolio Optimizer Sandbox", "riskfolio_sandbox_latest.json"),
    ("v1.4", "Optimizer Robustness Check", "optimizer_robustness_latest.json"),
    ("v1.7", "Stress Test Optimizer Weights", "optimizer_stress_latest.json"),
    ("v2.0", "Portfolio Optimizer Decision Center", "decision_center_latest.json"),
    ("v2.1", "Rebalance Candidate Generator", "rebalance_candidates_latest.json"),
    ("v2.2", "Risk Reduction Simulator", "risk_reduction_simulator_latest.json"),
    ("v2.3", "Constraint-Aware Rebalance Sandbox", "constraint_aware_rebalance_latest.json"),
    ("v2.4", "Human Approval Layer", "human_approval_layer_latest.json"),
    ("v2.5", "Action Audit Trail", "action_audit_trail_latest.json"),
    ("v3.0", "Regime-Aware Optimizer", "regime_aware_optimizer_latest.json"),
    ("v3.1", "Bayesian / Black-Litterman Sandbox", "black_litterman_sandbox_latest.json"),
    ("v3.2", "Expected Return Model", "expected_return_model_latest.json"),
    ("v3.3", "Walk-forward Backtest", "walk_forward_backtest_latest.json"),
]

SAFE_MODE_NOTE = (
    "v3.4 Model Governance Dashboard 追蹤模型版本、失效條件、樣本品質與過度最佳化風險；"
    "不是交易系統，不產生 BUY / SELL 指令，不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。"
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


def sample_quality(files: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    samples = []
    three_y_available = None
    for d in files.values():
        sample = d.get("sample") or {}
        n = finite(sample.get("strict_sample") or sample.get("sample_count") or sample.get("return_sample_count"), None)
        if n is not None:
            samples.append(int(n))
        if "windows" in d:
            three_y_available = any(str(w.get("label")) == "3Y" and str(w.get("status")) == "OK" for w in d.get("windows") or [] if isinstance(w, dict))
        if "sample_quality" in d:
            sq = d.get("sample_quality") or {}
            if sq.get("three_year_window_available") is not None:
                three_y_available = bool(sq.get("three_year_window_available"))
    min_sample = min(samples) if samples else None
    flags = []
    if min_sample is None:
        flags.append("missing_sample_metadata")
    elif min_sample < 252:
        flags.append("sample_under_1y")
    if three_y_available is False:
        flags.append("three_year_window_unavailable")
    return {"min_observed_sample": min_sample, "three_year_window_available": three_y_available, "flags": flags}


def extract_execution_violations(files: Dict[str, Dict[str, Any]]) -> List[str]:
    violations = []
    def scan(obj: Any, path: str, limit: int = 3000) -> None:
        if len(violations) > 50:
            return
        if isinstance(obj, dict):
            if obj.get("execution_permission") is True:
                violations.append(f"{path}.execution_permission_true")
            for k, v in list(obj.items())[:limit]:
                scan(v, f"{path}.{k}", limit)
        elif isinstance(obj, list):
            for i, v in enumerate(obj[:limit]):
                scan(v, f"{path}[{i}]", limit)
    for name, d in files.items():
        scan(d, name)
    return violations


def governance_flags(files: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    flags = []
    sq = sample_quality(files)
    for f in sq.get("flags", []):
        flags.append({"severity": "warning", "code": f, "message": "樣本品質限制：" + f})
    v32 = files.get("expected_return_model_latest.json", {})
    pol = v32.get("model_policy") or {}
    if pol.get("absolute_expected_return_forecast_enabled") is not False:
        flags.append({"severity": "critical", "code": "absolute_er_forecast_enabled", "message": "Expected return forecast should remain disabled until alpha model is validated."})
    if pol.get("maximum_sharpe_optimization_enabled") is not False:
        flags.append({"severity": "critical", "code": "max_sharpe_enabled", "message": "Maximum Sharpe must remain disabled without reliable alpha model."})
    v33 = files.get("walk_forward_backtest_latest.json", {})
    if v33.get("status") == "PROXY_ONLY":
        flags.append({"severity": "warning", "code": "walk_forward_proxy_only", "message": "Walk-forward backtest is proxy-only; do not promote optimizer based on it."})
    fold_count = ((v33.get("summary") or {}).get("fold_count") or 0)
    if fold_count < 6:
        flags.append({"severity": "warning", "code": "walk_forward_low_fold_count", "message": f"Walk-forward fold count too low: {fold_count}."})
    violations = extract_execution_violations(files)
    if violations:
        flags.append({"severity": "critical", "code": "execution_permission_true", "message": "Some sandbox output has execution_permission=true.", "examples": violations[:5]})
    v31 = files.get("black_litterman_sandbox_latest.json", {})
    if (v31.get("view_engine") or {}).get("status") not in {"rules_based_stable", "rules_based"}:
        flags.append({"severity": "warning", "code": "bl_view_engine_not_confirmed", "message": "Black-Litterman view engine is not clearly rules-based stable."})
    # High turnover risk from v2.3/v3.0
    high_turnover = 0
    for key in ["constraint_aware_rebalance_latest.json", "regime_aware_optimizer_latest.json"]:
        d = files.get(key, {})
        rows = d.get("constraint_aware_drafts") or d.get("regime_aware_drafts") or d.get("drafts") or []
        for r in rows if isinstance(rows, list) else []:
            t = finite(r.get("turnover_vs_current_pct"), 0.0) or 0.0
            if t >= 30:
                high_turnover += 1
    if high_turnover:
        flags.append({"severity": "warning", "code": "high_turnover_drafts", "message": f"High-turnover drafts detected: {high_turnover}."})
    return flags


def model_rows(files: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for version, name, fname in REGISTRY:
        d = files.get(fname, {})
        exists = bool(d)
        status = d.get("status") if exists else "MISSING"
        warnings = d.get("warnings") if isinstance(d.get("warnings"), list) else []
        generated_at = d.get("generated_at") or d.get("timestamp_utc")
        safe = d.get("safe_mode") is True or fname == "riskfolio_dependency_status.json"
        rows.append({
            "version": version,
            "name": name,
            "file": f"data/optimizer/{fname}",
            "exists": exists,
            "status": status,
            "generated_at": generated_at,
            "safe_mode": safe,
            "warning_count": len(warnings),
            "governance_status": "ok" if exists and str(status).upper() in {"OK", "PROXY_ONLY"} and safe else "review_required",
        })
    return rows


def build() -> Dict[str, Any]:
    files = {fname: load_json(OUT_DIR / fname) for _, _, fname in REGISTRY}
    rows = model_rows(files)
    flags = governance_flags(files)
    critical = [f for f in flags if f.get("severity") == "critical"]
    warnings = [f for f in flags if f.get("severity") == "warning"]
    missing = [r for r in rows if not r["exists"]]
    review = [r for r in rows if r["governance_status"] != "ok"]
    score = 100 - 25 * len(critical) - 8 * len(warnings) - 5 * len(missing)
    score = max(0, min(100, score))
    if critical:
        verdict = "blocked"
    elif warnings or missing:
        verdict = "watch_only_with_governance_warnings"
    else:
        verdict = "governance_ok_watch_only"
    failure_conditions = [
        "Any execution_permission=true in sandbox outputs.",
        "Expected return absolute forecast or maximum Sharpe optimization becomes enabled before validation.",
        "Walk-forward backtest is proxy-only or fold count remains too low.",
        "3Y robustness window unavailable while model is promoted beyond watch-only.",
        "Black-Litterman view engine accepts arbitrary subjective views.",
        "High-turnover drafts are promoted without explicit manual approval.",
    ]
    return {
        "version": VERSION,
        "status": "OK",
        "generated_at": now_utc(),
        "mode": "model_governance_dashboard",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "model_registry": rows,
        "sample_quality": sample_quality(files),
        "governance_flags": flags,
        "failure_conditions": failure_conditions,
        "summary": {
            "model_count": len(rows),
            "missing_model_count": len(missing),
            "review_required_count": len(review),
            "critical_flag_count": len(critical),
            "warning_flag_count": len(warnings),
            "governance_score": score,
            "verdict": verdict,
        },
        "execution_permission": False,
        "not_trade_order": True,
        "requires_manual_approval": True,
    }


def write_md(result: Dict[str, Any]) -> str:
    s = result.get("summary", {})
    lines = [
        "# Model Governance Dashboard v3.4",
        "",
        f"Generated: `{result.get('generated_at')}`",
        "",
        "## Safety boundary",
        "",
        "- 追蹤模型版本、失效條件、樣本品質、過度最佳化風險。",
        "- 不是交易指令；不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。",
        "",
        "## Summary",
        "",
        f"- Governance score: `{s.get('governance_score')}`",
        f"- Verdict: `{s.get('verdict')}`",
        f"- Critical flags: `{s.get('critical_flag_count')}`",
        f"- Warning flags: `{s.get('warning_flag_count')}`",
        f"- Missing models: `{s.get('missing_model_count')}`",
        "",
        "## Model registry",
        "",
        "| Version | Model | Exists | Status | Safe mode | Governance |",
        "|---|---|---:|---|---:|---|",
    ]
    for r in result.get("model_registry", []):
        lines.append(f"| `{r.get('version')}` | {r.get('name')} | {r.get('exists')} | `{r.get('status')}` | {r.get('safe_mode')} | `{r.get('governance_status')}` |")
    lines += ["", "## Governance flags", ""]
    flags = result.get("governance_flags", [])
    if not flags:
        lines.append("None.")
    for f in flags:
        lines.append(f"- `{f.get('severity')}` / `{f.get('code')}` — {f.get('message')}")
    lines += ["", "## Failure conditions", ""]
    for f in result.get("failure_conditions", []):
        lines.append(f"- {f}")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = build()
    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(write_md(result), encoding="utf-8")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Governance score: {result['summary']['governance_score']}")
    print(f"Verdict: {result['summary']['verdict']}")


if __name__ == "__main__":
    main()
