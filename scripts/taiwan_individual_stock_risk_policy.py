"""Backward-compatible Taiwan-only facade.

New code should import individual_stock_risk_policy directly.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Tuple

from individual_stock_risk_policy import (
    classify_instrument as _classify_instrument,
    enforce_individual_stock_policy,
    load_policy,
)


def classify_instrument(row: Dict[str, Any]) -> str:
    classification = _classify_instrument(row)
    return classification if classification.startswith("tw_") else "other"


def enforce_taiwan_individual_stock_policy(
    *,
    root: Path,
    weights: Dict[str, float],
    asset_rows: List[Dict[str, Any]],
    investable: float,
    min_weight: float,
    global_max_weight: float,
    policy: Dict[str, Any],
) -> Tuple[Dict[str, float], Dict[str, Any], List[str]]:
    generic_policy = deepcopy(policy)
    if "markets" not in generic_policy:
        generic_policy = load_policy({})
    # Preserve the old function's Taiwan-only behavior: US direct stocks are not constrained here.
    generic_policy.setdefault("markets", {})["us"] = {
        "individual_max_weight": global_max_weight,
        "individual_sleeve_max_weight": 1.0,
        "issuer_lookthrough_max_weight": 1.0,
    }
    guarded, diagnostics, warnings = enforce_individual_stock_policy(
        root=root,
        weights=weights,
        asset_rows=asset_rows,
        investable=investable,
        min_weight=min_weight,
        global_max_weight=global_max_weight,
        policy=generic_policy,
    )
    tw_cfg = generic_policy.get("markets", {}).get("taiwan", {})
    tw_diag = diagnostics.get("markets", {}).get("taiwan", {})
    legacy = {
        "enabled": diagnostics.get("enabled", True),
        "tw_individual_stock_max_weight_pct": round(float(tw_cfg.get("individual_max_weight", 0.08)) * 100, 6),
        "tw_individual_stock_sleeve_max_weight_pct": round(float(tw_cfg.get("individual_sleeve_max_weight", 0.15)) * 100, 6),
        "tw_single_issuer_lookthrough_max_weight_pct": round(float(tw_cfg.get("issuer_lookthrough_max_weight", 0.10)) * 100, 6),
        "tw_individual_stock_target_weight_pct": tw_diag.get("individual_stock_target_weight_pct", 0.0),
        "individual_tickers": tw_diag.get("individual_tickers", []),
        "effective_direct_caps_pct": tw_diag.get("effective_direct_caps_pct", {}),
        "etf_lookthrough_exposure_pct": tw_diag.get("etf_lookthrough_exposure_pct", {}),
        "final_issuer_exposure_pct": tw_diag.get("final_issuer_exposure_pct", {}),
        "issuer_breaches_pct": tw_diag.get("issuer_breaches_pct", {}),
        "classification_policy": generic_policy.get("classification_policy"),
        "issuer_cap_policy": generic_policy.get("issuer_cap_policy"),
    }
    return guarded, legacy, warnings
