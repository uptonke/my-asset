#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

OUT_DIR = Path("data/optimizer")
SKFOLIO = OUT_DIR / "skfolio_sandbox_latest.json"
RISKFOLIO = OUT_DIR / "riskfolio_sandbox_latest.json"
STRESS = OUT_DIR / "optimizer_stress_latest.json"
ROBUSTNESS = OUT_DIR / "optimizer_robustness_latest.json"
CONSTRAINT = OUT_DIR / "constraint_aware_rebalance_latest.json"
DECISION = OUT_DIR / "decision_center_latest.json"
JSON_OUT = OUT_DIR / "regime_aware_optimizer_latest.json"
MD_OUT = OUT_DIR / "regime_aware_optimizer_summary.md"

VERSION = "v3.0"
CASH_TICKER = "BOXX"
GOLD_TICKER = "GLDM"

SAFE_MODE_NOTE = (
    "v3.0 Regime-Aware Optimizer 只根據本地 optimizer / stress / robustness outputs 建立 regime-aware "
    "covariance policy、constraint policy、risk budget 與草案分級；不產生 BUY / SELL 指令，不自動交易，"
    "不寫入 Supabase，不修改正式持倉或正式權重。"
)

BASELINE_POLICY = {
    "max_single_weight_pct": 25.0,
    "max_crypto_weight_pct": 15.0,
    "max_taiwan_weight_pct": 30.0,
    "min_cash_weight_pct": 8.0,
    "soft_gold_target_pct": 5.0,
    "max_watchlist_turnover_pct": 8.0,
    "max_candidate_turnover_pct": 15.0,
}

