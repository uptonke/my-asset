from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DEFAULT_TW_INDIVIDUAL_MAX_WEIGHT = 0.08
DEFAULT_TW_INDIVIDUAL_SLEEVE_MAX_WEIGHT = 0.15
DEFAULT_TW_ISSUER_LOOKTHROUGH_MAX_WEIGHT = 0.10
DEFAULT_US_INDIVIDUAL_MAX_WEIGHT = 0.10
DEFAULT_US_INDIVIDUAL_SLEEVE_MAX_WEIGHT = 0.25
DEFAULT_US_ISSUER_LOOKTHROUGH_MAX_WEIGHT = 0.15

KNOWN_US_FUND_OR_WRAPPER_TICKERS = {
    "AVUV", "BIL", "BOXX", "COPX", "GLD", "GLDM", "GRID", "IAU", "IFRA",
    "IVV", "PICK", "QQQ", "SGOV", "SHV", "SHY", "SLV", "SPY", "SRVR",
    "TBIL", "USMV", "VEA", "VNM", "VOO", "VTI", "VWO", "VXUS",
}
KNOWN_US_CASH_LIKE_TICKERS = {"BIL", "BOXX", "SGOV", "SHV", "SHY", "TBIL"}


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


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _holdings_document(root: Path | None, ticker: str) -> Dict[str, Any]:
    if root is None or not ticker:
        return {}
    return _read_json(root / "data" / "holdings" / "latest" / f"{ticker}.json")


def _has_fund_holdings(root: Path | None, ticker: str) -> bool:
    doc = _holdings_document(root, ticker)
    rows = doc.get("holdings") if isinstance(doc, dict) else None
    return isinstance(rows, list) and len(rows) > 0


def classify_instrument(row: Dict[str, Any], root: Path | None = None) -> str:
    """Classify direct stocks separately from ETFs/wrappers for TW and US risk caps."""
    ticker = _ticker(row)
    asset_kind = str(row.get("asset_kind") or "").strip().lower()
    category = str(row.get("category") or "").strip().lower()
    explicit = " ".join(
        str(row.get(key) or "").strip().lower()
        for key in ("instrument_type", "security_type", "asset_type", "type")
    )

    if asset_kind == "crypto" or "加密" in category or ticker.endswith("-USD"):
        return "crypto"

    is_taiwan = (
        asset_kind == "taiwan"
        or "台股" in category
        or ticker.endswith(".TW")
        or ticker.endswith(".TWO")
    )
    if is_taiwan:
        bare = ticker.removesuffix(".TW").removesuffix(".TWO")
        if any(token in explicit for token in ("etf", "fund", "index fund", "exchange traded")):
            return "tw_etf"
        if any(token in explicit for token in ("stock", "common", "ordinary", "equity")):
            return "tw_individual_stock"
        if bare.startswith("00"):
            return "tw_etf"
        if re.fullmatch(r"\d{4}", bare):
            return "tw_individual_stock"
        return "tw_other"

    is_us = asset_kind == "us" or "美股" in category
    if is_us:
        if ticker in KNOWN_US_CASH_LIKE_TICKERS:
            return "us_cash_like"
        if any(token in explicit for token in ("etf", "fund", "index fund", "exchange traded", "trust")):
            return "us_etf"
        if any(token in explicit for token in ("stock", "common", "ordinary", "equity")):
            return "us_individual_stock"
        if ticker in KNOWN_US_FUND_OR_WRAPPER_TICKERS or _has_fund_holdings(root, ticker):
            return "us_etf"
        # Holdings rows currently identify US securities only as asset_kind='us'.
        # Unknown US symbols therefore default to direct stock unless fund evidence exists.
        if re.fullmatch(r"[A-Z][A-Z0-9.\-/]{0,9}", ticker):
            return "us_individual_stock"
        return "us_other"

    return "other"


