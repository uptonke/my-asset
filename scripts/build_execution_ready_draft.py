#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "execution_ready_draft_latest.json"
SUMMARY_MD = OUT_DIR / "execution_ready_draft_summary.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(rel: str, default: Any = None) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def main() -> None:
    validation = read_json("data/alpha/alpha_validation_gate_latest.json", {}) or {}
    proposal = read_json("data/alpha/manual_rebalance_proposal_latest.json", {}) or {}

    validation_status = str((validation.get("summary") or {}).get("validation_status") or "missing_validation")
    proposals = proposal.get("proposal_rows") or []
    eligible = [p for p in proposals if p.get("proposal_status") == "manual_research_proposal"]

    # v8 deliberately remains a pre-execution draft. It does not enable execution.
    # A row can become "draftable_for_manual_entry_review" only after v6 pass and v7 manual_research_proposal.
    draft_rows: List[Dict[str, Any]] = []
    for p in eligible[:5]:
        draft_rows.append({
            "draft_id": f"v8_pre_execution_{p.get('source_ranking_id')}",
            "source_proposal_id": p.get("proposal_id"),
            "source_ranking_id": p.get("source_ranking_id"),
            "draft_status": "draftable_for_manual_entry_review" if validation_status == "research_validation_pass" else "blocked_by_alpha_validation_gate",
            "research_priority_rank": p.get("research_priority_rank"),
            "ranking_score": p.get("ranking_score"),
            "turnover_vs_current_pct": p.get("turnover_vs_current_pct"),
            "pre_execution_checklist": [
                {"item": "重新確認目前實際持倉與現金餘額", "required": True, "done": False},
                {"item": "重新確認報價、匯率、交易成本與稅費", "required": True, "done": False},
                {"item": "確認約束條件仍然通過", "required": True, "done": False},
                {"item": "確認此草案仍非交易指令，需人工獨立判斷", "required": True, "done": False},
                {"item": "若要實際操作，需由人手動重新輸入並承擔決策責任", "required": True, "done": False},
            ],
            "draft_is_not_order_ticket": True,
            "not_trade_order": True,
            "execution_permission": False,
            "manual_entry_required": True,
            "broker_submission_enabled": False,
        })

    if validation_status != "research_validation_pass":
        readiness_status = "blocked_by_alpha_validation_gate"
    elif not draft_rows:
        readiness_status = "no_manual_research_proposal"
    else:
        readiness_status = "pre_execution_draft_available_for_manual_review"

    output = {
        "version": "v8.0",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "execution_ready_draft",
        "safe_mode": True,
        "research_only": True,
        "execution_ready_draft_enabled": True,
        "broker_submission_enabled": False,
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
            "manual_rebalance_proposal": "data/alpha/manual_rebalance_proposal_latest.json",
        },
        "readiness_policy": {
            "purpose": "Package manual-review proposals into pre-execution checklists without enabling execution.",
            "execution_ready_draft_is_not_trade_order": True,
            "manual_entry_required": True,
            "system_cannot_submit_orders": True,
            "human_must_independently_validate": True,
        },
        "summary": {
            "readiness_status": readiness_status,
            "validation_status": validation_status,
            "source_proposal_count": len(proposals),
            "eligible_proposal_count": len(eligible),
            "draft_count": len(draft_rows),
            "broker_submission_enabled": False,
            "trade_signal_enabled": False,
            "execution_permission": False,
        },
        "draft_rows": draft_rows,
        "global_pre_execution_checklist": [
            "確認 GitHub Actions 與 Validation Gate 均為 OK",
            "確認前端顯示仍為非交易指令 / 不自動執行",
            "確認沒有 execution_permission=true、trade_signal_enabled=true、official_rebalance_enabled=true",
            "確認實際交易前重新檢查最新市價、匯率、現金、稅費、流動性與個人限制",
        ],
        "safety_boundary": [
            "v8 is a pre-execution draft layer only.",
            "It does not generate broker orders, does not submit trades, and does not approve buy/sell.",
            "execution_permission remains false and broker_submission_enabled remains false.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# v8.0 Execution-Ready Draft",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Readiness status: **{readiness_status}**",
        f"- Draft count: `{len(draft_rows)}`",
        f"- Broker submission enabled: `{output['broker_submission_enabled']}`",
        f"- Execution permission: `{output['execution_permission']}`",
        "",
        "## Safety boundary",
        "- This is a pre-execution checklist draft, not an order ticket.",
        "- It does not mean buy, sell, bullish, or best allocation.",
        "- Human review and manual re-entry are required for any real-world action.",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Readiness status: {readiness_status}")
    print(f"Draft count: {len(draft_rows)}")
    print("Execution permission: False")


if __name__ == "__main__":
    main()