REGIME_POLICIES: Dict[str, Dict[str, Any]] = {
    "risk_off_liquidity_pressure": {
        "label": "Risk-off liquidity pressure",
        "covariance_policy": {
            "mode": "stress_weighted_short_window_proxy",
            "preferred_windows": ["6M", "1Y"],
            "shrinkage_intensity_proxy": "high",
            "stress_scenarios_weighted": ["risk_off_usd_squeeze", "rate_hike_2022_like"],
            "note": "缺完整 covariance matrix 時，v3.0 只切換 covariance policy，不假裝已重估精確共變異數。",
        },
        "constraint_policy": {
            "max_single_weight_pct": 20.0,
            "max_crypto_weight_pct": 10.0,
            "max_taiwan_weight_pct": 25.0,
            "min_cash_weight_pct": 12.0,
            "soft_gold_target_pct": 5.0,
            "max_watchlist_turnover_pct": 8.0,
            "max_candidate_turnover_pct": 12.0,
        },
        "risk_budget_pct": {
            "cash_min": 12.0,
            "gold_target": 5.0,
            "crypto_max": 8.0,
            "taiwan_tech_max": 20.0,
            "us_tech_max": 18.0,
            "theme_etf_max": 18.0,
        },
    },
    "inflation_rate_hike_pressure": {
        "label": "Inflation / rate-hike pressure",
        "covariance_policy": {
            "mode": "rate_hike_stress_weighted_proxy",
            "preferred_windows": ["1Y", "FULL_STRICT"],
            "shrinkage_intensity_proxy": "medium_high",
            "stress_scenarios_weighted": ["rate_hike_2022_like", "gold_hedge_failure"],
            "note": "重點是避免對長久期科技與加密風險低估。",
        },
        "constraint_policy": {
            "max_single_weight_pct": 22.0,
            "max_crypto_weight_pct": 12.0,
            "max_taiwan_weight_pct": 25.0,
            "min_cash_weight_pct": 10.0,
            "soft_gold_target_pct": 6.0,
            "max_watchlist_turnover_pct": 8.0,
            "max_candidate_turnover_pct": 13.0,
        },
        "risk_budget_pct": {
            "cash_min": 10.0,
            "gold_target": 6.0,
            "crypto_max": 10.0,
            "taiwan_tech_max": 22.0,
            "us_tech_max": 18.0,
            "theme_etf_max": 20.0,
        },
    },
    "crypto_specific_stress": {
        "label": "Crypto-specific stress",
        "covariance_policy": {
            "mode": "crypto_tail_stress_proxy",
            "preferred_windows": ["6M", "1Y"],
            "shrinkage_intensity_proxy": "high_for_crypto_bucket",
            "stress_scenarios_weighted": ["crypto_crash", "risk_off_usd_squeeze"],
            "note": "針對 crypto tail risk 加權，不把低相關視為穩定避險。",
        },
        "constraint_policy": {
            "max_single_weight_pct": 22.0,
            "max_crypto_weight_pct": 8.0,
            "max_taiwan_weight_pct": 30.0,
            "min_cash_weight_pct": 10.0,
            "soft_gold_target_pct": 5.0,
            "max_watchlist_turnover_pct": 8.0,
            "max_candidate_turnover_pct": 12.0,
        },
        "risk_budget_pct": {
            "cash_min": 10.0,
            "gold_target": 5.0,
            "crypto_max": 7.0,
            "taiwan_tech_max": 25.0,
            "us_tech_max": 20.0,
            "theme_etf_max": 20.0,
        },
    },
    "taiwan_tech_concentration": {
        "label": "Taiwan tech concentration",
        "covariance_policy": {
            "mode": "taiwan_tech_stress_proxy",
            "preferred_windows": ["1Y", "FULL_STRICT"],
            "shrinkage_intensity_proxy": "medium_high_for_taiwan_bucket",
            "stress_scenarios_weighted": ["taiwan_tech_correction", "risk_off_usd_squeeze"],
            "note": "避免台股科技與美股科技在壓力時同向下跌被低估。",
        },
        "constraint_policy": {
            "max_single_weight_pct": 22.0,
            "max_crypto_weight_pct": 12.0,
            "max_taiwan_weight_pct": 22.0,
            "min_cash_weight_pct": 10.0,
            "soft_gold_target_pct": 5.0,
            "max_watchlist_turnover_pct": 8.0,
            "max_candidate_turnover_pct": 12.0,
        },
        "risk_budget_pct": {
            "cash_min": 10.0,
            "gold_target": 5.0,
            "crypto_max": 10.0,
            "taiwan_tech_max": 18.0,
            "us_tech_max": 20.0,
            "theme_etf_max": 20.0,
        },
    },
    "neutral_growth": {
        "label": "Neutral / growth baseline",
        "covariance_policy": {
            "mode": "full_strict_baseline_proxy",
            "preferred_windows": ["FULL_STRICT", "2Y", "1Y"],
            "shrinkage_intensity_proxy": "medium",
            "stress_scenarios_weighted": [],
            "note": "未偵測明確壓力 regime 時，維持 v2.3 基準約束。",
        },
        "constraint_policy": BASELINE_POLICY,
        "risk_budget_pct": {
            "cash_min": 8.0,
            "gold_target": 5.0,
            "crypto_max": 12.0,
            "taiwan_tech_max": 25.0,
            "us_tech_max": 22.0,
            "theme_etf_max": 22.0,
        },
    },
}


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
    if t == CASH_TICKER or "CASH" in t:
        return "cash"
    if t in {"GLDM", "GLD", "IAU"} or "GOLD" in t:
        return "gold"
    if t in {"BTC-USD", "ETH-USD"} or "BTC" in t or "ETH" in t:
        return "crypto"
    if t in {"00981A", "2330"} or t.startswith("00") or t.isdigit():
        return "taiwan_tech"
    if t in {"QQQ"}:
        return "us_tech"
    if t in {"GRID", "IFRA", "SRVR", "PICK"}:
        return "theme_etf"
    if t in {"VOO", "USMV", "AVUV", "VEA", "VNM"}:
        return "diversified_equity"
    return "other_risk"


