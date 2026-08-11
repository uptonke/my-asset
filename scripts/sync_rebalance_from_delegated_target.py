#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from supabase import create_client

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET_FILE = ROOT / "data" / "alpha" / "delegated_target_weight_draft_latest.json"
TABLE = os.getenv("SUPABASE_TABLE", "portfolio_db")
ROW_ID = int(os.getenv("PORTFOLIO_ROW_ID", "1"))
DEFAULT_RULE_THRESHOLD_PP = 1.0


def _num(value: Any, default: float = 0.0) -> float:
    try:
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def _load_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"target file must contain an object: {path}")
    return data


def _validated_target(payload: Dict[str, Any]) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]], Dict[str, Any]]:
    if str(payload.get("status")) != "OK":
        raise RuntimeError(f"delegated target status is not OK: {payload.get('status')}")

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    raw_weights = payload.get("machine_target_weights_pct")
    rows = payload.get("machine_target_rows")
    if not isinstance(raw_weights, dict) or not raw_weights:
        raise RuntimeError("machine_target_weights_pct is missing")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("machine_target_rows is missing")

    weights: Dict[str, float] = {}
    for ticker, value in raw_weights.items():
        t = str(ticker or "").strip()
        if not t:
            continue
        w = _num(value, -1.0)
        if w < 0:
            raise RuntimeError(f"invalid target weight for {t}: {value}")
        weights[t] = w

    row_map: Dict[str, Dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        t = str(raw.get("ticker") or "").strip()
        if t:
            row_map[t] = dict(raw)

    cash_target_pct = _num(summary.get("cash_target_weight_pct"), 0.0)
    target_sum_pct = sum(weights.values())
    expected_sum_pct = 100.0 - cash_target_pct
    reported_sum_pct = _num(summary.get("target_asset_weight_sum_pct"), target_sum_pct)

    if abs(target_sum_pct - reported_sum_pct) > 0.15:
        raise RuntimeError(
            f"target vector sum mismatch: vector={target_sum_pct:.4f}% reported={reported_sum_pct:.4f}%"
        )
    if abs((target_sum_pct + cash_target_pct) - 100.0) > 0.15:
        raise RuntimeError(
            f"target vector is not portfolio-complete: assets={target_sum_pct:.4f}% cash={cash_target_pct:.4f}%"
        )
    if abs(target_sum_pct - expected_sum_pct) > 0.15:
        raise RuntimeError("target vector does not match the declared cash target")

    missing_rows = sorted(set(weights) - set(row_map))
    if missing_rows:
        raise RuntimeError(f"machine_target_rows missing target tickers: {missing_rows}")

    return weights, row_map, summary


def build_rebalance_meta(
    payload: Dict[str, Any],
    old_meta: Dict[str, Any] | None = None,
    *,
    rule_threshold_pp: float = DEFAULT_RULE_THRESHOLD_PP,
) -> Dict[str, Any]:
    weights, row_map, summary = _validated_target(payload)
    old = dict(old_meta or {})

    hard_buffer_tickers = [str(x) for x in (old.get("hard_buffer_tickers") or ["SHY", "BOXX"]) if str(x)]
    hard_buffer_set = set(hard_buffer_tickers)
    buffer_floor_pct = _num(old.get("buffer_floor_pct"), 0.0)
    current_buffer_pct = _num(old.get("current_buffer_pct"), 0.0)
    buffer_gap_pct = max(0.0, buffer_floor_pct - current_buffer_pct)
    buffer_blocking = buffer_gap_pct > 0.05

    economic_dust = set(str(x) for x in (old.get("economic_dust_tickers_excluded") or []) if str(x))
    sheet_only = list(old.get("sheet_only_tickers_excluded") or [])
    nav_twd = _num(summary.get("nav_twd"), 0.0)

    sell_signals: List[Dict[str, Any]] = []
    buffer_buy_signals: List[Dict[str, Any]] = []
    risk_buy_signals: List[Dict[str, Any]] = []
    blocked_signals: List[Dict[str, Any]] = []
    target_rows: List[Dict[str, Any]] = []

    for ticker, target_pct in weights.items():
        row = row_map[ticker]
        current_pct = _num(row.get("current_weight_pct"), 0.0)
        signed_drift_pp = current_pct - target_pct
        delta_to_target_pp = target_pct - current_pct
        target_rows.append({
            "ticker": ticker,
            "current_weight_pct": round(current_pct, 4),
            "target_weight_pct": round(target_pct, 4),
            "signed_drift_pp": round(signed_drift_pp, 4),
            "delta_to_target_pp": round(delta_to_target_pp, 4),
            "selected_in_target": bool(row.get("selected_in_target", target_pct > 0)),
            "dual_target_direction_conflict": bool(row.get("dual_target_direction_conflict", False)),
            "daily_quant_mc_multiplier": row.get("daily_quant_mc_multiplier"),
        })

        if ticker in economic_dust:
            continue
        if abs(signed_drift_pp) <= rule_threshold_pp:
            continue

        direction = "TRIM" if signed_drift_pp > 0 else "ADD"
        signal_type = "BUFFER_REPLENISHMENT" if direction == "ADD" and ticker in hard_buffer_set and buffer_blocking else "TARGET_DRIFT"
        signal = {
            "ticker": ticker,
            "direction": direction,
            "signal_type": signal_type,
            "execution_status": "ACTIONABLE",
            "action": "SELL (減碼)" if direction == "TRIM" else "BUY (加碼)",
            "current_weight": f"{current_pct:.2f}%",
            "target_weight": f"{target_pct:.2f}%",
            "delta_weight": f"{delta_to_target_pp:.2f}%",
            "current_weight_pct": round(current_pct, 4),
            "target_weight_pct": round(target_pct, 4),
            "signed_drift_pp": round(signed_drift_pp, 4),
            "delta_to_target_pp": round(delta_to_target_pp, 4),
            "rule_threshold_pp": rule_threshold_pp,
            "trade_amount": round(nav_twd * delta_to_target_pp / 100.0, 2) if nav_twd > 0 else 0.0,
            "target_weight_source": "delegated_blended_machine_target",
            "reason": (
                "目前權重高於完整 delegated / blended 目標超過規則門檻，候選動作為 TRIM"
                if direction == "TRIM"
                else "目前權重低於完整 delegated / blended 目標超過規則門檻，候選動作為 ADD"
            ),
        }

        if direction == "TRIM":
            sell_signals.append(signal)
        elif buffer_blocking and ticker not in hard_buffer_set:
            blocked = dict(signal)
            blocked["execution_status"] = "BLOCKED_BY_BUFFER"
            blocked["reason"] = "完整 delegated / blended 目標顯示低配，但硬緩衝缺口尚未補足；ADD 暫不可執行"
            blocked_signals.append(blocked)
        elif signal_type == "BUFFER_REPLENISHMENT":
            buffer_buy_signals.append(signal)
        else:
            risk_buy_signals.append(signal)

    signals = sell_signals + buffer_buy_signals + risk_buy_signals
    target_sum_pct = round(sum(weights.values()), 4)
    cash_target_pct = round(_num(summary.get("cash_target_weight_pct"), 0.0), 4)

    merged = dict(old)
    merged.update({
        "universe_policy": "material_ledger_holdings_plus_hard_buffer_only",
        "target_weight_source": "dual_blend_cloud_target_and_v105_native_target",
        "target_source_mode": payload.get("mode") or "dual_target_blend_cloud_and_v105_native_engine",
        "target_source_generated_at": payload.get("generated_at"),
        "target_vector_complete": True,
        "target_asset_weight_sum_pct": target_sum_pct,
        "cash_target_weight_pct": cash_target_pct,
        "target_total_with_cash_pct": round(target_sum_pct + cash_target_pct, 4),
        "target_weights_pct": {k: round(v, 4) for k, v in weights.items()},
        "target_rows": sorted(target_rows, key=lambda r: r["ticker"]),
        "rule_threshold_pp": rule_threshold_pp,
        "signals": signals,
        "blocked_signals": blocked_signals,
        "buffer_floor_pct": round(buffer_floor_pct, 4),
        "current_buffer_pct": round(current_buffer_pct, 4),
        "buffer_gap_pct": round(buffer_gap_pct, 4),
        "buffer_blocking_risk_buys": buffer_blocking,
        "hard_buffer_tickers": hard_buffer_tickers,
        "economic_dust_tickers_excluded": sorted(economic_dust),
        "sheet_only_tickers_excluded": sheet_only,
        "target_sync_status": "COMPLETE_DELEGATED_TARGET_SYNCED",
    })
    return merged


def sync_to_supabase(target_file: Path, *, dry_run: bool = False) -> Dict[str, Any]:
    payload = _load_json(target_file)

    if dry_run:
        meta = build_rebalance_meta(payload, {})
        return meta

    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_SECRET_KEY", "")).strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing")

    supabase = create_client(url, key)
    response = supabase.table(TABLE).select("stock_meta").eq("id", ROW_ID).single().execute()
    data = response.data or {}
    stock_meta = data.get("stock_meta") if isinstance(data.get("stock_meta"), dict) else {}
    old_meta = stock_meta.get("__portfolio_rebalance__") if isinstance(stock_meta.get("__portfolio_rebalance__"), dict) else {}

    new_meta = build_rebalance_meta(payload, old_meta)
    stock_meta = dict(stock_meta)
    stock_meta["__portfolio_rebalance__"] = new_meta
    supabase.table(TABLE).update({"stock_meta": stock_meta}).eq("id", ROW_ID).execute()
    return new_meta


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync complete delegated/blended target vector into Rebalance Monitor metadata")
    parser.add_argument("--target-file", default=str(DEFAULT_TARGET_FILE))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    meta = sync_to_supabase(Path(args.target_file), dry_run=args.dry_run)
    print(
        "OK delegated rebalance sync: "
        f"targets={len(meta.get('target_weights_pct') or {})} "
        f"sum={meta.get('target_asset_weight_sum_pct')}% "
        f"cash={meta.get('cash_target_weight_pct')}% "
        f"signals={len(meta.get('signals') or [])} "
        f"blocked={len(meta.get('blocked_signals') or [])}"
    )
    for signal in meta.get("signals") or []:
        print(
            f"  {signal.get('direction')} {signal.get('ticker')}: "
            f"{signal.get('current_weight_pct')}% -> {signal.get('target_weight_pct')}% "
            f"drift={signal.get('signed_drift_pp')}pp"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
