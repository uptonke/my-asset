#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
LATEST_JSON = OUT_DIR / "alpha_research_sandbox_latest.json"
SUMMARY_MD = OUT_DIR / "alpha_research_sandbox_summary.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def finite_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def normalize_score(value: Optional[float], scale: float = 5.0) -> float:
    x = finite_float(value, 0.0) or 0.0
    return max(-3.0, min(3.0, x / scale))


def load_bucket_priors() -> Dict[str, float]:
    data = load_json(ROOT / "data/optimizer/expected_return_model_latest.json", {})
    priors: Dict[str, float] = {}
    for row in (data.get("bucket_priors") or []):
        b = row.get("bucket")
        if b:
            priors[str(b)] = finite_float(row.get("relative_score"), 0.0) or 0.0
    return priors


def load_regime_adjustments() -> Dict[str, float]:
    data = load_json(ROOT / "data/optimizer/regime_aware_optimizer_latest.json", {})
    selected = (((data or {}).get("regime") or {}).get("selected_regime") or "neutral")
    # Conservative, bounded research-only tilts. These are not return forecasts.
    if selected == "risk_off_liquidity_pressure":
        return {
            "cash": 1.0,
            "gold": 0.35,
            "crypto": -0.9,
            "us_tech": -0.25,
            "taiwan_tech": -0.35,
            "theme_etf": -0.2,
        }
    if selected == "crypto_specific_stress":
        return {"crypto": -1.2, "cash": 0.5, "gold": 0.2}
    if selected == "taiwan_tech_concentration":
        return {"taiwan_tech": -0.8, "cash": 0.4, "global_equity": 0.1}
    if selected == "inflation_rate_hike_pressure":
        return {"cash": 0.6, "gold": 0.2, "us_tech": -0.35, "theme_etf": -0.25}
    return {}


def alpha_band(score: float, confidence: float, feature_status: str) -> str:
    if feature_status != "price_return_features_available" or confidence < 0.35:
        return "insufficient_data"
    if score >= 1.25:
        return "positive_research_prior"
    if score <= -1.25:
        return "negative_research_prior"
    return "neutral_research_prior"


def research_disposition(score: float, confidence: float, band: str, risk_flags: List[str]) -> str:
    if band == "insufficient_data":
        return "observe_only_insufficient_data"
    if any(flag in risk_flags for flag in ["high_volatility_penalty", "deep_drawdown_penalty"]):
        return "observe_only_risk_penalty"
    if band == "positive_research_prior" and confidence >= 0.5:
        return "further_research"
    if band == "negative_research_prior":
        return "negative_prior_observe"
    return "observe_only"


