#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
LATEST_JSON = OUT_DIR / "rebalance_candidate_ranking_latest.json"
SUMMARY_MD = OUT_DIR / "rebalance_candidate_ranking_summary.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def finite_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def get_alpha_map(alpha: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = alpha.get("asset_alpha_research") or []
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        ticker = row.get("ticker")
        if ticker:
            out[str(ticker)] = row
    return out


def get_walk_forward_context(wf: Dict[str, Any]) -> Dict[str, Any]:
    summary = wf.get("summary") or {}
    aggregate = wf.get("aggregate_results") or []
    method_map = {str(row.get("method")): row for row in aggregate if row.get("method")}
    return {
        "status": wf.get("status"),
        "fold_count": summary.get("fold_count") or wf.get("sample", {}).get("fold_count"),
        "verdict": summary.get("verdict"),
        "likely_better_than_current": summary.get("likely_better_than_current") or [],
        "method_map": method_map,
    }


def get_governance_context(gov: Dict[str, Any]) -> Dict[str, Any]:
    summary = gov.get("summary") or {}
    flags = gov.get("governance_flags") or []
    sample_quality = gov.get("sample_quality") or {}
    critical = [f for f in flags if str(f.get("severity", "")).lower() == "critical"]
    warnings = [f for f in flags if str(f.get("severity", "")).lower() == "warning"]
    return {
        "score": finite_float(summary.get("governance_score"), 0.0) or 0.0,
        "verdict": summary.get("verdict"),
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "sample_flags": sample_quality.get("flags") or [],
        "three_year_window_available": sample_quality.get("three_year_window_available"),
    }


def collect_base_drafts(ca: Dict[str, Any]) -> List[Dict[str, Any]]:
    drafts: List[Dict[str, Any]] = []
    for source_bucket in ["constraint_aware_rebalance_drafts", "constraint_aware_risk_reduction_drafts"]:
        for row in ca.get(source_bucket) or []:
            r = dict(row)
            r["source_bucket"] = source_bucket
            drafts.append(r)
    return drafts


