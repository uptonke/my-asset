#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
LATEST_JSON = OUT_DIR / "feature_store_latest.json"
SUMMARY_MD = OUT_DIR / "feature_store_summary.md"

SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

if not os.getenv("SUPABASE_SECRET_KEY") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SECRET_KEY"] = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def finite_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def load_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def bucket_for_ticker(ticker: str) -> str:
    t = str(ticker).upper()
    if t in {"BOXX", "BIL", "SGOV", "SHV", "CASH", "USD", "TWD"}:
        return "cash"
    if t in {"GLDM", "IAU", "GLD", "SGLN"}:
        return "gold"
    if "BTC" in t or "ETH" in t or "USD" in t and ("BTC" in t or "ETH" in t):
        return "crypto"
    if t in {"00981A", "2330", "0050", "006208", "00878", "00922"} or t.isdigit():
        return "taiwan_tech"
    if t in {"QQQ", "XLK", "VGT", "SMH", "SOXX"}:
        return "us_tech"
    if t in {"GRID", "IFRA", "SRVR", "PICK", "COPX", "URA", "ICLN"}:
        return "theme_etf"
    if t in {"VEA", "AVDE", "AVDV", "AVEM", "VNM"}:
        return "global_equity"
    if t in {"VOO", "VTI", "USMV", "AVUV", "SPY", "IVV"}:
        return "us_equity"
    return "other"


def load_current_weights_from_outputs() -> Dict[str, float]:
    for rel in ["data/optimizer/skfolio_sandbox_latest.json", "data/optimizer/riskfolio_sandbox_latest.json"]:
        data = load_json(ROOT / rel, {})
        current = (((data or {}).get("portfolios") or {}).get("current_weight") or {}).get("weights") or []
        if current:
            return {str(row.get("ticker")): (finite_float(row.get("weight_pct"), 0.0) or 0.0) for row in current if row.get("ticker")}
    constraint = load_json(ROOT / "data/optimizer/constraint_aware_rebalance_latest.json", {})
    w = (((constraint or {}).get("baseline") or {}).get("weights_pct") or {})
    return {str(k): (finite_float(v, 0.0) or 0.0) for k, v in w.items()}


def try_load_returns() -> Tuple[Optional[pd.DataFrame], Dict[str, float], Dict[str, Any]]:
    """Return strict TWD returns, current weights in pct, and metadata if live data access is available."""
    try:
        from run_skfolio_sandbox import load_strict_returns_and_weights  # type: ignore

        returns, weights, meta = load_strict_returns_and_weights()
        weights_pct = {str(k): round(float(v) * 100.0, 6) for k, v in weights.items()}
        meta = dict(meta or {})
        meta["feature_source"] = "live_strict_returns_from_update_stock_meta"
        return returns, weights_pct, meta
    except Exception as exc:
        return None, load_current_weights_from_outputs(), {
            "feature_source": "fallback_from_existing_optimizer_outputs",
            "fallback_reason": str(exc)[:500],
            "strict_sample": None,
            "strict_start": None,
            "strict_end": None,
        }


def pct_return(series: pd.Series, days: int) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < max(5, days):
        return None
    r = float((1.0 + s.tail(days)).prod() - 1.0)
    return round(r * 100.0, 3)


def ann_vol(series: pd.Series, days: int) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna().tail(days)
    if len(s) < max(20, min(days, 40)):
        return None
    v = float(s.std(ddof=1) * math.sqrt(252))
    return round(v * 100.0, 3)


def realized_drawdown(series: pd.Series, days: int = 252) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna().tail(days)
    if len(s) < 40:
        return None
    curve = (1.0 + s).cumprod()
    peak = curve.cummax()
    dd = curve / peak - 1.0
    return round(float(dd.iloc[-1]) * 100.0, 3)


def trend_proxy(series: pd.Series) -> Dict[str, Any]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 60:
        return {"trend_score": None, "price_proxy_vs_ma60_pct": None, "trend_state": "insufficient_sample"}
    curve = (1.0 + s).cumprod()
    last = float(curve.iloc[-1])
    ma60 = float(curve.tail(60).mean())
    ma120 = float(curve.tail(min(120, len(curve))).mean())
    vs60 = (last / ma60 - 1.0) * 100.0 if ma60 else 0.0
    vs120 = (last / ma120 - 1.0) * 100.0 if ma120 else 0.0
    score = max(-2.0, min(2.0, 0.06 * vs60 + 0.04 * vs120))
    state = "positive_trend" if score > 0.35 else "negative_trend" if score < -0.35 else "neutral_trend"
    return {"trend_score": round(score, 3), "price_proxy_vs_ma60_pct": round(vs60, 3), "trend_state": state}


