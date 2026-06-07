#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

OUT_DIR = Path("data/optimizer")
DECISION_CENTER = OUT_DIR / "decision_center_latest.json"
SKFOLIO = OUT_DIR / "skfolio_sandbox_latest.json"
RISKFOLIO = OUT_DIR / "riskfolio_sandbox_latest.json"
JSON_OUT = OUT_DIR / "rebalance_candidates_latest.json"
MD_OUT = OUT_DIR / "rebalance_candidates_summary.md"

VERSION = "v2.1"
MATERIAL_DELTA_PCT = 0.75
WATCH_STEP_FRACTION = 0.25
CANDIDATE_STEP_FRACTION = 0.50
WATCH_MAX_SINGLE_STEP_PCT = 2.00
CANDIDATE_MAX_SINGLE_STEP_PCT = 4.00
MAX_ROWS_PER_DRAFT = 12

SAFE_MODE_NOTE = (
    "v2.1 只產生再平衡候選草案，不產生 BUY / SELL 指令，不寫入 Supabase，"
    "不修改正式持倉或正式權重；所有草案都需要人工確認。"
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
        if value is None:
            return default
        value = float(value)
        if math.isfinite(value):
            return value
        return default
    except Exception:
        return default


def round_or_none(value: Any, ndigits: int = 3) -> Optional[float]:
    v = safe_float(value)
    return round(v, ndigits) if v is not None else None


def normalize_ticker(ticker: Any) -> str:
    return str(ticker or "").strip()


def weight_map(weights: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for row in weights or []:
        if not isinstance(row, dict):
            continue
        ticker = normalize_ticker(row.get("ticker"))
        if not ticker:
            continue
        out[ticker] = safe_float(row.get("weight_pct"), 0.0) or 0.0
    return out


def portfolio_lookup(*payloads: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for payload in payloads:
        portfolios = payload.get("portfolios", {}) if isinstance(payload, dict) else {}
        if not isinstance(portfolios, dict):
            continue
        for pid, portfolio in portfolios.items():
            if isinstance(portfolio, dict):
                out[str(pid)] = portfolio
    return out


def decision_lookup(decision_center: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    rows = decision_center.get("candidates", []) if isinstance(decision_center, dict) else []
    if not isinstance(rows, list):
        return out
    for row in rows:
        if isinstance(row, dict) and row.get("id"):
            out[str(row["id"])] = row
    return out


def get_status(row: Dict[str, Any]) -> str:
    decision = row.get("decision", {}) if isinstance(row, dict) else {}
    if isinstance(decision, dict):
        return str(decision.get("status", "unknown"))
    return str(row.get("status", "unknown"))


def get_current_weights(portfolios: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    current = portfolios.get("current_weight", {})
    weights = current.get("weights", []) if isinstance(current, dict) else []
    return weight_map(weights)


def material_changes(current: Dict[str, float], target: Dict[str, float], *, step_fraction: float, max_step_pct: float) -> Tuple[List[Dict[str, Any]], float, float]:
    tickers = sorted(set(current) | set(target))
    changes: List[Dict[str, Any]] = []
    full_turnover = 0.0
    proposed_turnover = 0.0

    for ticker in tickers:
        cur = current.get(ticker, 0.0)
        tgt = target.get(ticker, 0.0)
        full_delta = tgt - cur
        full_turnover += abs(full_delta)
        raw_step = full_delta * step_fraction
        capped_step = max(-max_step_pct, min(max_step_pct, raw_step))
        proposed = cur + capped_step
        if abs(capped_step) < 0.001:
            proposed = cur
        proposed_turnover += abs(capped_step)

        direction = "HOLD"
        if capped_step > 0.001:
            direction = "UP"
        elif capped_step < -0.001:
            direction = "DOWN"

        changes.append({
            "ticker": ticker,
            "current_weight_pct": round(cur, 3),
            "model_target_weight_pct": round(tgt, 3),
            "full_delta_pct": round(full_delta, 3),
            "proposed_delta_pct": round(capped_step, 3),
            "proposed_candidate_weight_pct": round(proposed, 3),
            "direction": direction,
            "is_material": abs(full_delta) >= MATERIAL_DELTA_PCT,
        })

    changes.sort(key=lambda r: abs(safe_float(r.get("full_delta_pct"), 0.0) or 0.0), reverse=True)
    material = [r for r in changes if r["is_material"]][:MAX_ROWS_PER_DRAFT]
    return material, round(full_turnover / 2.0, 3), round(proposed_turnover / 2.0, 3)


def gate_level(status: str, pid: str, candidate_for_v21: List[str], top_ranked: List[str]) -> str:
    if pid in candidate_for_v21 or status == "candidate":
        return "approved_candidate"
    if status == "watch" and (not top_ranked or pid in top_ranked):
        return "watch_review_only"
    if status == "baseline":
        return "baseline_reference"
    if status == "reject":
        return "rejected_source"
    return "not_eligible"


def make_draft(pid: str, model: Dict[str, Any], decision_row: Dict[str, Any], current_weights: Dict[str, float], gate: str) -> Optional[Dict[str, Any]]:
    weights = model.get("weights", []) if isinstance(model, dict) else []
    target_weights = weight_map(weights)
    if not target_weights or not current_weights:
        return None

    if gate == "approved_candidate":
        step_fraction = CANDIDATE_STEP_FRACTION
        max_step = CANDIDATE_MAX_SINGLE_STEP_PCT
        review_status = "candidate_requires_manual_approval"
    elif gate == "watch_review_only":
        step_fraction = WATCH_STEP_FRACTION
        max_step = WATCH_MAX_SINGLE_STEP_PCT
        review_status = "watch_only_not_approved"
    else:
        return None

    changes, full_turnover, proposed_turnover = material_changes(
        current_weights,
        target_weights,
        step_fraction=step_fraction,
        max_step_pct=max_step,
    )

    decision = decision_row.get("decision", {}) if isinstance(decision_row, dict) else {}
    metrics = decision_row.get("metrics", {}) if isinstance(decision_row, dict) else {}
    exposure = decision_row.get("exposure", {}) if isinstance(decision_row, dict) else {}
    stress = decision_row.get("stress", {}) if isinstance(decision_row, dict) else {}
    robustness = decision_row.get("robustness", {}) if isinstance(decision_row, dict) else {}
    flags = decision_row.get("constraint_flags", []) if isinstance(decision_row, dict) else []
    violations = [f for f in flags if isinstance(f, dict) and f.get("level") == "violation"]
    warnings = [f for f in flags if isinstance(f, dict) and f.get("level") == "warning"]

    return {
        "proposal_id": f"v2_1_{pid}",
        "source_model_id": pid,
        "source_model_name": str(decision_row.get("name") or pid).replace("_", " "),
        "source": decision_row.get("source", "unknown"),
        "gate": gate,
        "review_status": review_status,
        "execution_permission": False,
        "requires_manual_approval": True,
        "not_trade_order": True,
        "step_policy": {
            "step_fraction_of_model_delta": step_fraction,
            "max_single_step_pct": max_step,
            "material_delta_threshold_pct": MATERIAL_DELTA_PCT,
            "note": "候選草案只走向模型目標的一部分，避免一次性高換手率。",
        },
        "source_decision": {
            "status": decision.get("status"),
            "score": round_or_none(decision.get("score")),
            "reason": decision.get("reason"),
        },
        "risk_snapshot": {
            "annual_vol_pct": round_or_none(metrics.get("annual_vol_pct")),
            "es95_pct": round_or_none(metrics.get("es95_pct")),
            "max_drawdown_pct": round_or_none(metrics.get("max_drawdown_pct")),
            "turnover_vs_current_pct": round_or_none(metrics.get("turnover_vs_current_pct")),
            "worst_scenario_return_pct": round_or_none(stress.get("worst_scenario_return_pct") if isinstance(stress, dict) else None),
            "robustness_status": robustness.get("status") if isinstance(robustness, dict) else None,
        },
        "exposure_snapshot": exposure,
        "constraint_summary": {
            "violation_count": len(violations),
            "warning_count": len(warnings),
            "flags": flags,
        },
        "turnover_estimate": {
            "full_model_turnover_pct": full_turnover,
            "proposed_candidate_turnover_pct": proposed_turnover,
        },
        "material_adjustments": changes,
        "safety_boundary": [
            "This is not a BUY / SELL list.",
            "execution_permission is always false in v2.1.",
            "No Supabase write.",
            "No official portfolio weight update.",
            "Human approval is mandatory before any real-world action.",
        ],
    }


def build() -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    decision_center = load_json(DECISION_CENTER)
    skfolio = load_json(SKFOLIO)
    riskfolio = load_json(RISKFOLIO)

    portfolios = portfolio_lookup(skfolio, riskfolio)
    current_weights = get_current_weights(portfolios)
    decisions = decision_lookup(decision_center)
    summary = decision_center.get("decision_summary", {}) if isinstance(decision_center, dict) else {}
    candidate_for_v21 = summary.get("candidate_for_v2_1", []) if isinstance(summary, dict) else []
    top_ranked = summary.get("top_ranked", []) if isinstance(summary, dict) else []
    candidate_for_v21 = [str(x) for x in candidate_for_v21] if isinstance(candidate_for_v21, list) else []
    top_ranked = [str(x) for x in top_ranked] if isinstance(top_ranked, list) else []

    approved: List[Dict[str, Any]] = []
    watch: List[Dict[str, Any]] = []
    rejected_source: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []

    for pid, row in decisions.items():
        status = get_status(row)
        gate = gate_level(status, pid, candidate_for_v21, top_ranked)
        model = portfolios.get(pid)

        if gate in {"approved_candidate", "watch_review_only"}:
            draft = make_draft(pid, model or {}, row, current_weights, gate)
            if draft is None:
                skipped.append({"id": pid, "gate": gate, "reason": "missing_weights"})
                continue
            if gate == "approved_candidate":
                approved.append(draft)
            else:
                watch.append(draft)
        elif gate == "rejected_source":
            rejected_source.append({
                "id": pid,
                "decision_status": status,
                "reason": (row.get("decision") or {}).get("reason") if isinstance(row.get("decision"), dict) else None,
            })
        else:
            skipped.append({"id": pid, "gate": gate, "decision_status": status})

    payload = {
        "version": VERSION,
        "status": "OK" if decision_center else "MISSING_DECISION_CENTER",
        "generated_at": now_utc(),
        "mode": "rebalance_candidate_generator",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "source_files": {
            "decision_center": str(DECISION_CENTER),
            "skfolio": str(SKFOLIO),
            "riskfolio": str(RISKFOLIO),
        },
        "input_gate": {
            "candidate_for_v2_1": candidate_for_v21,
            "top_ranked": top_ranked,
            "decision_center_verdict": summary.get("verdict") if isinstance(summary, dict) else None,
        },
        "policy": {
            "approved_candidate_step_fraction": CANDIDATE_STEP_FRACTION,
            "approved_candidate_max_single_step_pct": CANDIDATE_MAX_SINGLE_STEP_PCT,
            "watch_step_fraction": WATCH_STEP_FRACTION,
            "watch_max_single_step_pct": WATCH_MAX_SINGLE_STEP_PCT,
            "material_delta_threshold_pct": MATERIAL_DELTA_PCT,
            "output_is_not_trade_order": True,
        },
        "approved_candidates": approved,
        "watchlist_drafts": watch,
        "rejected_sources": rejected_source,
        "skipped": skipped,
        "summary": {
            "approved_candidate_count": len(approved),
            "watchlist_draft_count": len(watch),
            "rejected_source_count": len(rejected_source),
            "skipped_count": len(skipped),
            "execution_permission_count": 0,
            "human_approval_required": True,
            "verdict": "無可直接進入人工批准的候選；僅產生觀察草案。" if not approved and watch else (
                "已有候選草案，但仍需人工批准。" if approved else "無候選草案。"
            ),
            "top_watchlist_draft": watch[0]["proposal_id"] if watch else None,
        },
    }
    return payload


def write_md(payload: Dict[str, Any]) -> str:
    s = payload.get("summary", {})
    lines = [
        "# Rebalance Candidate Generator v2.1",
        "",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Safety Boundary",
        "",
        "- This is not a BUY / SELL list.",
        "- execution_permission is always false in v2.1.",
        "- No Supabase write.",
        "- No official portfolio weight update.",
        "- Human approval is mandatory before any real-world action.",
        "",
        "## Summary",
        "",
        f"- Approved candidate count: `{s.get('approved_candidate_count')}`",
        f"- Watchlist draft count: `{s.get('watchlist_draft_count')}`",
        f"- Rejected source count: `{s.get('rejected_source_count')}`",
        f"- Verdict: {s.get('verdict')}",
        "",
    ]

    approved = payload.get("approved_candidates", []) or []
    watch = payload.get("watchlist_drafts", []) or []

    def add_table(title: str, drafts: List[Dict[str, Any]]) -> None:
        lines.extend([f"## {title}", ""])
        if not drafts:
            lines.extend(["None.", ""])
            return
        lines.extend([
            "| Proposal | Gate | Source model | Proposed turnover | Top material changes |",
            "|---|---|---|---:|---|",
        ])
        for d in drafts:
            changes = d.get("material_adjustments", [])[:5]
            change_text = "; ".join(
                f"{c.get('ticker')} {c.get('direction')} {c.get('proposed_delta_pct')}pp"
                for c in changes
            ) or "-"
            turnover = (d.get("turnover_estimate", {}) or {}).get("proposed_candidate_turnover_pct")
            lines.append(
                f"| `{d.get('proposal_id')}` | `{d.get('gate')}` | {d.get('source_model_id')} | {turnover}% | {change_text} |"
            )
        lines.append("")

    add_table("Approved Candidates", approved)
    add_table("Watchlist Drafts", watch)

    rejected = payload.get("rejected_sources", []) or []
    lines.extend(["## Rejected Sources", ""])
    if not rejected:
        lines.extend(["None.", ""])
    else:
        lines.extend(["| Source | Reason |", "|---|---|"])
        for r in rejected:
            reason = str(r.get("reason") or "-").replace("\n", " ")
            lines.append(f"| `{r.get('id')}` | {reason} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    payload = build()
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(write_md(payload), encoding="utf-8")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Approved candidates: {payload['summary']['approved_candidate_count']}")
    print(f"Watchlist drafts: {payload['summary']['watchlist_draft_count']}")


if __name__ == "__main__":
    main()