def normalize_pct(weights_pct: Dict[str, Any]) -> Dict[str, float]:
    clean = {str(k): max(0.0, safe_float(v, 0.0) or 0.0) for k, v in (weights_pct or {}).items() if str(k)}
    total = sum(clean.values())
    if total <= 0:
        return {}
    return {k: v / total * 100.0 for k, v in clean.items()}


def weights_from_portfolio(port: Dict[str, Any]) -> Dict[str, float]:
    if isinstance(port.get("weights_pct"), dict):
        return normalize_pct(port.get("weights_pct") or {})
    rows = port.get("weights") or []
    out: Dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip()
        if not ticker:
            continue
        out[ticker] = safe_float(row.get("weight_pct"), 0.0) or 0.0
    return normalize_pct(out)


def current_weights() -> Dict[str, float]:
    sk = load_json(SKFOLIO)
    cur = ((sk.get("portfolios") or {}).get("current_weight") or {}) if isinstance(sk, dict) else {}
    w = weights_from_portfolio(cur)
    if w:
        return w
    rf = load_json(RISKFOLIO)
    cur = ((rf.get("portfolios") or {}).get("current_weight") or {}) if isinstance(rf, dict) else {}
    return weights_from_portfolio(cur)


def exposure(weights_pct: Dict[str, float]) -> Dict[str, Any]:
    w = normalize_pct(weights_pct)
    out = {"cash_pct": 0.0, "gold_pct": 0.0, "crypto_pct": 0.0, "taiwan_tech_pct": 0.0, "us_tech_pct": 0.0, "theme_etf_pct": 0.0, "other_pct": 0.0}
    max_ticker = None
    max_weight = -1.0
    for ticker, weight in w.items():
        b = ticker_bucket(ticker)
        if b == "cash": out["cash_pct"] += weight
        elif b == "gold": out["gold_pct"] += weight
        elif b == "crypto": out["crypto_pct"] += weight
        elif b == "taiwan_tech": out["taiwan_tech_pct"] += weight
        elif b == "us_tech": out["us_tech_pct"] += weight
        elif b == "theme_etf": out["theme_etf_pct"] += weight
        else: out["other_pct"] += weight
        if weight > max_weight:
            max_ticker, max_weight = ticker, weight
    return {
        **{k: round(v, 3) for k, v in out.items()},
        "max_single_weight_pct": round(max_weight, 3) if max_weight >= 0 else None,
        "max_single_ticker": max_ticker,
    }


def get_current_stress_row(stress: Dict[str, Any]) -> Dict[str, Any]:
    rows = stress.get("comparison_rows") or []
    for row in rows:
        if isinstance(row, dict) and row.get("key") == "current_weight":
            return row
    return rows[0] if rows and isinstance(rows[0], dict) else {}


def scenario_return(row: Dict[str, Any], key: str) -> Optional[float]:
    s = (row.get("scenario_returns") or {}).get(key) or {}
    return safe_float(s.get("return_pct"))


