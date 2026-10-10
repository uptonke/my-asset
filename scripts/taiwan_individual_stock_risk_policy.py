from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DEFAULT_TW_INDIVIDUAL_MAX_WEIGHT = 0.08
DEFAULT_TW_INDIVIDUAL_SLEEVE_MAX_WEIGHT = 0.15
DEFAULT_TW_ISSUER_LOOKTHROUGH_MAX_WEIGHT = 0.10


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        number = float(value)
        return number if math.isfinite(number) else default
    except Exception:
        return default


def _ratio(value: Any, default: float) -> float:
    number = _num(value, default)
    if number > 1.0:
        number /= 100.0
    return max(0.0, min(1.0, number))


def _ticker(row: Dict[str, Any]) -> str:
    return str(row.get("ticker") or row.get("symbol") or "").strip().upper()


def classify_instrument(row: Dict[str, Any]) -> str:
    """Classify only what this guard needs; unknowns remain uncapped by TW-stock rules."""
    ticker = _ticker(row)
    asset_kind = str(row.get("asset_kind") or "").strip().lower()
    category = str(row.get("category") or "").strip().lower()
    explicit = " ".join(
        str(row.get(key) or "").strip().lower()
        for key in ("instrument_type", "security_type", "asset_type", "type")
    )

    is_taiwan = asset_kind == "taiwan" or "台股" in category or ticker.endswith(".TW") or ticker.endswith(".TWO")
    if not is_taiwan:
        return "other"

    bare = ticker.removesuffix(".TW").removesuffix(".TWO")
    if any(token in explicit for token in ("etf", "fund", "index fund", "exchange traded")):
        return "tw_etf"
    if any(token in explicit for token in ("stock", "common", "ordinary", "equity")):
        return "tw_individual_stock"

    # TWSE/TPEX ETFs and active ETFs use 00-prefixed tickers (e.g. 0050, 00981A).
    if bare.startswith("00"):
        return "tw_etf"
    # Ordinary Taiwan listed stocks are generally four numeric digits (e.g. 2303, 2317, 2382).
    if re.fullmatch(r"\d{4}", bare):
        return "tw_individual_stock"
    return "tw_other"


def load_policy(config: Dict[str, Any]) -> Dict[str, Any]:
    delegated = config.get("delegated_draft_policy") if isinstance(config, dict) else {}
    delegated = delegated if isinstance(delegated, dict) else {}
    enabled = delegated.get("taiwan_individual_stock_policy_enabled", True)
    return {
        "enabled": bool(enabled),
        "tw_individual_stock_max_weight": _ratio(
            delegated.get("taiwan_individual_stock_max_weight_pct"),
            DEFAULT_TW_INDIVIDUAL_MAX_WEIGHT,
        ),
        "tw_individual_stock_sleeve_max_weight": _ratio(
            delegated.get("taiwan_individual_stock_sleeve_max_weight_pct"),
            DEFAULT_TW_INDIVIDUAL_SLEEVE_MAX_WEIGHT,
        ),
        "tw_issuer_lookthrough_max_weight": _ratio(
            delegated.get("taiwan_single_issuer_lookthrough_max_weight_pct"),
            DEFAULT_TW_ISSUER_LOOKTHROUGH_MAX_WEIGHT,
        ),
        "classification_policy": "explicit_metadata_then_taiwan_ticker_heuristic",
        "issuer_cap_policy": "cap_direct_stock_after_etf_lookthrough; do_not_force_trim_etf",
    }


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _is_taiwan_common_ticker(value: Any) -> bool:
    ticker = str(value or "").strip().upper().removesuffix(".TW").removesuffix(".TWO")
    return bool(re.fullmatch(r"\d{4}", ticker) and not ticker.startswith("00"))


def etf_taiwan_issuer_exposure(
    root: Path,
    weights: Dict[str, float],
    asset_rows: Iterable[Dict[str, Any]],
) -> Dict[str, float]:
    row_map = {_ticker(row): row for row in asset_rows if _ticker(row)}
    exposure: Dict[str, float] = {}
    for ticker, target_weight in weights.items():
        row = row_map.get(ticker.upper(), {})
        if classify_instrument(row) == "tw_individual_stock":
            continue
        holdings = _read_json(root / "data" / "holdings" / "latest" / f"{ticker}.json")
        rows = holdings.get("holdings") if isinstance(holdings, dict) else None
        if not isinstance(rows, list):
            continue
        for holding in rows:
            if not isinstance(holding, dict):
                continue
            if str(holding.get("asset_class") or "").strip().lower() != "equity":
                continue
            country = str(holding.get("country") or "").strip().lower()
            underlying = str(holding.get("ticker") or holding.get("id") or "").strip().upper()
            taiwan_countries = {"taiwan", "tw", "taiwan, province of china"}
            if country and country not in taiwan_countries:
                continue
            if not country and not (underlying.endswith(".TW") or underlying.endswith(".TWO")):
                continue
            if not _is_taiwan_common_ticker(underlying):
                continue
            bare = underlying.removesuffix(".TW").removesuffix(".TWO")
            holding_weight = _ratio(holding.get("weight"), 0.0)
            if holding_weight <= 0:
                continue
            exposure[bare] = exposure.get(bare, 0.0) + max(0.0, target_weight) * holding_weight
    return exposure


