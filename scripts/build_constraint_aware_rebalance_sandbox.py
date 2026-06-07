#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

OUT_DIR = Path("data/optimizer")
REBALANCE = OUT_DIR / "rebalance_candidates_latest.json"
RISK_REDUCTION = OUT_DIR / "risk_reduction_simulator_latest.json"
DECISION_CENTER = OUT_DIR / "decision_center_latest.json"
SKFOLIO = OUT_DIR / "skfolio_sandbox_latest.json"
JSON_OUT = OUT_DIR / "constraint_aware_rebalance_latest.json"
MD_OUT = OUT_DIR / "constraint_aware_rebalance_summary.md"

VERSION = "v2.3"
CASH_TICKER = "BOXX"
GOLD_TICKER = "GLDM"

DEFAULT_POLICY = {
    "max_single_weight_pct": 25.0,
    "max_crypto_weight_pct": 15.0,
    "max_taiwan_weight_pct": 30.0,
    "min_cash_weight_pct": 8.0,
    "soft_gold_target_pct": 5.0,
    "soft_gold_min_pct": 2.0,
    "max_watchlist_turnover_pct": 8.0,
    "max_candidate_turnover_pct": 15.0,
}

SAFE_MODE_NOTE = (
    "v2.3 將 v2.1 候選草案與 v2.2 風險降低模擬套上約束條件；"
    "只產生約束感知草案，不產生 BUY / SELL 指令，不寫入 Supabase，"
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


def round_or_none(value: Any, ndigits: int = 3) -> Optional[float]:
    v = safe_float(value)
    return round(v, ndigits) if v is not None else None


def ticker_bucket(ticker: str) -> str:
    t = str(ticker or "").upper()
    if t == "BOXX" or "CASH" in t:
        return "cash"
    if t in {"GLDM", "GLD"} or "GOLD" in t:
        return "gold"
    if t in {"BTC-USD", "ETH-USD"} or "BTC" in t or "ETH" in t:
        return "crypto"
    if t in {"00981A", "2330"} or t.startswith("00") or t.isdigit():
        return "taiwan_tech"
    return "risk"


def normalize(weights: Dict[str, float]) -> Dict[str, float]:
    clean = {str(k): max(0.0, safe_float(v, 0.0) or 0.0) for k, v in weights.items() if str(k)}
    total = sum(clean.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in clean.items()}


def current_weights_from_skfolio() -> Dict[str, float]:
    payload = load_json(SKFOLIO)
    current = ((payload.get("portfolios") or {}).get("current_weight") or {}) if isinstance(payload, dict) else {}
    rows = current.get("weights", []) if isinstance(current, dict) else []
    out: Dict[str, float] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip()
        if not ticker:
            continue
        out[ticker] = (safe_float(row.get("weight_pct"), 0.0) or 0.0) / 100.0
    return normalize(out)


def build_policy(decision_center: Dict[str, Any]) -> Dict[str, float]:
    policy = dict(DEFAULT_POLICY)
    c = decision_center.get("constraints", {}) if isinstance(decision_center, dict) else {}
    if isinstance(c, dict):
        for key in ("max_single_weight_pct", "max_crypto_weight_pct", "max_taiwan_weight_pct"):
            v = safe_float(c.get(key))
            if v is not None:
                policy[key] = v
        # If upstream minimum cash is zero, keep v2.3's practical floor.
        v = safe_float(c.get("min_cash_weight_pct"))
        if v is not None and v > 0:
            policy["min_cash_weight_pct"] = v
    return {k: float(v) for k, v in policy.items()}


def exposure(weights: Dict[str, float]) -> Dict[str, Any]:
    w = normalize(weights)
    out = {"cash_pct": 0.0, "gold_pct": 0.0, "crypto_pct": 0.0, "taiwan_pct": 0.0, "other_pct": 0.0}
    max_ticker = None
    max_weight = -1.0
    for ticker, weight in w.items():
        b = ticker_bucket(ticker)
        if b == "cash":
            out["cash_pct"] += weight * 100.0
        elif b == "gold":
            out["gold_pct"] += weight * 100.0
        elif b == "crypto":
            out["crypto_pct"] += weight * 100.0
        elif b == "taiwan_tech":
            out["taiwan_pct"] += weight * 100.0
        else:
            out["other_pct"] += weight * 100.0
        if weight > max_weight:
            max_ticker = ticker
            max_weight = weight
    return {
        **{k: round(v, 3) for k, v in out.items()},
        "max_single_weight_pct": round(max_weight * 100.0, 3) if max_weight >= 0 else None,
        "max_single_ticker": max_ticker,
    }


def constraint_flags(weights: Dict[str, float], policy: Dict[str, float]) -> List[Dict[str, Any]]:
    exp = exposure(weights)
    flags: List[Dict[str, Any]] = []
    checks = [
        ("max_single_weight_pct", exp.get("max_single_weight_pct"), policy["max_single_weight_pct"], "max"),
        ("max_crypto_weight_pct", exp.get("crypto_pct"), policy["max_crypto_weight_pct"], "max"),
        ("max_taiwan_weight_pct", exp.get("taiwan_pct"), policy["max_taiwan_weight_pct"], "max"),
        ("min_cash_weight_pct", exp.get("cash_pct"), policy["min_cash_weight_pct"], "min"),
    ]
    for name, value, limit, kind in checks:
        v = safe_float(value, 0.0) or 0.0
        if kind == "max" and v > limit + 1e-9:
            flags.append({"level": "violation", "constraint": name, "value_pct": round(v, 3), "limit_pct": limit})
        if kind == "min" and v < limit - 1e-9:
            flags.append({"level": "violation", "constraint": name, "value_pct": round(v, 3), "limit_pct": limit})

    gold = safe_float(exp.get("gold_pct"), 0.0) or 0.0
    if gold < policy["soft_gold_min_pct"]:
        flags.append({"level": "warning", "constraint": "soft_gold_min_pct", "value_pct": round(gold, 3), "limit_pct": policy["soft_gold_min_pct"]})
    return flags


def pro_rata_trim(weights: Dict[str, float], predicate, amount: float, actions: List[Dict[str, Any]], reason: str) -> Dict[str, float]:
    w = dict(weights)
    keys = [k for k, v in w.items() if predicate(k) and v > 0]
    pool = sum(w[k] for k in keys)
    if amount <= 0 or pool <= 0:
        return w
    trim = min(amount, pool)
    for k in keys:
        cut = trim * (w[k] / pool)
        w[k] = max(0.0, w[k] - cut)
        actions.append({"action": "trim", "ticker": k, "amount_pct": round(cut * 100.0, 3), "reason": reason})
    w[CASH_TICKER] = w.get(CASH_TICKER, 0.0) + trim
    actions.append({"action": "add", "ticker": CASH_TICKER, "amount_pct": round(trim * 100.0, 3), "reason": reason})
    return normalize(w)


def trim_largest_risk_asset(weights: Dict[str, float], amount: float, actions: List[Dict[str, Any]], reason: str) -> Dict[str, float]:
    w = dict(weights)
    candidates = [(k, v) for k, v in w.items() if ticker_bucket(k) not in {"cash", "gold"} and v > 0]
    if not candidates or amount <= 0:
        return w
    k, v = max(candidates, key=lambda x: x[1])
    cut = min(amount, v)
    w[k] = max(0.0, v - cut)
    w[CASH_TICKER] = w.get(CASH_TICKER, 0.0) + cut
    actions.append({"action": "trim", "ticker": k, "amount_pct": round(cut * 100.0, 3), "reason": reason})
    actions.append({"action": "add", "ticker": CASH_TICKER, "amount_pct": round(cut * 100.0, 3), "reason": reason})
    return normalize(w)


def apply_constraints(raw: Dict[str, float], policy: Dict[str, float]) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    w = normalize(raw)
    actions: List[Dict[str, Any]] = []

    exp = exposure(w)
    crypto_excess = max(0.0, (safe_float(exp.get("crypto_pct"), 0.0) or 0.0) - policy["max_crypto_weight_pct"]) / 100.0
    w = pro_rata_trim(w, lambda k: ticker_bucket(k) == "crypto", crypto_excess, actions, "max_crypto_weight_pct")

    exp = exposure(w)
    taiwan_excess = max(0.0, (safe_float(exp.get("taiwan_pct"), 0.0) or 0.0) - policy["max_taiwan_weight_pct"]) / 100.0
    w = pro_rata_trim(w, lambda k: ticker_bucket(k) == "taiwan_tech", taiwan_excess, actions, "max_taiwan_weight_pct")

    # Enforce max single position, largest-first.
    for _ in range(10):
        exp = exposure(w)
        max_w = (safe_float(exp.get("max_single_weight_pct"), 0.0) or 0.0) / 100.0
        max_ticker = exp.get("max_single_ticker")
        excess = max(0.0, max_w - policy["max_single_weight_pct"] / 100.0)
        if excess <= 1e-8 or not max_ticker:
            break
        k = str(max_ticker)
        w[k] = max(0.0, w.get(k, 0.0) - excess)
        w[CASH_TICKER] = w.get(CASH_TICKER, 0.0) + excess
        actions.append({"action": "trim", "ticker": k, "amount_pct": round(excess * 100.0, 3), "reason": "max_single_weight_pct"})
        actions.append({"action": "add", "ticker": CASH_TICKER, "amount_pct": round(excess * 100.0, 3), "reason": "max_single_weight_pct"})
        w = normalize(w)

    exp = exposure(w)
    cash_gap = max(0.0, policy["min_cash_weight_pct"] / 100.0 - (safe_float(exp.get("cash_pct"), 0.0) or 0.0) / 100.0)
    w = trim_largest_risk_asset(w, cash_gap, actions, "min_cash_weight_pct")

    # Soft gold nudge: not a hard mandate; capped to 1pp to avoid forcing a trade-like output.
    exp = exposure(w)
    gold_gap = max(0.0, policy["soft_gold_target_pct"] / 100.0 - (safe_float(exp.get("gold_pct"), 0.0) or 0.0) / 100.0)
    gold_nudge = min(gold_gap, 0.01)
    if gold_nudge > 1e-8:
        before = dict(w)
        w = trim_largest_risk_asset(w, gold_nudge, actions, "soft_gold_target_pct_source_funding")
        funded = before.get(CASH_TICKER, 0.0) - w.get(CASH_TICKER, 0.0)
        # trim_largest_risk_asset routes to cash; move that funded amount from cash to GLDM.
        move = min(gold_nudge, max(0.0, w.get(CASH_TICKER, 0.0) - before.get(CASH_TICKER, 0.0)))
        if move <= 1e-8:
            move = min(gold_nudge, w.get(CASH_TICKER, 0.0))
        if move > 1e-8:
            w[CASH_TICKER] = max(0.0, w.get(CASH_TICKER, 0.0) - move)
            w[GOLD_TICKER] = w.get(GOLD_TICKER, 0.0) + move
            actions.append({"action": "add", "ticker": GOLD_TICKER, "amount_pct": round(move * 100.0, 3), "reason": "soft_gold_target_pct"})
            actions.append({"action": "fund", "ticker": CASH_TICKER, "amount_pct": round(-move * 100.0, 3), "reason": "soft_gold_target_pct"})
            w = normalize(w)

    return normalize(w), actions


def apply_material_adjustments(current: Dict[str, float], draft: Dict[str, Any]) -> Dict[str, float]:
    w = dict(current)
    for row in draft.get("material_adjustments", []) or []:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip()
        if not ticker:
            continue
        proposed = safe_float(row.get("proposed_candidate_weight_pct"))
        if proposed is not None:
            w[ticker] = max(0.0, proposed / 100.0)
    # If material subset does not sum to 100%, allocate small residual to cash.
    total = sum(w.values())
    if total > 0:
        diff = 1.0 - total
        if abs(diff) > 1e-8:
            w[CASH_TICKER] = max(0.0, w.get(CASH_TICKER, 0.0) + diff)
    return normalize(w)


def turnover_pct(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = set(a) | set(b)
    return round(0.5 * sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys) * 100.0, 3)


def top_adjustments(current: Dict[str, float], target: Dict[str, float], limit: int = 15) -> List[Dict[str, Any]]:
    rows = []
    for ticker in sorted(set(current) | set(target)):
        cur = current.get(ticker, 0.0) * 100.0
        tgt = target.get(ticker, 0.0) * 100.0
        delta = tgt - cur
        if abs(delta) < 0.05:
            continue
        rows.append({
            "ticker": ticker,
            "current_weight_pct": round(cur, 3),
            "constraint_aware_weight_pct": round(tgt, 3),
            "delta_pct": round(delta, 3),
            "direction": "UP" if delta > 0 else "DOWN",
        })
    rows.sort(key=lambda r: abs(r["delta_pct"]), reverse=True)
    return rows[:limit]


def status_after_constraints(flags: List[Dict[str, Any]], turnover: float, gate: str, policy: Dict[str, float]) -> str:
    violations = [f for f in flags if f.get("level") == "violation"]
    if violations:
        return "constraint_violation_unresolved"
    limit = policy["max_candidate_turnover_pct"] if gate == "approved_candidate" else policy["max_watchlist_turnover_pct"]
    if turnover > limit:
        return "turnover_too_high_review_only"
    if gate == "approved_candidate":
        return "constraint_pass_candidate_review"
    return "constraint_pass_watch_only"


def build_rebalance_drafts(current: Dict[str, float], policy: Dict[str, float], rebalance: Dict[str, Any]) -> List[Dict[str, Any]]:
    drafts: List[Dict[str, Any]] = []
    inputs = []
    for d in rebalance.get("approved_candidates", []) or []:
        if isinstance(d, dict):
            inputs.append((d, "approved_candidate"))
    for d in rebalance.get("watchlist_drafts", []) or []:
        if isinstance(d, dict):
            inputs.append((d, "watch_review_only"))

    for draft, gate in inputs:
        raw = apply_material_adjustments(current, draft)
        adjusted, actions = apply_constraints(raw, policy)
        flags = constraint_flags(adjusted, policy)
        turn = turnover_pct(current, adjusted)
        status = status_after_constraints(flags, turn, gate, policy)
        drafts.append({
            "draft_id": f"v2_3_{draft.get('proposal_id')}",
            "source": "v2.1_rebalance_candidate_generator",
            "source_proposal_id": draft.get("proposal_id"),
            "source_model_id": draft.get("source_model_id"),
            "gate": gate,
            "constraint_status": status,
            "execution_permission": False,
            "not_trade_order": True,
            "requires_manual_approval": True,
            "raw_proposal_exposure": exposure(raw),
            "constraint_aware_exposure": exposure(adjusted),
            "constraint_flags_after_adjustment": flags,
            "constraint_actions": actions,
            "turnover_vs_current_pct": turn,
            "top_constraint_aware_adjustments": top_adjustments(current, adjusted),
            "weights_pct": {k: round(v * 100.0, 3) for k, v in sorted(adjusted.items())},
        })
    return drafts


def risk_reduction_constraint_drafts(current: Dict[str, float], policy: Dict[str, float], risk_reduction: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for sim in (risk_reduction.get("simulations", []) or [])[:8]:
        if not isinstance(sim, dict):
            continue
        if sim.get("verdict") not in {"risk_reduction_candidate", "tradeoff_review"}:
            continue
        weights = dict(current)
        ticker = str(sim.get("target_ticker") or "")
        trimmed = (safe_float(sim.get("trimmed_weight_pct"), 0.0) or 0.0) / 100.0
        if ticker and trimmed > 0:
            weights[ticker] = max(0.0, weights.get(ticker, 0.0) - trimmed)
            weights[CASH_TICKER] = weights.get(CASH_TICKER, 0.0) + trimmed
        weights = normalize(weights)
        adjusted, actions = apply_constraints(weights, policy)
        flags = constraint_flags(adjusted, policy)
        turn = turnover_pct(current, adjusted)
        out.append({
            "draft_id": f"v2_3_from_{sim.get('simulation_id')}",
            "source": "v2.2_risk_reduction_simulator",
            "source_simulation_id": sim.get("simulation_id"),
            "source_verdict": sim.get("verdict"),
            "constraint_status": status_after_constraints(flags, turn, "watch_review_only", policy),
            "execution_permission": False,
            "not_trade_order": True,
            "requires_manual_approval": True,
            "risk_reduction_score": sim.get("risk_reduction_score"),
            "risk_reduction_improvement": sim.get("improvement_vs_current"),
            "constraint_aware_exposure": exposure(adjusted),
            "constraint_flags_after_adjustment": flags,
            "constraint_actions": actions,
            "turnover_vs_current_pct": turn,
            "top_constraint_aware_adjustments": top_adjustments(current, adjusted),
            "weights_pct": {k: round(v * 100.0, 3) for k, v in sorted(adjusted.items())},
        })
    return out


def build() -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    decision = load_json(DECISION_CENTER)
    rebalance = load_json(REBALANCE)
    risk_reduction = load_json(RISK_REDUCTION)
    policy = build_policy(decision)
    current = current_weights_from_skfolio()

    rebalance_drafts = build_rebalance_drafts(current, policy, rebalance) if current else []
    risk_drafts = risk_reduction_constraint_drafts(current, policy, risk_reduction) if current else []
    all_drafts = rebalance_drafts + risk_drafts
    pass_count = sum(1 for d in all_drafts if str(d.get("constraint_status", "")).startswith("constraint_pass"))
    unresolved_count = sum(1 for d in all_drafts if d.get("constraint_status") == "constraint_violation_unresolved")
    high_turnover_count = sum(1 for d in all_drafts if d.get("constraint_status") == "turnover_too_high_review_only")

    payload = {
        "version": VERSION,
        "status": "OK" if current else "MISSING_CURRENT_WEIGHTS",
        "generated_at": now_utc(),
        "mode": "constraint_aware_rebalance_sandbox",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "source_files": {
            "rebalance_candidates": str(REBALANCE),
            "risk_reduction_simulator": str(RISK_REDUCTION),
            "decision_center": str(DECISION_CENTER),
            "skfolio": str(SKFOLIO),
        },
        "policy": policy,
        "baseline": {
            "weights_pct": {k: round(v * 100.0, 3) for k, v in sorted(current.items())},
            "exposure": exposure(current) if current else {},
            "constraint_flags": constraint_flags(current, policy) if current else [],
        },
        "constraint_aware_rebalance_drafts": rebalance_drafts,
        "constraint_aware_risk_reduction_drafts": risk_drafts,
        "summary": {
            "total_draft_count": len(all_drafts),
            "rebalance_draft_count": len(rebalance_drafts),
            "risk_reduction_draft_count": len(risk_drafts),
            "constraint_pass_count": pass_count,
            "unresolved_violation_count": unresolved_count,
            "high_turnover_review_count": high_turnover_count,
            "execution_permission_count": 0,
            "human_approval_required": True,
            "verdict": "有通過約束的觀察草案，但仍不得執行；下一步才是 Human Approval Layer。" if pass_count else "沒有通過約束的草案；保留為研究輸出。",
        },
        "warnings": [
            "v2.3 is not an execution engine and never grants execution_permission.",
            "Constraint repair rules are heuristic and conservative; real-world tax, spread, unit size and liquidity constraints are not fully modeled.",
            "Soft gold target is a review nudge, not a mandatory allocation command.",
        ],
    }
    return payload


def write_md(payload: Dict[str, Any]) -> str:
    s = payload.get("summary", {}) or {}
    lines = [
        "# Constraint-Aware Rebalance Sandbox v2.3",
        "",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Safety Boundary",
        "",
        "- This is not a BUY / SELL list.",
        "- execution_permission is always false in v2.3.",
        "- No Supabase write.",
        "- No official portfolio weight update.",
        "- Human approval is mandatory before any real-world action.",
        "",
        "## Summary",
        "",
        f"- Total draft count: `{s.get('total_draft_count')}`",
        f"- Rebalance draft count: `{s.get('rebalance_draft_count')}`",
        f"- Risk-reduction draft count: `{s.get('risk_reduction_draft_count')}`",
        f"- Constraint pass count: `{s.get('constraint_pass_count')}`",
        f"- High-turnover review count: `{s.get('high_turnover_review_count')}`",
        f"- Verdict: {s.get('verdict')}",
        "",
        "## Drafts",
        "",
        "| Draft | Source | Status | Turnover | Cash | Crypto | Taiwan | Gold | Top adjustments |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    drafts = (payload.get("constraint_aware_rebalance_drafts") or []) + (payload.get("constraint_aware_risk_reduction_drafts") or [])
    for d in drafts:
        exp = d.get("constraint_aware_exposure", {}) or {}
        top = "; ".join(
            f"{r.get('ticker')} {r.get('direction')} {r.get('delta_pct')}pp"
            for r in (d.get("top_constraint_aware_adjustments") or [])[:5]
        ) or "-"
        lines.append(
            f"| `{d.get('draft_id')}` | {d.get('source')} | `{d.get('constraint_status')}` | "
            f"{d.get('turnover_vs_current_pct')}% | {exp.get('cash_pct')}% | {exp.get('crypto_pct')}% | "
            f"{exp.get('taiwan_pct')}% | {exp.get('gold_pct')}% | {top} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(write_md(payload), encoding="utf-8")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Total drafts: {payload['summary']['total_draft_count']}")
    print(f"Constraint pass: {payload['summary']['constraint_pass_count']}")


if __name__ == "__main__":
    main()