def load_policy(config: Dict[str, Any]) -> Dict[str, Any]:
    delegated = config.get("delegated_draft_policy") if isinstance(config, dict) else {}
    delegated = delegated if isinstance(delegated, dict) else {}
    enabled = delegated.get(
        "individual_stock_policy_enabled",
        delegated.get("taiwan_individual_stock_policy_enabled", True),
    )
    return {
        "enabled": bool(enabled),
        "markets": {
            "taiwan": {
                "individual_max_weight": _ratio(
                    delegated.get("taiwan_individual_stock_max_weight_pct"),
                    DEFAULT_TW_INDIVIDUAL_MAX_WEIGHT,
                ),
                "individual_sleeve_max_weight": _ratio(
                    delegated.get("taiwan_individual_stock_sleeve_max_weight_pct"),
                    DEFAULT_TW_INDIVIDUAL_SLEEVE_MAX_WEIGHT,
                ),
                "issuer_lookthrough_max_weight": _ratio(
                    delegated.get("taiwan_single_issuer_lookthrough_max_weight_pct"),
                    DEFAULT_TW_ISSUER_LOOKTHROUGH_MAX_WEIGHT,
                ),
            },
            "us": {
                "individual_max_weight": _ratio(
                    delegated.get("us_individual_stock_max_weight_pct"),
                    DEFAULT_US_INDIVIDUAL_MAX_WEIGHT,
                ),
                "individual_sleeve_max_weight": _ratio(
                    delegated.get("us_individual_stock_sleeve_max_weight_pct"),
                    DEFAULT_US_INDIVIDUAL_SLEEVE_MAX_WEIGHT,
                ),
                "issuer_lookthrough_max_weight": _ratio(
                    delegated.get("us_single_issuer_lookthrough_max_weight_pct"),
                    DEFAULT_US_ISSUER_LOOKTHROUGH_MAX_WEIGHT,
                ),
            },
        },
        "classification_policy": "explicit_metadata_then_holdings_evidence_then_market_ticker_heuristic",
        "issuer_cap_policy": "cap_direct_stock_after_etf_lookthrough; do_not_force_trim_etf",
    }


def _market_for_classification(classification: str) -> str | None:
    if classification.startswith("tw_"):
        return "taiwan"
    if classification.startswith("us_"):
        return "us"
    return None


def _issuer_id(value: Any, market: str) -> str:
    ticker = str(value or "").strip().upper()
    if market == "taiwan":
        ticker = ticker.removesuffix(".TW").removesuffix(".TWO")
        return ticker if re.fullmatch(r"\d{4}", ticker) else ""
    if market == "us":
        ticker = ticker.removesuffix(".US")
        if " " in ticker:
            ticker = ticker.split()[0]
        ticker = ticker.replace("/", ".").replace("-", ".")
        return ticker if re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", ticker) else ""
    return ""


def etf_issuer_exposure(
    root: Path,
    weights: Dict[str, float],
    asset_rows: Iterable[Dict[str, Any]],
    direct_issuers: Dict[str, str],
    market: str,
) -> Dict[str, float]:
    """Return ETF/wrapper look-through exposure only for issuers held directly."""
    row_map = {_ticker(row): row for row in asset_rows if _ticker(row)}
    wanted = set(direct_issuers.values())
    exposure: Dict[str, float] = {issuer: 0.0 for issuer in wanted}

    for ticker, target_weight in weights.items():
        row = row_map.get(ticker.upper(), {})
        classification = classify_instrument(row, root)
        if classification in {"tw_individual_stock", "us_individual_stock"}:
            continue

        holdings = _holdings_document(root, ticker)
        rows = holdings.get("holdings") if isinstance(holdings, dict) else None
        if not isinstance(rows, list):
            continue

        for holding in rows:
            if not isinstance(holding, dict):
                continue
            asset_class = str(holding.get("asset_class") or "").strip().lower()
            if asset_class and asset_class != "equity":
                continue
            issuer = _issuer_id(holding.get("ticker") or holding.get("id"), market)
            if issuer not in wanted:
                continue
            holding_weight = _ratio(holding.get("weight"), 0.0)
            if holding_weight <= 0:
                continue
            exposure[issuer] = exposure.get(issuer, 0.0) + max(0.0, target_weight) * holding_weight

    return {issuer: value for issuer, value in exposure.items() if value > 0.0}