def _normalize_with_caps(
    raw: Dict[str, float],
    investable: float,
    min_weight: float,
    caps: Dict[str, float],
) -> Tuple[Dict[str, float], List[str]]:
    warnings: List[str] = []
    selected = {k: max(0.0, float(v)) for k, v in raw.items() if _num(v) > 1e-12}
    if investable <= 0 or not selected:
        return {}, ["tw_stock_guard_no_investable_weight_or_empty_pool"]

    if min_weight > 0:
        max_selected = max(1, int(math.floor(investable / min_weight)))
        if len(selected) > max_selected:
            selected = dict(sorted(selected.items(), key=lambda kv: kv[1], reverse=True)[:max_selected])
            warnings.append("tw_stock_guard_pool_pruned_by_min_weight_capacity")

    # Drop names that cannot satisfy the configured minimum because their own cap is lower.
    impossible = [k for k in selected if caps.get(k, 1.0) + 1e-12 < min_weight]
    for key in impossible:
        selected.pop(key, None)
        warnings.append(f"tw_stock_guard_min_weight_exceeds_cap:{key}")
    if not selected:
        return {}, warnings + ["tw_stock_guard_no_assets_after_cap_filter"]

    # Water-fill using original relative weights while respecting heterogeneous caps.
    free = dict(selected)
    fixed: Dict[str, float] = {}
    remaining = investable
    while free and remaining > 1e-12:
        raw_total = sum(free.values()) or 1.0
        proposed = {k: remaining * value / raw_total for k, value in free.items()}
        hit = [k for k, value in proposed.items() if value > caps.get(k, 1.0) + 1e-12]
        if not hit:
            fixed.update(proposed)
            remaining = 0.0
            break
        for key in hit:
            cap = max(0.0, caps.get(key, 1.0))
            fixed[key] = cap
            remaining -= cap
            free.pop(key, None)
        remaining = max(0.0, remaining)

    if free and remaining > 1e-12:
        raw_total = sum(free.values()) or 1.0
        for key, value in free.items():
            fixed[key] = remaining * value / raw_total
        remaining = 0.0

    if remaining > 1e-8:
        warnings.append(f"tw_stock_guard_capacity_shortfall:{remaining:.8f}")

    # Enforce min weight on selected positions, then re-water-fill without reintroducing dropped names.
    while len(fixed) > 1:
        low = [k for k, value in fixed.items() if 0 < value < min_weight - 1e-12]
        if not low:
            break
        for key in low:
            fixed.pop(key, None)
            warnings.append(f"tw_stock_guard_dropped_below_min_weight:{key}")
        raw2 = {k: selected[k] for k in fixed}
        caps2 = {k: caps.get(k, 1.0) for k in fixed}
        fixed, more = _normalize_with_caps(raw2, investable, 0.0, caps2)
        warnings.extend(more)
        break

    return {k: round(v, 8) for k, v in fixed.items() if v > 1e-10}, warnings


