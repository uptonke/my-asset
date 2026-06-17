#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "delegated_target_weight_draft_latest.json"
SUMMARY_MD = OUT_DIR / "delegated_target_weight_draft_summary.md"

MIN_INCLUDED_WEIGHT = 0.02
MAX_SINGLE_WEIGHT = 0.40
DEFAULT_LIQUIDITY_BUFFER = 0.05
MAX_POOL_SIZE = 50


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(rel: str, default: Any = None) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def num(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        x = float(v)
        if math.isfinite(x):
            return x
    except Exception:
        pass
    return default


def pct_to_float(v: Any, default: float) -> float:
    x = num(v, default)
    if x > 1.0:
        x = x / 100.0
    return max(0.0, min(0.90, x))


def has_value(d: Dict[str, Any], key: str) -> bool:
    return key in d and d.get(key) is not None and d.get(key) != ""


def resolve_liquidity_buffer_pct(config: Dict[str, Any], constraints: Dict[str, Any]) -> Tuple[float, str]:
    delegated = as_dict(config.get("delegated_draft_policy"))
    portfolio_settings = as_dict(constraints.get("portfolio_settings"))
    summary = as_dict(constraints.get("summary"))

    # Source of truth: dashboard/Supabase settings.liquidityBufferRatio. Explicit 0 is valid.
    for source_name, source in [
        ("portfolio_settings.liquidity_buffer_ratio_pct", portfolio_settings),
        ("summary.liquidity_buffer_ratio_pct", summary),
    ]:
        key = source_name.split(".")[-1]
        if has_value(source, key):
            return pct_to_float(source.get(key), DEFAULT_LIQUIDITY_BUFFER), source_name

    # Config override is only used when the dashboard setting is unavailable. Explicit 0 is valid.
    for key in ["liquidity_buffer_pct", "liquidityBufferRatio", "cash_target_weight_pct"]:
        if has_value(delegated, key):
            return pct_to_float(delegated.get(key), DEFAULT_LIQUIDITY_BUFFER), f"config.delegated_draft_policy.{key}"
    for key in ["liquidity_buffer_pct", "liquidityBufferRatio", "cash_target_weight_pct"]:
        if has_value(config, key):
            return pct_to_float(config.get(key), DEFAULT_LIQUIDITY_BUFFER), f"config.{key}"

    default_from_policy = delegated.get("default_liquidity_buffer_pct", DEFAULT_LIQUIDITY_BUFFER)
    return pct_to_float(default_from_policy, DEFAULT_LIQUIDITY_BUFFER), "default_missing_setting"


def round6(x: float) -> float:
    return round(float(x), 6)


def load_policy(config: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
    delegated = as_dict(config.get("delegated_draft_policy"))
    liquidity_buffer_pct, liquidity_buffer_source = resolve_liquidity_buffer_pct(config, constraints)
    return {
        "version": "v10.5.1",
        "name": "Dual Target Blend + Daily Quant Risk-Adjusted Delegated Draft Generator",
        "eligible_pool_policy": {
            "pool_source": "all_current_assets",
            "max_pool_size": int(num(delegated.get("max_pool_size"), MAX_POOL_SIZE)),
            "asset_class_required": False,
            "allow_all_assets_into_pool": True,
        },
        "target_generation_policy": {
            "target_weight_source": "dual_blend_cloud_target_and_v105_native_target",
            "cloud_target_weight_source": "stock_meta[ticker].target_weight",
            "v105_native_target_source": "ranking_alpha_daily_quant_native_engine",
            "cloud_target_blend_weight": 0.50,
            "v105_native_blend_weight": 0.50,
            "use_external_target_weights": True,
            "uses_frontend_mc_percent_target": False,
            "daily_quant_monte_carlo_inputs_enabled": True,
            "included_asset_min_weight_pct": MIN_INCLUDED_WEIGHT,
            "single_asset_max_weight_pct": MAX_SINGLE_WEIGHT,
            "min_weight_applies_to": "selected_assets_only",
            "allow_zero_weight_for_unselected_assets": True,
            "respect_liquidity_buffer": True,
            "no_leverage": True,
            "no_shorting": True,
        },
        "cash_policy": {
            "cash_ratio_source": "liquidity_buffer_pct",
            "liquidity_buffer_pct": liquidity_buffer_pct,
            "liquidity_buffer_source": liquidity_buffer_source,
            "zero_liquidity_buffer_is_valid": True,
            "buying_power_policy": "surplus_above_liquidity_buffer_or_internal_rebalance",
        },
        "trade_sizing_policy": {
            "use_absolute_trade_budget_cap": False,
            "use_single_trade_cap": False,
            "size_to_machine_generated_target": True,
            "prevent_overshoot_after_lot_rounding": True,
        },
        "lot_rules": {
            "us_fractional_shares_allowed": False,
            "tw_odd_lot_allowed": True,
            "crypto_fractional_units_allowed": True,
        },
    }



def load_daily_quant_context() -> Dict[str, Any]:
    daily = as_dict(read_json("data/alpha/daily_quant_reference_latest.json", {}))
    synthetic = as_dict(daily.get("synthetic_risk_reference"))
    mc = as_dict(daily.get("monte_carlo_reference"))
    settings_ref = as_dict(daily.get("settings_reference"))
    fragile_nodes = {str(x).strip() for x in as_list(mc.get("fragile_nodes")) if str(x).strip()}
    metrics = as_dict(synthetic.get("metrics"))
    stressed_es95 = abs(num(mc.get("stressed_es95_pct")))
    stressed_var95 = abs(num(mc.get("stressed_var95_pct")))
    liquidity_run_prob = num(mc.get("liquidity_run_probability_pct"))
    ann_vol = abs(num(metrics.get("ann_vol_pct")))
    es95 = abs(num(metrics.get("es95_pct")))
    high_tail_pressure = bool(stressed_es95 >= 8.0 or liquidity_run_prob >= 20.0 or ann_vol >= 18.0)
    moderate_tail_pressure = bool(stressed_es95 >= 5.0 or liquidity_run_prob >= 10.0 or es95 >= 1.5)
    if high_tail_pressure:
        risk_mode = "high_tail_pressure"
        current_coeff, rank_coeff, alpha_coeff = 0.60, 0.28, 0.12
    elif moderate_tail_pressure:
        risk_mode = "moderate_tail_pressure"
        current_coeff, rank_coeff, alpha_coeff = 0.55, 0.32, 0.13
    else:
        risk_mode = "normal_reference"
        current_coeff, rank_coeff, alpha_coeff = 0.50, 0.35, 0.15
    return {
        "available": bool(daily),
        "daily_reference_generated_at": daily.get("generated_at"),
        "portfolio_source": daily.get("portfolio_source"),
        "synthetic_risk_available": bool(synthetic.get("available")),
        "monte_carlo_reference_available": bool(mc.get("available")),
        "settings_reference": settings_ref,
        "synthetic_risk_metrics": metrics,
        "monte_carlo_reference": {
            "stressed_var95_pct": mc.get("stressed_var95_pct"),
            "stressed_es95_pct": mc.get("stressed_es95_pct"),
            "liquidity_run_probability_pct": mc.get("liquidity_run_probability_pct"),
            "fragile_nodes": sorted(fragile_nodes),
        },
        "risk_mode": risk_mode,
        "target_weight_coefficients": {
            "current_weight": current_coeff,
            "ranking_prior": rank_coeff,
            "alpha_research": alpha_coeff,
        },
        "fragile_nodes": sorted(fragile_nodes),
        "high_tail_pressure": high_tail_pressure,
        "moderate_tail_pressure": moderate_tail_pressure,
        "source_priority_policy": [
            "Supabase stock_meta[ticker].target_weight is the cloud target weight source.",
            "v10.5 native target is generated from current weights, v5.2 ranking, alpha research, and Daily Quant / Monte Carlo risk context.",
            "Final target is a 50/50 blend of cloud target and v10.5 native target; front-end manual MC% is not used.",
            "Monte Carlo / chaos_meta fragile nodes and synthetic risk are risk modifiers and warnings, not browser MC% target weights.",
        ],
    }


def daily_quant_mc_multiplier(ticker: str, context: Dict[str, Any]) -> Tuple[float, List[str]]:
    reasons: List[str] = []
    multiplier = 1.0
    fragile_nodes = set(context.get("fragile_nodes") or [])
    if ticker in fragile_nodes:
        multiplier *= 0.70
        reasons.append("monte_carlo_fragile_node_penalty")
    if context.get("high_tail_pressure") and ticker in fragile_nodes:
        multiplier *= 0.90
        reasons.append("high_tail_pressure_extra_fragile_penalty")
    if not context.get("synthetic_risk_available"):
        reasons.append("synthetic_risk_reference_unavailable_no_penalty")
    if not context.get("monte_carlo_reference_available"):
        reasons.append("monte_carlo_reference_unavailable_no_penalty")
    return round6(multiplier), reasons

def asset_key(row: Dict[str, Any]) -> str:
    return str(row.get("ticker") or row.get("symbol") or "").strip()


def select_ranking_candidate(ranking: Dict[str, Any]) -> Dict[str, Any]:
    rows = [as_dict(x) for x in as_list(ranking.get("ranking_rows"))]
    rows = sorted(rows, key=lambda r: num(r.get("rank"), 999999))
    preferred = [r for r in rows if str(r.get("ranking_status")) == "further_research"]
    return (preferred or rows or [{}])[0]


def weights_pct_to_float_map(weights_pct: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for k, v in as_dict(weights_pct).items():
        key = str(k).strip()
        if not key:
            continue
        out[key] = max(0.0, min(1.0, num(v) / 100.0))
    return out


def normalize_simple(raw: Dict[str, float], investable: float) -> Dict[str, float]:
    positive = {k: max(0.0, v) for k, v in raw.items() if v > 1e-12}
    total = sum(positive.values())
    if total <= 0 or investable <= 0:
        return {}
    return {k: round6(investable * v / total) for k, v in positive.items()}


def alpha_research_weight_map(alpha: Dict[str, Any], tickers: List[str], current_weights: Dict[str, float], investable: float) -> Dict[str, float]:
    rows = [as_dict(x) for x in as_list(alpha.get("asset_alpha_research"))]
    score_map = {str(r.get("ticker") or "").strip(): num(r.get("alpha_research_score")) for r in rows if str(r.get("ticker") or "").strip()}
    raw: Dict[str, float] = {}
    for t in tickers:
        # Keep alpha as a mild tilt rather than an independent trade signal.
        # Score range is compressed so v10.5 native target remains anchored to current/ranking.
        score = score_map.get(t, 0.0)
        tilt = max(0.50, min(1.50, 1.0 + 0.12 * score))
        raw[t] = max(0.0, current_weights.get(t, 0.0)) * tilt
    return normalize_simple(raw, investable)


def build_v105_native_target_weights(
    asset_rows: List[Dict[str, Any]],
    nav_twd: float,
    investable_weight: float,
    ranking: Dict[str, Any],
    alpha: Dict[str, Any],
    daily_quant_context: Dict[str, Any],
    min_w: float,
    max_w: float,
) -> Tuple[Dict[str, float], List[Dict[str, Any]], Dict[str, Any], List[str]]:
    tickers = [asset_key(r) for r in asset_rows if asset_key(r)]
    current_weights = {
        t: (num(next((r.get("market_value_twd") for r in asset_rows if asset_key(r) == t), 0.0)) / nav_twd if nav_twd > 0 else 0.0)
        for t in tickers
    }
    ranking_candidate = select_ranking_candidate(ranking)
    ranking_weights = weights_pct_to_float_map(as_dict(ranking_candidate.get("weights_pct")))
    ranking_weights = {t: ranking_weights.get(t, current_weights.get(t, 0.0)) for t in tickers}
    ranking_weights = normalize_simple(ranking_weights, investable_weight) or {t: current_weights.get(t, 0.0) for t in tickers}
    alpha_weights = alpha_research_weight_map(alpha, tickers, current_weights, investable_weight) or {t: current_weights.get(t, 0.0) for t in tickers}
    coeffs = as_dict(daily_quant_context.get("target_weight_coefficients"))
    current_coeff = num(coeffs.get("current_weight"), 0.50)
    ranking_coeff = num(coeffs.get("ranking_prior"), 0.35)
    alpha_coeff = num(coeffs.get("alpha_research"), 0.15)
    coeff_sum = current_coeff + ranking_coeff + alpha_coeff
    if coeff_sum <= 0:
        current_coeff, ranking_coeff, alpha_coeff, coeff_sum = 0.50, 0.35, 0.15, 1.0
    current_coeff, ranking_coeff, alpha_coeff = current_coeff / coeff_sum, ranking_coeff / coeff_sum, alpha_coeff / coeff_sum

    raw: Dict[str, float] = {}
    rows: List[Dict[str, Any]] = []
    for t in tickers:
        dq_multiplier, dq_reasons = daily_quant_mc_multiplier(t, daily_quant_context)
        before_risk = (
            current_coeff * current_weights.get(t, 0.0)
            + ranking_coeff * ranking_weights.get(t, 0.0)
            + alpha_coeff * alpha_weights.get(t, 0.0)
        )
        after_risk = before_risk * dq_multiplier
        raw[t] = after_risk
        rows.append({
            "ticker": t,
            "current_weight_pct": round6(current_weights.get(t, 0.0) * 100),
            "ranking_target_weight_pct": round6(ranking_weights.get(t, 0.0) * 100),
            "alpha_tilt_weight_pct": round6(alpha_weights.get(t, 0.0) * 100),
            "native_raw_before_daily_quant_mc_pct": round6(before_risk * 100),
            "native_raw_after_daily_quant_mc_pct": round6(after_risk * 100),
            "daily_quant_mc_multiplier": dq_multiplier,
            "daily_quant_mc_reasons": dq_reasons,
            "mc_fragile_node": t in set(daily_quant_context.get("fragile_nodes") or []),
        })
    native_weights, warnings = normalize_with_bounds(raw, investable_weight, min_w, max_w)
    row_map = {r["ticker"]: r for r in rows}
    for t, w in native_weights.items():
        if t in row_map:
            row_map[t]["v105_native_target_weight_pct"] = round6(w * 100)
    meta = {
        "ranking_candidate_id": ranking_candidate.get("ranking_id"),
        "ranking_status": ranking_candidate.get("ranking_status"),
        "current_weight_coeff": round6(current_coeff),
        "ranking_prior_coeff": round6(ranking_coeff),
        "alpha_research_coeff": round6(alpha_coeff),
        "native_target_weight_sum_pct": round6(sum(native_weights.values()) * 100),
    }
    return native_weights, list(row_map.values()), meta, warnings


def parse_cloud_target_weight(row: Dict[str, Any]) -> Tuple[float | None, str]:
    if has_value(row, "cloud_target_weight_pct"):
        return max(0.0, min(1.0, num(row.get("cloud_target_weight_pct")) / 100.0)), str(row.get("cloud_target_source") or "stock_meta.target_weight")
    if has_value(row, "stock_meta_target_weight_pct"):
        return max(0.0, min(1.0, num(row.get("stock_meta_target_weight_pct")) / 100.0)), "stock_meta.target_weight"
    return None, "missing_stock_meta_target_weight"


def build_dual_blended_targets(
    asset_rows: List[Dict[str, Any]],
    nav_twd: float,
    investable_weight: float,
    native_weights: Dict[str, float],
    min_w: float,
    max_w: float,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    tickers = [asset_key(r) for r in asset_rows if asset_key(r)]
    current_weights = {asset_key(r): (num(r.get("market_value_twd")) / nav_twd if nav_twd > 0 else 0.0) for r in asset_rows if asset_key(r)}
    cloud_map: Dict[str, float | None] = {}
    meta_by_ticker: Dict[str, Dict[str, Any]] = {}
    conflict_warnings: List[Dict[str, Any]] = []
    raw_blend: Dict[str, float] = {}
    for row in asset_rows:
        t = asset_key(row)
        cloud_w, cloud_source = parse_cloud_target_weight(row)
        native_w = native_weights.get(t, 0.0)
        current_w = current_weights.get(t, 0.0)
        cloud_available = cloud_w is not None
        cloud_component = cloud_w if cloud_available else native_w
        preliminary = 0.50 * cloud_component + 0.50 * native_w
        gap_pct = abs((cloud_component - native_w) * 100) if cloud_available else None
        cloud_delta = (cloud_component - current_w) if cloud_available else 0.0
        native_delta = native_w - current_w
        direction_conflict = bool(cloud_available and abs(cloud_delta) > 0.001 and abs(native_delta) > 0.001 and cloud_delta * native_delta < 0)
        conflict_adjustment_factor = 1.0
        conflict_code = None
        if direction_conflict:
            conflict_adjustment_factor = 0.0
            conflict_code = "dual_target_direction_conflict"
        elif gap_pct is not None and gap_pct > 15.0:
            conflict_adjustment_factor = 0.25
            conflict_code = "major_dual_target_gap"
        elif gap_pct is not None and gap_pct > 5.0:
            conflict_adjustment_factor = 0.50
            conflict_code = "moderate_dual_target_gap"
        adjusted = current_w + conflict_adjustment_factor * (preliminary - current_w)
        raw_blend[t] = max(0.0, adjusted)
        if conflict_code:
            conflict_warnings.append({
                "code": conflict_code,
                "severity": "warning",
                "ticker": t,
                "message": "雲端% 與 v10.5 原生目標分歧，已縮小或暫停該檔 drift 調整。",
                "cloud_target_weight_pct": None if not cloud_available else round6(cloud_component * 100),
                "v105_native_target_weight_pct": round6(native_w * 100),
                "current_weight_pct": round6(current_w * 100),
                "gap_pct": None if gap_pct is None else round6(gap_pct),
                "conflict_adjustment_factor": conflict_adjustment_factor,
            })
        meta_by_ticker[t] = {
            "cloud_target_weight_available": cloud_available,
            "cloud_target_weight_pct": None if not cloud_available else round6(cloud_component * 100),
            "cloud_target_source": cloud_source,
            "v105_native_target_weight_pct": round6(native_w * 100),
            "dual_blend_preliminary_target_pct": round6(preliminary * 100),
            "dual_target_gap_pct": None if gap_pct is None else round6(gap_pct),
            "dual_target_direction_conflict": direction_conflict,
            "conflict_adjustment_factor": conflict_adjustment_factor,
            "final_target_raw_before_residual_pct": round6(adjusted * 100),
        }
    total_raw = sum(raw_blend.values())
    residual_policy = "none"
    if investable_weight > 0 and total_raw < investable_weight - 1e-9:
        residual = investable_weight - total_raw
        anchors = {t: max(0.0, current_weights.get(t, 0.0)) for t in tickers}
        anchor_sum = sum(anchors.values())
        if anchor_sum <= 1e-12:
            anchors = {t: max(0.0, native_weights.get(t, 0.0)) for t in tickers}
            anchor_sum = sum(anchors.values())
            residual_policy = "native_target_residual_anchor"
        else:
            residual_policy = "current_weight_residual_anchor"
        if anchor_sum > 0:
            for t in tickers:
                raw_blend[t] = raw_blend.get(t, 0.0) + residual * anchors.get(t, 0.0) / anchor_sum
    elif investable_weight > 0 and total_raw > investable_weight + 1e-9:
        scale = investable_weight / total_raw
        raw_blend = {t: v * scale for t, v in raw_blend.items()}
        residual_policy = "scaled_down_to_investable_weight"

    final_weights, bound_warnings = normalize_with_bounds(raw_blend, investable_weight, min_w, max_w)
    for t, w in final_weights.items():
        meta_by_ticker.setdefault(t, {})["final_target_weight_pct"] = round6(w * 100)
        meta_by_ticker[t]["residual_policy"] = residual_policy
    return final_weights, meta_by_ticker, conflict_warnings, bound_warnings


def normalize_with_bounds(raw: Dict[str, float], investable: float, min_w: float, max_w: float) -> Tuple[Dict[str, float], List[str]]:
    warnings: List[str] = []
    if investable <= 0 or not raw:
        return {}, ["no_investable_weight_or_empty_pool"]

    # Keep positive raw weights only; min weight is applied only after an asset is selected.
    selected = {k: max(0.0, v) for k, v in raw.items() if v > 1e-12}
    if not selected:
        return {}, ["no_positive_raw_scores"]

    # If too many selected assets for the min weight, keep the strongest names.
    max_selected_by_min = max(1, int(math.floor(investable / min_w))) if min_w > 0 else len(selected)
    if len(selected) > max_selected_by_min:
        selected = dict(sorted(selected.items(), key=lambda kv: kv[1], reverse=True)[:max_selected_by_min])
        warnings.append("pool_pruned_by_min_weight_capacity")

    # Initial normalization.
    total = sum(selected.values()) or 1.0
    weights = {k: investable * v / total for k, v in selected.items()}

    # Drop names below min and renormalize until stable.
    changed = True
    while changed and weights:
        changed = False
        low = [k for k, v in weights.items() if v < min_w - 1e-12]
        if low and len(weights) > 1:
            for k in low:
                weights.pop(k, None)
            total = sum(weights.values()) or 1.0
            weights = {k: investable * v / total for k, v in weights.items()}
            changed = True
            warnings.append("low_weight_assets_excluded")

    # Cap high weights and redistribute residual among uncapped names.
    capped: Dict[str, float] = {}
    free = dict(weights)
    remaining = investable
    while free:
        total_free = sum(free.values()) or 1.0
        proposed = {k: remaining * v / total_free for k, v in free.items()}
        newly_capped = {k: max_w for k, v in proposed.items() if v > max_w}
        if not newly_capped:
            capped.update(proposed)
            break
        capped.update(newly_capped)
        for k in newly_capped:
            free.pop(k, None)
        remaining = investable - sum(capped.values())
        if remaining <= 1e-12:
            break
        warnings.append("single_asset_cap_applied")

    # Final tiny residual correction on largest nonzero row.
    total_out = sum(capped.values())
    if capped and abs(total_out - investable) > 1e-8:
        k = max(capped, key=lambda x: capped[x])
        capped[k] = max(0.0, min(max_w, capped[k] + (investable - total_out)))

    return {k: round6(v) for k, v in capped.items() if v > 1e-8}, warnings


def build_order_lines(
    asset_rows: List[Dict[str, Any]],
    target_weights: Dict[str, float],
    nav_twd: float,
    liquidity_buffer_pct: float,
    cash_balance_twd: float | None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    rows_by_ticker = {asset_key(r): r for r in asset_rows if asset_key(r)}
    current_weights = {
        t: (num(r.get("market_value_twd")) / nav_twd if nav_twd > 0 else 0.0)
        for t, r in rows_by_ticker.items()
    }
    draft_lines: List[Dict[str, Any]] = []
    unit_warnings: List[Dict[str, Any]] = []
    price_quality_excluded: List[Dict[str, Any]] = []

    # First build requested sell/buy lines before buying-power scaling.
    sell_lines: List[Dict[str, Any]] = []
    buy_candidates: List[Dict[str, Any]] = []
    for ticker, row in rows_by_ticker.items():
        current_w = current_weights.get(ticker, 0.0)
        target_w = target_weights.get(ticker, 0.0)
        delta_w = target_w - current_w
        delta_value = delta_w * nav_twd
        price_twd = num(row.get("price_twd"))
        shares = num(row.get("shares"))
        min_unit = max(1.0, num(row.get("minimum_trade_unit"), 1.0))
        asset_kind = str(row.get("asset_kind") or "").lower()
        real_world = bool(row.get("real_world_price_fetched"))
        holdings_snapshot = bool(row.get("holdings_snapshot_price_used"))
        trade_sizing_allowed = bool(row.get("trade_sizing_allowed")) and price_twd > 0
        threshold_unit = min_unit
        if asset_kind == "crypto":
            threshold_unit = max(min_unit, 0.00000001)
        if abs(delta_value) < max(1.0, price_twd * threshold_unit * 0.25):
            continue
        if not trade_sizing_allowed:
            price_quality_excluded.append({
                "ticker": ticker,
                "code": "excluded_from_delegated_draft_due_to_price_quality",
                "severity": "warning",
                "message": "此資產缺少可用的庫存現價 / real-world 價格；可進 target weight pool，但不得產生 BUY / SELL 草案列。",
                "side_if_sized": "BUY" if delta_value > 0 else "SELL",
                "estimated_delta_value_twd_if_sized": round(delta_value, 2),
                "price_provider": row.get("price_provider"),
                "price_quality_status": row.get("price_quality_status", "fallback_or_unavailable"),
                "real_world_price_fetched": real_world,
                "holdings_snapshot_price_used": holdings_snapshot,
            })
            continue
        if price_twd <= 0:
            unit_warnings.append({"ticker": ticker, "code": "missing_price_twd", "severity": "warning", "message": "缺少 TWD 價格，無法 sizing。"})
            continue
        requested_qty = abs(delta_value) / price_twd
        # User rule v10.3: US no fractional shares, TW odd-lot accepted, crypto fractional units allowed.
        if asset_kind == "crypto":
            min_unit = max(0.00000001, min_unit)
        rounded_qty = math.floor(requested_qty / min_unit) * min_unit
        if rounded_qty <= 0:
            unit_warnings.append({"ticker": ticker, "code": "below_minimum_trade_unit", "severity": "warning", "message": "調整金額低於最小交易單位。"})
            continue
        side = "BUY" if delta_value > 0 else "SELL"
        if side == "SELL":
            max_qty = math.floor(shares / min_unit) * min_unit
            if max_qty <= 0:
                unit_warnings.append({"ticker": ticker, "code": "no_sellable_whole_unit", "severity": "warning", "message": "依最小交易單位規則，沒有可賣整數單位。"})
                continue
            rounded_qty = min(rounded_qty, max_qty)
        line = {
            "ticker": ticker,
            "side": side,
            "quantity": round6(rounded_qty),
            "estimated_price_twd": round6(price_twd),
            "estimated_value_twd": round(rounded_qty * price_twd, 2),
            "current_weight_pct": round6(current_w * 100),
            "target_weight_pct": round6(target_w * 100),
            "delta_weight_pct": round6(delta_w * 100),
            "asset_kind": asset_kind,
            "minimum_trade_unit": min_unit,
            "real_world_price_fetched": real_world,
            "holdings_snapshot_price_used": holdings_snapshot,
            "price_quality_status": row.get("price_quality_status", "real_world"),
            "price_provider": row.get("price_provider"),
            "trade_sizing_allowed": trade_sizing_allowed,
            "not_trade_order": True,
        }
        if side == "SELL":
            sell_lines.append(line)
        else:
            buy_candidates.append(line)

    sell_proceeds = sum(num(x.get("estimated_value_twd")) for x in sell_lines)
    cash = cash_balance_twd if cash_balance_twd is not None else 0.0
    cash_buffer_target = nav_twd * liquidity_buffer_pct
    buying_power = max(0.0, cash - cash_buffer_target) + sell_proceeds
    requested_buy = sum(num(x.get("estimated_value_twd")) for x in buy_candidates)
    buy_lines: List[Dict[str, Any]] = []
    scale = 1.0 if requested_buy <= buying_power or requested_buy <= 0 else buying_power / requested_buy

    for line in buy_candidates:
        if scale < 0.999999:
            row = rows_by_ticker[line["ticker"]]
            price_twd = num(row.get("price_twd"))
            min_unit = max(1.0, num(row.get("minimum_trade_unit"), 1.0))
            scaled_qty = math.floor((num(line.get("quantity")) * scale) / min_unit) * min_unit
            if scaled_qty <= 0:
                unit_warnings.append({"ticker": line["ticker"], "code": "buy_scaled_below_minimum_unit", "severity": "warning", "message": "買入因資金約束縮小後低於最小交易單位。"})
                continue
            line = {**line, "quantity": round6(scaled_qty), "estimated_value_twd": round(scaled_qty * price_twd, 2), "buy_scaled_by_available_power": True}
        buy_lines.append(line)

    draft_lines = sorted(sell_lines, key=lambda x: -abs(num(x.get("estimated_value_twd")))) + sorted(buy_lines, key=lambda x: -abs(num(x.get("estimated_value_twd"))))
    price_quality_guard = {
        "enabled": True,
        "rule": "missing_prices_may_enter_target_pool_but_cannot_create_delegated_buy_sell_lines; holdings-table current price is allowed for delegated sizing",
        "trade_sizing_requires_real_world_price": False,
        "holdings_snapshot_price_allowed": True,
        "excluded_line_count": len(price_quality_excluded),
        "excluded_rows": price_quality_excluded,
    }
    sizing_summary = {
        "nav_twd": round(nav_twd, 2),
        "liquidity_buffer_pct": round6(liquidity_buffer_pct * 100),
        "cash_balance_twd": None if cash_balance_twd is None else round(cash_balance_twd, 2),
        "cash_balance_missing_but_internal_rebalance_allowed": cash_balance_twd is None and sell_proceeds > 0,
        "cash_buffer_target_twd": round(cash_buffer_target, 2),
        "sell_proceeds_twd": round(sell_proceeds, 2),
        "requested_buy_twd": round(requested_buy, 2),
        "buying_power_twd": round(buying_power, 2),
        "buy_scaling_factor": round6(scale),
        "draft_line_count": len(draft_lines),
        "unit_warning_count": len(unit_warnings),
        "price_quality_excluded_line_count": len(price_quality_excluded),
    }
    return draft_lines, unit_warnings, sizing_summary, price_quality_guard

def main() -> None:
    config = as_dict(read_json("config/manual_approval_override.json", {}))
    constraints = as_dict(read_json("data/alpha/trading_constraints_snapshot_latest.json", {}))
    policy = load_policy(config, constraints)
    liquidity_buffer_pct = policy["cash_policy"]["liquidity_buffer_pct"]
    liquidity_buffer_source = policy["cash_policy"].get("liquidity_buffer_source", "unknown")

    ranking = as_dict(read_json("data/alpha/rebalance_candidate_ranking_latest.json", {}))  # kept for source context only
    alpha = as_dict(read_json("data/alpha/alpha_research_sandbox_latest.json", {}))  # kept for diagnostics only
    validation = as_dict(read_json("data/alpha/alpha_validation_gate_latest.json", {}))
    daily_quant_context = load_daily_quant_context()

    asset_rows_all = [as_dict(x) for x in as_list(constraints.get("asset_rows")) if asset_key(as_dict(x))]
    pool_limit = int(policy["eligible_pool_policy"]["max_pool_size"])
    asset_rows = asset_rows_all[:pool_limit]
    blockers: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    if len(asset_rows_all) > pool_limit:
        warnings.append({"code": "pool_truncated_to_50", "severity": "warning", "message": "eligible pool 超過 50 檔，已截斷至前 50 檔。"})
    if not asset_rows:
        blockers.append({"code": "no_asset_pool", "severity": "blocker", "message": "沒有可建立 pool 的目前資產。"})
    if not daily_quant_context.get("available"):
        warnings.append({"code": "daily_quant_reference_missing", "severity": "warning", "message": "未讀到 v10.5 Daily Quant / Monte Carlo 參考層；本輪目標權重將退回 v10.4 scoring。"})
    elif not daily_quant_context.get("synthetic_risk_available") or not daily_quant_context.get("monte_carlo_reference_available"):
        warnings.append({"code": "daily_quant_reference_partial", "severity": "warning", "message": "Daily Quant / Monte Carlo 參考不完整；仍納入可用部分，但不啟用交易。"})

    summary0 = as_dict(constraints.get("summary"))
    total_mv = num(summary0.get("total_market_value_twd"), sum(num(r.get("market_value_twd")) for r in asset_rows))
    cash_raw = as_dict(constraints.get("cash_balance")).get("cash_balance_twd", summary0.get("cash_balance_twd"))
    cash_available = cash_raw is not None
    cash_balance_twd = num(cash_raw, 0.0) if cash_available else None
    nav_twd = total_mv + (cash_balance_twd or 0.0)
    if nav_twd <= 0:
        blockers.append({"code": "invalid_nav", "severity": "blocker", "message": "NAV 小於等於 0，不能產生機器委任草案。"})

    # v10.5.1 target source: dual blend of Supabase cloud target and v10.5 native target.
    # Front-end manual MC% remains excluded because it is not materialized for GitHub Actions.
    ranking_rows = [as_dict(x) for x in as_list(ranking.get("ranking_rows"))]
    ranking_rows = sorted(ranking_rows, key=lambda r: num(r.get("rank"), 999999))
    preferred = [r for r in ranking_rows if str(r.get("ranking_status")) == "further_research"] or ranking_rows[:1]
    source_candidate = preferred[0] if preferred else select_ranking_candidate(ranking)

    investable_weight = max(0.0, 1.0 - liquidity_buffer_pct)
    native_weights, native_target_rows, native_meta, native_warnings = build_v105_native_target_weights(
        asset_rows,
        nav_twd,
        investable_weight,
        ranking,
        alpha,
        daily_quant_context,
        MIN_INCLUDED_WEIGHT,
        MAX_SINGLE_WEIGHT,
    )
    for code in native_warnings:
        warnings.append({"code": f"native_target_{code}", "severity": "warning", "message": f"v10.5 原生目標權重正規化警示：{code}"})

    pool_rows: List[Dict[str, Any]] = []
    cloud_available_count = 0
    cloud_missing_count = 0
    native_row_map = {str(r.get("ticker")): r for r in native_target_rows}
    for row in asset_rows:
        ticker = asset_key(row)
        mv = num(row.get("market_value_twd"))
        current_w = mv / nav_twd if nav_twd > 0 else 0.0
        cloud_target_w, cloud_source = parse_cloud_target_weight(row)
        cloud_target_available = cloud_target_w is not None
        if cloud_target_available:
            cloud_available_count += 1
        else:
            cloud_missing_count += 1
        sizing_allowed = bool(row.get("trade_sizing_allowed")) and num(row.get("price_twd")) > 0
        native_row = native_row_map.get(ticker, {})
        pool_rows.append({
            "ticker": ticker,
            "current_weight_pct": round6(current_w * 100),
            "cloud_target_weight_pct": round6(cloud_target_w * 100) if cloud_target_available else None,
            "stock_meta_target_weight_pct": round6(cloud_target_w * 100) if cloud_target_available else None,
            "base_target_weight_source": cloud_source,
            "v105_native_target_weight_pct": native_row.get("v105_native_target_weight_pct"),
            "ranking_target_weight_pct": native_row.get("ranking_target_weight_pct"),
            "alpha_tilt_weight_pct": native_row.get("alpha_tilt_weight_pct"),
            "frontend_mc_percent_target_used": False,
            "market_value_twd": round(mv, 2),
            "real_world_price_fetched": bool(row.get("real_world_price_fetched")),
            "holdings_snapshot_price_used": bool(row.get("holdings_snapshot_price_used")),
            "price_quality_status": row.get("price_quality_status", "real_world" if bool(row.get("real_world_price_fetched")) else "fallback_or_unavailable"),
            "trade_sizing_allowed": sizing_allowed,
            "price_provider": row.get("price_provider"),
            "daily_quant_mc_multiplier": native_row.get("daily_quant_mc_multiplier", 1.0),
            "daily_quant_mc_reasons": native_row.get("daily_quant_mc_reasons", []),
            "mc_fragile_node": bool(native_row.get("mc_fragile_node")),
            "native_raw_before_daily_quant_mc_pct": native_row.get("native_raw_before_daily_quant_mc_pct"),
            "native_raw_after_daily_quant_mc_pct": native_row.get("native_raw_after_daily_quant_mc_pct"),
            "eligible": True,
        })
        if not cloud_target_available:
            warnings.append({"code": "cloud_target_weight_missing", "severity": "warning", "ticker": ticker, "message": "此資產缺少 Supabase stock_meta.target_weight；v10.5.1 會以 v10.5 原生目標補足雲端缺值，不使用前端 MC%。"})
        if not sizing_allowed:
            warnings.append({"code": "non_sizing_price_in_pool", "severity": "warning", "ticker": ticker, "message": "此資產在 pool 中，但缺少可用的庫存現價 / real-world 價格，不能產生交易草案列。"})
        elif bool(row.get("holdings_snapshot_price_used")) and not bool(row.get("real_world_price_fetched")):
            warnings.append({"code": "holdings_snapshot_price_used", "severity": "info", "ticker": ticker, "message": "此資產使用庫存頁現價(TWD)作為委任草案 sizing 價格。"})

    if cloud_available_count <= 0:
        warnings.append({"code": "cloud_target_weights_missing_native_only", "severity": "warning", "message": "未讀到任何 Supabase stock_meta[ticker].target_weight；本輪將退回 v10.5 原生目標權重，不使用前端 MC%。"})

    target_weights, blend_meta_by_ticker, conflict_warnings, weight_warnings = build_dual_blended_targets(
        asset_rows,
        nav_twd,
        investable_weight,
        native_weights,
        MIN_INCLUDED_WEIGHT,
        MAX_SINGLE_WEIGHT,
    )
    warnings.extend(conflict_warnings)
    for code in weight_warnings:
        warnings.append({"code": code, "severity": "warning", "message": code})

    target_rows: List[Dict[str, Any]] = []
    rows_by_ticker = {asset_key(r): r for r in asset_rows}
    for ticker in sorted(rows_by_ticker):
        row = rows_by_ticker[ticker]
        current_w = (num(row.get("market_value_twd")) / nav_twd) if nav_twd > 0 else 0.0
        target_w = target_weights.get(ticker, 0.0)
        delta_w = target_w - current_w
        if abs(delta_w) < 0.000001 and target_w <= 0:
            direction = "UNCHANGED_ZERO"
        elif delta_w > 0.000001:
            direction = "UP"
        elif delta_w < -0.000001:
            direction = "DOWN"
        else:
            direction = "HOLD"
        target_rows.append({
            "ticker": ticker,
            "current_weight_pct": round6(current_w * 100),
            "cloud_target_weight_pct": blend_meta_by_ticker.get(ticker, {}).get("cloud_target_weight_pct"),
            "v105_native_target_weight_pct": blend_meta_by_ticker.get(ticker, {}).get("v105_native_target_weight_pct"),
            "dual_blend_preliminary_target_pct": blend_meta_by_ticker.get(ticker, {}).get("dual_blend_preliminary_target_pct"),
            "machine_target_weight_pct": round6(target_w * 100),
            "final_suggested_weight_pct": round6(target_w * 100),
            "delta_weight_pct": round6(delta_w * 100),
            "dual_target_gap_pct": blend_meta_by_ticker.get(ticker, {}).get("dual_target_gap_pct"),
            "dual_target_direction_conflict": blend_meta_by_ticker.get(ticker, {}).get("dual_target_direction_conflict"),
            "conflict_adjustment_factor": blend_meta_by_ticker.get(ticker, {}).get("conflict_adjustment_factor"),
            "direction": direction,
            "selected_in_target": target_w >= MIN_INCLUDED_WEIGHT - 1e-9,
            "min_weight_rule_pct": round6(MIN_INCLUDED_WEIGHT * 100),
            "max_weight_rule_pct": round6(MAX_SINGLE_WEIGHT * 100),
            "daily_quant_mc_multiplier": next((pr.get("daily_quant_mc_multiplier") for pr in pool_rows if pr.get("ticker") == ticker), 1.0),
            "mc_fragile_node": next((pr.get("mc_fragile_node") for pr in pool_rows if pr.get("ticker") == ticker), False),
        })

    draft_lines: List[Dict[str, Any]] = []
    unit_warnings: List[Dict[str, Any]] = []
    sizing_summary: Dict[str, Any] = {}
    price_quality_guard: Dict[str, Any] = {"enabled": True, "excluded_line_count": 0, "excluded_rows": []}
    if not blockers:
        draft_lines, unit_warnings, sizing_summary, price_quality_guard = build_order_lines(asset_rows, target_weights, nav_twd, liquidity_buffer_pct, cash_balance_twd)
        warnings.extend(as_list(price_quality_guard.get("excluded_rows")))
        warnings.extend(unit_warnings)

    selected_count = sum(1 for v in target_weights.values() if v > 0)
    target_sum_pct = sum(target_weights.values()) * 100
    if blockers:
        status = "blocked"
    elif selected_count > 0 and len(draft_lines) > 0:
        status = "machine_delegated_draft_available"
    elif selected_count > 0:
        status = "machine_delegated_target_available_no_sizing_lines"
    else:
        status = "blocked"

    output = {
        "version": "v10.5.1",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "dual_target_blend_cloud_and_v105_native_engine",
        "safe_mode": True,
        "research_only": True,
        "review_only": True,
        "delegated_draft_mode_enabled": True,
        "target_weight_source": "dual_blend_cloud_target_and_v105_native_target",
        "cloud_target_weight_source": "stock_meta[ticker].target_weight",
        "v105_native_target_source": "ranking_alpha_daily_quant_native_engine",
        "dual_blend_formula": "0.5_cloud_target_plus_0.5_v105_native_target",
        "frontend_mc_percent_target_used": False,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "auto_trade_enabled": False,
        "supabase_write_enabled": False,
        "not_trade_order": True,
        "not_buy_signal": True,
        "not_sell_signal": True,
        "delegated_draft_status": status,
        "policy": policy,
        "summary": {
            "delegated_draft_status": status,
            "pool_asset_count": len(asset_rows),
            "selected_asset_count": selected_count,
            "target_asset_weight_sum_pct": round6(target_sum_pct),
            "liquidity_buffer_pct": round6(liquidity_buffer_pct * 100),
            "cash_target_weight_pct": round6(liquidity_buffer_pct * 100),
            "liquidity_buffer_source": liquidity_buffer_source,
            "zero_liquidity_buffer_is_valid": True,
            "included_asset_min_weight_pct": round6(MIN_INCLUDED_WEIGHT * 100),
            "single_asset_max_weight_pct": round6(MAX_SINGLE_WEIGHT * 100),
            "draft_line_count": len(draft_lines),
            "price_quality_excluded_line_count": int(num(price_quality_guard.get("excluded_line_count"))),
            "trade_sizing_requires_real_world_price": False,
            "holdings_snapshot_price_allowed": True,
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
            "cash_balance_available": cash_available,
            "internal_rebalance_can_fund_buys": True,
            "liquidity_buffer_source": liquidity_buffer_source,
            "cash_balance_twd": None if cash_balance_twd is None else round(cash_balance_twd, 2),
            "cash_balance_missing_but_internal_rebalance_allowed": cash_balance_twd is None and num(sizing_summary.get("sell_proceeds_twd")) > 0,
            "nav_twd": round(nav_twd, 2),
            "cloud_target_weight_available_count": cloud_available_count,
            "cloud_target_weight_missing_count": cloud_missing_count,
            "target_weight_source": "dual_blend_cloud_target_and_v105_native_target",
            "cloud_target_weight_source": "stock_meta[ticker].target_weight",
            "v105_native_target_source": "ranking_alpha_daily_quant_native_engine",
            "dual_blend_cloud_weight": 0.5,
            "dual_blend_v105_native_weight": 0.5,
            "frontend_mc_percent_target_used": False,
            "native_target_weight_sum_pct": native_meta.get("native_target_weight_sum_pct"),
            "native_ranking_candidate_id": native_meta.get("ranking_candidate_id"),
            "native_coefficients": {
                "current_weight": native_meta.get("current_weight_coeff"),
                "ranking_prior": native_meta.get("ranking_prior_coeff"),
                "alpha_research": native_meta.get("alpha_research_coeff"),
            },
            "dual_target_conflict_count": sum(1 for w in warnings if str(w.get("code", "")).startswith(("major_dual_target", "moderate_dual_target", "dual_target_direction"))),
            "source_candidate_id": native_meta.get("ranking_candidate_id"),
            "daily_quant_reference_available": bool(daily_quant_context.get("available")),
            "daily_quant_reference_source": daily_quant_context.get("portfolio_source"),
            "synthetic_risk_available": bool(daily_quant_context.get("synthetic_risk_available")),
            "monte_carlo_reference_available": bool(daily_quant_context.get("monte_carlo_reference_available")),
            "daily_quant_mc_risk_mode": daily_quant_context.get("risk_mode"),
            "mc_fragile_node_count": len(daily_quant_context.get("fragile_nodes") or []),
            "alpha_validation_status": as_dict(validation.get("summary")).get("validation_status"),
            "trade_signal_enabled": False,
            "execution_permission": False,
            "broker_submission_enabled": False,
        },
        "eligible_pool_rows": pool_rows,
        "machine_target_rows": sorted(target_rows, key=lambda x: (-abs(num(x.get("delta_weight_pct"))), x.get("ticker"))),
        "machine_target_weights_pct": {k: round6(v * 100) for k, v in sorted(target_weights.items())},
        "delegated_draft_lines": draft_lines,
        "sizing_summary": sizing_summary,
        "price_quality_guard": price_quality_guard,
        "daily_quant_monte_carlo_context": daily_quant_context,
        "target_weight_generation_notes": [
            "v10.5.1 blends Supabase stock_meta[ticker].target_weight / 雲端% with v10.5 native target weights at 50/50.",
            "v10.5 native target is generated from current weights, v5.2 ranking, alpha research, and Daily Quant / Monte Carlo risk context.",
            "Front-end manual MC% is not used because it is not materialized into Supabase or repo JSON for GitHub Actions.",
            "Large cloud/native conflicts shrink drift; direction conflicts can pause that asset's delegated trade line.",
        ],
        "blockers": blockers,
        "warnings": warnings,
        "source_context": {
            "ranking_candidate_id": source_candidate.get("ranking_id"),
            "ranking_status": source_candidate.get("ranking_status"),
            "alpha_validation_status": as_dict(validation.get("summary")).get("validation_status"),
            "trading_constraints_asset_count": len(asset_rows_all),
        },
        "safety_boundary": [
            "v10.5.1 may generate dual-source machine target weights and a delegated review draft, but it is not a trade order.",
            "Final suggested weight blends Supabase stock_meta[ticker].target_weight / 雲端% and v10.5 native target at 50/50; front-end manual MC% is not used.",
            "It cannot enable trade_signal_enabled, execution_permission, official_rebalance_enabled, auto_trade_enabled, or broker_submission_enabled.",
            "All current assets enter the eligible pool; missing prices cannot create delegated BUY/SELL draft lines, but holdings-table current prices are allowed for delegated sizing.",
            "Internal sells can fund buys even when explicit cash balance is missing; cash balance is not fabricated.",
        ],
    }

    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v10.5.1 Dual Target Blend Engine",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Delegated draft status: **{status}**",
        f"- Pool asset count: `{len(asset_rows)}`",
        f"- Selected asset count: `{selected_count}`",
        f"- Liquidity buffer: `{round6(liquidity_buffer_pct * 100)}`%",
        f"- Liquidity buffer source: `{liquidity_buffer_source}`",
        f"- Daily Quant reference source: `{daily_quant_context.get('portfolio_source')}`",
        f"- Target source: `50% stock_meta[ticker].target_weight + 50% v10.5 native target`",
        f"- v10.5 native candidate: `{native_meta.get('ranking_candidate_id')}`",
        f"- Front-end MC% target used: `False`",
        f"- Cloud target available count: `{cloud_available_count}`",
        f"- Cloud target missing count: `{cloud_missing_count}`",
        f"- Daily Quant / MC risk mode: `{daily_quant_context.get('risk_mode')}`",
        f"- Synthetic risk available: `{daily_quant_context.get('synthetic_risk_available')}`",
        f"- Monte Carlo reference available: `{daily_quant_context.get('monte_carlo_reference_available')}`",
        f"- MC fragile nodes: `{len(daily_quant_context.get('fragile_nodes') or [])}`",
        f"- Target asset weight sum: `{round6(target_sum_pct)}`%",
        f"- Draft line count: `{len(draft_lines)}`",
        f"- Price-quality excluded lines: `{int(num(price_quality_guard.get('excluded_line_count')))} `",
        f"- Blockers: `{len(blockers)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Trade signal enabled: `{output['trade_signal_enabled']}`",
        f"- Execution permission: `{output['execution_permission']}`",
        f"- Broker submission enabled: `{output['broker_submission_enabled']}`",
        "",
        "## Boundary",
        "- v10.5 is an integrated delegated machine draft, not a broker order and not a human-confirmed ticket.",
        "- Final suggested weights blend Supabase stock_meta[ticker].target_weight / 雲端% and v10.5 native target weights at 50/50.",
        "- Daily Quant / Monte Carlo are used inside the v10.5 native target and risk checks; this version still does not consume the browser-only MC% target column.",
        "- Holdings-table current prices may be used for delegated sizing; missing prices cannot generate BUY/SELL draft lines. Internal sells may fund buys even when explicit cash balance is missing.",
    ]) + "\n", encoding="utf-8")

    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Delegated draft status: {status}")
    print(f"Selected assets: {selected_count}")
    print(f"Target source: dual_blend_cloud_50_v105_native_50")
    print(f"Daily Quant / MC risk mode: {daily_quant_context.get('risk_mode')}")
    print(f"MC fragile nodes: {len(daily_quant_context.get('fragile_nodes') or [])}")
    print(f"Draft lines: {len(draft_lines)}")
    print("Execution permission: False")


if __name__ == "__main__":
    main()