def infer_regime(stress: Dict[str, Any], robust: Dict[str, Any], base_exp: Dict[str, Any]) -> Dict[str, Any]:
    row = get_current_stress_row(stress)
    worst = safe_float(row.get("worst_scenario_return_pct"))
    avg = safe_float(row.get("avg_scenario_return_pct"))
    rate = scenario_return(row, "rate_hike_2022_like")
    crypto = scenario_return(row, "crypto_crash")
    taiwan = scenario_return(row, "taiwan_tech_correction")
    riskoff = scenario_return(row, "risk_off_usd_squeeze")

    scores = {
        "risk_off_liquidity_pressure": 0.0,
        "inflation_rate_hike_pressure": 0.0,
        "crypto_specific_stress": 0.0,
        "taiwan_tech_concentration": 0.0,
        "neutral_growth": 0.1,
    }

    if worst is not None:
        if worst <= -22: scores["risk_off_liquidity_pressure"] += 3
        elif worst <= -18: scores["risk_off_liquidity_pressure"] += 1.5
    if avg is not None and avg <= -16:
        scores["risk_off_liquidity_pressure"] += 1
    if riskoff is not None:
        if riskoff <= -18: scores["risk_off_liquidity_pressure"] += 2
        elif riskoff <= -14: scores["risk_off_liquidity_pressure"] += 1
    if rate is not None:
        if rate <= -20: scores["inflation_rate_hike_pressure"] += 2.5
        elif rate <= -16: scores["inflation_rate_hike_pressure"] += 1
    if crypto is not None:
        if crypto <= -14: scores["crypto_specific_stress"] += 2
        elif crypto <= -10: scores["crypto_specific_stress"] += 1
    if taiwan is not None:
        if taiwan <= -13: scores["taiwan_tech_concentration"] += 2
        elif taiwan <= -10: scores["taiwan_tech_concentration"] += 1

    if (safe_float(base_exp.get("crypto_pct"), 0.0) or 0.0) >= 12:
        scores["crypto_specific_stress"] += 1
    if (safe_float(base_exp.get("taiwan_tech_pct"), 0.0) or 0.0) >= 18:
        scores["taiwan_tech_concentration"] += 1

    selected = max(scores, key=scores.get)
    if scores[selected] < 1.0:
        selected = "neutral_growth"
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    confidence = min(0.95, max(0.35, 0.35 + scores[selected] * 0.12))
    if selected != "neutral_growth" and len(sorted_scores) > 1 and sorted_scores[0][1] - sorted_scores[1][1] < 0.75:
        confidence = min(confidence, 0.62)
    reasons: List[str] = []
    if worst is not None: reasons.append(f"current worst scenario {worst:.2f}%")
    if riskoff is not None: reasons.append(f"risk_off_usd_squeeze {riskoff:.2f}%")
    if rate is not None: reasons.append(f"rate_hike_2022_like {rate:.2f}%")
    if crypto is not None: reasons.append(f"crypto_crash {crypto:.2f}%")
    if taiwan is not None: reasons.append(f"taiwan_tech_correction {taiwan:.2f}%")

    return {
        "selected_regime": selected,
        "selected_regime_label": REGIME_POLICIES[selected]["label"],
        "confidence": round(confidence, 3),
        "scoreboard": {k: round(v, 3) for k, v in scores.items()},
        "evidence": {
            "worst_scenario_return_pct": round_or_none(worst),
            "avg_scenario_return_pct": round_or_none(avg),
            "rate_hike_2022_like_pct": round_or_none(rate),
            "crypto_crash_pct": round_or_none(crypto),
            "taiwan_tech_correction_pct": round_or_none(taiwan),
            "risk_off_usd_squeeze_pct": round_or_none(riskoff),
            "base_exposure": base_exp,
        },
        "reason_codes": reasons,
    }


def trim_bucket(weights_pct: Dict[str, float], bucket: str, target_max_pct: float, actions: List[Dict[str, Any]], reason: str) -> Dict[str, float]:
    w = normalize_pct(weights_pct)
    keys = [k for k, v in w.items() if ticker_bucket(k) == bucket and v > 0]
    total = sum(w[k] for k in keys)
    if total <= target_max_pct + 1e-9:
        return w
    excess = total - target_max_pct
    for k in keys:
        cut = excess * (w[k] / total)
        w[k] = max(0.0, w[k] - cut)
        actions.append({"action": "trim", "ticker": k, "amount_pct": round(cut, 3), "reason": reason})
    w[CASH_TICKER] = w.get(CASH_TICKER, 0.0) + excess
    actions.append({"action": "add", "ticker": CASH_TICKER, "amount_pct": round(excess, 3), "reason": reason})
    return normalize_pct(w)


