#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib

OUT_DIR = Path("data/optimizer")
CONSTRAINT = OUT_DIR / "constraint_aware_rebalance_latest.json"
JSON_OUT = OUT_DIR / "human_approval_layer_latest.json"
MD_OUT = OUT_DIR / "human_approval_layer_summary.md"

VERSION = "v2.4"
ALLOWED_STATUSES = [
    "pending_review",
    "approved_for_manual_execution",
    "rejected",
    "watch_only",
]
SAFE_MODE_NOTE = (
    "v2.4 Human Approval Layer 將 v2.3 約束感知草案轉成需要人工確認的審核票據；"
    "所有輸出都只是決策支援，不是交易指令，不自動下單，不寫入 Supabase，"
    "不修改正式持倉或正式權重。"
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "READ_ERROR", "error": str(exc)[:800]}


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def short_hash(obj: Any, n: int = 12) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:n]


def stable_ticket_id(prefix: str, draft: Dict[str, Any]) -> str:
    key = {
        "source": prefix,
        "draft_id": draft.get("draft_id"),
        "source_proposal_id": draft.get("source_proposal_id"),
        "source_model_id": draft.get("source_model_id"),
        "simulation_id": draft.get("source_simulation_id") or draft.get("simulation_id"),
    }
    base = str(draft.get("draft_id") or draft.get("source_proposal_id") or draft.get("source_model_id") or "draft")
    return f"v2_4_{base}_{short_hash(key, 8)}"


def status_label(draft: Dict[str, Any]) -> str:
    status = str(draft.get("constraint_status") or draft.get("gate") or "").lower()
    if "violation" in status or "reject" in status:
        return "blocked_review_required"
    if "high_turnover" in status:
        return "high_turnover_review_required"
    if "pass" in status:
        return "constraint_pass_review_required"
    return "pending_review"


def reason_codes(draft: Dict[str, Any]) -> List[str]:
    codes = ["manual_approval_required", "not_trade_order", "decision_support_only"]
    gate = str(draft.get("gate") or "")
    status = str(draft.get("constraint_status") or "")
    if "watch" in gate.lower():
        codes.append("watch_only_source")
    if "risk_reduction" in str(draft.get("source") or "").lower() or draft.get("source_simulation_id"):
        codes.append("risk_reduction_simulation")
    if "pass" in status.lower():
        codes.append("constraint_pass")
    if "violation" in status.lower() or "blocked" in status.lower():
        codes.append("constraint_violation_or_blocker")
    if "high_turnover" in status.lower():
        codes.append("high_turnover_review")
    flags = draft.get("constraint_flags_after_adjustment") or draft.get("constraint_flags") or []
    if flags:
        codes.append("constraint_flags_present")
    turnover = safe_float(draft.get("turnover_vs_current_pct"))
    if turnover is not None:
        if turnover >= 15:
            codes.append("turnover_above_candidate_threshold")
        elif turnover >= 8:
            codes.append("turnover_watch_threshold")
    out: List[str] = []
    for c in codes:
        if c not in out:
            out.append(c)
    return out