def _normalize_with_caps(
    raw: Dict[str, float],
    investable: float,
    min_weight: float,
    caps: Dict[str, float],
) -> Tuple[Dict[str, float], List[str]]:
    warnings: List[str] = []
    selected = {k: max(0.0, _num(v)) for k, v in raw.items() if _num(v) > 1e-12}
    if investable <= 0 or not selected:
        return {}, ["individual_stock_guard_no_investable_weight_or_empty_pool"]

    if min_weight > 0:
        max_selected = max(1, int(math.floor(investable / min_weight)))
        if len(selected) > max_selected:
            selected = dict(sorted(selected.items(), key=lambda kv: kv[1], reverse=True)[:max_selected])
            warnings.append("individual_stock_guard_pool_pruned_by_min_weight_capacity")

    impossible = [k for k in selected if caps.get(k, 1.0) + 1e-12 < min_weight]
    for key in impossible:
        selected.pop(key, None)
        warnings.append(f"individual_stock_guard_min_weight_exceeds_cap:{key}")
    if not selected:
        return {}, warnings + ["individual_stock_guard_no_assets_after_cap_filter"]

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
        warnings.append(f"individual_stock_guard_capacity_shortfall:{remaining:.8f}")

    while len(fixed) > 1:
        low = [k for k, value in fixed.items() if 0 < value < min_weight - 1e-12]
        if not low:
            break
        for key in low:
            fixed.pop(key, None)
            warnings.append(f"individual_stock_guard_dropped_below_min_weight:{key}")
        raw2 = {k: selected[k] for k in fixed}
        caps2 = {k: caps.get(k, 1.0) for k in fixed}
        fixed, more = _normalize_with_caps(raw2, investable, 0.0, caps2)
        warnings.extend(more)
        break

    return {k: round(v, 8) for k, v in fixed.items() if v > 1e-10}, warnings


