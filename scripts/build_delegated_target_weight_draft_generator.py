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
        "version": "v10.4",
        "name": "Delegated Target Weight & Draft Generator with Liquidity Buffer Source-of-Truth Guard",
        "eligible_pool_policy": {
            "pool_source": "all_current_assets",
            "max_pool_size": int(num(delegated.get("max_pool_size"), MAX_POOL_SIZE)),
            "asset_class_required": False,
            "allow_all_assets_into_pool": True,
        },
        "target_generation_policy": {
            "target_weight_source": "machine_generated_this_run",
            "use_external_target_weights": False,
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


def asset_key(row: Dict[str, Any]) -> str:
    return str(row.get("ticker") or row.get("symbol") or "").strip()


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

    ranking = as_dict(read_json("data/alpha/rebalance_candidate_ranking_latest.json", {}))
    alpha = as_dict(read_json("data/alpha/alpha_research_sandbox_latest.json", {}))
    validation = as_dict(read_json("data/alpha/alpha_validation_gate_latest.json", {}))

    asset_rows_all = [as_dict(x) for x in as_list(constraints.get("asset_rows")) if asset_key(as_dict(x))]
    pool_limit = int(policy["eligible_pool_policy"]["max_pool_size"])
    asset_rows = asset_rows_all[:pool_limit]
    blockers: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    if len(asset_rows_all) > pool_limit:
        warnings.append({"code": "pool_truncated_to_50", "severity": "warning", "message": "eligible pool 超過 50 檔，已截斷至前 50 檔。"})
    if not asset_rows:
        blockers.append({"code": "no_asset_pool", "severity": "blocker", "message": "沒有可建立 pool 的目前資產。"})

    summary0 = as_dict(constraints.get("summary"))
    total_mv = num(summary0.get("total_market_value_twd"), sum(num(r.get("market_value_twd")) for r in asset_rows))
    cash_raw = as_dict(constraints.get("cash_balance")).get("cash_balance_twd", summary0.get("cash_balance_twd"))
    cash_available = cash_raw is not None
    cash_balance_twd = num(cash_raw, 0.0) if cash_available else None
    nav_twd = total_mv + (cash_balance_twd or 0.0)
    if nav_twd <= 0:
        blockers.append({"code": "invalid_nav", "severity": "blocker", "message": "NAV 小於等於 0，不能產生機器委任草案。"})

    # Ranking prior: use top-ranked research candidate when available, but do not require it.
    ranking_rows = [as_dict(x) for x in as_list(ranking.get("ranking_rows"))]
    ranking_rows = sorted(ranking_rows, key=lambda r: num(r.get("rank"), 999999))
    preferred = [r for r in ranking_rows if str(r.get("ranking_status")) == "further_research"] or ranking_rows[:1]
    source_candidate = preferred[0] if preferred else {}
    ranking_weights = {str(k): num(v) / 100.0 for k, v in as_dict(source_candidate.get("weights_pct")).items()}

    alpha_rows = {str(r.get("ticker")): as_dict(r) for r in as_list(alpha.get("asset_alpha_research")) if as_dict(r).get("ticker")}
    alpha_scores = {k: num(v.get("alpha_research_score")) for k, v in alpha_rows.items()}
    score_min = min(alpha_scores.values()) if alpha_scores else 0.0
    score_max = max(alpha_scores.values()) if alpha_scores else 1.0
    denom = score_max - score_min if score_max > score_min else 1.0

    raw: Dict[str, float] = {}
    pool_rows: List[Dict[str, Any]] = []
    for row in asset_rows:
        ticker = asset_key(row)
        mv = num(row.get("market_value_twd"))
        current_w = mv / nav_twd if nav_twd > 0 else 0.0
        rank_w = ranking_weights.get(ticker, 0.0)
        alpha_score = alpha_scores.get(ticker)
        alpha_norm = 0.5 if alpha_score is None else (alpha_score - score_min) / denom
        sizing_allowed = bool(row.get("trade_sizing_allowed")) and num(row.get("price_twd")) > 0
        data_quality_multiplier = 1.0 if sizing_allowed else 0.55
        raw_score = max(0.0001, (0.50 * current_w) + (0.35 * rank_w) + (0.15 * alpha_norm / max(1, len(asset_rows)))) * data_quality_multiplier
        raw[ticker] = raw_score
        pool_rows.append({
            "ticker": ticker,
            "current_weight_pct": round6(current_w * 100),
            "market_value_twd": round(mv, 2),
            "real_world_price_fetched": bool(row.get("real_world_price_fetched")),
            "holdings_snapshot_price_used": bool(row.get("holdings_snapshot_price_used")),
            "price_quality_status": row.get("price_quality_status", "real_world" if bool(row.get("real_world_price_fetched")) else "fallback_or_unavailable"),
            "trade_sizing_allowed": sizing_allowed,
            "price_provider": row.get("price_provider"),
            "alpha_research_score": None if alpha_score is None else round6(alpha_score),
            "ranking_prior_weight_pct": round6(rank_w * 100),
            "eligible": True,
        })
        if not sizing_allowed:
            warnings.append({"code": "non_sizing_price_in_pool", "severity": "warning", "ticker": ticker, "message": "此資產在 pool 中，但缺少可用的庫存現價 / real-world 價格，不能產生交易草案列。"})
        elif bool(row.get("holdings_snapshot_price_used")) and not bool(row.get("real_world_price_fetched")):
            warnings.append({"code": "holdings_snapshot_price_used", "severity": "info", "ticker": ticker, "message": "此資產使用庫存頁現價(TWD)作為委任草案 sizing 價格。"})

    investable_weight = max(0.0, 1.0 - liquidity_buffer_pct)
    target_weights, weight_warnings = normalize_with_bounds(raw, investable_weight, MIN_INCLUDED_WEIGHT, MAX_SINGLE_WEIGHT)
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
            "machine_target_weight_pct": round6(target_w * 100),
            "delta_weight_pct": round6(delta_w * 100),
            "direction": direction,
            "selected_in_target": target_w >= MIN_INCLUDED_WEIGHT - 1e-9,
            "min_weight_rule_pct": round6(MIN_INCLUDED_WEIGHT * 100),
            "max_weight_rule_pct": round6(MAX_SINGLE_WEIGHT * 100),
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
        "version": "v10.4",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "delegated_target_weight_and_draft_generator",
        "safe_mode": True,
        "research_only": True,
        "review_only": True,
        "delegated_draft_mode_enabled": True,
        "target_weight_source": "machine_generated_this_run",
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
            "source_candidate_id": source_candidate.get("ranking_id"),
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
        "blockers": blockers,
        "warnings": warnings,
        "source_context": {
            "ranking_candidate_id": source_candidate.get("ranking_id"),
            "ranking_status": source_candidate.get("ranking_status"),
            "alpha_validation_status": as_dict(validation.get("summary")).get("validation_status"),
            "trading_constraints_asset_count": len(asset_rows_all),
        },
        "safety_boundary": [
            "v10.4 may generate machine target weights and a delegated review draft, but it is not a trade order.",
            "It cannot enable trade_signal_enabled, execution_permission, official_rebalance_enabled, auto_trade_enabled, or broker_submission_enabled.",
            "All current assets enter the eligible pool; missing prices cannot create delegated BUY/SELL draft lines, but holdings-table current prices are allowed for delegated sizing.",
            "Internal sells can fund buys even when explicit cash balance is missing; cash balance is not fabricated.",
        ],
    }

    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v10.4 Delegated Target Weight & Draft Generator",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Delegated draft status: **{status}**",
        f"- Pool asset count: `{len(asset_rows)}`",
        f"- Selected asset count: `{selected_count}`",
        f"- Liquidity buffer: `{round6(liquidity_buffer_pct * 100)}`%",
        f"- Liquidity buffer source: `{liquidity_buffer_source}`",
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
        "- v10.4 is a delegated machine draft, not a broker order and not a human-confirmed ticket.",
        "- The target weights are generated this run from current assets, ranking priors, alpha research scores, liquidity buffer and unit constraints. Holdings-table current prices may be used for delegated sizing; missing prices cannot generate BUY/SELL draft lines. Internal sells may fund buys even when explicit cash balance is missing.",
    ]) + "\n", encoding="utf-8")

    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Delegated draft status: {status}")
    print(f"Selected assets: {selected_count}")
    print(f"Draft lines: {len(draft_lines)}")
    print("Execution permission: False")


if __name__ == "__main__":
    main()
