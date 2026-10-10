#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import build_delegated_target_weight_draft_generator as base
from individual_stock_risk_policy import (
    classify_instrument,
    enforce_individual_stock_policy,
    load_policy,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "manual_approval_override.json"
LATEST_PATH = ROOT / "data" / "alpha" / "delegated_target_weight_draft_latest.json"


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


CONFIG = _read_json(CONFIG_PATH)
STOCK_POLICY = load_policy(CONFIG)
LAST_DIAGNOSTICS: Dict[str, Any] = {"enabled": bool(STOCK_POLICY.get("enabled", True))}
LAST_WARNINGS: List[str] = []

_ORIGINAL_NATIVE = base.build_v105_native_target_weights
_ORIGINAL_BLEND = base.build_dual_blended_targets


def _apply_guard(
    weights: Dict[str, float],
    asset_rows: List[Dict[str, Any]],
    investable_weight: float,
    min_w: float,
    max_w: float,
) -> Tuple[Dict[str, float], Dict[str, Any], List[str]]:
    return enforce_individual_stock_policy(
        root=ROOT,
        weights=weights,
        asset_rows=asset_rows,
        investable=investable_weight,
        min_weight=min_w,
        global_max_weight=max_w,
        policy=STOCK_POLICY,
    )


def guarded_native_target_weights(
    asset_rows: List[Dict[str, Any]],
    nav_twd: float,
    investable_weight: float,
    ranking: Dict[str, Any],
    alpha: Dict[str, Any],
    daily_quant_context: Dict[str, Any],
    min_w: float,
    max_w: float,
):
    weights, rows, meta, warnings = _ORIGINAL_NATIVE(
        asset_rows,
        nav_twd,
        investable_weight,
        ranking,
        alpha,
        daily_quant_context,
        min_w,
        max_w,
    )
    guarded, diagnostics, guard_warnings = _apply_guard(
        weights, asset_rows, investable_weight, min_w, max_w
    )
    for row in rows:
        ticker = str(row.get("ticker") or "").strip()
        row["v105_native_target_weight_pct"] = round(guarded.get(ticker, 0.0) * 100, 6)
    meta = dict(meta or {})
    meta["individual_stock_risk_policy"] = diagnostics
    meta["taiwan_individual_stock_risk_policy"] = diagnostics.get("markets", {}).get("taiwan", {})
    meta["us_individual_stock_risk_policy"] = diagnostics.get("markets", {}).get("us", {})
    return guarded, rows, meta, list(warnings or []) + guard_warnings


def guarded_dual_blended_targets(
    asset_rows: List[Dict[str, Any]],
    nav_twd: float,
    investable_weight: float,
    native_weights: Dict[str, float],
    min_w: float,
    max_w: float,
):
    global LAST_DIAGNOSTICS, LAST_WARNINGS
    weights, meta_by_ticker, conflict_warnings, bound_warnings = _ORIGINAL_BLEND(
        asset_rows,
        nav_twd,
        investable_weight,
        native_weights,
        min_w,
        max_w,
    )
    guarded, diagnostics, guard_warnings = _apply_guard(
        weights, asset_rows, investable_weight, min_w, max_w
    )
    asset_map = {str(row.get("ticker") or "").strip(): row for row in asset_rows}
    all_tickers = set(meta_by_ticker) | set(asset_map) | set(guarded)
    for ticker in all_tickers:
        classification = classify_instrument(asset_map.get(ticker, {}), ROOT)
        meta_by_ticker.setdefault(ticker, {})["final_target_weight_pct"] = round(
            guarded.get(ticker, 0.0) * 100, 6
        )
        meta_by_ticker[ticker]["individual_stock_risk_policy_applied"] = classification in {
            "tw_individual_stock",
            "us_individual_stock",
        }
        meta_by_ticker[ticker]["instrument_classification"] = classification
    LAST_DIAGNOSTICS = diagnostics
    LAST_WARNINGS = guard_warnings
    return guarded, meta_by_ticker, conflict_warnings, list(bound_warnings or []) + guard_warnings


def _market_policy(market: str) -> Dict[str, Any]:
    markets = STOCK_POLICY.get("markets") if isinstance(STOCK_POLICY.get("markets"), dict) else {}
    value = markets.get(market)
    return value if isinstance(value, dict) else {}


def _postprocess_output() -> None:
    if not LATEST_PATH.exists():
        return
    doc = _read_json(LATEST_PATH)
    if not doc:
        return

    policy = doc.setdefault("policy", {})
    policy["individual_stock_risk_policy"] = LAST_DIAGNOSTICS
    policy["taiwan_individual_stock_risk_policy"] = LAST_DIAGNOSTICS.get("markets", {}).get("taiwan", {})
    policy["us_individual_stock_risk_policy"] = LAST_DIAGNOSTICS.get("markets", {}).get("us", {})
    target_policy = policy.setdefault("target_generation_policy", {})
    target_policy["individual_stock_policy_enabled"] = bool(STOCK_POLICY.get("enabled", True))

    tw = _market_policy("taiwan")
    us = _market_policy("us")
    target_policy["taiwan_individual_stock_policy_enabled"] = bool(STOCK_POLICY.get("enabled", True))
    target_policy["taiwan_individual_stock_max_weight_pct"] = round(float(tw.get("individual_max_weight", 0.08)) * 100, 6)
    target_policy["taiwan_individual_stock_sleeve_max_weight_pct"] = round(float(tw.get("individual_sleeve_max_weight", 0.15)) * 100, 6)
    target_policy["taiwan_single_issuer_lookthrough_max_weight_pct"] = round(float(tw.get("issuer_lookthrough_max_weight", 0.10)) * 100, 6)
    target_policy["us_individual_stock_max_weight_pct"] = round(float(us.get("individual_max_weight", 0.10)) * 100, 6)
    target_policy["us_individual_stock_sleeve_max_weight_pct"] = round(float(us.get("individual_sleeve_max_weight", 0.25)) * 100, 6)
    target_policy["us_single_issuer_lookthrough_max_weight_pct"] = round(float(us.get("issuer_lookthrough_max_weight", 0.15)) * 100, 6)

    summary = doc.setdefault("summary", {})
    summary["individual_stock_policy_enabled"] = bool(STOCK_POLICY.get("enabled", True))
    for market, prefix in (("taiwan", "taiwan"), ("us", "us")):
        cfg = _market_policy(market)
        diag = LAST_DIAGNOSTICS.get("markets", {}).get(market, {})
        summary[f"{prefix}_individual_stock_target_weight_pct"] = diag.get("individual_stock_target_weight_pct", 0.0)
        summary[f"{prefix}_individual_stock_sleeve_max_weight_pct"] = round(float(cfg.get("individual_sleeve_max_weight", 0.0)) * 100, 6)
        summary[f"{prefix}_single_issuer_lookthrough_max_weight_pct"] = round(float(cfg.get("issuer_lookthrough_max_weight", 0.0)) * 100, 6)

    constraints = _read_json(ROOT / "data" / "alpha" / "trading_constraints_snapshot_latest.json")
    asset_rows = constraints.get("asset_rows") if isinstance(constraints.get("asset_rows"), list) else []
    asset_map = {
        str(row.get("ticker") or "").strip(): row
        for row in asset_rows
        if isinstance(row, dict)
    }
    effective_caps = LAST_DIAGNOSTICS.get("effective_direct_caps_pct", {}) if isinstance(LAST_DIAGNOSTICS, dict) else {}
    global_cap = float(target_policy.get("single_asset_max_weight_pct", 0.40))
    default_cap_pct = round(global_cap * (100 if global_cap <= 1 else 1), 6)

    for section in ("eligible_pool_rows", "machine_target_rows", "delegated_draft_lines"):
        rows = doc.get(section)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            ticker = str(row.get("ticker") or "").strip()
            classification = classify_instrument(asset_map.get(ticker, row), ROOT)
            row["instrument_classification"] = classification
            row["effective_max_weight_rule_pct"] = effective_caps.get(ticker, default_cap_pct)

    warnings = doc.get("warnings") if isinstance(doc.get("warnings"), list) else []
    for warning in LAST_WARNINGS:
        if warning not in warnings:
            warnings.append(warning)
    doc["warnings"] = warnings
    summary["warning_count"] = len(warnings)

    notes = doc.get("target_weight_generation_notes") if isinstance(doc.get("target_weight_generation_notes"), list) else []
    note = (
        "Individual stocks are guarded separately from ETFs. Taiwan: direct stock <= 8%, TW direct-stock sleeve <= 15%, "
        "ETF look-through plus direct exposure to the same issuer <= 10% when feasible. "
        "US: direct stock <= 10%, US direct-stock sleeve <= 25%, ETF look-through plus direct exposure to the same issuer <= 15% when feasible."
    )
    if note not in notes:
        notes.append(note)
    doc["target_weight_generation_notes"] = notes

    LATEST_PATH.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    base.build_v105_native_target_weights = guarded_native_target_weights
    base.build_dual_blended_targets = guarded_dual_blended_targets
    base.main()
    _postprocess_output()


if __name__ == "__main__":
    main()
