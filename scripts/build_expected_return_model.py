#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

OUT_DIR = Path("data/optimizer")
SKFOLIO = OUT_DIR / "skfolio_sandbox_latest.json"
RISKFOLIO = OUT_DIR / "riskfolio_sandbox_latest.json"
REGIME = OUT_DIR / "regime_aware_optimizer_latest.json"
BLACK_LITTERMAN = OUT_DIR / "black_litterman_sandbox_latest.json"
ROBUSTNESS = OUT_DIR / "optimizer_robustness_latest.json"
STRESS = OUT_DIR / "optimizer_stress_latest.json"
JSON_OUT = OUT_DIR / "expected_return_model_latest.json"
MD_OUT = OUT_DIR / "expected_return_model_summary.md"
VERSION = "v3.2"

SAFE_MODE_NOTE = (
    "v3.2 Expected Return Model 是 relative prior / expected-return proxy sandbox；"
    "不啟用 alpha forecast、不啟用最大夏普最佳化、不產生 BUY / SELL 指令，"
    "不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。"
)

BUCKET_MAP = {
    "BOXX": "cash",
    "GLDM": "gold",
    "BTC-USD": "crypto",
    "ETH-USD": "crypto",
    "00981A": "taiwan_tech",
    "QQQ": "us_tech",
    "VTI": "us_equity",
    "VOO": "us_equity",
    "VT": "global_equity",
    "GRID": "theme_etf",
    "IFRA": "theme_etf",
    "SRVR": "theme_etf",
    "COPX": "commodity_equity",
    "VNM": "emerging_market",
}

BASE_BUCKET_PRIORS = {
    "cash": 0.4,
    "gold": 0.1,
    "crypto": -0.4,
    "taiwan_tech": -0.2,
    "us_tech": -0.15,
    "us_equity": 0.0,
    "global_equity": 0.0,
    "theme_etf": -0.15,
    "commodity_equity": -0.1,
    "emerging_market": -0.1,
    "other": 0.0,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> Dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "READ_ERROR", "error": str(exc)[:500]}


