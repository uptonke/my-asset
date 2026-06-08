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
LATEST_JSON = OUT_DIR / "manual_rebalance_proposal_latest.json"
SUMMARY_MD = OUT_DIR / "manual_rebalance_proposal_summary.md"


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


def proposal_status_from(row: Dict[str, Any], validation_status: str) -> tuple[str, List[str]]:
    reasons = list(row.get("reason_codes") or [])
    status_raw = str(row.get("ranking_status") or row.get("status") or "").lower()
    turnover = num(row.get("turnover_vs_current_pct"), 0)
    score = num(row.get("ranking_score"), 0)

    if validation_status in {"blocked_by_validation_gate", "research_validation_failed"}:
        return "blocked_by_alpha_validation_gate", ["alpha_validation_gate_not_passed", *reasons]
    if "constraint" in status_raw or "violation" in status_raw:
        return "blocked_constraint", ["constraint_or_policy_block", *reasons]
    if turnover >= 30:
        return "watch_high_turnover", ["high_turnover_review_required", *reasons]
    if "exclude" in status_raw or "reject" in status_raw or "blocked" in status_raw:
        return "blocked_by_ranking", ["ranking_status_blocked", *reasons]
    if score >= 70 and validation_status == "research_validation_pass":
        return "manual_research_proposal", ["passed_machine_research_threshold", *reasons]
    return "watch_only_proposal", ["insufficient_for_manual_proposal", *reasons]


def main() -> None:
    validation = read_json("data/alpha/alpha_validation_gate_latest.json", {}) or {}
    ranking = read_json("data/alpha/rebalance_candidate_ranking_latest.json", {}) or {}
    constraint = read_json("data/optimizer/constraint_aware_rebalance_latest.json", {}) or {}

    validation_status = str((validation.get("summary") or {}).get("validation_status") or "missing_validation")
    rows = ranking.get("ranking_rows") or []
    constraint_rows = constraint.get("drafts") or constraint.get("rebalance_drafts") or []
    constraint_by_id = {}
    for d in constraint_rows if isinstance(constraint_rows, list) else []:
        cid = d.get("draft_id") or d.get("candidate_id") or d.get("id")
        if cid:
            constraint_by_id[str(cid)] = d

    proposals: List[Dict[str, Any]] = []
    for row in rows[:15]:
        rid = str(row.get("ranking_id") or row.get("candidate_id") or row.get("id") or f"candidate_{len(proposals)+1}")
        proposal_status, reason_codes = proposal_status_from(row, validation_status)
        linked = constraint_by_id.get(rid) or {}
        proposals.append({
            "proposal_id": f"v7_manual_review_{rid}",
            "source_ranking_id": rid,
            "proposal_status": proposal_status,
            "proposal_type": "manual_research_review",
            "research_priority_rank": row.get("rank"),
            "ranking_score": row.get("ranking_score"),
            "turnover_vs_current_pct": row.get("turnover_vs_current_pct"),
            "constraint_status": row.get("constraint_status") or linked.get("constraint_status") or linked.get("status"),
            "risk_reduction_score": row.get("risk_reduction_score"),
            "alpha_research_score": row.get("alpha_research_score"),
            "governance_status": row.get("governance_status"),
            "reason_codes": list(dict.fromkeys(reason_codes))[:12],
            "human_review_checklist": [
                "確認是否只是靠提高 BOXX / 現金降低風險",
                "確認換手率、稅費、滑價與最小交易單位",
                "確認是否違反加密、台股、現金或單一資產限制",
                "確認 v6 Alpha Validation Gate 狀態與樣本外證據",
                "確認此草案不代表買入、不代表看多、不代表正式調倉",
            ],
            "not_trade_order": True,
            "execution_permission": False,
            "requires_manual_review": True,
        })

    manual_count = sum(1 for p in proposals if p["proposal_status"] == "manual_research_proposal")
    watch_count = sum(1 for p in proposals if "watch" in p["proposal_status"])
    blocked_count = len(proposals) - manual_count - watch_count

    output = {
        "version": "v7.0",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "manual_rebalance_proposal",
        "safe_mode": True,
        "research_only": True,
        "manual_proposal_enabled": True,
        "official_rebalance_enabled": False,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "not_trade_order": True,
        "not_buy_signal": True,
        "not_sell_signal": True,
        "maximum_sharpe_optimization_enabled": False,
        "supabase_write_enabled": False,
        "source_files": {
            "alpha_validation_gate": "data/alpha/alpha_validation_gate_latest.json",
            "rebalance_candidate_ranking": "data/alpha/rebalance_candidate_ranking_latest.json",
            "constraint_aware_rebalance": "data/optimizer/constraint_aware_rebalance_latest.json",
        },
        "proposal_policy": {
            "purpose": "Create manual research-review proposals from ranked candidates after v6 validation.",
            "manual_proposal_is_not_trade_order": True,
            "execution_ready_draft_requires": [
                "v6 research_validation_pass",
                "proposal_status manual_research_proposal",
                "turnover and constraint review",
                "human review outside this system",
            ],
        },
        "summary": {
            "validation_status": validation_status,
            "source_candidate_count": len(rows),
            "proposal_count": len(proposals),
            "manual_research_proposal_count": manual_count,
            "watch_only_proposal_count": watch_count,
            "blocked_count": blocked_count,
            "trade_signal_enabled": False,
            "execution_permission": False,
        },
        "proposal_rows": proposals,
        "safety_boundary": [
            "v7 creates manual research proposals only; no trade order is created.",
            "A proposal does not mean buy, sell, bullish, or best allocation.",
            "execution_permission remains false and official_rebalance_enabled remains false.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# v7.0 Manual Rebalance Proposal",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Validation status: `{validation_status}`",
        f"- Proposal count: `{len(proposals)}`",
        f"- Manual research proposals: `{manual_count}`",
        f"- Watch-only proposals: `{watch_count}`",
        f"- Blocked: `{blocked_count}`",
        f"- Trade signal enabled: `{output['trade_signal_enabled']}`",
        "",
        "## Safety boundary",
        "- This file is a research-review queue, not a rebalance instruction.",
        "- It does not approve buy/sell or official portfolio changes.",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Proposal count: {len(proposals)}")
    print(f"Manual research proposals: {manual_count}")
    print("Trade signal enabled: False")


if __name__ == "__main__":
    main()