def _redistribute_to_non_individual(
    weights: Dict[str, float],
    asset_rows: Iterable[Dict[str, Any]],
    caps: Dict[str, float],
    released: float,
) -> Tuple[Dict[str, float], float]:
    if released <= 1e-12:
        return weights, 0.0
    row_map = {_ticker(row): row for row in asset_rows if _ticker(row)}
    out = dict(weights)
    remaining = released
    for _ in range(20):
        candidates = [
            ticker for ticker, value in out.items()
            if classify_instrument(row_map.get(ticker.upper(), {})) != "tw_individual_stock"
            and caps.get(ticker, 1.0) - value > 1e-12
        ]
        if not candidates or remaining <= 1e-12:
            break
        basis = sum(max(out.get(t, 0.0), 1e-6) for t in candidates)
        consumed = 0.0
        for ticker in candidates:
            headroom = max(0.0, caps.get(ticker, 1.0) - out.get(ticker, 0.0))
            allocation = remaining * max(out.get(ticker, 0.0), 1e-6) / basis
            add = min(headroom, allocation)
            out[ticker] = out.get(ticker, 0.0) + add
            consumed += add
        if consumed <= 1e-12:
            break
        remaining = max(0.0, remaining - consumed)
    return out, remaining


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
    if not policy.get("enabled", True):
        return dict(weights), {"enabled": False}, []

    row_map = {_ticker(row): row for row in asset_rows if _ticker(row)}
    individual_tickers = {
        ticker for ticker in weights
        if classify_instrument(row_map.get(ticker.upper(), {})) == "tw_individual_stock"
    }
    warnings: List[str] = []
    guarded = dict(weights)
    diagnostics: Dict[str, Any] = {}

    if not individual_tickers:
        etf_exposure = etf_taiwan_issuer_exposure(root, guarded, asset_rows)
        diagnostics = {
            "enabled": True,
            "tw_individual_stock_max_weight_pct": round(policy["tw_individual_stock_max_weight"] * 100, 6),
            "tw_individual_stock_sleeve_max_weight_pct": round(policy["tw_individual_stock_sleeve_max_weight"] * 100, 6),
            "tw_single_issuer_lookthrough_max_weight_pct": round(policy["tw_issuer_lookthrough_max_weight"] * 100, 6),
            "tw_individual_stock_target_weight_pct": 0.0,
            "individual_tickers": [],
            "effective_direct_caps_pct": {},
            "etf_lookthrough_exposure_pct": {k: round(v * 100, 6) for k, v in etf_exposure.items()},
            "final_issuer_exposure_pct": {k: round(v * 100, 6) for k, v in etf_exposure.items()},
            "issuer_breaches_pct": {},
            "classification_policy": policy["classification_policy"],
            "issuer_cap_policy": policy["issuer_cap_policy"],
        }
        return dict(weights), diagnostics, []

    for _ in range(4):
        etf_exposure = etf_taiwan_issuer_exposure(root, guarded, asset_rows)
        caps = {ticker: global_max_weight for ticker in guarded}
        effective_direct_caps: Dict[str, float] = {}
        for ticker in individual_tickers:
            bare = ticker.upper().removesuffix(".TW").removesuffix(".TWO")
            issuer_headroom = max(0.0, policy["tw_issuer_lookthrough_max_weight"] - etf_exposure.get(bare, 0.0))
            cap = min(policy["tw_individual_stock_max_weight"], issuer_headroom, global_max_weight)
            caps[ticker] = cap
            effective_direct_caps[ticker] = cap
            if etf_exposure.get(bare, 0.0) > policy["tw_issuer_lookthrough_max_weight"] + 1e-12:
                warnings.append(f"tw_issuer_cap_exceeded_by_etf_alone:{bare}")

        guarded, bound_warnings = _normalize_with_caps(guarded, investable, min_weight, caps)
        warnings.extend(bound_warnings)

        individual_total = sum(guarded.get(t, 0.0) for t in individual_tickers)
        sleeve_cap = policy["tw_individual_stock_sleeve_max_weight"]
        if individual_total > sleeve_cap + 1e-12 and individual_total > 0:
            scale = sleeve_cap / individual_total
            released = 0.0
            for ticker in individual_tickers:
                if ticker in guarded:
                    old = guarded[ticker]
                    guarded[ticker] = old * scale
                    released += old - guarded[ticker]
            guarded, residual = _redistribute_to_non_individual(guarded, asset_rows, caps, released)
            if residual > 1e-8:
                warnings.append(f"tw_individual_sleeve_redistribution_shortfall:{residual:.8f}")
            warnings.append("tw_individual_stock_sleeve_cap_applied")

        diagnostics = {
            "enabled": True,
            "tw_individual_stock_max_weight_pct": round(policy["tw_individual_stock_max_weight"] * 100, 6),
            "tw_individual_stock_sleeve_max_weight_pct": round(policy["tw_individual_stock_sleeve_max_weight"] * 100, 6),
            "tw_single_issuer_lookthrough_max_weight_pct": round(policy["tw_issuer_lookthrough_max_weight"] * 100, 6),
            "tw_individual_stock_target_weight_pct": round(sum(guarded.get(t, 0.0) for t in individual_tickers) * 100, 6),
            "individual_tickers": sorted(individual_tickers),
            "effective_direct_caps_pct": {k: round(v * 100, 6) for k, v in effective_direct_caps.items()},
            "etf_lookthrough_exposure_pct": {k: round(v * 100, 6) for k, v in etf_exposure.items()},
            "classification_policy": policy["classification_policy"],
            "issuer_cap_policy": policy["issuer_cap_policy"],
        }

    final_etf_exposure = etf_taiwan_issuer_exposure(root, guarded, asset_rows)
    issuer_exposure = dict(final_etf_exposure)
    for ticker in individual_tickers:
        bare = ticker.upper().removesuffix(".TW").removesuffix(".TWO")
        issuer_exposure[bare] = issuer_exposure.get(bare, 0.0) + guarded.get(ticker, 0.0)
    breaches = {
        ticker: value for ticker, value in issuer_exposure.items()
        if value > policy["tw_issuer_lookthrough_max_weight"] + 1e-7
    }
    diagnostics["final_issuer_exposure_pct"] = {k: round(v * 100, 6) for k, v in issuer_exposure.items()}
    diagnostics["issuer_breaches_pct"] = {k: round(v * 100, 6) for k, v in breaches.items()}
    for ticker in sorted(breaches):
        if ticker not in individual_tickers:
            warnings.append(f"tw_issuer_cap_breach_not_caused_by_direct_stock:{ticker}")
        else:
            warnings.append(f"tw_issuer_cap_breach_after_guard:{ticker}")

    # De-duplicate while preserving order.
    seen = set()
    warnings = [item for item in warnings if not (item in seen or seen.add(item))]
    return {k: round(v, 8) for k, v in guarded.items()}, diagnostics, warnings
