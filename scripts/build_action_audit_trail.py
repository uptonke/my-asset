#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
import hashlib

OUT_DIR = Path("data/optimizer")
HUMAN = OUT_DIR / "human_approval_layer_latest.json"
JSON_OUT = OUT_DIR / "action_audit_trail_latest.json"
MD_OUT = OUT_DIR / "action_audit_trail_summary.md"
VERSION = "v2.5"
MAX_EVENTS = 500

SAFE_MODE_NOTE = (
    "v2.5 Action Audit Trail 記錄模型候選、審核狀態與拒絕/觀察原因；"
    "這是 append/dedupe 型審計紀錄，不是交易系統，不自動下單，不寫入 Supabase，"
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


def short_hash(obj: Any, n: int = 16) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:n]


def content_hash(ticket: Dict[str, Any]) -> str:
    key = {
        "source_draft_id": ticket.get("source_draft_id"),
        "source_type": ticket.get("source_type"),
        "model_status": ticket.get("model_status"),
        "constraint_status": ticket.get("constraint_status"),
        "turnover_vs_current_pct": ticket.get("turnover_vs_current_pct"),
        "reason_codes": ticket.get("reason_codes") or [],
        "top_adjustments": ticket.get("top_adjustments") or [],
        "constraint_flags": ticket.get("constraint_flags") or [],
    }
    return short_hash(key, 20)


def build_event(ticket: Dict[str, Any], generated_at: str) -> Dict[str, Any]:
    ch = content_hash(ticket)
    event_type = "model_candidate_generated"
    event_id = f"v2_5_{event_type}_{ch}"
    human = ticket.get("human_approval") or {}
    return {
        "event_id": event_id,
        "event_content_hash": ch,
        "event_type": event_type,
        "created_at": generated_at,
        "source_version": ticket.get("source_version") or "v2.4",
        "approval_ticket_id": ticket.get("approval_ticket_id"),
        "candidate_id": ticket.get("source_draft_id"),
        "source_type": ticket.get("source_type"),
        "model_status": ticket.get("model_status"),
        "constraint_status": ticket.get("constraint_status"),
        "human_status": human.get("status") or "pending_review",
        "requires_manual_approval": bool(ticket.get("requires_manual_approval", True)),
        "execution_permission": False,
        "not_trade_order": True,
        "reason_codes": ticket.get("reason_codes") or [],
        "turnover_vs_current_pct": ticket.get("turnover_vs_current_pct"),
        "top_adjustments": ticket.get("top_adjustments") or [],
    }


def merge_events(previous: Dict[str, Any], new_events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
    old_events = previous.get("audit_events") or previous.get("events") or []
    merged: Dict[str, Dict[str, Any]] = {}
    for ev in old_events:
        if not isinstance(ev, dict):
            continue
        key = ev.get("event_content_hash") or ev.get("event_id")
        if key:
            merged[str(key)] = ev
    added = 0
    unchanged = 0
    for ev in new_events:
        key = ev.get("event_content_hash") or ev.get("event_id")
        if key in merged:
            # Preserve original creation time, refresh last_seen_at.
            old = merged[key]
            old["last_seen_at"] = ev.get("created_at")
            old["seen_count"] = int(old.get("seen_count") or 1) + 1
            merged[key] = old
            unchanged += 1
        else:
            ev["first_seen_at"] = ev.get("created_at")
            ev["last_seen_at"] = ev.get("created_at")
            ev["seen_count"] = 1
            merged[str(key)] = ev
            added += 1
    events = list(merged.values())
    events.sort(key=lambda x: str(x.get("last_seen_at") or x.get("created_at") or ""), reverse=True)
    return events[:MAX_EVENTS], added, unchanged


def summarize(events: List[Dict[str, Any]], added: int, unchanged: int) -> Dict[str, Any]:
    pending = sum(1 for e in events if e.get("human_status") == "pending_review")
    rejected = sum(1 for e in events if e.get("human_status") == "rejected")
    approved = sum(1 for e in events if e.get("human_status") == "approved_for_manual_execution")
    watch = sum(1 for e in events if e.get("human_status") == "watch_only")
    return {
        "stored_events": len(events),
        "new_events_added_this_run": added,
        "existing_events_seen_again": unchanged,
        "pending_review": pending,
        "approved_for_manual_execution": approved,
        "rejected": rejected,
        "watch_only": watch,
        "execution_permission_true": sum(1 for e in events if e.get("execution_permission") is True),
    }


def write_markdown(payload: Dict[str, Any]) -> None:
    s = payload.get("summary") or {}
    events = payload.get("audit_events") or []
    lines = [
        "# Action Audit Trail v2.5",
        "",
        f"Generated: `{payload.get('generated_at')}`",
        "",
        "## Safety boundary",
        "",
        "- 記錄模型候選與人工審核狀態。",
        "- 不是交易指令。",
        "- 不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。",
        "",
        "## Summary",
        "",
        f"- Stored events: {s.get('stored_events', 0)}",
        f"- New events added this run: {s.get('new_events_added_this_run', 0)}",
        f"- Existing events seen again: {s.get('existing_events_seen_again', 0)}",
        f"- Pending review: {s.get('pending_review', 0)}",
        f"- Approved for manual execution: {s.get('approved_for_manual_execution', 0)}",
        f"- Rejected: {s.get('rejected', 0)}",
        f"- Watch only: {s.get('watch_only', 0)}",
        "",
        "## Recent events",
        "",
    ]
    for e in events[:20]:
        lines.extend([
            f"### {e.get('event_id')}",
            "",
            f"- Candidate: `{e.get('candidate_id')}`",
            f"- Approval ticket: `{e.get('approval_ticket_id')}`",
            f"- Model status: `{e.get('model_status')}`",
            f"- Human status: `{e.get('human_status')}`",
            f"- Reason codes: `{', '.join(e.get('reason_codes') or [])}`",
            f"- First seen: `{e.get('first_seen_at')}`",
            f"- Last seen: `{e.get('last_seen_at')}`",
            "",
        ])
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    human = load_json(HUMAN)
    previous = load_json(JSON_OUT)
    generated_at = now_utc()
    tickets = [t for t in (human.get("approval_tickets") or []) if isinstance(t, dict)]
    new_events = [build_event(t, generated_at) for t in tickets]
    events, added, unchanged = merge_events(previous, new_events)
    payload = {
        "version": VERSION,
        "status": "OK" if events else "NO_EVENTS",
        "generated_at": generated_at,
        "mode": "action_audit_trail",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "source_files": {
            "human_approval_layer": str(HUMAN),
            "previous_audit_trail": str(JSON_OUT),
        },
        "audit_policy": {
            "append_dedupe": True,
            "dedupe_key": "event_content_hash",
            "max_events": MAX_EVENTS,
            "execution_permission_default": False,
            "not_trade_order": True,
        },
        "summary": summarize(events, added, unchanged),
        "audit_events": events,
        "warnings": [
            "v2.5 第一版只記錄模型事件與預設人工審核狀態；沒有提供前端採納/拒絕寫回介面。",
            "若未來要記錄人工採納/拒絕，應新增 manual override 檔或資料庫表，不應直接改模型輸出。",
        ],
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Stored events: {payload['summary']['stored_events']}")
    print(f"New events added this run: {payload['summary']['new_events_added_this_run']}")


if __name__ == "__main__":
    main()
