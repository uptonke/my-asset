#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "trade_ticket_explainability_latest.json"
SUMMARY_MD = OUT_DIR / "trade_ticket_explainability_summary.md"


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


def zh_reason(code: Any) -> str:
    c = str(code or "")
    mapping = {
        "blocked_by_formal_rebalance_draft_gate": "正式再平衡草案閘門未通過，因此不能產生人工交易票據。",
        "blocked_by_formal_pass_conditions": "正式草案通過條件未滿足，因此不能進入票據層。",
        "alpha_validation_not_passed": "Alpha 驗證仍是觀察狀態，不能升級正式草案。",
        "no_further_research_candidates": "調倉排序沒有進一步研究候選。",
        "manual_override_disabled": "人工 override 未啟用；系統只能保持研究模式。",
        "missing_cash_balance": "缺少現金餘額，無法計算可交易金額。",
        "incomplete_real_world_price_fetch": "部分價格不是即時抓取，不應產生交易票據。",
        "missing_explicit_trade_lines_or_target_weights": "缺少明確交易列或目標權重，系統不得自行捏造買賣明細。",
        "missing_trade_budget": "缺少最大交易預算，無法限制票據規模。",
    }
    return mapping.get(c, c or "未提供原因")


def main() -> None:
    manual_ticket = as_dict(read_json("data/alpha/manual_trade_ticket_latest.json", {}))
    formal_gate = as_dict(read_json("data/alpha/formal_rebalance_draft_gate_latest.json", {}))
    diagnostics = as_dict(read_json("data/alpha/trade_sizing_diagnostics_latest.json", {}))
    approval_console = as_dict(read_json("data/alpha/manual_approval_console_latest.json", {}))
    performance = as_dict(read_json("data/alpha/paper_trade_performance_evaluator_latest.json", {}))
    sizing = as_dict(read_json("data/alpha/trading_constraints_snapshot_latest.json", {}))

    ticket_rows = as_list(manual_ticket.get("ticket_rows"))
    formal_rows = as_list(formal_gate.get("formal_draft_rows"))
    issues = as_list(diagnostics.get("issues"))
    ticket_summary = as_dict(manual_ticket.get("summary"))
    gate_summary = as_dict(formal_gate.get("summary"))
    approval_summary = as_dict(approval_console.get("summary"))

    explanations: List[Dict[str, Any]] = []
    if ticket_rows:
        for row0 in ticket_rows:
            row = as_dict(row0)
            explanations.append({
                "ticket_id": row.get("ticket_id"),
                "source_formal_draft_id": row.get("source_formal_draft_id"),
                "explainability_status": "ticket_shell_available_for_manual_review",
                "plain_language_summary": "此票據只是人工檢查外殼，需重新確認價格、現金、交易單位與風險理由；不是交易指令。",
                "why_generated": row.get("reason_codes") or ["formal_draft_available", "explicit_trade_lines_or_target_weights_present"],
                "why_not_executable": ["broker_submission_disabled", "execution_permission_false", "requires_final_human_confirmation"],
                "pre_trade_checklist_count": len(as_list(row.get("pre_trade_checklist"))),
            })
    else:
        blocker_codes = []
        for item in issues:
            d = as_dict(item)
            if d.get("severity") == "blocker":
                blocker_codes.append(str(d.get("code") or "unknown_blocker"))
        blocker_codes.extend(str(x) for x in as_list(manual_ticket.get("blocked_reason_codes")))
        # de-duplicate preserving order
        seen = set()
        blocker_codes = [x for x in blocker_codes if not (x in seen or seen.add(x))]
        explanations.append({
            "ticket_id": None,
            "explainability_status": "ticket_not_generated",
            "plain_language_summary": "人工交易票據未產生，因為上游正式草案、人工輸入、現金或價格條件未滿足。這是保護性阻擋。",
            "primary_blockers": [{"code": c, "message": zh_reason(c)} for c in blocker_codes[:12]],
            "why_not_executable": ["trade_signal_enabled_false", "execution_permission_false", "broker_submission_disabled", "not_trade_order_true"],
        })

    output = {
        "version": "v9.6",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "trade_ticket_explainability",
        "safe_mode": True,
        "research_only": True,
        "explainability_status": "ticket_explanations_available" if explanations else "no_explanations",
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
            "explainability_status": "ticket_explanations_available" if explanations else "no_explanations",
            "manual_ticket_count": len(ticket_rows),
            "formal_draft_count": len(formal_rows),
            "blocker_count": len([i for i in issues if as_dict(i).get("severity") == "blocker"]),
            "manual_override_enabled": approval_summary.get("manual_override_enabled", False),
            "cash_balance_available": as_dict(sizing.get("summary")).get("cash_balance_available", False),
            "performance_evaluator_status": as_dict(performance.get("summary")).get("evaluator_status"),
        },
        "explanation_rows": explanations,
        "source_status": {
            "manual_ticket_status": ticket_summary.get("ticket_status") or manual_ticket.get("ticket_status"),
            "formal_gate_status": gate_summary.get("formal_draft_gate_status") or formal_gate.get("formal_draft_gate_status"),
            "diagnostic_status": as_dict(diagnostics.get("summary")).get("diagnostic_status"),
        },
        "safety_boundary": [
            "v9.6 explains why a ticket exists or is blocked; it does not approve or execute trades.",
            "Generated explanations are for manual review and model governance only.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v9.6 Trade Ticket Explainability",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Explainability status: **{output['explainability_status']}**",
        f"- Manual ticket count: `{len(ticket_rows)}`",
        f"- Explanation rows: `{len(explanations)}`",
        f"- Trade signal enabled: `{output['trade_signal_enabled']}`",
        "",
        "## Boundary",
        "- This explains ticket generation/blocking. It is not buy/sell advice and cannot execute trades.",
    ]) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Explainability status: {output['explainability_status']}")
    print(f"Explanation rows: {len(explanations)}")


if __name__ == "__main__":
    main()
