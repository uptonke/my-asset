#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "human_confirmed_trade_ticket_latest.json"
SUMMARY_MD = OUT_DIR / "human_confirmed_trade_ticket_summary.md"


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


def add_blocker(rows: List[Dict[str, Any]], code: str, message: str, severity: str = "blocker") -> None:
    if any(row.get("code") == code for row in rows):
        return
    rows.append({"code": code, "severity": severity, "message": message})


def main() -> None:
    config = as_dict(read_json("config/manual_approval_override.json", {}))
    manual_ticket = as_dict(read_json("data/alpha/manual_trade_ticket_latest.json", {}))
    diagnostics = as_dict(read_json("data/alpha/trade_sizing_diagnostics_latest.json", {}))
    explainability = as_dict(read_json("data/alpha/trade_ticket_explainability_latest.json", {}))
    approval_console = as_dict(read_json("data/alpha/manual_approval_console_latest.json", {}))
    formal_gate = as_dict(read_json("data/alpha/formal_rebalance_draft_gate_latest.json", {}))
    sizing = as_dict(read_json("data/alpha/trading_constraints_snapshot_latest.json", {}))

    manual_ticket_summary = as_dict(manual_ticket.get("summary"))
    diagnostics_summary = as_dict(diagnostics.get("summary"))
    approval_summary = as_dict(approval_console.get("summary"))
    formal_summary = as_dict(formal_gate.get("summary"))
    sizing_summary = as_dict(sizing.get("summary"))
    ticket_rows = as_list(manual_ticket.get("ticket_rows"))
    diagnostic_issues = [as_dict(x) for x in as_list(diagnostics.get("issues"))]
    explanation_rows = as_list(explainability.get("explanation_rows"))

    human_confirmation_enabled = bool(config.get("human_final_confirmation_enabled", False))
    confirmed_ticket_ids = [str(x) for x in as_list(config.get("human_confirmed_ticket_ids"))]
    confirmed_candidate_ids = [str(x) for x in as_list(config.get("human_confirmed_candidate_ids"))]
    confirmation_note = str(config.get("human_confirmation_note") or "")

    blockers: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    if not ticket_rows:
        add_blocker(blockers, "no_manual_trade_ticket_rows", "v9.0 尚未產生人工交易票據草案，因此 v10.0 不能建立人工確認票據。")
    if str(manual_ticket_summary.get("ticket_status") or manual_ticket.get("ticket_status") or "") != "manual_trade_ticket_review_draft_available":
        add_blocker(blockers, "manual_trade_ticket_not_available", "v9.0 人工交易票據草案尚未可用。")
    if not human_confirmation_enabled:
        add_blocker(blockers, "human_final_confirmation_disabled", "config/manual_approval_override.json 尚未啟用 human_final_confirmation_enabled。")
    if not confirmed_ticket_ids and not confirmed_candidate_ids:
        add_blocker(blockers, "missing_human_confirmed_ids", "缺少 human_confirmed_ticket_ids 或 human_confirmed_candidate_ids；v10.0 不會猜測要確認哪張票據。")
    if diagnostics_summary.get("diagnostic_status") in {"blocked", "error"}:
        add_blocker(blockers, "trade_sizing_diagnostics_blocked", "v9.3 阻擋原因與交易 sizing 診斷仍為 blocked。")
    for issue in diagnostic_issues:
        if issue.get("severity") == "blocker":
            add_blocker(blockers, f"diagnostic_{issue.get('code') or 'blocker'}", str(issue.get("message") or issue.get("code") or "v9.3 blocker"))
    if approval_summary.get("manual_override_enabled") is not True:
        add_blocker(blockers, "manual_override_disabled", "v9.4 人工審閱控制台顯示 manual_override_enabled=false。")
    if sizing_summary.get("cash_balance_available") is not True:
        add_blocker(blockers, "cash_balance_missing", "缺少現金餘額；不能確認任何人工交易票據。")
    if sizing_summary.get("all_prices_real_world") is not True:
        add_blocker(blockers, "not_all_prices_real_world", "仍有價格不是 real-world fetch 成功，不應進入人工確認票據。")

    selected_rows: List[Dict[str, Any]] = []
    for row0 in ticket_rows:
        row = as_dict(row0)
        ticket_id = str(row.get("ticket_id") or "")
        source_candidate_id = str(row.get("source_candidate_id") or row.get("source_formal_draft_id") or "")
        if ticket_id in confirmed_ticket_ids or source_candidate_id in confirmed_candidate_ids:
            selected_rows.append(row)

    if ticket_rows and (confirmed_ticket_ids or confirmed_candidate_ids) and not selected_rows:
        add_blocker(blockers, "confirmed_ids_not_found", "人工確認的 ticket_id / candidate_id 在 v9.0 ticket_rows 中找不到。")

    confirmed_rows: List[Dict[str, Any]] = []
    if not blockers:
        for row in selected_rows:
            confirmed_rows.append({
                "human_ticket_id": f"v10_human_confirmed_{row.get('ticket_id')}",
                "source_ticket_id": row.get("ticket_id"),
                "source_formal_draft_id": row.get("source_formal_draft_id"),
                "ticket_status": "human_confirmed_manual_entry_ticket",
                "manual_entry_only": True,
                "requires_human_final_confirmation": True,
                "human_final_confirmation_enabled": human_confirmation_enabled,
                "confirmation_note": confirmation_note,
                "estimated_orders": as_list(row.get("estimated_orders")),
                "proposed_weight_changes": row.get("proposed_weight_changes") or [],
                "target_weights": row.get("target_weights") or {},
                "cash_balance_twd": row.get("cash_balance_twd"),
                "pre_trade_checklist": as_list(row.get("pre_trade_checklist")),
                "explainability_summary": [as_dict(x).get("plain_language_summary") for x in explanation_rows[:3] if as_dict(x).get("plain_language_summary")],
                "not_trade_order": True,
                "trade_signal_enabled": False,
                "execution_permission": False,
                "broker_submission_enabled": False,
                "official_rebalance_enabled": False,
            })

    if confirmed_rows:
        ticket_status = "human_confirmed_manual_entry_ticket_available"
    elif blockers:
        ticket_status = "blocked"
    else:
        ticket_status = "no_selected_ticket_rows"

    output = {
        "version": "v10.0",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "human_confirmed_trade_ticket",
        "safe_mode": True,
        "review_only": True,
        "manual_entry_only": True,
        "human_confirmed_trade_ticket_enabled": True,
        "human_confirmed_ticket_status": ticket_status,
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
            "human_confirmed_ticket_status": ticket_status,
            "source_manual_ticket_count": len(ticket_rows),
            "selected_ticket_count": len(selected_rows),
            "confirmed_ticket_count": len(confirmed_rows),
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
            "human_final_confirmation_enabled": human_confirmation_enabled,
            "confirmed_ticket_id_count": len(confirmed_ticket_ids),
            "confirmed_candidate_id_count": len(confirmed_candidate_ids),
            "manual_override_enabled": approval_summary.get("manual_override_enabled", False),
            "diagnostic_status": diagnostics_summary.get("diagnostic_status"),
            "formal_gate_status": formal_summary.get("formal_draft_gate_status"),
            "cash_balance_available": sizing_summary.get("cash_balance_available", False),
            "all_prices_real_world": sizing_summary.get("all_prices_real_world", False),
            "trade_signal_enabled": False,
            "execution_permission": False,
            "broker_submission_enabled": False,
        },
        "confirmed_ticket_rows": confirmed_rows,
        "blockers": blockers,
        "warnings": warnings,
        "human_confirmation_input_snapshot": {
            "manual_override_config": "config/manual_approval_override.json",
            "human_final_confirmation_enabled": human_confirmation_enabled,
            "human_confirmed_ticket_ids": confirmed_ticket_ids,
            "human_confirmed_candidate_ids": confirmed_candidate_ids,
            "confirmation_note_present": bool(confirmation_note),
        },
        "source_status": {
            "manual_trade_ticket_status": manual_ticket_summary.get("ticket_status") or manual_ticket.get("ticket_status"),
            "trade_sizing_diagnostic_status": diagnostics_summary.get("diagnostic_status"),
            "manual_approval_console_status": approval_summary.get("console_status") or approval_console.get("console_status"),
            "formal_rebalance_gate_status": formal_summary.get("formal_draft_gate_status") or formal_gate.get("formal_draft_gate_status"),
        },
        "safety_boundary": [
            "v10.0 is a human-confirmed manual-entry ticket layer, not broker submission.",
            "It cannot enable trade_signal_enabled, execution_permission, official_rebalance_enabled, or broker_submission_enabled.",
            "If any upstream gate, sizing rule, cash balance, price source, or human confirmation input is missing, v10.0 outputs zero confirmed tickets.",
        ],
    }

    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v10.0 Human-Confirmed Trade Ticket",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Human confirmed ticket status: **{ticket_status}**",
        f"- Source manual ticket count: `{len(ticket_rows)}`",
        f"- Confirmed ticket count: `{len(confirmed_rows)}`",
        f"- Blockers: `{len(blockers)}`",
        f"- Trade signal enabled: `{output['trade_signal_enabled']}`",
        f"- Execution permission: `{output['execution_permission']}`",
        f"- Broker submission enabled: `{output['broker_submission_enabled']}`",
        "",
        "## Boundary",
        "- v10.0 is not a broker order, not automatic execution, and not buy/sell advice.",
        "- It only prepares a human-confirmed, manual-entry review ticket when all gates pass.",
    ]) + "\n", encoding="utf-8")

    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Human confirmed ticket status: {ticket_status}")
    print(f"Confirmed ticket count: {len(confirmed_rows)}")
    print("Execution permission: False")


if __name__ == "__main__":
    main()