def trim_largest_to_cash(weights_pct: Dict[str, float], amount_pct: float, actions: List[Dict[str, Any]], reason: str) -> Dict[str, float]:
    w = normalize_pct(weights_pct)
    if amount_pct <= 0:
        return w
    candidates = [(k, v) for k, v in w.items() if ticker_bucket(k) not in {"cash", "gold"} and v > 0]
    if not candidates:
        return w
    k, v = max(candidates, key=lambda x: x[1])
    cut = min(amount_pct, v)
    w[k] = max(0.0, v - cut)
    w[CASH_TICKER] = w.get(CASH_TICKER, 0.0) + cut
    actions.append({"action": "trim", "ticker": k, "amount_pct": round(cut, 3), "reason": reason})
    actions.append({"action": "add", "ticker": CASH_TICKER, "amount_pct": round(cut, 3), "reason": reason})
    return normalize_pct(w)


def apply_regime_budget(weights_pct: Dict[str, float], risk_budget: Dict[str, Any], constraint_policy: Dict[str, Any]) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    w = normalize_pct(weights_pct)
    actions: List[Dict[str, Any]] = []
    w = trim_bucket(w, "crypto", safe_float(risk_budget.get("crypto_max"), 100.0) or 100.0, actions, "regime_crypto_risk_budget")
    w = trim_bucket(w, "taiwan_tech", safe_float(risk_budget.get("taiwan_tech_max"), 100.0) or 100.0, actions, "regime_taiwan_tech_risk_budget")
    w = trim_bucket(w, "us_tech", safe_float(risk_budget.get("us_tech_max"), 100.0) or 100.0, actions, "regime_us_tech_risk_budget")
    w = trim_bucket(w, "theme_etf", safe_float(risk_budget.get("theme_etf_max"), 100.0) or 100.0, actions, "regime_theme_etf_risk_budget")

    exp = exposure(w)
    cash_min = safe_float(risk_budget.get("cash_min"), safe_float(constraint_policy.get("min_cash_weight_pct"), 0.0) or 0.0) or 0.0
    cash_gap = cash_min - (safe_float(exp.get("cash_pct"), 0.0) or 0.0)
    if cash_gap > 1e-9:
        w = trim_largest_to_cash(w, cash_gap, actions, "regime_cash_minimum")

    # Soft gold target: fund max 1pp per run; diagnostic sandbox only.
    exp = exposure(w)
    gold_target = safe_float(risk_budget.get("gold_target"), safe_float(constraint_policy.get("soft_gold_target_pct"), 0.0) or 0.0) or 0.0
    gold_gap = min(1.0, max(0.0, gold_target - (safe_float(exp.get("gold_pct"), 0.0) or 0.0)))
    if gold_gap > 1e-9:
        before_cash = w.get(CASH_TICKER, 0.0)
        w = trim_largest_to_cash(w, gold_gap, actions, "regime_gold_target_source_funding")
        after_cash = w.get(CASH_TICKER, 0.0)
        newly_funded = max(0.0, after_cash - before_cash)
        move = min(gold_gap, newly_funded if newly_funded > 0 else w.get(CASH_TICKER, 0.0))
        if move > 1e-9:
            w[CASH_TICKER] = max(0.0, w.get(CASH_TICKER, 0.0) - move)
            w[GOLD_TICKER] = w.get(GOLD_TICKER, 0.0) + move
            actions.append({"action": "add", "ticker": GOLD_TICKER, "amount_pct": round(move, 3), "reason": "regime_gold_target"})
            actions.append({"action": "fund", "ticker": CASH_TICKER, "amount_pct": round(-move, 3), "reason": "regime_gold_target"})
            w = normalize_pct(w)
    return w, actions


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
            "current_weight_pct": round(cur, 3),
            "regime_weight_pct": round(tgt, 3),
            "delta_pct": round(delta, 3),
            "direction": "UP" if delta > 0 else "DOWN",
        })
    rows.sort(key=lambda x: abs(x["delta_pct"]), reverse=True)
    return rows[:limit]


