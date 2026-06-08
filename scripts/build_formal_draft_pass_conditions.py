#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "formal_draft_pass_conditions_latest.json"
SUMMARY_MD = OUT_DIR / "formal_draft_pass_conditions_summary.md"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def read_json(rel: str, default: Any = None) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default

def num(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default

def gate(name: str, passed: bool, severity: str, actual: Any, required: Any, reason: str) -> Dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "severity": severity,
        "actual": actual,
        "required": required,
        "reason_code": reason,
    }

def main() -> None:
    validation = read_json("data/alpha/alpha_validation_gate_latest.json", {}) or {}
    ranking = read_json("data/alpha/rebalance_candidate_ranking_latest.json", {}) or {}
    manual = read_json("data/alpha/manual_rebalance_proposal_latest.json", {}) or {}
    execution = read_json("data/alpha/execution_ready_draft_latest.json", {}) or {}
    governance = read_json("data/optimizer/model_governance_dashboard_latest.json", {}) or {}
    walk = read_json("data/optimizer/walk_forward_backtest_latest.json", {}) or {}
    override = read_json("config/manual_approval_override.json", {}) or {}

    validation_status = str((validation.get("summary") or {}).get("validation_status") or validation.get("validation_status") or "missing")
    ranking_summary = ranking.get("summary") or {}
    manual_summary = manual.get("summary") or {}
    execution_summary = execution.get("summary") or {}
    gov_summary = governance.get("summary") or {}
    walk_summary = walk.get("summary") or {}

    governance_score = num(gov_summary.get("governance_score") or governance.get("governance_score"), 0)
    governance_verdict = str(gov_summary.get("verdict") or governance.get("verdict") or "UNKNOWN")
    wf_status = str(walk_summary.get("status") or walk.get("status") or "UNKNOWN")
    wf_folds = int(num(walk_summary.get("fold_count") or walk.get("fold_count"), 0))

    override_enabled = bool(override.get("manual_override_enabled"))
    watch_override = override_enabled and bool(override.get("allow_formal_draft_when_validation_watch_only"))

    validation_pass = validation_status in {"research_validation_pass", "conditional_research_validation_pass", "conditional_pass", "pass"}
    if watch_override and validation_status == "watch_only_validation":
        validation_pass = True

    further_research = int(num(ranking_summary.get("further_research_count"), 0))
    manual_research = int(num(manual_summary.get("manual_research_proposal_count"), 0))
    execution_drafts = int(num(execution_summary.get("draft_count"), 0))

    gates = [
        gate("alpha_validation", validation_pass, "hard", validation_status, "pass_or_conditional_pass", "alpha_validation_gate_not_passed"),
        gate("governance_score", governance_score >= 90, "hard", governance_score, ">=90", "governance_score_below_threshold"),
        gate("governance_verdict", "fail" not in governance_verdict.lower(), "hard", governance_verdict, "not_fail", "governance_verdict_failed"),
        gate("rebalance_ranking", further_research > 0, "hard", further_research, ">=1 further research candidate", "no_rebalance_candidate_cleared_research_threshold"),
        gate("manual_research_proposal", manual_research > 0, "hard", manual_research, ">=1 manual research proposal", "no_manual_research_proposal"),
        gate("pre_execution_draft", execution_drafts > 0, "hard", execution_drafts, ">=1 execution-ready draft shell", "no_pre_execution_draft"),
        gate("walk_forward", wf_status == "OK" and wf_folds >= 6, "watch", {"status": wf_status, "folds": wf_folds}, "OK and >=6 folds", "walk_forward_evidence_not_enough"),
    ]
    hard_failed = [g for g in gates if g["severity"] == "hard" and not g["passed"]]
    watch_failed = [g for g in gates if g["severity"] == "watch" and not g["passed"]]

    if hard_failed:
        pass_status = "blocked"
    elif watch_failed:
        pass_status = "conditional_pass_with_watch_items"
    else:
        pass_status = "pass"

    output = {
        "version": "v8.1-pass-conditions",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "formal_draft_pass_conditions",
        "safe_mode": True,
        "research_only": True,
        "pass_status": pass_status,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "not_trade_order": True,
        "formal_draft_allowed_by_machine_gate": pass_status in {"pass", "conditional_pass_with_watch_items"},
        "manual_override": {
            "manual_override_enabled": override_enabled,
            "allow_formal_draft_when_validation_watch_only": bool(override.get("allow_formal_draft_when_validation_watch_only")),
            "approved_candidate_ids": override.get("approved_candidate_ids") or [],
            "rejected_candidate_ids": override.get("rejected_candidate_ids") or [],
            "approval_mode": override.get("approval_mode") or "research_only",
        },
        "summary": {
            "pass_status": pass_status,
            "hard_fail_count": len(hard_failed),
            "watch_fail_count": len(watch_failed),
            "alpha_validation_status": validation_status,
            "governance_score": governance_score,
            "governance_verdict": governance_verdict,
            "further_research_count": further_research,
            "manual_research_proposal_count": manual_research,
            "execution_draft_count": execution_drafts,
            "walk_forward_status": wf_status,
            "walk_forward_fold_count": wf_folds,
        },
        "gates": gates,
        "block_reasons": [g["reason_code"] for g in hard_failed],
        "watch_reasons": [g["reason_code"] for g in watch_failed],
        "safety_boundary": [
            "Pass conditions decide whether a formal review draft may be generated.",
            "They do not approve buy/sell actions and never enable execution or broker submission.",
            "Manual override can only promote review-only drafts, not trade orders.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v8.1 Formal Draft Pass Conditions",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Pass status: **{pass_status}**",
        f"- Hard fails: `{len(hard_failed)}`",
        f"- Watch items: `{len(watch_failed)}`",
        f"- Alpha validation: `{validation_status}`",
        f"- Governance: `{governance_score}` / `{governance_verdict}`",
        "",
        "## Boundary",
        "- Passing this gate only permits a review-only formal draft; it is not a trade signal.",
    ]) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Pass status: {pass_status}")
    print(f"Hard fails: {len(hard_failed)}")

if __name__ == "__main__":
    main()