def build_regime_index(regime: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in regime.get("regime_aware_drafts") or []:
        source_id = row.get("source_draft_id")
        if source_id:
            out[str(source_id)] = row
    return out


def constraint_penalty_and_flags(draft: Dict[str, Any]) -> Tuple[float, List[str]]:
    flags = draft.get("constraint_flags_after_adjustment") or []
    status = str(draft.get("constraint_status") or "")
    reasons: List[str] = []
    score = 1.0
    if not flags and "pass" in status:
        reasons.append("constraint_pass")
    for flag in flags:
        level = str(flag.get("level") or "").lower()
        constraint = str(flag.get("constraint") or "constraint_flag")
        if level in {"error", "critical", "fail"}:
            score -= 4.0
            reasons.append(f"constraint_violation:{constraint}")
        elif level in {"warning", "warn"}:
            score -= 0.8
            reasons.append(f"constraint_warning:{constraint}")
        else:
            score -= 0.4
            reasons.append(f"constraint_flag:{constraint}")
    if "too_high" in status or "high_turnover" in status:
        reasons.append(status)
    if "violation" in status or "fail" in status:
        score -= 3.0
        reasons.append(status)
    return clamp(score, -5.0, 2.0), reasons


def turnover_score(turnover: float) -> Tuple[float, List[str]]:
    if turnover <= 0:
        return 0.0, ["turnover_unknown_or_zero"]
    if turnover <= 8:
        return 1.5, ["turnover_low"]
    if turnover <= 15:
        return 0.5, ["turnover_moderate"]
    if turnover <= 30:
        return -1.5, ["turnover_high_review"]
    return -4.0, ["turnover_too_high"]


def risk_reduction_score(draft: Dict[str, Any]) -> Tuple[float, List[str]]:
    raw = finite_float(draft.get("risk_reduction_score"), None)
    improvement = draft.get("risk_reduction_improvement") or {}
    reasons: List[str] = []
    if raw is not None:
        if raw > 0:
            reasons.append("risk_reduction_detected")
        return clamp(raw / 4.0, -3.0, 4.0), reasons
    # Non-risk-reduction candidates may still be useful but do not get a risk-reduction bonus.
    if improvement:
        vals = [finite_float(v, 0.0) or 0.0 for v in improvement.values()]
        avg = sum(vals) / len(vals) if vals else 0.0
        if avg > 0:
            reasons.append("risk_reduction_detected")
        return clamp(avg / 2.0, -3.0, 3.0), reasons
    reasons.append("no_explicit_risk_reduction_score")
    return 0.0, reasons


def alpha_alignment_score(draft: Dict[str, Any], alpha_map: Dict[str, Dict[str, Any]]) -> Tuple[float, List[str], List[Dict[str, Any]]]:
    weights = draft.get("weights_pct") or {}
    reasons: List[str] = []
    contributions: List[Dict[str, Any]] = []
    if not isinstance(weights, dict) or not weights or not alpha_map:
        return 0.0, ["alpha_alignment_unavailable"], contributions
    total_abs_delta = 0.0
    weighted = 0.0
    for ticker, new_w in weights.items():
        arow = alpha_map.get(str(ticker))
        if not arow:
            continue
        current_w = finite_float(arow.get("current_weight_pct"), 0.0) or 0.0
        new_weight = finite_float(new_w, current_w) or current_w
        delta = new_weight - current_w
        if abs(delta) < 0.05:
            continue
        alpha_score = finite_float(arow.get("alpha_research_score"), 0.0) or 0.0
        contribution = delta * alpha_score
        weighted += contribution
        total_abs_delta += abs(delta)
        contributions.append({
            "ticker": ticker,
            "delta_pct": round(delta, 3),
            "alpha_research_score": round(alpha_score, 3),
            "alignment_contribution": round(contribution, 3),
        })
    if total_abs_delta <= 0:
        return 0.0, ["alpha_alignment_no_material_delta"], contributions
    score = clamp(weighted / total_abs_delta, -3.0, 3.0)
    if score > 0.5:
        reasons.append("alpha_alignment_positive")
    elif score < -0.5:
        reasons.append("alpha_alignment_negative")
    else:
        reasons.append("alpha_alignment_neutral")
    contributions.sort(key=lambda r: abs(finite_float(r.get("alignment_contribution"), 0.0) or 0.0), reverse=True)
    return round(score, 3), reasons, contributions[:8]


def regime_score_for(draft: Dict[str, Any], regime_index: Dict[str, Dict[str, Any]]) -> Tuple[float, List[str], Optional[Dict[str, Any]]]:
    rd = regime_index.get(str(draft.get("draft_id")))
    if not rd:
        return 0.0, ["regime_overlay_unavailable"], None
    status = str(rd.get("model_status") or "")
    reasons = [f"regime_status:{status}"]
    if "high_turnover" in status:
        return -1.0, reasons, rd
    if "review_required" in status or "watch" in status:
        return 0.25, reasons, rd
    return 0.0, reasons, rd


def cash_disguise_penalty(draft: Dict[str, Any]) -> Tuple[float, List[str]]:
    exposure = draft.get("constraint_aware_exposure") or draft.get("exposure") or {}
    cash = finite_float(exposure.get("cash_pct"), 0.0) or 0.0
    max_single = finite_float(exposure.get("max_single_weight_pct"), 0.0) or 0.0
    max_ticker = str(exposure.get("max_single_ticker") or "")
    reasons: List[str] = []
    score = 0.0
    if cash >= 30:
        score -= 3.0
        reasons.append("cash_disguise_high_cash")
    elif cash >= 22:
        score -= 1.0
        reasons.append("cash_disguise_watch")
    if max_ticker == "BOXX" and max_single >= 25:
        score -= 1.5
        reasons.append("cash_disguise_single_cash_proxy")
    return score, reasons


def sample_governance_score(wf_ctx: Dict[str, Any], gov_ctx: Dict[str, Any]) -> Tuple[float, List[str]]:
    reasons: List[str] = []
    score = 0.0
    if gov_ctx.get("critical_count", 0) > 0:
        score -= 5.0
        reasons.append("governance_critical_flag")
    if gov_ctx.get("warning_count", 0) > 0:
        score -= 0.75
        reasons.append("governance_warning_flag")
    if gov_ctx.get("three_year_window_available") is False:
        score -= 0.5
        reasons.append("three_year_window_unavailable")
    if wf_ctx.get("status") != "OK":
        score -= 1.0
        reasons.append("walk_forward_not_ok")
    if wf_ctx.get("verdict") == "needs_more_out_of_sample_evidence":
        score -= 0.5
        reasons.append("needs_more_out_of_sample_evidence")
    return clamp(score, -5.0, 1.0), reasons


def disposition(row: Dict[str, Any]) -> str:
    reasons = row.get("reason_codes") or []
    turnover = finite_float(row.get("turnover_vs_current_pct"), 0.0) or 0.0
    score = finite_float(row.get("ranking_score"), 0.0) or 0.0
    if row.get("execution_permission") is True:
        return "blocked_governance"
    if any(str(r).startswith("constraint_violation") for r in reasons):
        return "exclude_constraint_violation"
    if turnover > 30 or "turnover_too_high" in reasons:
        return "exclude_high_turnover"
    if "governance_critical_flag" in reasons:
        return "blocked_governance"
    if "walk_forward_not_ok" in reasons:
        return "observe_sample_quality"
    if score >= 1.0:
        return "further_research"
    if score >= -1.0:
        return "observe_only"
    return "exclude_low_research_value"


def build_ranking() -> Dict[str, Any]:
    ca = load_json(ROOT / "data/optimizer/constraint_aware_rebalance_latest.json", {})
    regime = load_json(ROOT / "data/optimizer/regime_aware_optimizer_latest.json", {})
    alpha = load_json(ROOT / "data/alpha/alpha_research_sandbox_latest.json", {})
    wf = load_json(ROOT / "data/optimizer/walk_forward_backtest_latest.json", {})
    gov = load_json(ROOT / "data/optimizer/model_governance_dashboard_latest.json", {})

    alpha_map = get_alpha_map(alpha)
    wf_ctx = get_walk_forward_context(wf)
    gov_ctx = get_governance_context(gov)
    regime_index = build_regime_index(regime)
    drafts = collect_base_drafts(ca)

    rows: List[Dict[str, Any]] = []
    warnings: List[str] = []
    if not drafts:
        warnings.append("constraint_aware_rebalance_latest.json did not contain any candidate drafts.")
    if not alpha_map:
        warnings.append("alpha_research_sandbox_latest.json did not contain asset alpha research rows; alpha alignment score set to zero.")

    for draft in drafts:
        turnover = finite_float(draft.get("turnover_vs_current_pct"), 0.0) or 0.0
        c_score, c_reasons = constraint_penalty_and_flags(draft)
        t_score, t_reasons = turnover_score(turnover)
        r_score, r_reasons = risk_reduction_score(draft)
        a_score, a_reasons, a_contrib = alpha_alignment_score(draft, alpha_map)
        rg_score, rg_reasons, rg_draft = regime_score_for(draft, regime_index)
        cash_score, cash_reasons = cash_disguise_penalty(draft)
        sg_score, sg_reasons = sample_governance_score(wf_ctx, gov_ctx)

        # Bounded research ranking score. It is intentionally not an expected return estimate.
        ranking_score = (
            0.30 * r_score
            + 0.25 * a_score
            + 0.20 * c_score
            + 0.15 * t_score
            + 0.10 * rg_score
            + 0.10 * sg_score
            + cash_score
        )
        ranking_score = round(clamp(ranking_score, -10.0, 10.0), 3)
        reasons = [*c_reasons, *t_reasons, *r_reasons, *a_reasons, *rg_reasons, *cash_reasons, *sg_reasons]
        # Deduplicate while preserving order.
        seen = set()
        reasons = [x for x in reasons if not (x in seen or seen.add(x))]
        row = {
            "ranking_id": f"v5_2_{draft.get('draft_id')}",
            "source_draft_id": draft.get("draft_id"),
            "source": draft.get("source"),
            "source_bucket": draft.get("source_bucket"),
            "constraint_status": draft.get("constraint_status"),
            "execution_permission": False,
            "not_trade_order": True,
            "not_buy_signal": True,
            "not_sell_signal": True,
            "requires_manual_review": True,
            "research_only": True,
            "turnover_vs_current_pct": round(turnover, 3),
            "risk_reduction_score": draft.get("risk_reduction_score"),
            "ranking_score": ranking_score,
            "ranking_status": None,
            "score_components": {
                "risk_reduction_component": round(r_score, 3),
                "alpha_alignment_component": round(a_score, 3),
                "constraint_component": round(c_score, 3),
                "turnover_component": round(t_score, 3),
                "regime_component": round(rg_score, 3),
                "sample_governance_component": round(sg_score, 3),
                "cash_disguise_penalty": round(cash_score, 3),
            },
            "alpha_alignment_top_contributors": a_contrib,
            "regime_overlay_status": (rg_draft or {}).get("model_status"),
            "constraint_aware_exposure": draft.get("constraint_aware_exposure") or draft.get("exposure"),
            "top_adjustments": draft.get("top_constraint_aware_adjustments") or draft.get("top_regime_adjustments") or [],
            "weights_pct": draft.get("weights_pct") or {},
            "reason_codes": reasons,
        }
        row["ranking_status"] = disposition(row)
        rows.append(row)

    rows.sort(key=lambda r: finite_float(r.get("ranking_score"), 0.0) or 0.0, reverse=True)
    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx

    counts: Dict[str, int] = {}
    for row in rows:
        counts[row["ranking_status"]] = counts.get(row["ranking_status"], 0) + 1

    result = {
        "version": "v5.2",
        "status": "OK" if rows else "NO_CANDIDATES",
        "generated_at": now_iso(),
        "mode": "rebalance_candidate_ranking_engine",
        "safe_mode": True,
        "safe_mode_note": "v5.2 只做調倉研究候選排序；不輸出買賣訊號、不選最佳配置、不做最大夏普、不自動調倉、不寫 Supabase。",
        "research_only": True,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "not_trade_order": True,
        "not_buy_signal": True,
        "not_sell_signal": True,
        "alpha_model_enabled": False,
        "official_alpha_enabled": False,
        "maximum_sharpe_optimization_enabled": False,
        "official_rebalance_enabled": False,
        "source_files": {
            "constraint_aware_rebalance": "data/optimizer/constraint_aware_rebalance_latest.json",
            "regime_aware_optimizer": "data/optimizer/regime_aware_optimizer_latest.json",
            "alpha_research_sandbox": "data/alpha/alpha_research_sandbox_latest.json",
            "walk_forward_backtest": "data/optimizer/walk_forward_backtest_latest.json",
            "model_governance_dashboard": "data/optimizer/model_governance_dashboard_latest.json",
        },
        "ranking_policy": {
            "allowed_use": "research_candidate_ranking_only",
            "disallowed_use": ["BUY_SELL", "best_allocation", "auto_trade", "official_weight_update", "supabase_write", "maximum_sharpe_rebalance"],
            "score_components": ["risk_reduction", "alpha_alignment", "constraints", "turnover", "regime_overlay", "sample_governance", "cash_disguise_penalty"],
            "interpretation": "進一步研究只代表值得研究，不代表值得買入、不代表看多、不代表正式調倉。",
        },
        "context": {
            "walk_forward": {k: v for k, v in wf_ctx.items() if k != "method_map"},
            "governance": gov_ctx,
        },
        "ranking_rows": rows,
        "summary": {
            "candidate_count": len(rows),
            "status_counts": counts,
            "further_research_count": counts.get("further_research", 0),
            "observe_only_count": counts.get("observe_only", 0) + counts.get("observe_sample_quality", 0),
            "excluded_count": sum(v for k, v in counts.items() if k.startswith("exclude") or k.startswith("blocked")),
            "top_ranked_candidates": [r.get("ranking_id") for r in rows[:5]],
            "top_further_research": [r.get("ranking_id") for r in rows if r.get("ranking_status") == "further_research"][:5],
            "research_boundary": "調倉研究候選排序不是買入建議、不是賣出建議、不是最佳配置，也不是交易指令。",
        },
        "warnings": warnings,
    }
    return result


def write_summary(result: Dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    counts = result.get("summary", {}).get("status_counts") or {}
    lines = [
        "# v5.2 Rebalance Candidate Ranking",
        "",
        f"- Status: **{result.get('status')}**",
        f"- Generated at: `{result.get('generated_at')}`",
        f"- Candidate count: `{result.get('summary', {}).get('candidate_count')}`",
        f"- Further research count: `{result.get('summary', {}).get('further_research_count')}`",
        f"- Observe-only count: `{result.get('summary', {}).get('observe_only_count')}`",
        f"- Excluded count: `{result.get('summary', {}).get('excluded_count')}`",
        "",
        "## Status counts",
    ]
    if counts:
        for key, val in sorted(counts.items()):
            lines.append(f"- `{key}`: `{val}`")
    else:
        lines.append("- None")
    lines += ["", "## Top ranked candidates"]
    for row in (result.get("ranking_rows") or [])[:10]:
        lines.append(f"- Rank {row.get('rank')}: `{row.get('ranking_id')}` — `{row.get('ranking_status')}` — score `{row.get('ranking_score')}`")
    if not result.get("ranking_rows"):
        lines.append("- None")
    lines += [
        "",
        "## Safety boundary",
        "- Research candidate ranking only.",
        "- Not a BUY / SELL signal.",
        "- Not a best-allocation recommendation.",
        "- Official alpha and maximum Sharpe remain disabled.",
        "- No auto-trading and no Supabase write.",
    ]
    if result.get("warnings"):
        lines += ["", "## Warnings"]
        for w in result.get("warnings", []):
            lines.append(f"- {w}")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_ranking()
    LATEST_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(result)
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Candidate count: {result.get('summary', {}).get('candidate_count')}")
    print(f"Further research: {result.get('summary', {}).get('further_research_count')}")
    print("Trade signal enabled: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
