#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "manual_approval_console_latest.json"
SUMMARY_MD = OUT_DIR / "manual_approval_console_summary.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(rel: str, default: Any = None) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def num(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def status_label(enabled: bool, missing: List[str], hard_blocked: bool) -> str:
    if hard_blocked:
        return "blocked_by_upstream_gates"
    if missing:
        return "incomplete_manual_inputs"
    if enabled:
        return "manual_review_console_active"
    return "manual_review_console_disabled"


def main() -> None:
    override = as_dict(read_json("config/manual_approval_override.json", {}))
    manual_input = as_dict(read_json("data/alpha/manual_approval_input_latest.json", {}))
    formal_conditions = as_dict(read_json("data/alpha/formal_draft_pass_conditions_latest.json", {}))
    formal_gate = as_dict(read_json("data/alpha/formal_rebalance_draft_gate_latest.json", {}))
    manual_ticket = as_dict(read_json("data/alpha/manual_trade_ticket_latest.json", {}))
    sizing = as_dict(read_json("data/alpha/trading_constraints_snapshot_latest.json", {}))
    diagnostics = as_dict(read_json("data/alpha/trade_sizing_diagnostics_latest.json", {}))
    ranking = as_dict(read_json("data/alpha/rebalance_candidate_ranking_latest.json", {}))

    override_enabled = bool(override.get("manual_override_enabled"))
    approved_ids = [str(x) for x in as_list(override.get("approved_candidate_ids"))]
    rejected_ids = [str(x) for x in as_list(override.get("rejected_candidate_ids"))]
    cash_balance_twd = override.get("cash_balance_twd")
    max_trade_budget_twd = override.get("max_trade_budget_twd")
    approval_mode = str(override.get("approval_mode") or "research_only")

    missing_inputs: List[Dict[str, Any]] = []
    if cash_balance_twd is None:
        missing_inputs.append({"field": "cash_balance_twd", "severity": "blocker", "message": "缺少現金餘額；無法做交易 sizing。"})
    if max_trade_budget_twd is None:
        missing_inputs.append({"field": "max_trade_budget_twd", "severity": "blocker", "message": "缺少最大可交易金額；無法限制票據規模。"})
    if override_enabled and not approved_ids:
        missing_inputs.append({"field": "approved_candidate_ids", "severity": "watch", "message": "已啟用人工 override，但沒有指定已批准候選。"})

    formal_summary = as_dict(formal_conditions.get("summary"))
    hard_fails = int(num(formal_summary.get("hard_fail_count"), len(as_list(formal_conditions.get("block_reasons")))))
    pass_status = str(formal_conditions.get("pass_status") or formal_summary.get("pass_status") or "missing")
    hard_blocked = hard_fails > 0 or pass_status not in {"pass", "conditional_pass", "manual_review_allowed"}

    ranking_rows = as_list(ranking.get("ranking_rows"))
    ranking_by_id = {str(as_dict(r).get("ranking_id") or as_dict(r).get("candidate_id") or as_dict(r).get("source_candidate_id") or ""): as_dict(r) for r in ranking_rows}
    approved_candidates = []
    for cid in approved_ids:
        r = ranking_by_id.get(cid, {})
        approved_candidates.append({
            "candidate_id": cid,
            "exists_in_latest_ranking": bool(r),
            "ranking_score": r.get("ranking_score"),
            "research_disposition": r.get("research_disposition"),
            "manual_status": "approved_for_review_only",
        })
    rejected_candidates = []
    for cid in rejected_ids:
        r = ranking_by_id.get(cid, {})
        rejected_candidates.append({
            "candidate_id": cid,
            "exists_in_latest_ranking": bool(r),
            "manual_status": "rejected_by_user_input",
        })

    console_status = status_label(override_enabled, missing_inputs, hard_blocked)
    if override_enabled and approval_mode not in {"research_only", "paper_tracking_only", "formal_review_only"}:
        missing_inputs.append({"field": "approval_mode", "severity": "blocker", "message": "approval_mode 只能是 research_only / paper_tracking_only / formal_review_only。"})
        console_status = "invalid_manual_approval_mode"

    permissions = {
        "can_promote_to_formal_review_draft": bool(override_enabled and not hard_blocked and cash_balance_twd is not None and max_trade_budget_twd is not None),
        "can_generate_manual_trade_ticket_shell": False,
        "can_submit_broker_order": False,
        "can_auto_execute": False,
        "can_enable_trade_signal": False,
    }

    actions = [
        {"action": "補 cash_balance_twd", "required": cash_balance_twd is None, "purpose": "讓 sizing 層知道可用現金；不代表允許交易。"},
        {"action": "補 max_trade_budget_twd", "required": max_trade_budget_twd is None, "purpose": "限制任一票據的最大名目金額。"},
        {"action": "若要研究正式草案，填 approved_candidate_ids", "required": bool(override_enabled and not approved_ids), "purpose": "只允許被指定的候選進入人工研究流程。"},
        {"action": "維持 manual_override_enabled=false 直到 v6/v8 gate 改善", "required": hard_blocked, "purpose": "避免用人工 override 繞過 alpha / governance gate。"},
    ]

    output = {
        "version": "v9.4",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "manual_approval_console",
        "safe_mode": True,
        "research_only": True,
        "console_status": console_status,
        "manual_override_enabled": override_enabled,
        "approval_mode": approval_mode,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "auto_trade_enabled": False,
        "supabase_write_enabled": False,
        "not_trade_order": True,
        "not_buy_signal": True,
        "not_sell_signal": True,
        "summary": {
            "console_status": console_status,
            "manual_override_enabled": override_enabled,
            "approval_mode": approval_mode,
            "approved_candidate_count": len(approved_ids),
            "rejected_candidate_count": len(rejected_ids),
            "missing_input_count": len(missing_inputs),
            "cash_balance_twd": cash_balance_twd,
            "max_trade_budget_twd": max_trade_budget_twd,
            "formal_pass_status": pass_status,
            "formal_hard_fail_count": hard_fails,
            "formal_draft_count": as_dict(formal_gate.get("summary")).get("formal_draft_count", 0),
            "manual_ticket_count": as_dict(manual_ticket.get("summary")).get("manual_ticket_count", 0),
        },
        "manual_input_snapshot": {
            "override_version": override.get("version"),
            "manual_override_enabled": override_enabled,
            "approval_mode": approval_mode,
            "allow_formal_draft_when_validation_watch_only": bool(override.get("allow_formal_draft_when_validation_watch_only")),
            "cash_balance_twd": cash_balance_twd,
            "max_trade_budget_twd": max_trade_budget_twd,
            "notes": override.get("notes"),
        },
        "approved_candidates": approved_candidates,
        "rejected_candidates": rejected_candidates,
        "missing_inputs": missing_inputs,
        "permissions": permissions,
        "recommended_actions": actions,
        "source_files": {
            "manual_override_config": "config/manual_approval_override.json",
            "manual_approval_input": "data/alpha/manual_approval_input_latest.json",
            "formal_pass_conditions": "data/alpha/formal_draft_pass_conditions_latest.json",
            "trade_sizing_diagnostics": "data/alpha/trade_sizing_diagnostics_latest.json",
        },
        "safety_boundary": [
            "v9.4 is a manual review console, not an order approval console.",
            "Manual override may only affect review-only draft promotion and cannot enable broker submission or auto execution.",
            "trade_signal_enabled, execution_permission, broker_submission_enabled, and official_rebalance_enabled must remain false.",
        ],
    }

    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v9.4 Manual Approval Console",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Console status: **{console_status}**",
        f"- Manual override enabled: `{override_enabled}`",
        f"- Missing inputs: `{len(missing_inputs)}`",
        f"- Approved candidates: `{len(approved_ids)}`",
        f"- Trade signal enabled: `{output['trade_signal_enabled']}`",
        "",
        "## Boundary",
        "- This console does not approve trades, does not submit broker orders, and does not enable execution.",
    ]) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Console status: {console_status}")
    print(f"Missing inputs: {len(missing_inputs)}")
    print(f"Manual override enabled: {override_enabled}")


if __name__ == "__main__":
    main()
