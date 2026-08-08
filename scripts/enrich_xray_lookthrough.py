#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

SUPPORTED_FUNDS: Tuple[str, ...] = ("QQQ", "IFRA", "GRID", "COPX", "VNM", "SRVR")
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOLDINGS_DIR = REPO_ROOT / "data" / "holdings" / "latest"

SPECIAL_EXPOSURE_MODES = {
    "BOXX": "DERIVATIVE_STRATEGY",
    "SHY": "BOND_LOOKTHROUGH",
    "GLDM": "COMMODITY_PHYSICAL",
    "BTC": "DIRECT_CRYPTO",
    "BTC-USD": "DIRECT_CRYPTO",
    "ETH": "DIRECT_CRYPTO",
    "ETH-USD": "DIRECT_CRYPTO",
    "加密貨幣": "DIRECT_CRYPTO",
}

CORPORATE_SUFFIXES = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY",
    "LTD", "LIMITED", "PLC", "SA", "AG", "NV", "SE", "SPA",
    "HOLDING", "HOLDINGS", "ORD", "COMMON", "STOCK",
}


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except (TypeError, ValueError):
        return default


def _ticker(value: Any) -> str:
    return str(value or "").strip().upper()


def _norm_name(value: Any) -> str:
    text = str(value or "").upper().replace("&", " AND ")
    tokens = re.findall(r"[A-Z0-9]+", text)
    while tokens and tokens[-1] in CORPORATE_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def _is_simple_exchange_ticker(value: str) -> bool:
    # Safe for the US-style symbols that dominate cross-fund overlap here.
    # International vendor-specific tickers fall back to normalized issuer name.
    return bool(re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", value))


def security_key(holding: Mapping[str, Any]) -> str:
    ticker = _ticker(holding.get("ticker"))
    name = _norm_name(holding.get("name"))
    asset_class = str(holding.get("asset_class") or "").strip().lower()

    if asset_class != "equity":
        return ""
    if ticker and _is_simple_exchange_ticker(ticker) and ticker not in {"USD", "CASH"}:
        return f"T:{ticker}"
    if name:
        return f"N:{name}"

    ident = str(holding.get("id") or "").strip().upper()
    id_type = str(holding.get("id_type") or "ID").strip().upper()
    return f"{id_type}:{ident}" if ident else ""


def load_snapshot(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"snapshot is not an object: {path}")
    holdings = payload.get("holdings")
    if not isinstance(holdings, list) or not holdings:
        raise ValueError(f"snapshot has no holdings: {path}")
    return payload


def load_holdings_set(holdings_dir: Path = DEFAULT_HOLDINGS_DIR) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    snapshots: Dict[str, Dict[str, Any]] = {}
    errors: Dict[str, str] = {}

    summary: Dict[str, Any] = {}
    summary_path = holdings_dir / "summary.json"
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors["summary"] = f"{type(exc).__name__}: {exc}"

    for fund in SUPPORTED_FUNDS:
        path = holdings_dir / f"{fund}.json"
        if not path.exists():
            errors[fund] = "snapshot_missing"
            continue
        try:
            snapshots[fund] = load_snapshot(path)
        except Exception as exc:
            errors[fund] = f"{type(exc).__name__}: {exc}"

    return snapshots, {"summary": summary, "errors": errors}


def portfolio_asset_weights_from_xray(xray_meta: Mapping[str, Any]) -> Dict[str, float]:
    """Return exact-label capital weights as decimal portfolio weights.

    fix_xray_twd_weights.py writes weight_pct against total TWD holdings. Rows whose
    labels combine multiple assets ("A/B") are intentionally not split because the
    individual capital weights are not recoverable from that aggregate row.
    """
    weights: Dict[str, float] = {}
    for row in xray_meta.get("mrc_table") or []:
        if not isinstance(row, Mapping):
            continue
        label = str(row.get("ticker") or "").strip()
        if not label or "/" in label:
            continue
        weight_pct = _num(row.get("weight_pct"))
        if weight_pct is None or weight_pct <= 0:
            continue
        weights[_ticker(label)] = weight_pct / 100.0
    return weights


def _snapshot_freshness_days(snapshot: Mapping[str, Any]) -> int | None:
    raw = str(snapshot.get("as_of") or "").strip()
    try:
        as_of = date.fromisoformat(raw)
    except ValueError:
        return None
    return max(0, (datetime.now(timezone.utc).date() - as_of).days)


def _fund_equity_map(snapshot: Mapping[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = defaultdict(float)
    for holding in snapshot.get("holdings") or []:
        if not isinstance(holding, Mapping):
            continue
        key = security_key(holding)
        weight = _num(holding.get("weight"), 0.0) or 0.0
        if key and weight > 0:
            out[key] += weight
    return dict(out)


def _representative_security(snapshot: Mapping[str, Any], key: str) -> Tuple[str, str]:
    for holding in snapshot.get("holdings") or []:
        if isinstance(holding, Mapping) and security_key(holding) == key:
            return _ticker(holding.get("ticker")), str(holding.get("name") or "").strip()
    return "", ""


def pairwise_overlap_pct(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    return sum(min(float(a.get(k, 0.0)), float(b.get(k, 0.0))) for k in (set(a) & set(b))) * 100.0


def build_lookthrough(
    xray_meta: Mapping[str, Any],
    snapshots: Mapping[str, Mapping[str, Any]],
    summary: Mapping[str, Any] | None = None,
    errors: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    summary = summary or {}
    errors = errors or {}
    asset_weights = portfolio_asset_weights_from_xray(xray_meta)
    held_supported = [fund for fund in SUPPORTED_FUNDS if asset_weights.get(fund, 0.0) > 0]
    loaded_held = [fund for fund in held_supported if fund in snapshots]
    missing_held = [fund for fund in held_supported if fund not in snapshots]

    if not held_supported:
        return {
            "status": "no_supported_equity_etf_in_portfolio",
            "note": "目前資產權重中沒有可用 QQQ/IFRA/GRID/COPX/VNM/SRVR 做 equity look-through 的部位。",
            "supported_funds": list(SUPPORTED_FUNDS),
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }

    if not loaded_held:
        return {
            "status": "missing_holdings_snapshot",
            "note": "ETF look-through 尚無可用 holdings snapshot；等待 Update Portfolio Holdings 產生 data/holdings/latest。",
            "held_supported_funds": held_supported,
            "missing_funds": missing_held,
            "errors": {k: errors[k] for k in missing_held if k in errors},
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }

    summary_funds = summary.get("funds") if isinstance(summary.get("funds"), Mapping) else {}
    fund_maps: Dict[str, Dict[str, float]] = {}
    fund_coverage: Dict[str, Dict[str, Any]] = {}
    aggregate: Dict[str, Dict[str, Any]] = {}

    held_supported_etf_sleeve_pct = sum(asset_weights.get(fund, 0.0) for fund in held_supported) * 100.0
    loaded_etf_sleeve_pct = 0.0
    mapped_equity_portfolio_pct = 0.0
    nonofficial_funds: List[str] = []
    stale_funds: List[str] = []

    for fund in loaded_held:
        snapshot = snapshots[fund]
        portfolio_weight = float(asset_weights[fund])
        loaded_etf_sleeve_pct += portfolio_weight * 100.0

        equity_map = _fund_equity_map(snapshot)
        fund_maps[fund] = equity_map
        equity_coverage = sum(equity_map.values())
        mapped_equity_portfolio_pct += portfolio_weight * equity_coverage * 100.0

        source_quality = str(snapshot.get("source_quality") or "UNKNOWN")
        stale_days = _snapshot_freshness_days(snapshot)
        if not source_quality.startswith("OFFICIAL"):
            nonofficial_funds.append(fund)
        if stale_days is None or stale_days > 5:
            stale_funds.append(fund)

        summary_status = None
        if isinstance(summary_funds, Mapping) and isinstance(summary_funds.get(fund), Mapping):
            summary_status = summary_funds[fund].get("status")

        fund_coverage[fund] = {
            "portfolio_weight_pct": round(portfolio_weight * 100.0, 3),
            "as_of": snapshot.get("as_of"),
            "stale_days_recomputed": stale_days,
            "source_quality": source_quality,
            "refresh_status": summary_status or "SNAPSHOT_PRESENT",
            "coverage_pct": _num(snapshot.get("coverage_pct")),
            "equity_coverage_pct": round(equity_coverage * 100.0, 4),
            "holdings_count": int(snapshot.get("holdings_count") or len(snapshot.get("holdings") or [])),
        }

        for holding in snapshot.get("holdings") or []:
            if not isinstance(holding, Mapping):
                continue
            key = security_key(holding)
            h_weight = _num(holding.get("weight"), 0.0) or 0.0
            if not key or h_weight <= 0:
                continue
            contribution_pct = portfolio_weight * h_weight * 100.0
            ticker, name = _representative_security(snapshot, key)
            rec = aggregate.setdefault(key, {
                "ticker": ticker,
                "name": name,
                "portfolio_weight_pct": 0.0,
                "source_funds": set(),
            })
            if not rec.get("ticker") and ticker:
                rec["ticker"] = ticker
            if not rec.get("name") and name:
                rec["name"] = name
            rec["portfolio_weight_pct"] += contribution_pct
            rec["source_funds"].add(fund)

    top_underlying: List[Dict[str, Any]] = []
    for rec in aggregate.values():
        top_underlying.append({
            "ticker": rec.get("ticker") or "",
            "name": rec.get("name") or "",
            "portfolio_weight_pct": round(float(rec["portfolio_weight_pct"]), 4),
            "source_funds": sorted(rec["source_funds"]),
        })
    top_underlying.sort(key=lambda x: x["portfolio_weight_pct"], reverse=True)

    pairwise: List[Dict[str, Any]] = []
    for i, fund_a in enumerate(loaded_held):
        for fund_b in loaded_held[i + 1:]:
            overlap = pairwise_overlap_pct(fund_maps[fund_a], fund_maps[fund_b])
            pairwise.append({
                "fund_a": fund_a,
                "fund_b": fund_b,
                "overlap_pct": round(overlap, 4),
            })
    pairwise.sort(key=lambda x: x["overlap_pct"], reverse=True)

    special_exposures = []
    for ticker, mode in SPECIAL_EXPOSURE_MODES.items():
        weight = asset_weights.get(_ticker(ticker), 0.0)
        if weight > 0:
            special_exposures.append({
                "ticker": ticker,
                "portfolio_weight_pct": round(weight * 100.0, 3),
                "lookthrough_mode": mode,
            })

    loaded_sleeve_equity_coverage_pct = (
        mapped_equity_portfolio_pct / loaded_etf_sleeve_pct * 100.0
        if loaded_etf_sleeve_pct > 0 else 0.0
    )
    held_supported_sleeve_coverage_pct = (
        mapped_equity_portfolio_pct / held_supported_etf_sleeve_pct * 100.0
        if held_supported_etf_sleeve_pct > 0 else 0.0
    )
    top5_pct = sum(row["portfolio_weight_pct"] for row in top_underlying[:5])
    top10_pct = sum(row["portfolio_weight_pct"] for row in top_underlying[:10])
    mapped_total = sum(row["portfolio_weight_pct"] for row in top_underlying)
    hhi = 0.0
    if mapped_total > 0:
        hhi = sum((row["portfolio_weight_pct"] / mapped_total) ** 2 for row in top_underlying) * 10000.0

    if missing_held:
        status = "partial_missing_funds"
    elif stale_funds:
        status = "available_stale_or_unknown_freshness"
    elif nonofficial_funds:
        status = "available_mixed_sources"
    else:
        status = "available_official"

    max_pair = pairwise[0] if pairwise else None
    top_name = top_underlying[0]["ticker"] or top_underlying[0]["name"] if top_underlying else "N/A"
    top_weight = top_underlying[0]["portfolio_weight_pct"] if top_underlying else 0.0
    pair_note = (
        f"；最高 ETF pair overlap {max_pair['fund_a']}/{max_pair['fund_b']} {max_pair['overlap_pct']:.1f}%"
        if max_pair else ""
    )
    source_note = f"；非官方來源 {', '.join(nonofficial_funds)}" if nonofficial_funds else ""
    missing_note = f"；缺少 {', '.join(missing_held)}" if missing_held else ""
    note = (
        f"Look-through 可用：已載入 ETF sleeve {loaded_etf_sleeve_pct:.1f}% / 持有支援 ETF {held_supported_etf_sleeve_pct:.1f}% of portfolio，"
        f"已映射 equity underlying {mapped_equity_portfolio_pct:.1f}% of portfolio；"
        f"最大底層部位 {top_name} {top_weight:.2f}%{pair_note}{source_note}{missing_note}。"
    )

    return {
        "status": status,
        "note": note,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "method": "constituent_weight_lookthrough_with_normalized_ticker_or_issuer_name_matching",
        "overlap_method": "sum_min_constituent_weights_on_normalized_security_key",
        "identity_limit": "No cross-vendor security master; international ticker/name normalization can undercount overlap.",
        "held_supported_funds": held_supported,
        "loaded_funds": loaded_held,
        "missing_funds": missing_held,
        "nonofficial_funds": nonofficial_funds,
        "stale_funds": stale_funds,
        "held_supported_etf_sleeve_pct": round(held_supported_etf_sleeve_pct, 4),
        "loaded_etf_sleeve_pct": round(loaded_etf_sleeve_pct, 4),
        "mapped_equity_portfolio_pct": round(mapped_equity_portfolio_pct, 4),
        "loaded_sleeve_equity_coverage_pct": round(loaded_sleeve_equity_coverage_pct, 4),
        "held_supported_sleeve_coverage_pct": round(held_supported_sleeve_coverage_pct, 4),
        "top5_underlying_portfolio_pct": round(top5_pct, 4),
        "top10_underlying_portfolio_pct": round(top10_pct, 4),
        "mapped_equity_hhi": round(hhi, 2),
        "fund_coverage": fund_coverage,
        "top_underlying": top_underlying[:20],
        "pairwise_overlap": pairwise,
        "special_exposures": special_exposures,
        "errors": {k: v for k, v in errors.items() if k in held_supported},
    }


def enrich_row(row: Mapping[str, Any], holdings_dir: Path = DEFAULT_HOLDINGS_DIR) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    chaos_meta = dict(row.get("chaos_meta") or {}) if isinstance(row.get("chaos_meta"), Mapping) else {}
    xray_meta = dict(chaos_meta.get("xray_meta") or {}) if isinstance(chaos_meta.get("xray_meta"), Mapping) else {}

    snapshots, aux = load_holdings_set(holdings_dir)
    lookthrough = build_lookthrough(
        xray_meta=xray_meta,
        snapshots=snapshots,
        summary=aux.get("summary") or {},
        errors=aux.get("errors") or {},
    )
    xray_meta["lookthrough_overlap"] = lookthrough
    chaos_meta["xray_meta"] = xray_meta
    return chaos_meta, lookthrough


def main() -> None:
    from supabase import create_client

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_SECRET_KEY", "")
    table = os.getenv("SUPABASE_TABLE", "portfolio_db")
    row_id = int(os.getenv("PORTFOLIO_ROW_ID", "1"))

    if not url or not key:
        raise SystemExit("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")

    client = create_client(url, key)
    row = client.table(table).select("chaos_meta").eq("id", row_id).single().execute().data
    if not row:
        raise SystemExit("ERROR: portfolio row not found")

    chaos_meta, lookthrough = enrich_row(row)
    client.table(table).update({"chaos_meta": chaos_meta}).eq("id", row_id).execute()

    print(
        "OK ETF look-through enriched: "
        f"status={lookthrough.get('status')} "
        f"mapped={lookthrough.get('mapped_equity_portfolio_pct', 0)}% "
        f"funds={','.join(lookthrough.get('loaded_funds') or [])}"
    )


if __name__ == "__main__":
    main()
