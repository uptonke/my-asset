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
LATEST_JSON = OUT_DIR / "formal_rebalance_draft_gate_latest.json"
SUMMARY_MD = OUT_DIR / "formal_rebalance_draft_gate_summary.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(rel: str, default: Any = None) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
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


def unique_reasons(*lists: Any) -> List[str]:
    out: List[str] = []
    for xs in lists:
        if not isinstance(xs, list):
            continue
        for x in xs:
            s = str(x)
            if s and s not in out:
                out.append(s)
    return out


def main() -> None:
    validation = read_json("data/alpha/alpha_validation_gate_latest.json", {}) or {}
    manual = read_json("data/alpha/manual_rebalance_proposal_latest.json", {}) or {}
    execution = read_json("data/alpha/execution_ready_draft_latest.json", {}) or {}
    ranking = read_json("data/alpha/rebalance_candidate_ranking_latest.json", {}) or {}
    governance = read_json("data/optimizer/model_governance_dashboard_latest.json", {}) or {}

    validation_summary = validation.get("summary") or {}
    manual_summary = manual.get("summary") or {}
    execution_summary = execution.get("summary") or {}
    ranking_summary = ranking.get("summary") or {}
    governance_summary = governance.get("summary") or {}

    validation_status = str(validation_summary.get("validation_status") or "missing_validation")
    governance_verdict = str(governance_summary.get("verdict") or governance.get("verdict") or "UNKNOWN")
    governance_score = num(governance_summary.get("governance_score") or governance.get("governance_score"), 0)

    manual_rows = manual.get("proposal_rows") or []
    execution_rows = execution.get("draft_rows") or []
    ranking_rows = ranking.get("ranking_rows") or []

    proposal_by_id: Dict[str, Dict[str, Any]] = {}
    for p in manual_rows if isinstance(manual_rows, list) else []:
        pid = str(p.get("proposal_id") or "")
        srid = str(p.get("source_ranking_id") or "")
        if pid:
            proposal_by_id[pid] = p
        if srid:
            proposal_by_id[srid] = p

    ranking_by_id: Dict[str, Dict[str, Any]] = {}
    for r in ranking_rows if isinstance(ranking_rows, list) else []:
        rid = str(r.get("ranking_id") or r.get("candidate_id") or r.get("id") or "")
        if rid:
            ranking_by_id[rid] = r

    formal_rows: List[Dict[str, Any]] = []
    block_reasons: List[str] = []

    validation_pass = validation_status in {"research_validation_pass", "conditional_research_validation_pass", "conditional_pass"}
    if not validation_pass:
        block_reasons.append("alpha_validation_gate_not_passed")
    if governance_score < 95 or "pass" not in governance_verdict.lower():
        block_reasons.append("governance_not_full_pass")
    if int(num(ranking_summary.get("further_research_count"), 0)) <= 0:
        block_reasons.append("no_rebalance_candidate_cleared_research_threshold")
    if int(num(manual_summary.get("manual_research_proposal_count"), 0)) <= 0:
        block_reasons.append("no_manual_research_proposal")
    if int(num(execution_summary.get("draft_count"), 0)) <= 0:
        block_reasons.append("no_pre_execution_draft")

    for d in execution_rows if isinstance(execution_rows, list) else []:
        source_proposal_id = str(d.get("source_proposal_id") or "")
        source_ranking_id = str(d.get("source_ranking_id") or "")
        p = proposal_by_id.get(source_proposal_id) or proposal_by_id.get(source_ranking_id) or {}
        r = ranking_by_id.get(source_ranking_id) or {}
        local_reasons = list(block_reasons)
        draft_status = str(d.get("draft_status") or "")
        proposal_status = str(p.get("proposal_status") or "")
        turnover = num(p.get("turnover_vs_current_pct") or r.get("turnover_vs_current_pct"), 0)
        ranking_score = num(p.get("ranking_score") or r.get("ranking_score"), 0)

        if draft_status != "draftable_for_manual_entry_review":
            local_reasons.append("pre_execution_draft_not_draftable")
        if proposal_status != "manual_research_proposal":
            local_reasons.append("manual_proposal_not_promoted")
        if turnover >= 30:
            local_reasons.append("turnover_above_formal_draft_threshold")
        if ranking_score < 70:
            local_reasons.append("ranking_score_below_formal_draft_threshold")

        status = "formal_review_draft" if not local_reasons else "blocked_formal_draft"
        if status == "formal_review_draft":
            formal_rows.append({
                "formal_draft_id": f"v8_1_formal_{source_ranking_id or source_proposal_id}",
                "source_execution_draft_id": d.get("draft_id"),
                "source_proposal_id": source_proposal_id,
                "source_ranking_id": source_ranking_id,
                "formal_draft_status": status,
                "research_priority_rank": d.get("research_priority_rank") or p.get("research_priority_rank") or r.get("rank"),
                "ranking_score": ranking_score,
                "turnover_vs_current_pct": turnover,
                "alpha_validation_status": validation_status,
                "governance_verdict": governance_verdict,
                "governance_score": governance_score,
                "required_human_decision": True,
                "formal_draft_is_not_trade_order": True,
                "not_trade_order": True,
                "trade_signal_enabled": False,
                "execution_permission": False,
                "official_rebalance_enabled": False,
                "broker_submission_enabled": False,
                "reason_codes": unique_reasons(p.get("reason_codes"), r.get("reason_codes")),
                "pre_execution_checklist": d.get("pre_execution_checklist") or [],
            })

    if formal_rows:
        gate_status = "formal_rebalance_review_draft_available"
    elif validation_status == "missing_validation":
        gate_status = "blocked_missing_alpha_validation"
    elif not validation_pass:
        gate_status = "blocked_by_alpha_validation_gate"
    elif "no_manual_research_proposal" in block_reasons:
        gate_status = "blocked_no_manual_research_proposal"
    elif "no_pre_execution_draft" in block_reasons:
        gate_status = "blocked_no_pre_execution_draft"
    else:
        gate_status = "blocked_no_formal_draft"

    output = {
        "version": "v8.1",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "formal_rebalance_draft_gate",
        "safe_mode": True,
        "research_only": True,
        "formal_rebalance_draft_enabled": True,
        "formal_draft_gate_status": gate_status,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "official_rebalance_enabled": False,
        "broker_submission_enabled": False,
        "not_trade_order": True,
        "not_buy_signal": True,
        "not_sell_signal": True,
        "maximum_sharpe_optimization_enabled": False,
        "supabase_write_enabled": False,
        "source_files": {
            "alpha_validation_gate": "data/alpha/alpha_validation_gate_latest.json",
            "manual_rebalance_proposal": "data/alpha/manual_rebalance_proposal_latest.json",
            "execution_ready_draft": "data/alpha/execution_ready_draft_latest.json",
            "rebalance_candidate_ranking": "data/alpha/rebalance_candidate_ranking_latest.json",
            "model_governance_dashboard": "data/optimizer/model_governance_dashboard_latest.json",
        },
        "formal_draft_policy": {
            "purpose": "Promote only machine-vetted, governance-supported, manual-review proposals into formal rebalance review drafts.",
            "formal_draft_is_not_trade_order": True,
            "requires_manual_decision": True,
            "minimum_validation_status": "research_validation_pass_or_conditional_pass",
            "minimum_governance_score": 95,
            "maximum_turnover_pct": 30,
            "ranking_score_floor": 70,
            "must_have_pre_execution_draft": True,
        },
        "summary": {
            "formal_draft_gate_status": gate_status,
            "alpha_validation_status": validation_status,
            "governance_score": governance_score,
            "governance_verdict": governance_verdict,
            "source_execution_draft_count": len(execution_rows) if isinstance(execution_rows, list) else 0,
            "source_manual_proposal_count": len(manual_rows) if isinstance(manual_rows, list) else 0,
            "formal_draft_count": len(formal_rows),
            "trade_signal_enabled": False,
            "execution_permission": False,
            "broker_submission_enabled": False,
            "block_reasons": block_reasons,
        },
        "formal_draft_rows": formal_rows,
        "blocked_reason_codes": block_reasons,
        "safety_boundary": [
            "v8.1 may create formal rebalance review drafts only after validation/governance gates pass.",
            "A formal draft is still not a trade order, not buy/sell advice, and not an approved rebalance.",
            "execution_permission, trade_signal_enabled, official_rebalance_enabled, and broker_submission_enabled remain false.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# v8.1 Formal Rebalance Draft Gate",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Gate status: **{gate_status}**",
        f"- Formal draft count: `{len(formal_rows)}`",
        f"- Alpha validation: `{validation_status}`",
        f"- Governance: `{governance_score}` / `{governance_verdict}`",
        f"- Block reasons: `{', '.join(block_reasons) if block_reasons else 'None'}`",
        "",
        "## Safety boundary",
        "- Formal draft does not mean buy, sell, bullish, or best allocation.",
        "- No broker submission, no automatic execution, and no official rebalance is enabled.",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Formal draft gate status: {gate_status}")
    print(f"Formal draft count: {len(formal_rows)}")
    print("Execution permission: False")


if __name__ == "__main__":
    main()
