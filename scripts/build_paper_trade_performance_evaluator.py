#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "paper_trade_performance_evaluator_latest.json"
SUMMARY_MD = OUT_DIR / "paper_trade_performance_evaluator_summary.md"


def now_dt() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_dt().isoformat(timespec="seconds")


def read_json(rel: str, default: Any = None) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def parse_date(s: Any) -> date | None:
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def main() -> None:
    tracker = as_dict(read_json("data/alpha/paper_trade_tracker_latest.json", {}))
    sizing = as_dict(read_json("data/alpha/trading_constraints_snapshot_latest.json", {}))
    rows = as_list(tracker.get("paper_trade_rows"))
    today = now_dt().date()
    evaluations: List[Dict[str, Any]] = []
    due_count = 0
    pending_count = 0
    pass_count = 0
    fail_count = 0
    insufficient_count = 0

    price_ready = bool(as_dict(sizing.get("summary")).get("all_prices_real_world"))

    for r0 in rows:
        r = as_dict(r0)
        cps = as_list(r.get("checkpoints"))
        cp_results = []
        for cp0 in cps:
            cp = as_dict(cp0)
            due = parse_date(cp.get("due_at"))
            is_due = bool(due and today >= due)
            if is_due:
                due_count += 1
                verdict = "evidence_insufficient"
                insufficient_count += 1
                detail = "檢查點已到期，但目前沒有完整 baseline / paper portfolio return series；只能標記證據不足。"
            else:
                pending_count += 1
                verdict = "pending"
                detail = "尚未到檢查日期。"
            cp_results.append({
                "horizon": cp.get("horizon"),
                "due_at": cp.get("due_at"),
                "is_due": is_due,
                "evaluation_status": verdict,
                "detail": detail,
                "paper_return": None,
                "baseline_return": None,
                "risk_improvement": None,
            })
        evaluations.append({
            "paper_id": r.get("paper_id"),
            "source_ticket_id": r.get("source_ticket_id"),
            "source_formal_draft_id": r.get("source_formal_draft_id"),
            "status": r.get("status"),
            "checkpoint_results": cp_results,
            "current_verdict": "tracking_pending" if cp_results else "no_checkpoints",
            "evaluator_note": "Performance evaluation requires stored baseline and paper portfolio return series; no trade signal is generated.",
        })

    if not rows:
        evaluator_status = "no_paper_trades_to_evaluate"
    elif due_count and insufficient_count == due_count:
        evaluator_status = "due_but_evidence_insufficient"
    else:
        evaluator_status = "tracking_pending"

    output = {
        "version": "v9.5",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "paper_trade_performance_evaluator",
        "safe_mode": True,
        "research_only": True,
        "evaluator_status": evaluator_status,
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
            "evaluator_status": evaluator_status,
            "paper_trade_count": len(rows),
            "checkpoint_due_count": due_count,
            "checkpoint_pending_count": pending_count,
            "checkpoint_pass_count": pass_count,
            "checkpoint_fail_count": fail_count,
            "checkpoint_insufficient_count": insufficient_count,
            "real_world_prices_ready": price_ready,
        },
        "evaluation_rows": evaluations,
        "methodology": {
            "baseline": "current_portfolio_no_action",
            "paper_candidate": "formal_review_draft_or_manual_ticket_hypothesis",
            "horizons": ["1W", "1M", "3M"],
            "required_future_extension": "store baseline and paper portfolio return series at entry and checkpoint dates",
        },
        "safety_boundary": [
            "v9.5 is a lagging accountability evaluator, not a forward signal.",
            "It cannot approve trades, generate broker orders, or enable execution.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v9.5 Paper Trade Performance Evaluator",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Evaluator status: **{evaluator_status}**",
        f"- Paper trade count: `{len(rows)}`",
        f"- Due checkpoints: `{due_count}`",
        f"- Evidence-insufficient checkpoints: `{insufficient_count}`",
        "",
        "## Boundary",
        "- This is a lagging model-accountability evaluator, not a trading signal.",
    ]) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Evaluator status: {evaluator_status}")
    print(f"Paper trade count: {len(rows)}")


if __name__ == "__main__":
    main()
