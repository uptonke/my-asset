#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

OUT_DIR = Path("data/optimizer")
REGIME = OUT_DIR / "regime_aware_optimizer_latest.json"
SKFOLIO = OUT_DIR / "skfolio_sandbox_latest.json"
JSON_OUT = OUT_DIR / "black_litterman_sandbox_latest.json"
MD_OUT = OUT_DIR / "black_litterman_sandbox_summary.md"
VERSION = "v3.1"
CASH_TICKER = "BOXX"
GOLD_TICKER = "GLDM"

SAFE_MODE_NOTE = (
    "v3.1 Bayesian / Black-Litterman Sandbox 使用 rules-based view engine，避免主觀 views 任意輸入；"
    "此版本是 posterior tilt proxy，不是正式 Black-Litterman 交易模型，不產生 BUY / SELL 指令，"
    "不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。"
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


def normalize_pct(weights_pct: Dict[str, Any]) -> Dict[str, float]:
    clean = {str(k): max(0.0, safe_float(v, 0.0) or 0.0) for k, v in (weights_pct or {}).items() if str(k)}
    total = sum(clean.values())
    if total <= 0:
        return {}
    return {k: v / total * 100.0 for k, v in clean.items()}


def ticker_bucket(ticker: str) -> str:
    t = str(ticker or "").upper()
    if t == CASH_TICKER or "CASH" in t:
        return "cash"
    if t in {"GLDM", "GLD", "IAU"} or "GOLD" in t:
        return "gold"
    if t in {"BTC-USD", "ETH-USD"} or "BTC" in t or "ETH" in t:
        return "crypto"
    if t in {"00981A", "2330"} or t.startswith("00") or t.isdigit():
        return "taiwan_tech"
    if t == "QQQ":
        return "us_tech"
    if t in {"GRID", "IFRA", "SRVR", "PICK"}:
        return "theme_etf"
    return "other"


def weights_from_current(skfolio: Dict[str, Any]) -> Dict[str, float]:
    cur = ((skfolio.get("portfolios") or {}).get("current_weight") or {}) if isinstance(skfolio, dict) else {}
    rows = cur.get("weights") or []
    out: Dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip()
        if ticker:
            out[ticker] = safe_float(row.get("weight_pct"), 0.0) or 0.0
    return normalize_pct(out)


def exposure(weights: Dict[str, float]) -> Dict[str, float]:
    out = {"cash": 0.0, "gold": 0.0, "crypto": 0.0, "taiwan_tech": 0.0, "us_tech": 0.0, "theme_etf": 0.0, "other": 0.0}
    for ticker, weight in normalize_pct(weights).items():
        b = ticker_bucket(ticker)
        out[b if b in out else "other"] += weight
    return {k: round(v, 3) for k, v in out.items()}


def build_views(regime_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    regime = ((regime_payload.get("regime") or {}).get("selected_regime")) or "neutral_growth"
    confidence = safe_float((regime_payload.get("regime") or {}).get("confidence"), 0.5) or 0.5
    budget = ((regime_payload.get("active_policy") or {}).get("risk_budget_pct") or {})
    views: List[Dict[str, Any]] = []

    def add(bucket: str, direction: str, magnitude_pct: float, rationale: str, conf_adj: float = 0.0) -> None:
        views.append({
            "view_id": f"v3_1_{bucket}_{direction}",
            "bucket": bucket,
            "direction": direction,
            "magnitude_pct": round(float(magnitude_pct), 3),
            "confidence": round(max(0.25, min(0.85, confidence + conf_adj)), 3),
            "rationale": rationale,
            "source": "rules_based_regime_view_engine",
        })

    if regime == "risk_off_liquidity_pressure":
        add("cash", "overweight", 2.5, "Risk-off regime raises liquidity buffer.", 0.05)
        add("crypto", "underweight", 2.0, "Crypto tail risk is penalized under liquidity pressure.", 0.05)
        add("us_tech", "underweight", 1.0, "High-duration tech is stress-sensitive.", 0.0)
        add("gold", "overweight", 0.8, "Small hedge allocation; not treated as guaranteed hedge.", -0.05)
    elif regime == "inflation_rate_hike_pressure":
        add("gold", "overweight", 1.0, "Inflation/rate-hike regime allows modest gold tilt.", 0.0)
        add("us_tech", "underweight", 1.2, "Rate pressure penalizes duration-heavy growth exposure.", 0.05)
        add("crypto", "underweight", 1.0, "Liquidity-sensitive crypto exposure capped.", 0.0)
        add("cash", "overweight", 1.0, "Cash floor raised for optionality.", 0.0)
    elif regime == "crypto_specific_stress":
        add("crypto", "underweight", 3.0, "Crypto-specific stress dominates current regime inference.", 0.1)
        add("cash", "overweight", 1.5, "Trimmed crypto risk is parked in cash proxy.", 0.0)
    elif regime == "taiwan_tech_concentration":
        add("taiwan_tech", "underweight", 2.0, "Taiwan tech concentration risk is elevated.", 0.05)
        add("cash", "overweight", 1.0, "Cash buffer absorbs concentration trim.", 0.0)
        add("gold", "overweight", 0.7, "Small diversifier tilt; not a hard hedge claim.", -0.05)
    else:
        add("cash", "neutral_to_slight_overweight", 0.5, "Neutral baseline keeps a small liquidity preference.", -0.1)
        add("gold", "neutral_to_slight_overweight", 0.5, "Soft target only; low-conviction view.", -0.1)

    # Attach budget references if available.
    for v in views:
        b = v["bucket"]
        ref = None
        if b == "cash": ref = budget.get("cash_min")
        if b == "gold": ref = budget.get("gold_target")
        if b == "crypto": ref = budget.get("crypto_max")
        if b == "taiwan_tech": ref = budget.get("taiwan_tech_max")
        if b == "us_tech": ref = budget.get("us_tech_max")
        if ref is not None:
            v["risk_budget_reference_pct"] = ref
    return views


def apply_views(prior: Dict[str, float], views: List[Dict[str, Any]], global_view_weight: float = 0.35) -> Dict[str, float]:
    w = normalize_pct(prior)
    if not w:
        return {}
    for view in views:
        bucket = str(view.get("bucket") or "")
        direction = str(view.get("direction") or "")
        magnitude = safe_float(view.get("magnitude_pct"), 0.0) or 0.0
        conf = safe_float(view.get("confidence"), 0.5) or 0.5
        step = magnitude * global_view_weight * conf
        keys = [k for k in w if ticker_bucket(k) == bucket and w.get(k, 0.0) > 0]
        if direction.startswith("under") and keys and step > 0:
            pool = sum(w[k] for k in keys)
            cut_total = min(step, pool)
            for k in keys:
                cut = cut_total * (w[k] / pool)
                w[k] = max(0.0, w[k] - cut)
            w[CASH_TICKER] = w.get(CASH_TICKER, 0.0) + cut_total
        elif direction.startswith("over") or direction.startswith("neutral_to_slight"):
            # Fund overweight from largest non-cash/non-target risk asset.
            target_keys = [k for k in w if ticker_bucket(k) == bucket]
            target = target_keys[0] if target_keys else (GOLD_TICKER if bucket == "gold" else CASH_TICKER if bucket == "cash" else None)
            if not target:
                continue
            candidates = [(k, v) for k, v in w.items() if ticker_bucket(k) not in {"cash", "gold", bucket} and v > 0]
            if not candidates:
                candidates = [(k, v) for k, v in w.items() if k != target and v > 0]
            if not candidates:
                continue
            source, src_w = max(candidates, key=lambda x: x[1])
            move = min(step, src_w)
            w[source] = max(0.0, src_w - move)
            w[target] = w.get(target, 0.0) + move
        w = normalize_pct(w)
    return w


def turnover(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = set(a) | set(b)
    return round(sum(abs((a.get(k, 0.0) or 0.0) - (b.get(k, 0.0) or 0.0)) for k in keys) / 2.0, 3)


def top_adjustments(base: Dict[str, float], target: Dict[str, float], limit: int = 12) -> List[Dict[str, Any]]:
    rows = []
    for k in sorted(set(base) | set(target)):
        cur = base.get(k, 0.0) or 0.0
        tgt = target.get(k, 0.0) or 0.0
        delta = tgt - cur
        if abs(delta) < 0.05:
            continue
        rows.append({
            "ticker": k,
            "prior_weight_pct": round(cur, 3),
            "posterior_weight_pct": round(tgt, 3),
            "delta_pct": round(delta, 3),
            "direction": "UP" if delta > 0 else "DOWN",
        })
    rows.sort(key=lambda x: abs(x["delta_pct"]), reverse=True)
    return rows[:limit]


def build_posterior_candidates(regime_payload: Dict[str, Any], views: List[Dict[str, Any]], prior: Dict[str, float]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    # Main posterior from current portfolio prior.
    posterior = apply_views(prior, views)
    if posterior:
        candidates.append({
            "candidate_id": "v3_1_current_prior_posterior_tilt",
            "prior_source": "current_weight",
            "posterior_method": "rules_based_bl_tilt_proxy",
            "view_count": len(views),
            "turnover_vs_prior_pct": turnover(prior, posterior),
            "prior_exposure": exposure(prior),
            "posterior_exposure": exposure(posterior),
            "top_posterior_adjustments": top_adjustments(prior, posterior),
            "posterior_weights_pct": {k: round(v, 3) for k, v in sorted(posterior.items())},
            "execution_permission": False,
            "not_trade_order": True,
            "requires_manual_approval": True,
            "model_status": "watch_only_bl_proxy_requires_review",
        })
    # Also generate a posterior from the top v3.0 regime-aware draft if available.
    drafts = regime_payload.get("regime_aware_drafts") or []
    for d in drafts[:1]:
        w = normalize_pct(d.get("weights_pct") or {})
        if not w:
            continue
        post = apply_views(w, views, global_view_weight=0.20)
        candidates.append({
            "candidate_id": f"v3_1_{d.get('draft_id')}_posterior_tilt",
            "prior_source": d.get("draft_id"),
            "posterior_method": "rules_based_bl_tilt_proxy_on_regime_draft",
            "view_count": len(views),
            "turnover_vs_prior_pct": turnover(w, post),
            "turnover_vs_current_pct": turnover(prior, post) if prior else None,
            "prior_exposure": exposure(w),
            "posterior_exposure": exposure(post),
            "top_posterior_adjustments": top_adjustments(w, post),
            "posterior_weights_pct": {k: round(v, 3) for k, v in sorted(post.items())},
            "execution_permission": False,
            "not_trade_order": True,
            "requires_manual_approval": True,
            "model_status": "watch_only_bl_proxy_requires_review",
        })
    return candidates


def write_markdown(payload: Dict[str, Any]) -> None:
    s = payload.get("summary") or {}
    engine = payload.get("view_engine") or {}
    views = payload.get("views") or []
    candidates = payload.get("posterior_candidates") or []
    lines = [
        "# Bayesian / Black-Litterman Sandbox v3.1",
        "",
        f"Generated: `{payload.get('generated_at')}`",
        "",
        "## Safety boundary",
        "",
        "- Rules-based view engine only; no arbitrary subjective views.",
        "- Posterior tilt is a proxy sandbox, not a production Black-Litterman optimizer.",
        "- 不是 BUY / SELL 指令，不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。",
        "",
        "## Summary",
        "",
        f"- Regime: `{payload.get('selected_regime')}`",
        f"- View engine status: `{engine.get('status')}`",
        f"- Views: {s.get('view_count', 0)}",
        f"- Posterior candidates: {s.get('posterior_candidate_count', 0)}",
        "",
        "## Views",
        "",
    ]
    for v in views:
        lines.extend([
            f"- `{v.get('bucket')}` {v.get('direction')} `{v.get('magnitude_pct')}`pp, confidence `{v.get('confidence')}` — {v.get('rationale')}",
        ])
    lines.extend(["", "## Posterior candidates", ""])
    for c in candidates:
        lines.extend([
            f"### {c.get('candidate_id')}",
            "",
            f"- Prior: `{c.get('prior_source')}`",
            f"- Method: `{c.get('posterior_method')}`",
            f"- Turnover vs prior: `{c.get('turnover_vs_prior_pct')}`%",
            f"- Status: `{c.get('model_status')}`",
            "",
        ])
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = now_utc()
    regime_payload = load_json(REGIME)
    skfolio = load_json(SKFOLIO)
    prior = weights_from_current(skfolio)
    views = build_views(regime_payload)
    candidates = build_posterior_candidates(regime_payload, views, prior)
    selected_regime = ((regime_payload.get("regime") or {}).get("selected_regime")) or "unknown"
    payload = {
        "version": VERSION,
        "status": "OK" if candidates else "NO_POSTERIOR_CANDIDATES",
        "generated_at": generated_at,
        "mode": "bayesian_black_litterman_sandbox",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "source_files": {
            "regime_aware_optimizer": str(REGIME),
            "skfolio": str(SKFOLIO),
        },
        "selected_regime": selected_regime,
        "view_engine": {
            "status": "rules_based_stable" if views else "no_views_generated",
            "subjective_views_allowed": False,
            "manual_view_input_allowed": False,
            "view_source": "v3.0 regime policy + deterministic rulebook",
            "reason": "避免 Black-Litterman views 變成任意主觀輸入；v3.1 只接受可重現的 regime-derived views。",
        },
        "bayesian_policy": {
            "method": "posterior_tilt_proxy",
            "prior": "current portfolio + optional top v3.0 regime draft",
            "tau": "not_estimated_in_proxy_version",
            "omega": "derived_from_rule_confidence_proxy",
            "expected_return_model": "disabled",
            "execution_permission_default": False,
            "not_trade_order": True,
        },
        "views": views,
        "summary": {
            "view_count": len(views),
            "posterior_candidate_count": len(candidates),
            "execution_permission_true": sum(1 for c in candidates if c.get("execution_permission") is True),
        },
        "posterior_candidates": candidates,
        "warnings": [
            "This is a Black-Litterman-style sandbox/proxy, not a production BL optimizer.",
            "Expected return model is disabled; no max-Sharpe / alpha model is introduced.",
            "All posterior candidates require manual review and are not trade orders.",
        ],
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload)
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Views: {len(views)}")
    print(f"Posterior candidates: {len(candidates)}")


if __name__ == "__main__":
    main()
