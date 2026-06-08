#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "alpha_validation_gate_latest.json"
SUMMARY_MD = OUT_DIR / "alpha_validation_gate_summary.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(rel: str, default: Any = None) -> Any:
    p = ROOT / rel
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def bool_false(obj: Dict[str, Any], key: str) -> bool:
    return obj.get(key) is False


def status_from_gate(gates: List[Dict[str, Any]]) -> str:
    critical_fail = any(g.get("status") == "fail" and g.get("severity") == "critical" for g in gates)
    fail = any(g.get("status") == "fail" for g in gates)
    warn = any(g.get("status") == "watch" for g in gates)
    if critical_fail:
        return "blocked_by_validation_gate"
    if fail:
        return "research_validation_failed"
    if warn:
        return "watch_only_validation"
    return "research_validation_pass"


def main() -> None:
    alpha = read_json("data/alpha/alpha_research_sandbox_latest.json", {}) or {}
    ranking = read_json("data/alpha/rebalance_candidate_ranking_latest.json", {}) or {}
    walk = read_json("data/optimizer/walk_forward_backtest_latest.json", {}) or {}
    governance = read_json("data/optimizer/model_governance_dashboard_latest.json", {}) or {}
    feature = read_json("data/alpha/feature_store_latest.json", {}) or {}

    alpha_rows = alpha.get("asset_alpha_research") or []
    ranking_rows = ranking.get("ranking_rows") or []
    walk_summary = walk.get("summary") or {}
    gov_summary = governance.get("summary") or {}
    feature_summary = feature.get("summary") or {}
    ranking_summary = ranking.get("summary") or {}

    further_research_assets = [r for r in alpha_rows if str(r.get("research_disposition", "")).lower() in {"further_research", "進一步研究"} or "further" in str(r.get("research_disposition", "")).lower()]
    further_research_rankings = [r for r in ranking_rows if str(r.get("ranking_status", "")).lower() in {"further_research", "machine_pass_watchlist", "research_queue"} or "further" in str(r.get("ranking_status", "")).lower()]

    fold_count = int(num(walk_summary.get("fold_count") or walk.get("fold_count") or len(walk.get("folds") or []), 0))
    walk_status = str(walk.get("status") or walk_summary.get("status") or "UNKNOWN")
    governance_verdict = str(gov_summary.get("verdict") or governance.get("verdict") or "UNKNOWN")
    governance_score = num(gov_summary.get("governance_score") or governance.get("governance_score"), 0)
    feature_ready = int(num(feature_summary.get("feature_ready_count") or feature_summary.get("asset_count"), 0))
    asset_count = int(num(feature_summary.get("asset_count") or len(alpha_rows), 0))

    safe_flags = {
        "alpha_trade_signal_disabled": bool_false(alpha, "trade_signal_enabled"),
        "ranking_trade_signal_disabled": bool_false(ranking, "trade_signal_enabled"),
        "ranking_execution_disabled": bool_false(ranking, "execution_permission"),
        "ranking_not_trade_order": ranking.get("not_trade_order") is True,
        "ranking_official_rebalance_disabled": bool_false(ranking, "official_rebalance_enabled"),
        "ranking_max_sharpe_disabled": bool_false(ranking, "maximum_sharpe_optimization_enabled"),
    }

    gates: List[Dict[str, Any]] = []
    gates.append({
        "gate_id": "g1_feature_coverage",
        "name": "Feature coverage",
        "status": "pass" if asset_count > 0 and feature_ready == asset_count else "watch",
        "severity": "medium",
        "evidence": {"asset_count": asset_count, "feature_ready_count": feature_ready},
        "reason_codes": [] if asset_count > 0 and feature_ready == asset_count else ["feature_coverage_incomplete"],
    })
    gates.append({
        "gate_id": "g2_alpha_research_exists",
        "name": "Alpha research rows exist",
        "status": "pass" if len(alpha_rows) > 0 else "fail",
        "severity": "critical",
        "evidence": {"asset_alpha_rows": len(alpha_rows), "further_research_assets": len(further_research_assets)},
        "reason_codes": [] if alpha_rows else ["missing_alpha_research_rows"],
    })
    gates.append({
        "gate_id": "g3_rebalance_ranking_exists",
        "name": "Rebalance ranking exists",
        "status": "pass" if len(ranking_rows) > 0 else "fail",
        "severity": "critical",
        "evidence": {"ranking_rows": len(ranking_rows), "further_research_rankings": len(further_research_rankings)},
        "reason_codes": [] if ranking_rows else ["missing_rebalance_ranking_rows"],
    })
    gates.append({
        "gate_id": "g4_walk_forward_sample",
        "name": "Walk-forward validation depth",
        "status": "pass" if walk_status == "OK" and fold_count >= 10 else ("watch" if walk_status == "OK" and fold_count >= 5 else "fail"),
        "severity": "medium",
        "evidence": {"walk_forward_status": walk_status, "fold_count": fold_count},
        "reason_codes": [] if walk_status == "OK" and fold_count >= 10 else ["walk_forward_evidence_limited"],
    })
    gates.append({
        "gate_id": "g5_model_governance",
        "name": "Model governance verdict",
        "status": "pass" if governance_score >= 95 and "pass" in governance_verdict.lower() else "watch",
        "severity": "high",
        "evidence": {"governance_score": governance_score, "governance_verdict": governance_verdict},
        "reason_codes": [] if governance_score >= 95 and "pass" in governance_verdict.lower() else ["governance_not_full_pass"],
    })
    gates.append({
        "gate_id": "g6_safety_flags",
        "name": "Safety flags remain disabled",
        "status": "pass" if all(safe_flags.values()) else "fail",
        "severity": "critical",
        "evidence": safe_flags,
        "reason_codes": [] if all(safe_flags.values()) else [k for k, v in safe_flags.items() if not v],
    })
    gates.append({
        "gate_id": "g7_candidate_availability",
        "name": "Research candidate availability",
        "status": "pass" if len(further_research_rankings) > 0 else "watch",
        "severity": "low",
        "evidence": {"further_research_rankings": len(further_research_rankings), "summary_further_research": ranking_summary.get("further_research_count")},
        "reason_codes": [] if further_research_rankings else ["no_rebalance_candidate_cleared_research_threshold"],
    })

    validation_status = status_from_gate(gates)
    pass_count = sum(1 for g in gates if g.get("status") == "pass")
    watch_count = sum(1 for g in gates if g.get("status") == "watch")
    fail_count = sum(1 for g in gates if g.get("status") == "fail")

    asset_validations = []
    for row in sorted(alpha_rows, key=lambda r: num(r.get("alpha_research_score"), -999), reverse=True)[:16]:
        asset_validations.append({
            "ticker": row.get("ticker") or row.get("asset") or row.get("symbol"),
            "alpha_research_score": row.get("alpha_research_score"),
            "alpha_research_band": row.get("alpha_research_band"),
            "research_disposition": row.get("research_disposition"),
            "confidence": row.get("confidence"),
            "validation_label": "進一步研究" if row in further_research_assets else "僅供觀察",
            "not_buy_signal": True,
            "not_bullish_signal": True,
        })

    output = {
        "version": "v6.0",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "alpha_validation_gate",
        "safe_mode": True,
        "research_only": True,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "not_trade_order": True,
        "not_buy_signal": True,
        "not_sell_signal": True,
        "official_alpha_enabled": False,
        "alpha_model_enabled": False,
        "maximum_sharpe_optimization_enabled": False,
        "official_rebalance_enabled": False,
        "source_files": {
            "feature_store": "data/alpha/feature_store_latest.json",
            "alpha_research_sandbox": "data/alpha/alpha_research_sandbox_latest.json",
            "rebalance_candidate_ranking": "data/alpha/rebalance_candidate_ranking_latest.json",
            "walk_forward_backtest": "data/optimizer/walk_forward_backtest_latest.json",
            "model_governance_dashboard": "data/optimizer/model_governance_dashboard_latest.json",
        },
        "validation_policy": {
            "purpose": "Validate whether v5 research outputs are mature enough to create manual review proposals.",
            "pass_is_not_trade_signal": True,
            "pass_is_not_buy_signal": True,
            "pass_is_not_bullish_signal": True,
            "manual_review_required_after_pass": True,
            "required_before_v7_manual_proposal": "research_validation_pass or watch_only_validation with explicit blocked/watch-only labels",
        },
        "summary": {
            "validation_status": validation_status,
            "gate_count": len(gates),
            "pass_count": pass_count,
            "watch_count": watch_count,
            "fail_count": fail_count,
            "asset_alpha_rows": len(alpha_rows),
            "ranking_rows": len(ranking_rows),
            "further_research_assets": len(further_research_assets),
            "further_research_rankings": len(further_research_rankings),
            "walk_forward_fold_count": fold_count,
            "governance_score": governance_score,
            "governance_verdict": governance_verdict,
        },
        "gates": gates,
        "asset_validations": asset_validations,
        "safety_boundary": [
            "v6 validates alpha research evidence only; it does not approve trades.",
            "Passing v6 does not mean buy, sell, bullish, or best allocation.",
            "execution_permission remains false and not_trade_order remains true.",
        ],
    }

    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# v6.0 Alpha Validation Gate",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Validation status: **{validation_status}**",
        f"- Gates: `{pass_count}` pass / `{watch_count}` watch / `{fail_count}` fail",
        f"- Further research rankings: `{len(further_research_rankings)}`",
        f"- Trade signal enabled: `{output['trade_signal_enabled']}`",
        "",
        "## Gates",
    ]
    for g in gates:
        lines.append(f"- `{g['gate_id']}` {g['name']}: **{g['status']}** — {', '.join(g.get('reason_codes') or ['ok'])}")
    lines += [
        "",
        "## Safety boundary",
        "- v6 pass/watch labels are validation labels only, not trade instructions.",
        "- This output does not approve buy/sell, max Sharpe, or official rebalance.",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Validation status: {validation_status}")
    print(f"Gates: {pass_count} pass / {watch_count} watch / {fail_count} fail")


if __name__ == "__main__":
    main()
