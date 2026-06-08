#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "manual_trade_ticket_latest.json"
SUMMARY_MD = OUT_DIR / "manual_trade_ticket_summary.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(rel: str, default: Any = None) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def has_weight_instructions(row: Dict[str, Any]) -> bool:
    for key in ("proposed_weight_changes", "trade_lines", "target_weights", "estimated_orders"):
        value = row.get(key)
        if isinstance(value, list) and value:
            return True
        if isinstance(value, dict) and value:
            return True
    return False


def main() -> None:
    formal = read_json("data/alpha/formal_rebalance_draft_gate_latest.json", {}) or {}
    formal_summary = formal.get("summary") or {}
    formal_rows = formal.get("formal_draft_rows") or []
    formal_gate_status = str(formal_summary.get("formal_draft_gate_status") or formal.get("formal_draft_gate_status") or "missing_formal_gate")

    ticket_rows: List[Dict[str, Any]] = []
    blocked_reasons: List[str] = []

    if formal_gate_status != "formal_rebalance_review_draft_available":
        blocked_reasons.append("formal_rebalance_draft_gate_not_available")
    if not formal_rows:
        blocked_reasons.append("no_formal_rebalance_draft_rows")

    for row in formal_rows if isinstance(formal_rows, list) else []:
        if row.get("formal_draft_status") != "formal_review_draft":
            continue
        if not has_weight_instructions(row):
            # Current upstream layers typically do not yet provide target weights/order lines.
            # Do not fabricate executable trade lines.
            continue
        ticket_rows.append({
            "ticket_id": f"v9_manual_ticket_{row.get('formal_draft_id')}",
            "source_formal_draft_id": row.get("formal_draft_id"),
            "ticket_status": "manual_ticket_draft_requires_human_entry",
            "ticket_type": "manual_trade_ticket_review_draft",
            "estimated_orders": row.get("estimated_orders") or row.get("trade_lines") or [],
            "proposed_weight_changes": row.get("proposed_weight_changes") or [],
            "target_weights": row.get("target_weights") or {},
            "risk_impact_summary": row.get("risk_impact_summary") or {},
            "turnover_vs_current_pct": row.get("turnover_vs_current_pct"),
            "pre_trade_checklist": [
                {"item": "確認實際持倉、現金、未交割款與最新市價", "required": True, "done": False},
                {"item": "確認交易單位、手續費、稅費、匯率與流動性", "required": True, "done": False},
                {"item": "確認此票據需人工重新輸入，不可自動送單", "required": True, "done": False},
                {"item": "確認沒有 broker_submission_enabled=true 或 execution_permission=true", "required": True, "done": False},
            ],
            "manual_entry_required": True,
            "requires_final_human_confirmation": True,
            "not_trade_order": True,
            "trade_signal_enabled": False,
            "execution_permission": False,
            "broker_submission_enabled": False,
            "official_rebalance_enabled": False,
        })

    if ticket_rows:
        ticket_status = "manual_trade_ticket_review_draft_available"
    elif "formal_rebalance_draft_gate_not_available" in blocked_reasons:
        ticket_status = "blocked_by_formal_rebalance_draft_gate"
    elif formal_rows:
        ticket_status = "blocked_missing_explicit_trade_lines_or_target_weights"
        blocked_reasons.append("missing_explicit_trade_lines_or_target_weights")
    else:
        ticket_status = "blocked_no_formal_rebalance_draft"

    output = {
        "version": "v9.0",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "manual_trade_ticket_generator",
        "safe_mode": True,
        "research_only": True,
        "manual_trade_ticket_generator_enabled": True,
        "ticket_status": ticket_status,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "auto_trade_enabled": False,
        "supabase_write_enabled": False,
        "not_trade_order": True,
        "not_buy_signal": True,
        "not_sell_signal": True,
        "maximum_sharpe_optimization_enabled": False,
        "source_files": {
            "formal_rebalance_draft_gate": "data/alpha/formal_rebalance_draft_gate_latest.json",
        },
        "ticket_policy": {
            "purpose": "Convert formal rebalance review drafts into manual-review ticket shells only when explicit target weights or order lines exist.",
            "system_cannot_submit_orders": True,
            "manual_entry_required": True,
            "requires_final_human_confirmation": True,
            "do_not_fabricate_order_lines": True,
            "ticket_is_not_broker_order": True,
        },
        "summary": {
            "ticket_status": ticket_status,
            "formal_gate_status": formal_gate_status,
            "source_formal_draft_count": len(formal_rows) if isinstance(formal_rows, list) else 0,
            "manual_ticket_count": len(ticket_rows),
            "trade_signal_enabled": False,
            "execution_permission": False,
            "broker_submission_enabled": False,
            "blocked_reason_codes": blocked_reasons,
        },
        "ticket_rows": ticket_rows,
        "blocked_reason_codes": blocked_reasons,
        "safety_boundary": [
            "v9.0 creates manual-review ticket shells only; it does not submit orders.",
            "No broker API, no automatic execution, no buy/sell approval, and no official rebalance is enabled.",
            "If explicit target weights or order lines are missing, v9.0 must output zero tickets rather than fabricate them.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# v9.0 Manual Trade Ticket Generator",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Ticket status: **{ticket_status}**",
        f"- Manual ticket count: `{len(ticket_rows)}`",
        f"- Broker submission enabled: `{output['broker_submission_enabled']}`",
        f"- Execution permission: `{output['execution_permission']}`",
        f"- Block reasons: `{', '.join(blocked_reasons) if blocked_reasons else 'None'}`",
        "",
        "## Safety boundary",
        "- A manual ticket is not a broker order and is not automatically executable.",
        "- Do not fabricate order lines when target weights are missing.",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Ticket status: {ticket_status}")
    print(f"Manual ticket count: {len(ticket_rows)}")
    print("Execution permission: False")


if __name__ == "__main__":
    main()