def build_alpha() -> Dict[str, Any]:
    fs = load_json(ROOT / "data/alpha/feature_store_latest.json", {})
    if not fs or not (fs.get("asset_features") or []):
        # Try to build the feature store if this script is run standalone.
        try:
            import subprocess, sys
            subprocess.run([sys.executable, "scripts/build_forecast_feature_store.py"], cwd=str(ROOT), check=True)
            fs = load_json(ROOT / "data/alpha/feature_store_latest.json", {})
        except Exception:
            fs = {}

    bucket_priors = load_bucket_priors()
    regime_adj = load_regime_adjustments()
    regime_data = load_json(ROOT / "data/optimizer/regime_aware_optimizer_latest.json", {})
    regime = (((regime_data or {}).get("regime") or {}).get("selected_regime") or "unknown")

    assets: List[Dict[str, Any]] = []
    warnings: List[str] = []
    if not fs.get("asset_features"):
        warnings.append("feature_store_latest.json missing or empty; alpha sandbox generated no asset rows.")

    for row in fs.get("asset_features") or []:
        ticker = str(row.get("ticker"))
        bucket = str(row.get("bucket") or "other")
        confidence = finite_float(row.get("confidence"), 0.0) or 0.0
        feature_status = str(row.get("feature_status") or "unknown")
        feature_score = finite_float(row.get("feature_composite_score"), 0.0) or 0.0
        momentum_score = finite_float(row.get("momentum_score"), 0.0) or 0.0
        vol_penalty = finite_float(row.get("volatility_penalty"), 0.0) or 0.0
        dd_penalty = finite_float(row.get("drawdown_penalty"), 0.0) or 0.0
        bucket_prior = bucket_priors.get(bucket, 0.0)
        regime_score = regime_adj.get(bucket, 0.0)
        # Conservative alpha research proxy. It is intentionally bounded and not calibrated as expected return.
        raw_score = 0.55 * feature_score + 0.2 * momentum_score + 0.15 * normalize_score(bucket_prior, 1.5) + 0.1 * regime_score
        raw_score = max(-5.0, min(5.0, raw_score))
        risk_flags: List[str] = []
        if vol_penalty <= -1.25:
            risk_flags.append("high_volatility_penalty")
        if dd_penalty <= -1.0:
            risk_flags.append("deep_drawdown_penalty")
        if feature_status != "price_return_features_available":
            risk_flags.append("feature_data_unavailable")
        band = alpha_band(raw_score, confidence, feature_status)
        disposition = research_disposition(raw_score, confidence, band, risk_flags)
        assets.append({
            "ticker": ticker,
            "bucket": bucket,
            "current_weight_pct": row.get("current_weight_pct"),
            "feature_status": feature_status,
            "alpha_research_score": round(raw_score, 3),
            "alpha_research_band": band,
            "research_disposition": disposition,
            "confidence": round(confidence, 3),
            "score_components": {
                "feature_composite_score": row.get("feature_composite_score"),
                "momentum_score": row.get("momentum_score"),
                "trend_score": row.get("trend_score"),
                "volatility_penalty": row.get("volatility_penalty"),
                "drawdown_penalty": row.get("drawdown_penalty"),
                "bucket_prior_score": round(bucket_prior, 3),
                "regime_adjustment_score": round(regime_score, 3),
            },
            "reason_codes": [
                f"feature_status:{feature_status}",
                f"bucket:{bucket}",
                f"regime:{regime}",
                f"band:{band}",
                *risk_flags,
            ],
            "not_trade_signal": True,
            "not_buy_signal": True,
            "not_sell_signal": True,
        })

    assets.sort(key=lambda r: finite_float(r.get("alpha_research_score"), 0.0) or 0.0, reverse=True)
    further = [a for a in assets if a.get("research_disposition") == "further_research"]
    observe = [a for a in assets if str(a.get("research_disposition", "")).startswith("observe")]
    negative = [a for a in assets if a.get("research_disposition") == "negative_prior_observe"]

    result = {
        "version": "v5.1",
        "status": "OK" if assets else "NO_ASSETS",
        "generated_at": now_iso(),
        "mode": "alpha_research_sandbox",
        "safe_mode": True,
        "safe_mode_note": "v5.1 Alpha Research Sandbox 只建立研究用 alpha proxy ranking；不輸出買賣訊號、不做最大夏普、不自動調倉、不寫 Supabase。",
        "research_only": True,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "not_trade_order": True,
        "not_buy_signal": True,
        "not_sell_signal": True,
        "alpha_model_enabled": False,
        "official_alpha_enabled": False,
        "maximum_sharpe_optimization_enabled": False,
        "source_files": {
            "feature_store": "data/alpha/feature_store_latest.json",
            "expected_return_model": "data/optimizer/expected_return_model_latest.json",
            "regime_aware_optimizer": "data/optimizer/regime_aware_optimizer_latest.json",
        },
        "model_policy": {
            "model_type": "research_proxy_score",
            "official_alpha_enabled": False,
            "absolute_return_forecast_enabled": False,
            "trade_signal_enabled": False,
            "max_sharpe_enabled": False,
            "allowed_use": "research_ranking_only",
            "disallowed_use": ["BUY_SELL", "auto_trade", "official_weight_update", "supabase_write", "maximum_sharpe_rebalance"],
        },
        "regime_context": {
            "selected_regime": regime,
            "regime_bucket_adjustments": regime_adj,
        },
        "asset_alpha_research": assets,
        "summary": {
            "asset_count": len(assets),
            "further_research_count": len(further),
            "observe_only_count": len(observe),
            "negative_prior_count": len(negative),
            "top_research_candidates": [a.get("ticker") for a in further[:5]],
            "top_ranked_assets": [a.get("ticker") for a in assets[:5]],
            "bottom_ranked_assets": [a.get("ticker") for a in assets[-5:]],
            "research_boundary": "通過 alpha research ranking 不代表值得買入、不代表看多、不代表正式調倉。",
        },
        "warnings": warnings,
    }
    return result


def write_summary(result: Dict[str, Any]) -> None:
    lines = [
        "# v5.1 Alpha Research Sandbox",
        "",
        f"- Status: **{result.get('status')}**",
        f"- Generated at: `{result.get('generated_at')}`",
        f"- Asset count: `{result.get('summary', {}).get('asset_count')}`",
        f"- Further research count: `{result.get('summary', {}).get('further_research_count')}`",
        f"- Observe-only count: `{result.get('summary', {}).get('observe_only_count')}`",
        f"- Negative prior count: `{result.get('summary', {}).get('negative_prior_count')}`",
        f"- Regime: `{result.get('regime_context', {}).get('selected_regime')}`",
        "",
        "## Top research candidates",
    ]
    top = result.get("summary", {}).get("top_research_candidates") or []
    if top:
        for ticker in top:
            lines.append(f"- `{ticker}`")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Safety boundary",
        "- Research ranking only.",
        "- Not a BUY / SELL signal.",
        "- Official alpha model remains disabled.",
        "- Maximum Sharpe optimization remains disabled.",
        "- No auto-trading and no Supabase write.",
    ]
    if result.get("warnings"):
        lines += ["", "## Warnings"]
        for w in result.get("warnings", []):
            lines.append(f"- {w}")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_alpha()
    LATEST_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_summary(result)
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Asset alpha rows: {result.get('summary', {}).get('asset_count')}")
    print(f"Further research: {result.get('summary', {}).get('further_research_count')}")
    print("Trade signal enabled: False")


if __name__ == "__main__":
    main()
