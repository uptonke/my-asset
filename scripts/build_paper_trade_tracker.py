#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "paper_trade_tracker_latest.json"
SUMMARY_MD = OUT_DIR / "paper_trade_tracker_summary.md"

def now_dt(): return datetime.now(timezone.utc)
def now_iso(): return now_dt().isoformat(timespec="seconds")

def read_json(rel: str, default: Any = None) -> Any:
    try: return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception: return default

def main() -> None:
    prev = read_json("data/alpha/paper_trade_tracker_latest.json", {}) or {}
    tickets = read_json("data/alpha/manual_trade_ticket_latest.json", {}) or {}
    formal = read_json("data/alpha/formal_rebalance_draft_gate_latest.json", {}) or {}
    sizing = read_json("data/alpha/trading_constraints_snapshot_latest.json", {}) or {}
    existing = prev.get("paper_trade_rows") or []
    by_source = {str(r.get("source_ticket_id") or r.get("source_formal_draft_id") or r.get("paper_id")): r for r in existing if isinstance(r, dict)}
    rows: List[Dict[str, Any]] = list(existing) if isinstance(existing, list) else []
    added = 0
    base_dt = now_dt()
    ticket_rows = tickets.get("ticket_rows") or []
    if not ticket_rows:
        # Track formal drafts as hypotheses if ticket rows are blocked, but do not invent order lines.
        ticket_rows = []
        for fr in formal.get("formal_draft_rows") or []:
            ticket_rows.append({"ticket_id": None, "source_formal_draft_id": fr.get("formal_draft_id"), "ticket_status": "formal_draft_hypothesis_only", "estimated_orders": []})
    for t in ticket_rows if isinstance(ticket_rows, list) else []:
        source_key = str(t.get("ticket_id") or t.get("source_formal_draft_id") or "")
        if not source_key or source_key in by_source:
            continue
        checkpoints = []
        for label, days in [("1W", 7), ("1M", 30), ("3M", 90)]:
            checkpoints.append({"horizon": label, "due_at": (base_dt + timedelta(days=days)).date().isoformat(), "status": "pending", "evaluation": None})
        rows.append({
            "paper_id": f"paper_{base_dt.strftime('%Y%m%d')}_{source_key}",
            "created_at": base_dt.isoformat(timespec="seconds"),
            "source_ticket_id": t.get("ticket_id"),
            "source_formal_draft_id": t.get("source_formal_draft_id"),
            "source_stage": "v9.0_manual_trade_ticket" if t.get("ticket_id") else "v8.1_formal_draft_hypothesis",
            "status": "active_tracking",
            "hypothesis_type": "formal_rebalance_or_manual_ticket_hypothesis",
            "not_trade_order": True,
            "execution_permission": False,
            "entry_snapshot": {
                "trading_constraints_generated_at": sizing.get("generated_at"),
                "cash_balance": sizing.get("cash_balance"),
                "total_market_value_twd": (sizing.get("summary") or {}).get("total_market_value_twd"),
                "real_world_price_success_count": (sizing.get("summary") or {}).get("real_world_price_success_count"),
            },
            "checkpoints": checkpoints,
            "current_verdict": "tracking_pending",
            "paper_tracking_note": "This is a formal paper-tracking record. It validates future outcomes and is not a live trading signal.",
        })
        added += 1
    output = {
        "version": "v9.2",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "paper_trade_tracker",
        "safe_mode": True,
        "research_only": True,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "not_trade_order": True,
        "summary": {
            "paper_trade_count": len(rows),
            "new_paper_trades_added": added,
            "active_tracking_count": sum(1 for r in rows if r.get("status") == "active_tracking"),
            "source_ticket_count": len(tickets.get("ticket_rows") or []),
            "source_formal_draft_count": len(formal.get("formal_draft_rows") or []),
        },
        "paper_trade_rows": rows,
        "tracking_policy": {
            "purpose": "Track review-only drafts over 1W/1M/3M horizons to test whether model hypotheses were useful after the fact.",
            "is_lagging_model_accountability_layer": True,
            "not_a_forward_trade_signal": True,
        },
        "safety_boundary": [
            "Paper tracking is retrospective model accountability, not a buy/sell signal.",
            "It cannot enable execution or broker submission.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v9.2 Paper Trade Tracker",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Paper trade count: `{len(rows)}`",
        f"- New added: `{added}`",
        "",
        "## Boundary",
        "- Paper tracking is a lagging accountability layer, not a trading signal.",
    ]) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Paper trade count: {len(rows)}")
    print(f"New added: {added}")

if __name__ == "__main__": main()