def finite(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def iter_current_weights(skfolio: Dict[str, Any], riskfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
    for source in (skfolio, riskfolio):
        p = (source.get("portfolios") or {}).get("current_weight") or {}
        rows = p.get("weights") or []
        if isinstance(rows, list) and rows:
            return rows
    return []


def bucket_for(ticker: str) -> str:
    if ticker in BUCKET_MAP:
        return BUCKET_MAP[ticker]
    if ticker.endswith(".TW") or ticker.startswith("00"):
        return "taiwan_equity"
    return "other"


def view_adjustments(bl: Dict[str, Any]) -> Dict[str, float]:
    adj: Dict[str, float] = {}
    for v in bl.get("views") or []:
        bucket = str(v.get("bucket") or "other")
        mag = finite(v.get("magnitude_pct"), 0.0) or 0.0
        conf = finite(v.get("confidence"), 0.5) or 0.5
        direction = str(v.get("direction") or "").lower()
        sign = 1.0 if "over" in direction else -1.0 if "under" in direction else 0.0
        adj[bucket] = adj.get(bucket, 0.0) + sign * mag * conf / 2.5
    return adj


def regime_adjustments(regime: Dict[str, Any]) -> Dict[str, float]:
    selected = str((regime.get("regime") or {}).get("selected_regime") or regime.get("selected_regime") or "neutral_growth")
    if selected == "risk_off_liquidity_pressure":
        return {"cash": 0.8, "gold": 0.25, "crypto": -0.9, "us_tech": -0.45, "taiwan_tech": -0.35, "theme_etf": -0.3, "emerging_market": -0.25}
    if selected == "inflation_rate_hike_pressure":
        return {"cash": 0.45, "gold": 0.35, "crypto": -0.55, "us_tech": -0.45, "theme_etf": -0.25}
    if selected == "crypto_specific_stress":
        return {"crypto": -1.0, "cash": 0.45, "gold": 0.15}
    if selected == "taiwan_tech_concentration":
        return {"taiwan_tech": -0.75, "cash": 0.35, "global_equity": 0.1}
    return {}


def stress_penalty_by_method(stress: Dict[str, Any]) -> Dict[str, float]:
    out = {}
    rows = stress.get("comparison_rows") or []
    if not isinstance(rows, list):
        return out
    for r in rows:
        name = str(r.get("candidate") or r.get("method") or r.get("id") or "")
        worst = finite(r.get("worst_scenario_pct") or r.get("worst_scenario_return_pct") or r.get("worst_scenario"), None)
        if name and worst is not None:
            # More negative worst scenario increases penalty.
            out[name] = max(0.0, min(1.0, abs(min(worst, 0.0)) / 30.0))
    return out


def robustness_bonus(robustness: Dict[str, Any]) -> Dict[str, float]:
    out = {}
    ms = robustness.get("method_stability") or {}
    if isinstance(ms, dict):
        items = ms.items()
    else:
        items = []
    for name, r in items:
        verdict = str(r.get("verdict") or "")
        avg_turn = finite(r.get("avg_pairwise_weight_turnover_pct"), 999.0) or 999.0
        bonus = 0.0
        if "穩定" in verdict or verdict.lower() == "stable":
            bonus += 0.25
        if avg_turn <= 10:
            bonus += 0.2
        elif avg_turn >= 40:
            bonus -= 0.25
        out[str(name)] = bonus
    return out


def clamp(x: float, lo: float = -3.0, hi: float = 3.0) -> float:
    return max(lo, min(hi, x))


def confidence_from_inputs(bucket: str, has_bl: bool, has_regime: bool, sample_count: Optional[int], three_y_available: bool) -> float:
    conf = 0.35
    if has_regime:
        conf += 0.15
    if has_bl:
        conf += 0.15
    if sample_count and sample_count >= 252:
        conf += 0.1
    if three_y_available:
        conf += 0.1
    if bucket in {"crypto", "theme_etf", "emerging_market"}:
        conf -= 0.05
    return round(max(0.1, min(0.75, conf)), 2)


def band(score: float) -> str:
    if score >= 0.75:
        return "relative_overweight_prior"
    if score <= -0.75:
        return "relative_underweight_prior"
    return "neutral_or_no_edge_prior"


def build() -> Dict[str, Any]:
    skfolio = load_json(SKFOLIO)
    riskfolio = load_json(RISKFOLIO)
    regime = load_json(REGIME)
    bl = load_json(BLACK_LITTERMAN)
    robustness = load_json(ROBUSTNESS)
    stress = load_json(STRESS)

    sample = skfolio.get("sample") or riskfolio.get("sample") or robustness.get("sample") or {}
    sample_count = finite(sample.get("strict_sample") or sample.get("sample_count"), None)
    windows = robustness.get("windows") or []
    three_y_available = any(str(w.get("label")) == "3Y" and str(w.get("status")) == "OK" for w in windows if isinstance(w, dict))

    has_bl = bool(bl.get("views"))
    has_regime = bool((regime.get("regime") or {}).get("selected_regime"))
    vadj = view_adjustments(bl)
    radj = regime_adjustments(regime)
    rows = iter_current_weights(skfolio, riskfolio)

    bucket_scores: Dict[str, Dict[str, Any]] = {}
    all_buckets = sorted(set(BASE_BUCKET_PRIORS) | set(vadj) | set(radj))
    for b in all_buckets:
        score = BASE_BUCKET_PRIORS.get(b, 0.0) + vadj.get(b, 0.0) + radj.get(b, 0.0)
        score = clamp(score)
        bucket_scores[b] = {
            "bucket": b,
            "relative_score": round(score, 3),
            "prior_band": band(score),
            "confidence": confidence_from_inputs(b, has_bl, has_regime, int(sample_count) if sample_count else None, three_y_available),
            "base_score": BASE_BUCKET_PRIORS.get(b, 0.0),
            "regime_adjustment": round(radj.get(b, 0.0), 3),
            "black_litterman_view_adjustment": round(vadj.get(b, 0.0), 3),
            "absolute_expected_return_pct": None,
            "rationale": "relative prior only; absolute expected return forecast is disabled",
        }

    asset_priors = []
    for w in rows:
        ticker = str(w.get("ticker") or "")
        if not ticker:
            continue
        b = bucket_for(ticker)
        bs = bucket_scores.get(b, bucket_scores.get("other", {}))
        asset_priors.append({
            "ticker": ticker,
            "bucket": b,
            "current_weight_pct": finite(w.get("current_weight_pct") or w.get("weight_pct"), 0.0),
            "relative_score": bs.get("relative_score", 0.0),
            "prior_band": bs.get("prior_band", "neutral_or_no_edge_prior"),
            "confidence": bs.get("confidence", 0.35),
            "absolute_expected_return_pct": None,
            "max_sharpe_input_allowed": False,
            "rationale": bs.get("rationale", "relative prior only"),
        })
    asset_priors.sort(key=lambda x: (x.get("relative_score") or 0), reverse=True)

    rb = robustness_bonus(robustness)
    sp = stress_penalty_by_method(stress)
    method_priors = []
    for name in sorted(set(rb) | set(sp)):
        score = clamp(rb.get(name, 0.0) - sp.get(name, 0.0), -2.0, 2.0)
        method_priors.append({
            "method": name,
            "relative_model_prior_score": round(score, 3),
            "robustness_bonus": round(rb.get(name, 0.0), 3),
            "stress_penalty": round(sp.get(name, 0.0), 3),
            "decision_use": "ranking_context_only",
            "max_sharpe_input_allowed": False,
        })
    method_priors.sort(key=lambda x: x["relative_model_prior_score"], reverse=True)

    warnings = []
    if not three_y_available:
        warnings.append("3Y robustness window unavailable; expected return confidence capped.")
    if not has_bl:
        warnings.append("Black-Litterman views unavailable; v3.2 uses regime/base priors only.")
    warnings.append("Absolute expected return forecast is disabled by design.")
    warnings.append("Maximum Sharpe optimization is disabled; no alpha model is trusted enough.")

    positive = [b for b in bucket_scores.values() if b["relative_score"] > 0.5]
    negative = [b for b in bucket_scores.values() if b["relative_score"] < -0.5]

    return {
        "version": VERSION,
        "status": "OK",
        "generated_at": now_utc(),
        "mode": "conservative_expected_return_model",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "source_files": {
            "skfolio": str(SKFOLIO),
            "riskfolio": str(RISKFOLIO),
            "regime_aware_optimizer": str(REGIME),
            "black_litterman_sandbox": str(BLACK_LITTERMAN),
            "optimizer_robustness": str(ROBUSTNESS),
            "optimizer_stress": str(STRESS),
        },
        "model_policy": {
            "absolute_expected_return_forecast_enabled": False,
            "alpha_model_enabled": False,
            "maximum_sharpe_optimization_enabled": False,
            "allowed_use": "relative_prior_context_only",
            "disallowed_use": ["BUY_SELL", "auto_trade", "official_weight_update", "supabase_write"],
        },
        "sample_quality": {
            "strict_sample": int(sample_count) if sample_count is not None else None,
            "three_year_window_available": three_y_available,
            "confidence_cap": 0.75,
        },
        "bucket_priors": list(sorted(bucket_scores.values(), key=lambda x: x["relative_score"], reverse=True)),
        "asset_expected_return_priors": asset_priors,
        "method_relative_priors": method_priors,
        "summary": {
            "asset_count": len(asset_priors),
            "bucket_count": len(bucket_scores),
            "positive_prior_bucket_count": len(positive),
            "negative_prior_bucket_count": len(negative),
            "max_confidence": max([a["confidence"] for a in asset_priors], default=0),
            "verdict": "relative_prior_only_no_max_sharpe",
        },
        "warnings": warnings,
        "execution_permission": False,
        "not_trade_order": True,
        "requires_manual_approval": True,
    }


def write_md(result: Dict[str, Any]) -> str:
    s = result.get("summary", {})
    lines = [
        "# Expected Return Model v3.2",
        "",
        f"Generated: `{result.get('generated_at')}`",
        "",
        "## Safety boundary",
        "",
        "- Relative prior only; absolute expected-return forecast is disabled.",
        "- Maximum Sharpe optimization is disabled.",
        "- 不是 BUY / SELL 指令，不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。",
        "",
        "## Summary",
        "",
        f"- Asset priors: `{s.get('asset_count', 0)}`",
        f"- Positive prior buckets: `{s.get('positive_prior_bucket_count', 0)}`",
        f"- Negative prior buckets: `{s.get('negative_prior_bucket_count', 0)}`",
        f"- Verdict: `{s.get('verdict')}`",
        "",
        "## Bucket priors",
        "",
        "| Bucket | Score | Band | Confidence | Regime adj | BL adj |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for b in result.get("bucket_priors", [])[:12]:
        lines.append(f"| `{b.get('bucket')}` | {b.get('relative_score')} | `{b.get('prior_band')}` | {b.get('confidence')} | {b.get('regime_adjustment')} | {b.get('black_litterman_view_adjustment')} |")
    lines += ["", "## Top asset priors", "", "| Ticker | Bucket | Score | Band | Confidence |", "|---|---|---:|---|---:|"]
    for a in result.get("asset_expected_return_priors", [])[:15]:
        lines.append(f"| `{a.get('ticker')}` | `{a.get('bucket')}` | {a.get('relative_score')} | `{a.get('prior_band')}` | {a.get('confidence')} |")
    lines += ["", "## Warnings", ""]
    for w in result.get("warnings", []):
        lines.append(f"- {w}")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = build()
    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(write_md(result), encoding="utf-8")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Asset priors: {result['summary']['asset_count']}")
    print(f"Max Sharpe enabled: {result['model_policy']['maximum_sharpe_optimization_enabled']}")


if __name__ == "__main__":
    main()