def top_adjustments(draft: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = draft.get("top_constraint_aware_adjustments") or draft.get("top_adjustments") or draft.get("adjustments") or []
    return [r for r in rows if isinstance(r, dict)][:8]


def build_ticket(draft: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    tid = stable_ticket_id(source_type, draft)
    top = top_adjustments(draft)
    flags = draft.get("constraint_flags_after_adjustment") or draft.get("constraint_flags") or []
    return {
        "approval_ticket_id": tid,
        "source_version": VERSION,
        "source_type": source_type,
        "source_draft_id": draft.get("draft_id"),
        "source_model_id": draft.get("source_model_id") or draft.get("model_id") or draft.get("source_simulation_id"),
        "gate": draft.get("gate"),
        "model_status": status_label(draft),
        "constraint_status": draft.get("constraint_status"),
        "turnover_vs_current_pct": draft.get("turnover_vs_current_pct"),
        "execution_permission": False,
        "not_trade_order": True,
        "requires_manual_approval": True,
        "human_approval": {
            "required": True,
            "status": "pending_review",
            "allowed_statuses": ALLOWED_STATUSES,
            "approval_note": None,
            "approved_by": None,
            "approved_at": None,
            "rejected_reason": None,
        },
        "ui_badges": [
            "需要人工確認",
            "僅供決策支援",
            "不是交易指令",
        ],
        "reason_codes": reason_codes(draft),
        "constraint_flags": flags if isinstance(flags, list) else [],
        "raw_exposure": draft.get("raw_proposal_exposure") or draft.get("raw_exposure"),
        "constraint_aware_exposure": draft.get("constraint_aware_exposure"),
        "top_adjustments": top,
        "constraint_actions": draft.get("constraint_actions") or [],
        "manual_review_checklist": [
            "確認資料日期、資產價格與持倉快照是否正確。",
            "確認換手率、稅費、滑價、匯差與最小交易單位。",
            "確認是否違反單一資產、加密、台股、現金與黃金約束。",
            "確認壓力測試改善是否足以抵消交易摩擦。",
            "若採納，仍需人工在正式交易系統另行操作；本檔案不會自動交易。",
        ],
    }


def build_summary(tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
    pending = sum(1 for t in tickets if (t.get("human_approval") or {}).get("status") == "pending_review")
    pass_review = sum(1 for t in tickets if str(t.get("model_status") or "").startswith("constraint_pass"))
    high_turnover = sum(1 for t in tickets if "high_turnover_review" in (t.get("reason_codes") or []))
    blocked = sum(1 for t in tickets if "constraint_violation_or_blocker" in (t.get("reason_codes") or []))
    execution_enabled = sum(1 for t in tickets if t.get("execution_permission") is True)
    return {
        "total_tickets": len(tickets),
        "pending_review": pending,
        "constraint_pass_review_required": pass_review,
        "high_turnover_review_required": high_turnover,
        "blocked_review_required": blocked,
        "execution_permission_true": execution_enabled,
        "execution_permission_false": len(tickets) - execution_enabled,
    }


def write_markdown(payload: Dict[str, Any]) -> None:
    summary = payload.get("summary") or {}
    tickets = payload.get("approval_tickets") or []
    lines = [
        "# Human Approval Layer v2.4",
        "",
        f"Generated: `{payload.get('generated_at')}`",
        "",
        "## Safety boundary",
        "",
        "- 需要人工確認。",
        "- 僅供決策支援。",
        "- 不是交易指令。",
        "- 不自動下單，不寫入 Supabase，不修改正式持倉或正式權重。",
        "",
        "## Summary",
        "",
        f"- Total tickets: {summary.get('total_tickets', 0)}",
        f"- Pending review: {summary.get('pending_review', 0)}",
        f"- Constraint-pass review required: {summary.get('constraint_pass_review_required', 0)}",
        f"- High-turnover review required: {summary.get('high_turnover_review_required', 0)}",
        f"- Blocked review required: {summary.get('blocked_review_required', 0)}",
        f"- Execution permission true: {summary.get('execution_permission_true', 0)}",
        "",
        "## Tickets",
        "",
    ]
    for t in tickets[:20]:
        lines.extend([
            f"### {t.get('approval_ticket_id')}",
            "",
            f"- Source draft: `{t.get('source_draft_id')}`",
            f"- Source type: `{t.get('source_type')}`",
            f"- Model status: `{t.get('model_status')}`",
            f"- Human status: `{(t.get('human_approval') or {}).get('status')}`",
            f"- Turnover vs current: `{t.get('turnover_vs_current_pct')}`%",
            f"- Reason codes: `{', '.join(t.get('reason_codes') or [])}`",
            "",
        ])
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    constraint = load_json(CONSTRAINT)
    tickets: List[Dict[str, Any]] = []
    for draft in constraint.get("constraint_aware_rebalance_drafts") or []:
        if isinstance(draft, dict):
            tickets.append(build_ticket(draft, "constraint_aware_rebalance"))
    for draft in constraint.get("constraint_aware_risk_reduction_drafts") or []:
        if isinstance(draft, dict):
            tickets.append(build_ticket(draft, "constraint_aware_risk_reduction"))

    payload = {
        "version": VERSION,
        "status": "OK" if tickets else "NO_TICKETS",
        "generated_at": now_utc(),
        "mode": "human_approval_layer",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "source_files": {
            "constraint_aware_rebalance": str(CONSTRAINT),
        },
        "approval_policy": {
            "default_status": "pending_review",
            "allowed_statuses": ALLOWED_STATUSES,
            "execution_permission_default": False,
            "not_trade_order": True,
            "requires_manual_approval": True,
        },
        "summary": build_summary(tickets),
        "approval_tickets": tickets,
        "warnings": [
            "v2.4 不提供前端直接批准按鈕；任何採納/拒絕都應由人工另行記錄。",
            "本層只標示審核狀態，不會產生 BUY / SELL，不會寫正式投組。",
        ],
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Approval tickets: {len(tickets)}")
    print(f"Pending review: {payload['summary']['pending_review']}")


if __name__ == "__main__":
    main()