def collect_source_drafts(constraint_payload: Dict[str, Any], skfolio: Dict[str, Any], riskfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
    drafts: List[Dict[str, Any]] = []
    for key in ["constraint_aware_rebalance_drafts", "constraint_aware_risk_reduction_drafts"]:
        for d in constraint_payload.get(key) or []:
            if isinstance(d, dict) and isinstance(d.get("weights_pct"), dict):
                drafts.append({"source": "v2.3", "source_bucket": key, **d})
    # Fallback if v2.3 is absent: use optimizer portfolios.
    if drafts:
        return drafts
    for source_name, payload in [("skfolio", skfolio), ("riskfolio", riskfolio)]:
        for key, port in (payload.get("portfolios") or {}).items():
            if key == "current_weight" or not isinstance(port, dict):
                continue
            w = weights_from_portfolio(port)
            if w:
                drafts.append({
                    "draft_id": f"v3_0_source_{key}",
                    "source": source_name,
                    "source_model_id": key,
                    "constraint_status": "source_optimizer_no_v2_3_constraints",
                    "turnover_vs_current_pct": port.get("turnover_vs_current_pct"),
                    "weights_pct": w,
                })
    return drafts


def score_draft(draft: Dict[str, Any], adjusted_weights: Dict[str, float], base_weights: Dict[str, float], actions: List[Dict[str, Any]], selected_regime: str, policy: Dict[str, Any]) -> Dict[str, Any]:
    exp = exposure(adjusted_weights)
    turnover_pct = turnover(base_weights, adjusted_weights)
    max_turnover = safe_float((policy.get("constraint_policy") or {}).get("max_candidate_turnover_pct"), 12.0) or 12.0
    reason_codes: List[str] = ["regime_policy_applied", selected_regime, "manual_approval_required", "not_trade_order"]
    if actions:
        reason_codes.append("regime_budget_adjusted")
    if turnover_pct > max_turnover:
        status = "regime_watch_high_turnover"
        reason_codes.append("high_turnover_review_required")
    else:
        status = "regime_watch_review_required"
    if (safe_float(exp.get("cash_pct"), 0.0) or 0.0) < (safe_float((policy.get("risk_budget_pct") or {}).get("cash_min"), 0.0) or 0.0) - 1e-9:
        status = "regime_reject_cash_budget_failed"
        reason_codes.append("cash_budget_failed")
    return {
        "draft_id": f"v3_0_{draft.get('draft_id') or draft.get('source_model_id') or 'candidate'}",
        "source_draft_id": draft.get("draft_id") or draft.get("source_model_id"),
        "source": draft.get("source"),
        "source_bucket": draft.get("source_bucket"),
        "selected_regime": selected_regime,
        "model_status": status,
        "execution_permission": False,
        "not_trade_order": True,
        "requires_manual_approval": True,
        "turnover_vs_current_pct": turnover_pct,
        "exposure": exp,
        "regime_actions": actions,
        "reason_codes": reason_codes,
        "top_regime_adjustments": top_adjustments(base_weights, adjusted_weights),
        "weights_pct": {k: round(v, 3) for k, v in sorted(adjusted_weights.items())},
    }


def write_markdown(payload: Dict[str, Any]) -> None:
    s = payload.get("summary") or {}
    regime = payload.get("regime") or {}
    policy = payload.get("active_policy") or {}
    drafts = payload.get("regime_aware_drafts") or []
    lines = [
        "# Regime-Aware Optimizer v3.0",
        "",
        f"Generated: `{payload.get('generated_at')}`",
        "",
        "## Safety boundary",
        "",
        "- 只做 regime-aware 決策支援與研究草案。",
        "- 不是 BUY / SELL 指令。",
        "- 不自動交易、不寫入 Supabase、不修改正式持倉或正式權重。",
        "",
        "## Regime",
        "",
        f"- Selected regime: `{regime.get('selected_regime')}`",
        f"- Label: {regime.get('selected_regime_label')}",
        f"- Confidence: `{regime.get('confidence')}`",
        f"- Covariance policy: `{(policy.get('covariance_policy') or {}).get('mode')}`",
        f"- Drafts: {s.get('draft_count', 0)}",
        f"- High-turnover review: {s.get('high_turnover_review', 0)}",
        "",
        "## Active risk budget",
        "",
    ]
    for k, v in (policy.get("risk_budget_pct") or {}).items():
        lines.append(f"- {k}: `{v}`%")
    lines.extend(["", "## Top drafts", ""])
    for d in drafts[:20]:
        lines.extend([
            f"### {d.get('draft_id')}",
            "",
            f"- Source: `{d.get('source_draft_id')}`",
            f"- Status: `{d.get('model_status')}`",
            f"- Turnover vs current: `{d.get('turnover_vs_current_pct')}`%",
            f"- Cash / Crypto / Taiwan tech: `{(d.get('exposure') or {}).get('cash_pct')}` / `{(d.get('exposure') or {}).get('crypto_pct')}` / `{(d.get('exposure') or {}).get('taiwan_tech_pct')}`%",
            f"- Reason codes: `{', '.join(d.get('reason_codes') or [])}`",
            "",
        ])
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = now_utc()
    skfolio = load_json(SKFOLIO)
    riskfolio = load_json(RISKFOLIO)
    stress = load_json(STRESS)
    robust = load_json(ROBUSTNESS)
    constraint_payload = load_json(CONSTRAINT)
    decision = load_json(DECISION)
    base_w = current_weights()
    base_exp = exposure(base_w)
    regime = infer_regime(stress, robust, base_exp)
    selected = regime["selected_regime"]
    active_policy = REGIME_POLICIES[selected]
    drafts = collect_source_drafts(constraint_payload, skfolio, riskfolio)
    out_drafts: List[Dict[str, Any]] = []
    for d in drafts:
        raw_w = normalize_pct(d.get("weights_pct") or weights_from_portfolio(d))
        if not raw_w:
            continue
        adj_w, actions = apply_regime_budget(raw_w, active_policy.get("risk_budget_pct") or {}, active_policy.get("constraint_policy") or {})
        out_drafts.append(score_draft(d, adj_w, base_w, actions, selected, active_policy))
    out_drafts.sort(key=lambda x: ("high_turnover" in x.get("model_status", ""), x.get("turnover_vs_current_pct") or 999))
    summary = {
        "draft_count": len(out_drafts),
        "regime_watch_review_required": sum(1 for d in out_drafts if d.get("model_status") == "regime_watch_review_required"),
        "high_turnover_review": sum(1 for d in out_drafts if "high_turnover" in str(d.get("model_status"))),
        "execution_permission_true": sum(1 for d in out_drafts if d.get("execution_permission") is True),
    }
    payload = {
        "version": VERSION,
        "status": "OK" if out_drafts else "NO_DRAFTS",
        "generated_at": generated_at,
        "mode": "regime_aware_optimizer",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "source_files": {
            "skfolio": str(SKFOLIO),
            "riskfolio": str(RISKFOLIO),
            "optimizer_stress": str(STRESS),
            "optimizer_robustness": str(ROBUSTNESS),
            "constraint_aware_rebalance": str(CONSTRAINT),
            "decision_center": str(DECISION),
        },
        "regime": regime,
        "active_policy": active_policy,
        "baseline_exposure": base_exp,
        "summary": summary,
        "regime_aware_drafts": out_drafts,
        "warnings": [
            "v3.0 uses local stress/optimizer outputs only; no live macro data is fetched.",
            "Covariance switching is represented as a policy layer/proxy unless upstream covariance matrices are available.",
            "All drafts require manual approval and are not trade orders.",
        ],
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload)
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Selected regime: {regime.get('selected_regime')}")
    print(f"Draft count: {len(out_drafts)}")


if __name__ == "__main__":
    main()