def feature_score(row: Dict[str, Any]) -> Dict[str, Any]:
    m1 = finite_float(row.get("momentum_1m_pct"), 0.0) or 0.0
    m3 = finite_float(row.get("momentum_3m_pct"), 0.0) or 0.0
    m6 = finite_float(row.get("momentum_6m_pct"), 0.0) or 0.0
    m12 = finite_float(row.get("momentum_12m_pct"), 0.0) or 0.0
    vol = finite_float(row.get("volatility_60d_pct"), None)
    dd = finite_float(row.get("drawdown_from_high_pct"), 0.0) or 0.0
    trend = finite_float(row.get("trend_score"), 0.0) or 0.0
    momentum_score = max(-3.0, min(3.0, 0.03 * m1 + 0.018 * m3 + 0.012 * m6 + 0.006 * m12))
    vol_penalty = -min(2.5, (vol or 0.0) / 45.0) if vol is not None else -0.4
    drawdown_penalty = max(-2.0, min(0.0, dd / 15.0)) if dd < 0 else 0.0
    risk_adjusted_momentum = None
    if vol and vol > 0:
        risk_adjusted_momentum = round((0.4 * m3 + 0.6 * m6) / vol, 3)
    composite = momentum_score + trend + vol_penalty + drawdown_penalty
    return {
        "momentum_score": round(momentum_score, 3),
        "volatility_penalty": round(vol_penalty, 3),
        "drawdown_penalty": round(drawdown_penalty, 3),
        "risk_adjusted_momentum": risk_adjusted_momentum,
        "feature_composite_score": round(max(-5.0, min(5.0, composite)), 3),
    }


