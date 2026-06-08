#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "manual_approval_input_latest.json"
SUMMARY_MD = OUT_DIR / "manual_approval_input_summary.md"
CONFIG = ROOT / "config" / "manual_approval_override.json"

def now_iso(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path, default: Any = None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def main():
    cfg = read_json(CONFIG, {}) or {}
    approved = cfg.get("approved_candidate_ids") or []
    rejected = cfg.get("rejected_candidate_ids") or []
    override_enabled = bool(cfg.get("manual_override_enabled"))
    cash_override = cfg.get("cash_balance_twd")
    trade_budget = cfg.get("max_trade_budget_twd")
    output = {
        "version": "v8.1-manual-approval-input",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "manual_approval_input_layer",
        "safe_mode": True,
        "research_only": True,
        "manual_input_file": "config/manual_approval_override.json",
        "manual_override_enabled": override_enabled,
        "approval_mode": cfg.get("approval_mode") or "research_only",
        "approved_candidate_ids": approved,
        "rejected_candidate_ids": rejected,
        "cash_balance_twd_override": cash_override,
        "max_trade_budget_twd": trade_budget,
        "allow_formal_draft_when_validation_watch_only": bool(cfg.get("allow_formal_draft_when_validation_watch_only")),
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "not_trade_order": True,
        "summary": {
            "manual_override_enabled": override_enabled,
            "approved_count": len(approved) if isinstance(approved, list) else 0,
            "rejected_count": len(rejected) if isinstance(rejected, list) else 0,
            "cash_balance_twd_override_present": cash_override is not None,
            "max_trade_budget_twd_present": trade_budget is not None,
        },
        "safety_boundary": [
            "This file is a manual input layer, not an execution approval layer.",
            "Even when enabled, it can only affect review-only draft generation.",
            "It cannot enable trade_signal_enabled, execution_permission, or broker submission.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v8.1 Manual Approval Input Layer",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Manual override enabled: `{override_enabled}`",
        f"- Approved candidate ids: `{output['summary']['approved_count']}`",
        f"- Rejected candidate ids: `{output['summary']['rejected_count']}`",
        f"- Cash balance override present: `{output['summary']['cash_balance_twd_override_present']}`",
        "",
        "## Boundary",
        "- Manual input does not mean trade approval.",
    ]) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Manual override enabled: {override_enabled}")

if __name__ == "__main__": main()