def _redistribute_to_non_individual(
    weights: Dict[str, float],
    asset_rows: Iterable[Dict[str, Any]],
    root: Path,
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
            if classify_instrument(row_map.get(ticker.upper(), {}), root)
            not in {"tw_individual_stock", "us_individual_stock"}
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


def enforce_individual_stock_policy(
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
    classifications = {
        ticker: classify_instrument(row_map.get(ticker.upper(), {}), root)
        for ticker in weights
    }
    markets = policy.get("markets") if isinstance(policy.get("markets"), dict) else {}
    direct_by_market: Dict[str, Dict[str, str]] = {"taiwan": {}, "us": {}}
    for ticker, classification in classifications.items():
        market = _market_for_classification(classification)
        if classification not in {"tw_individual_stock", "us_individual_stock"} or market is None:
            continue
        issuer = _issuer_id(ticker, market)
        if issuer:
            direct_by_market[market][ticker] = issuer

    if not direct_by_market["taiwan"] and not direct_by_market["us"]:
        return dict(weights), {
            "enabled": True,
            "individual_tickers": [],
            "effective_direct_caps_pct": {},
            "markets": {
                market: {
                    "individual_stock_target_weight_pct": 0.0,
                    "individual_stock_max_weight_pct": round(_num(cfg.get("individual_max_weight")) * 100, 6),
                    "individual_stock_sleeve_max_weight_pct": round(_num(cfg.get("individual_sleeve_max_weight")) * 100, 6),
                    "single_issuer_lookthrough_max_weight_pct": round(_num(cfg.get("issuer_lookthrough_max_weight")) * 100, 6),
                    "individual_tickers": [],
                    "etf_lookthrough_exposure_pct": {},
                    "final_issuer_exposure_pct": {},
                    "issuer_breaches_pct": {},
                }
                for market, cfg in markets.items()
            },
            "classification_policy": policy["classification_policy"],
            "issuer_cap_policy": policy["issuer_cap_policy"],
        }, []

    warnings: List[str] = []
    guarded = dict(weights)
    diagnostics: Dict[str, Any] = {}

    for _ in range(30):
        caps = {ticker: global_max_weight for ticker in guarded}
        market_diag: Dict[str, Any] = {}
        all_effective_caps: Dict[str, float] = {}

        for market in ("taiwan", "us"):
            cfg = markets.get(market, {})
            direct = direct_by_market[market]
            etf_exposure = etf_issuer_exposure(root, guarded, asset_rows, direct, market)
            effective_caps: Dict[str, float] = {}

            for ticker, issuer in direct.items():
                issuer_limit = _num(cfg.get("issuer_lookthrough_max_weight"))
                issuer_headroom = max(0.0, issuer_limit - etf_exposure.get(issuer, 0.0))
                cap = min(
                    _num(cfg.get("individual_max_weight"), global_max_weight),
                    issuer_headroom,
                    global_max_weight,
                )
                caps[ticker] = cap
                effective_caps[ticker] = cap
                all_effective_caps[ticker] = cap
                if etf_exposure.get(issuer, 0.0) > issuer_limit + 1e-12:
                    warnings.append(f"{market}_issuer_cap_exceeded_by_etf_alone:{issuer}")

            market_diag[market] = {
                "individual_stock_max_weight_pct": round(_num(cfg.get("individual_max_weight")) * 100, 6),
                "individual_stock_sleeve_max_weight_pct": round(_num(cfg.get("individual_sleeve_max_weight")) * 100, 6),
                "single_issuer_lookthrough_max_weight_pct": round(_num(cfg.get("issuer_lookthrough_max_weight")) * 100, 6),
                "individual_tickers": sorted(direct),
                "effective_direct_caps_pct": {k: round(v * 100, 6) for k, v in effective_caps.items()},
                "etf_lookthrough_exposure_pct": {k: round(v * 100, 6) for k, v in etf_exposure.items()},
            }

        guarded, bound_warnings = _normalize_with_caps(guarded, investable, min_weight, caps)
        warnings.extend(bound_warnings)

        for market in ("taiwan", "us"):
            direct = direct_by_market[market]
            cfg = markets.get(market, {})
            individual_total = sum(guarded.get(ticker, 0.0) for ticker in direct)
            sleeve_cap = _num(cfg.get("individual_sleeve_max_weight"))
            if individual_total > sleeve_cap + 1e-12 and individual_total > 0:
                scale = sleeve_cap / individual_total
                released = 0.0
                for ticker in direct:
                    if ticker in guarded:
                        old = guarded[ticker]
                        guarded[ticker] = old * scale
                        released += old - guarded[ticker]
                guarded, residual = _redistribute_to_non_individual(
                    guarded, asset_rows, root, caps, released
                )
                if residual > 1e-8:
                    warnings.append(f"{market}_individual_sleeve_redistribution_shortfall:{residual:.8f}")
                warnings.append(f"{market}_individual_stock_sleeve_cap_applied")

        diagnostics = {
            "enabled": True,
            "individual_tickers": sorted(direct_by_market["taiwan"]) + sorted(direct_by_market["us"]),
            "effective_direct_caps_pct": {k: round(v * 100, 6) for k, v in all_effective_caps.items()},
            "markets": market_diag,
            "classification_policy": policy["classification_policy"],
            "issuer_cap_policy": policy["issuer_cap_policy"],
        }

    for market in ("taiwan", "us"):
        cfg = markets.get(market, {})
        direct = direct_by_market[market]
        final_etf_exposure = etf_issuer_exposure(root, guarded, asset_rows, direct, market)
        issuer_exposure = dict(final_etf_exposure)
        for ticker, issuer in direct.items():
            issuer_exposure[issuer] = issuer_exposure.get(issuer, 0.0) + guarded.get(ticker, 0.0)
        issuer_limit = _num(cfg.get("issuer_lookthrough_max_weight"))
        breaches = {
            issuer: value for issuer, value in issuer_exposure.items()
            if value > issuer_limit + 1e-7
        }
        market_section = diagnostics.setdefault("markets", {}).setdefault(market, {})
        market_section["individual_stock_target_weight_pct"] = round(
            sum(guarded.get(ticker, 0.0) for ticker in direct) * 100, 6
        )
        market_section["final_issuer_exposure_pct"] = {
            k: round(v * 100, 6) for k, v in issuer_exposure.items()
        }
        market_section["issuer_breaches_pct"] = {
            k: round(v * 100, 6) for k, v in breaches.items()
        }
        for issuer in sorted(breaches):
            direct_issuer_ids = set(direct.values())
            if issuer in direct_issuer_ids:
                warnings.append(f"{market}_issuer_cap_breach_after_guard:{issuer}")
            else:
                warnings.append(f"{market}_issuer_cap_breach_not_caused_by_direct_stock:{issuer}")

    seen = set()
    warnings = [item for item in warnings if not (item in seen or seen.add(item))]
    return {k: round(v, 8) for k, v in guarded.items()}, diagnostics, warnings