def build_features() -> Dict[str, Any]:
    returns, weights_pct, meta = try_load_returns()
    rows: List[Dict[str, Any]] = []
    warnings: List[str] = []

    if returns is None or returns.empty:
        warnings.append("Return series unavailable in this environment; generated fallback metadata-only feature rows from existing optimizer outputs.")
        for ticker, weight_pct in sorted(weights_pct.items()):
            rows.append({
                "ticker": ticker,
                "bucket": bucket_for_ticker(ticker),
                "current_weight_pct": round(weight_pct, 3),
                "feature_status": "fallback_metadata_only",
                "sample_days": None,
                "momentum_1m_pct": None,
                "momentum_3m_pct": None,
                "momentum_6m_pct": None,
                "momentum_12m_pct": None,
                "volatility_20d_pct": None,
                "volatility_60d_pct": None,
                "volatility_252d_pct": None,
                "drawdown_from_high_pct": None,
                "trend_score": None,
                "trend_state": "unknown",
                "momentum_score": 0.0,
                "volatility_penalty": -0.4,
                "drawdown_penalty": 0.0,
                "risk_adjusted_momentum": None,
                "feature_composite_score": 0.0,
                "confidence": 0.15,
            })
    else:
        for ticker in sorted(returns.columns):
            s = pd.to_numeric(returns[ticker], errors="coerce").dropna()
            weight_pct = weights_pct.get(ticker, 0.0)
            base = {
                "ticker": ticker,
                "bucket": bucket_for_ticker(ticker),
                "current_weight_pct": round(float(weight_pct), 3),
                "feature_status": "price_return_features_available",
                "sample_days": int(len(s)),
                "momentum_1m_pct": pct_return(s, 21),
                "momentum_3m_pct": pct_return(s, 63),
                "momentum_6m_pct": pct_return(s, 126),
                "momentum_12m_pct": pct_return(s, 252),
                "volatility_20d_pct": ann_vol(s, 20),
                "volatility_60d_pct": ann_vol(s, 60),
                "volatility_252d_pct": ann_vol(s, 252),
                "drawdown_from_high_pct": realized_drawdown(s, 252),
            }
            base.update(trend_proxy(s))
            base.update(feature_score(base))
            sample_conf = min(0.9, max(0.25, len(s) / 504.0))
            if len(s) < 252:
                sample_conf = min(sample_conf, 0.55)
            base["confidence"] = round(float(sample_conf), 3)
            rows.append(base)

    bucket_summary: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        b = str(row.get("bucket"))
        agg = bucket_summary.setdefault(b, {"bucket": b, "asset_count": 0, "current_weight_pct": 0.0, "avg_feature_score": 0.0, "avg_confidence": 0.0})
        agg["asset_count"] += 1
        agg["current_weight_pct"] += finite_float(row.get("current_weight_pct"), 0.0) or 0.0
        agg["avg_feature_score"] += finite_float(row.get("feature_composite_score"), 0.0) or 0.0
        agg["avg_confidence"] += finite_float(row.get("confidence"), 0.0) or 0.0
    for agg in bucket_summary.values():
        n = max(1, int(agg["asset_count"]))
        agg["current_weight_pct"] = round(agg["current_weight_pct"], 3)
        agg["avg_feature_score"] = round(agg["avg_feature_score"] / n, 3)
        agg["avg_confidence"] = round(agg["avg_confidence"] / n, 3)

    rows_sorted = sorted(rows, key=lambda r: finite_float(r.get("feature_composite_score"), 0.0) or 0.0, reverse=True)
    generated = now_iso()
    live = all(r.get("feature_status") == "price_return_features_available" for r in rows) if rows else False
    result = {
        "version": "v5.0",
        "status": "OK" if rows else "NO_ASSETS",
        "generated_at": generated,
        "mode": "forecast_feature_store",
        "safe_mode": True,
        "safe_mode_note": "v5.0 Forecast Feature Store 建立研究用特徵資料層；不產生買賣訊號、不自動交易、不寫 Supabase、不修改正式持倉。",
        "research_only": True,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "not_trade_order": True,
        "alpha_model_enabled": False,
        "maximum_sharpe_optimization_enabled": False,
        "source_files": {
            "portfolio_return_loader": "scripts/run_skfolio_sandbox.py::load_strict_returns_and_weights",
            "fallback_current_weights": "data/optimizer/skfolio_sandbox_latest.json",
        },
        "sample": {
            "source": meta.get("feature_source"),
            "strict_sample": meta.get("strict_sample"),
            "strict_start": meta.get("strict_start"),
            "strict_end": meta.get("strict_end"),
            "asset_count": len(rows),
            "live_return_features_available": bool(live),
            "fallback_reason": meta.get("fallback_reason"),
        },
        "feature_definitions": {
            "momentum_1m_pct": "最近約 21 個交易日合成 TWD 報酬。",
            "momentum_3m_pct": "最近約 63 個交易日合成 TWD 報酬。",
            "momentum_6m_pct": "最近約 126 個交易日合成 TWD 報酬。",
            "momentum_12m_pct": "最近約 252 個交易日合成 TWD 報酬。",
            "volatility_*_pct": "日報酬年化波動率。",
            "drawdown_from_high_pct": "相對近一年價格代理高點的回撤。",
            "feature_composite_score": "研究用綜合特徵分數；不是買賣訊號。",
        },
        "asset_features": rows_sorted,
        "bucket_features": sorted(bucket_summary.values(), key=lambda x: x["current_weight_pct"], reverse=True),
        "summary": {
            "asset_count": len(rows),
            "feature_ready_count": sum(1 for r in rows if r.get("feature_status") == "price_return_features_available"),
            "fallback_count": sum(1 for r in rows if r.get("feature_status") != "price_return_features_available"),
            "top_feature_assets": [r.get("ticker") for r in rows_sorted[:5]],
            "bottom_feature_assets": [r.get("ticker") for r in rows_sorted[-5:]],
            "research_boundary": "Feature scores are research inputs only; they are not alpha forecasts, not BUY/SELL signals, and not rebalance advice.",
        },
        "warnings": warnings,
    }
    return result


def write_summary(result: Dict[str, Any]) -> None:
    lines = [
        "# v5.0 Forecast Feature Store",
        "",
        f"- Status: **{result.get('status')}**",
        f"- Generated at: `{result.get('generated_at')}`",
        f"- Asset count: `{result.get('summary', {}).get('asset_count')}`",
        f"- Feature-ready count: `{result.get('summary', {}).get('feature_ready_count')}`",
        f"- Fallback count: `{result.get('summary', {}).get('fallback_count')}`",
        f"- Return feature source: `{result.get('sample', {}).get('source')}`",
        "",
        "## Top feature assets",
    ]
    for ticker in result.get("summary", {}).get("top_feature_assets", []):
        lines.append(f"- `{ticker}`")
    lines += [
        "",
        "## Safety boundary",
        "- Research-only feature layer.",
        "- Not a BUY / SELL signal.",
        "- Not an official alpha model.",
        "- No auto-trading and no Supabase write.",
    ]
    if result.get("warnings"):
        lines += ["", "## Warnings"]
        for w in result.get("warnings", []):
            lines.append(f"- {w}")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_features()
    LATEST_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_summary(result)
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Asset features: {result.get('summary', {}).get('asset_count')}")
    print(f"Feature-ready: {result.get('summary', {}).get('feature_ready_count')}")


if __name__ == "__main__":
    main()
