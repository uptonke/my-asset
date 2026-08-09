from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from supabase import create_client

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evt_robustness import compute_evt_robustness
from scripts.fix_xray_twd_weights import fetch_yahoo_chart_close


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Refresh daily current-weight EVT robustness diagnostics.")
    p.add_argument("--dry-run", action="store_true", help="Compute and print without writing Supabase.")
    p.add_argument("--bootstrap", type=int, default=500, help="Block-bootstrap replicates.")
    return p.parse_args()


def _finite_weight(row: dict[str, Any]) -> float:
    try:
        value = float(row.get("weight_pct") or 0.0) / 100.0
        return value if value > 0 else 0.0
    except Exception:
        return 0.0


def _build_daily_portfolio_returns(weights: dict[str, float]) -> tuple[pd.Series, dict[str, Any]]:
    prices: dict[str, pd.Series] = {}
    failures: dict[str, str] = {}

    for ticker in weights:
        try:
            series = fetch_yahoo_chart_close(ticker, days=3700).sort_index()
            if len(series) < 30:
                raise ValueError(f"only {len(series)} daily prices")
            prices[ticker] = series.rename(ticker)
            time.sleep(0.06)
        except Exception as exc:
            failures[ticker] = f"{type(exc).__name__}: {exc}"

    available = {t: w for t, w in weights.items() if t in prices}
    available_weight = float(sum(available.values()))
    if available_weight <= 0:
        raise RuntimeError(f"No asset history available. failures={failures}")
    available = {t: w / available_weight for t, w in available.items()}

    # Union calendar + limited forward-fill: closed markets contribute zero price
    # movement for up to three calendar observations while crypto/weekend data can
    # still be represented. This is an approximation for mixed-market portfolios.
    frame = pd.concat([prices[t] for t in available], axis=1).sort_index()
    frame = frame.ffill(limit=3)
    returns = frame.pct_change(fill_method=None).replace([float("inf"), float("-inf")], pd.NA)
    returns = returns.dropna(how="any")
    if len(returns) < 120:
        raise RuntimeError(f"Only {len(returns)} aligned daily returns after calendar alignment")

    w = pd.Series(available, dtype=float).reindex(returns.columns).fillna(0.0)
    port = returns.mul(w, axis=1).sum(axis=1)
    port.name = "current_weight_portfolio_daily_return"

    meta = {
        "available_weight_pct": round(available_weight * 100.0, 4),
        "available_tickers": list(available),
        "failed_tickers": failures,
        "calendar_alignment_method": "outer_join_prices_ffill_limit_3_then_complete_case_daily_returns",
        "weight_method": "current_xray_capital_weights_renormalized_over_available_price_series",
    }
    return port, meta


def main() -> None:
    args = _parse_args()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    table = os.environ.get("SUPABASE_TABLE", "portfolio_db")
    row_id = int(os.environ.get("PORTFOLIO_ROW_ID", "1"))
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are required")

    client = create_client(url, key)
    row = client.table(table).select("chaos_meta").eq("id", row_id).single().execute().data or {}
    chaos = row.get("chaos_meta") or {}
    xray = chaos.get("xray_meta") or {}
    mrc_rows = xray.get("mrc_table") or []

    weights: dict[str, float] = {}
    for item in mrc_rows:
        ticker = str(item.get("yf_ticker") or "").strip()
        weight = _finite_weight(item)
        if ticker and weight > 0:
            weights[ticker] = weights.get(ticker, 0.0) + weight
    if not weights:
        raise RuntimeError("No usable X-Ray yf_ticker/weight_pct rows")

    port, input_meta = _build_daily_portfolio_returns(weights)
    result = compute_evt_robustness(port, n_boot=max(0, int(args.bootstrap)), block_days=5, seed=42)
    result.update(input_meta)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") not in {"available", "partial"}:
        raise RuntimeError(f"EVT robustness unavailable: {result.get('status')}: {result.get('error', '')}")

    if args.dry_run:
        return

    new_chaos = dict(chaos)
    new_chaos["evt_robustness"] = result

    tail_meta = dict(new_chaos.get("tail_meta") or {})
    tail_meta.update({
        "evt_var95": result.get("var95_pct"),
        "evt_es95": result.get("es95_pct"),
        "evt_shape_xi": result.get("shape_xi"),
        "evt_scale_beta": result.get("scale_beta"),
        "evt_threshold": -abs(float(result.get("threshold_loss_pct") or 0.0)) if result.get("threshold_loss_pct") is not None else None,
        "evt_exceedance_count": result.get("exceedance_count"),
        "evt_alpha_conf": result.get("alpha_conf", 0.95),
        "evt_return_frequency": "daily",
        "evt_horizon_days": 1,
        "evt_horizon_weeks": None,
        "evt_comparable_to_jd": False,
        "evt_comparison_note": "one_day_evt_not_directly_comparable_to_13_week_jump_stress",
        "evt_robustness": result,
    })
    new_chaos["tail_meta"] = tail_meta

    new_chaos["evt_tail"] = {
        "evt_var95": result.get("var95_pct"),
        "evt_es95": result.get("es95_pct"),
        "evt_shape_xi": result.get("shape_xi"),
        "evt_scale_beta": result.get("scale_beta"),
        "evt_threshold": -abs(float(result.get("threshold_loss_pct") or 0.0)) if result.get("threshold_loss_pct") is not None else None,
        "evt_exceedance_count": result.get("exceedance_count"),
        "evt_alpha_conf": result.get("alpha_conf", 0.95),
        "evt_return_frequency": "daily",
        "evt_horizon_days": 1,
        "evt_robustness": result,
    }

    client.table(table).update({"chaos_meta": new_chaos}).eq("id", row_id).execute()
    print("EVT robustness stored in Supabase.")


if __name__ == "__main__":
    main()
