#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DAILY_JSON = OUT_DIR / "daily_quant_reference_latest.json"
DAILY_MD = OUT_DIR / "daily_quant_reference_summary.md"
MC_JSON = OUT_DIR / "delegated_draft_monte_carlo_check_latest.json"
MC_MD = OUT_DIR / "delegated_draft_monte_carlo_check_summary.md"
SYNTHETIC_RISK_KEY = "__synthetic_portfolio_risk__"


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
        if x == x and abs(x) != float("inf"):
            return x
    except Exception:
        pass
    return default


def latest_backup_row() -> Tuple[Dict[str, Any], str]:
    paths = sorted((ROOT / "backups").glob("portfolio_backup_*.json"))
    if not paths:
        return {}, "backup_missing"
    try:
        data = json.loads(paths[-1].read_text(encoding="utf-8"))
        row = data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else {}
        return row if isinstance(row, dict) else {}, f"latest_backup:{paths[-1].name}"
    except Exception as exc:
        return {}, f"backup_error:{exc}"


def fetch_supabase_row() -> Tuple[Dict[str, Any], str]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    table = os.getenv("SUPABASE_TABLE", "portfolio_db")
    row_id = os.getenv("PORTFOLIO_ROW_ID", "1")
    if not url or not key:
        return {}, "supabase_env_missing"
    try:
        from supabase import create_client  # type: ignore
        client = create_client(url, key)
        resp = client.table(table).select("*").eq("id", int(row_id)).single().execute()
        if resp.data:
            return resp.data, "supabase_live"
    except Exception as exc:
        return {}, f"supabase_error:{exc}"
    return {}, "supabase_empty"


def resolve_row() -> Tuple[Dict[str, Any], str]:
    live, live_status = fetch_supabase_row()
    if live:
        return live, live_status
    backup, backup_status = latest_backup_row()
    if backup:
        return backup, backup_status
    return {}, live_status if live_status != "supabase_env_missing" else backup_status


def workflow_info() -> Dict[str, Any]:
    path = ROOT / ".github" / "workflows" / "daily_update.yml"
    exists = path.exists()
    text = path.read_text(encoding="utf-8") if exists else ""
    steps: List[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("- name:"):
            steps.append(s.split(":", 1)[1].strip().strip('"'))
    refs = []
    for token in ["main.py", "scripts/fix_xray_twd_weights.py", "scripts/update_market_compass.py", "scripts/update_stock_meta.py"]:
        if token in text:
            refs.append(token)
    return {
        "path": ".github/workflows/daily_update.yml",
        "exists": exists,
        "name": "Daily Quant Pipeline",
        "step_count": len(steps),
        "steps": steps,
        "referenced_scripts": refs,
        "role": "data_and_risk_foundation_for_v10_delegated_drafts",
    }


def compact_synthetic_risk(stock_meta: Dict[str, Any]) -> Dict[str, Any]:
    sr = as_dict(stock_meta.get(SYNTHETIC_RISK_KEY))
    metrics = as_dict(sr.get("metrics"))
    coverage = as_dict(sr.get("coverage"))
    quantstats = as_dict(sr.get("quantstats"))
    ewma_regime = as_dict(sr.get("ewma_regime"))
    component_tail = as_dict(sr.get("component_tail_risk"))
    risk_budgeting = as_dict(sr.get("risk_budgeting"))
    return {
        "available": bool(sr),
        "status": sr.get("status"),
        "confidence": sr.get("confidence"),
        "generated_at": sr.get("generated_at") or sr.get("timestamp_utc"),
        "method": sr.get("method"),
        "metrics": {
            "sample_count": metrics.get("sample_count"),
            "ann_vol_pct": metrics.get("ann_vol_pct"),
            "var95_pct": metrics.get("var95_pct"),
            "es95_pct": metrics.get("es95_pct"),
            "max_drawdown_pct": metrics.get("max_drawdown_pct"),
        },
        "coverage": {
            "strict_sample": coverage.get("strict_sample"),
            "flexible_sample": coverage.get("flexible_sample"),
            "usable_weight_pct": coverage.get("usable_weight_pct"),
        },
        "quantstats_status": quantstats.get("status"),
        "ewma_regime_status": ewma_regime.get("status"),
        "component_tail_status": as_dict(component_tail.get("var_es_95")).get("status"),
        "risk_budgeting_status": risk_budgeting.get("status"),
    }


def compact_monte_carlo_reference(chaos_meta: Dict[str, Any]) -> Dict[str, Any]:
    tail = as_dict(chaos_meta.get("tail_meta"))
    jd = as_dict(chaos_meta.get("jump_diffusion"))
    evt = as_dict(chaos_meta.get("evt_tail"))
    return {
        "available": bool(chaos_meta),
        "source": "Supabase chaos_meta produced by Daily Quant Pipeline / dashboard Monte Carlo layer",
        "stressed_var95_pct": chaos_meta.get("stressed_var95"),
        "stressed_es95_pct": chaos_meta.get("stressed_es95"),
        "contagion_loss_pct": chaos_meta.get("contagion_loss_pct"),
        "fire_sale_loss_pct": chaos_meta.get("fire_sale_loss_pct"),
        "liquidity_run_probability_pct": chaos_meta.get("liquidity_run_probability"),
        "fragile_nodes": as_list(chaos_meta.get("fragile_nodes"))[:10],
        "jump_diffusion": {
            "jd_var95": jd.get("jd_var95", tail.get("jd_var95")),
            "jd_es95": jd.get("jd_es95", tail.get("jd_es95")),
            "jd_tail_loss": jd.get("jd_tail_loss", tail.get("jd_tail_loss")),
            "jd_crash_prob": jd.get("jd_crash_prob", tail.get("jd_crash_prob")),
            "jd_horizon_weeks": jd.get("jd_horizon_weeks", tail.get("jd_horizon_weeks")),
        },
        "evt_tail": {
            "evt_var95": evt.get("evt_var95", tail.get("evt_var95")),
            "evt_es95": evt.get("evt_es95", tail.get("evt_es95")),
            "evt_shape_xi": evt.get("evt_shape_xi", tail.get("evt_shape_xi")),
            "evt_exceedance_count": evt.get("evt_exceedance_count", tail.get("evt_exceedance_count")),
        },
        "sample_context": {
            "sample_weeks": tail.get("sample_weeks"),
            "tail_sample_count": tail.get("tail_sample_count"),
            "crisis_sample_count": tail.get("crisis_sample_count"),
            "crisis_window_label": tail.get("crisis_window_label"),
        },
    }


def status_badge(checks: List[Dict[str, Any]]) -> str:
    if any(c.get("severity") == "blocker" for c in checks):
        return "blocked_by_missing_reference"
    if any(c.get("severity") == "warning" for c in checks):
        return "reference_available_with_warnings"
    return "reference_available"


def build_checks(daily: Dict[str, Any], mc: Dict[str, Any], delegated: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    wf = as_dict(daily.get("daily_update_workflow"))
    checks.append({
        "check": "daily_update_workflow_exists",
        "status": "pass" if wf.get("exists") else "fail",
        "severity": "info" if wf.get("exists") else "blocker",
        "message": ".github/workflows/daily_update.yml 已找到。" if wf.get("exists") else "找不到 .github/workflows/daily_update.yml。",
    })
    synthetic = as_dict(daily.get("synthetic_risk_reference"))
    checks.append({
        "check": "synthetic_risk_available",
        "status": "pass" if synthetic.get("available") else "watch",
        "severity": "info" if synthetic.get("available") else "warning",
        "message": "Daily Quant synthetic risk 可作為 v10.x 風險參考。" if synthetic.get("available") else "stock_meta.__synthetic_portfolio_risk__ 尚未可用，v10.5 只能使用其他風險摘要。",
    })
    mc_ref = as_dict(mc.get("monte_carlo_reference"))
    checks.append({
        "check": "monte_carlo_reference_available",
        "status": "pass" if mc_ref.get("available") else "watch",
        "severity": "info" if mc_ref.get("available") else "warning",
        "message": "chaos_meta / Monte Carlo 參考可用。" if mc_ref.get("available") else "chaos_meta / Monte Carlo 參考尚未可用。",
    })
    delegated_summary = as_dict(delegated.get("summary"))
    checks.append({
        "check": "delegated_draft_available",
        "status": "pass" if delegated_summary.get("pool_asset_count") else "watch",
        "severity": "info" if delegated_summary.get("pool_asset_count") else "warning",
        "message": "v10.x delegated target draft 已可作為檢查對象。" if delegated_summary.get("pool_asset_count") else "尚未讀到 v10.x delegated target draft。",
    })
    return checks


def concentration_delta(delegated: Dict[str, Any]) -> Dict[str, Any]:
    rows = [as_dict(x) for x in as_list(delegated.get("machine_target_rows"))]
    current_max = 0.0
    target_max = 0.0
    current_name = None
    target_name = None
    for r in rows:
        c = num(r.get("current_weight_pct"))
        t = num(r.get("machine_target_weight_pct"))
        if c > current_max:
            current_max, current_name = c, r.get("ticker")
        if t > target_max:
            target_max, target_name = t, r.get("ticker")
    return {
        "current_max_weight_pct": round(current_max, 6),
        "current_max_weight_ticker": current_name,
        "target_max_weight_pct": round(target_max, 6),
        "target_max_weight_ticker": target_name,
        "target_minus_current_max_weight_pct": round(target_max - current_max, 6),
    }


def main() -> None:
    generated_at = now_iso()
    row, row_source = resolve_row()
    settings = as_dict(row.get("settings"))
    stock_meta = as_dict(row.get("stock_meta"))
    chaos_meta = as_dict(row.get("chaos_meta"))
    delegated = as_dict(read_json("data/alpha/delegated_target_weight_draft_latest.json", {}))
    constraints = as_dict(read_json("data/alpha/trading_constraints_snapshot_latest.json", {}))

    synthetic_ref = compact_synthetic_risk(stock_meta)
    mc_ref = compact_monte_carlo_reference(chaos_meta)
    daily_reference = {
        "version": "v10.5",
        "status": "OK",
        "generated_at": generated_at,
        "mode": "daily_quant_reference_layer",
        "safe_mode": True,
        "research_only": True,
        "review_only": True,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "auto_trade_enabled": False,
        "supabase_write_enabled": False,
        "not_trade_order": True,
        "portfolio_source": row_source,
        "daily_update_workflow": workflow_info(),
        "settings_reference": {
            "exchange_rate": settings.get("exchangeRate"),
            "liquidity_buffer_ratio": settings.get("liquidityBufferRatio"),
            "price_map_count": len(as_dict(settings.get("priceMap"))),
        },
        "stock_meta_reference": {
            "stock_meta_count": len([k for k in stock_meta.keys() if not str(k).startswith("__")]),
            "synthetic_risk_key": SYNTHETIC_RISK_KEY,
            "synthetic_risk_available": bool(synthetic_ref.get("available")),
        },
        "synthetic_risk_reference": synthetic_ref,
        "monte_carlo_reference": mc_ref,
        "trading_constraints_reference": {
            "generated_at": constraints.get("generated_at"),
            "asset_count": as_dict(constraints.get("summary")).get("asset_count"),
            "real_world_price_success_count": as_dict(constraints.get("summary")).get("real_world_price_success_count"),
            "liquidity_buffer_ratio_pct": as_dict(constraints.get("summary")).get("liquidity_buffer_ratio_pct"),
        },
        "source_priority_policy": [
            "Daily Quant / stock_meta / holdings snapshot is the first reference layer for portfolio state and synthetic risk.",
            "Monte Carlo / chaos_meta is used as a risk reference, not as an execution trigger.",
            "v10.x delegated drafts may use this reference layer for warnings and diagnostics only.",
        ],
    }

    mc_check_base = {"monte_carlo_reference": mc_ref}
    preliminary = {"daily_update_workflow": daily_reference["daily_update_workflow"], "synthetic_risk_reference": synthetic_ref}
    checks = build_checks(preliminary, mc_check_base, delegated)
    check_status = status_badge(checks)
    draft_summary = as_dict(delegated.get("summary"))
    concentration = concentration_delta(delegated)

    risk_notes: List[Dict[str, Any]] = []
    if num(mc_ref.get("stressed_es95_pct")) > 0:
        risk_notes.append({"code": "mc_stressed_es95_reference", "severity": "info", "message": f"Monte Carlo / chaos_meta stressed ES95 約 {mc_ref.get('stressed_es95_pct')}%。"})
    if num(mc_ref.get("liquidity_run_probability_pct")) >= 20:
        risk_notes.append({"code": "liquidity_run_probability_watch", "severity": "warning", "message": f"流動性擠兌機率參考值約 {mc_ref.get('liquidity_run_probability_pct')}%，v10.x 草案應避免增加不可流動部位。"})
    if concentration.get("target_minus_current_max_weight_pct", 0) > 5:
        risk_notes.append({"code": "target_concentration_increase_watch", "severity": "warning", "message": "v10.x 目標權重最大單檔集中度較目前提高超過 5 個百分點。"})

    mc_check = {
        "version": "v10.5",
        "status": "OK",
        "generated_at": generated_at,
        "mode": "delegated_draft_monte_carlo_reference_check",
        "safe_mode": True,
        "research_only": True,
        "review_only": True,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "auto_trade_enabled": False,
        "supabase_write_enabled": False,
        "not_trade_order": True,
        "reference_check_status": check_status,
        "summary": {
            "reference_check_status": check_status,
            "daily_update_workflow_exists": daily_reference["daily_update_workflow"].get("exists"),
            "synthetic_risk_available": synthetic_ref.get("available"),
            "monte_carlo_reference_available": mc_ref.get("available"),
            "delegated_draft_status": draft_summary.get("delegated_draft_status"),
            "delegated_draft_line_count": draft_summary.get("draft_line_count"),
            "target_asset_weight_sum_pct": draft_summary.get("target_asset_weight_sum_pct"),
            "cash_target_weight_pct": draft_summary.get("cash_target_weight_pct"),
            "stressed_var95_pct": mc_ref.get("stressed_var95_pct"),
            "stressed_es95_pct": mc_ref.get("stressed_es95_pct"),
            "liquidity_run_probability_pct": mc_ref.get("liquidity_run_probability_pct"),
            "risk_note_count": len(risk_notes),
            "check_count": len(checks),
            "trade_signal_enabled": False,
            "execution_permission": False,
            "broker_submission_enabled": False,
        },
        "reference_checks": checks,
        "monte_carlo_reference": mc_ref,
        "synthetic_risk_reference": synthetic_ref,
        "delegated_draft_reference": {
            "generated_at": delegated.get("generated_at"),
            "status": delegated.get("delegated_draft_status"),
            "summary": draft_summary,
            "concentration_delta": concentration,
        },
        "risk_notes": risk_notes,
        "safety_boundary": [
            "v10.5 only references Daily Quant and Monte Carlo outputs; it does not rerun Monte Carlo and does not replace daily_update.yml.",
            "Monte Carlo reference is a risk diagnostic layer, not a buy/sell signal.",
            "This layer cannot enable execution_permission, broker_submission_enabled, auto_trade_enabled, official_rebalance_enabled, or trade_signal_enabled.",
        ],
    }

    DAILY_JSON.write_text(json.dumps(daily_reference, ensure_ascii=False, indent=2), encoding="utf-8")
    MC_JSON.write_text(json.dumps(mc_check, ensure_ascii=False, indent=2), encoding="utf-8")
    DAILY_MD.write_text("\n".join([
        "# v10.5 Daily Quant Reference Layer",
        "",
        f"- Generated: `{generated_at}`",
        f"- Portfolio source: `{row_source}`",
        f"- Daily update workflow exists: `{daily_reference['daily_update_workflow'].get('exists')}`",
        f"- Synthetic risk available: `{synthetic_ref.get('available')}`",
        f"- Monte Carlo / chaos_meta available: `{mc_ref.get('available')}`",
        f"- Execution permission: `False`",
    ]) + "\n", encoding="utf-8")
    MC_MD.write_text("\n".join([
        "# v10.5 Delegated Draft Monte Carlo Reference Check",
        "",
        f"- Generated: `{generated_at}`",
        f"- Reference check status: **{check_status}**",
        f"- Delegated draft status: `{draft_summary.get('delegated_draft_status')}`",
        f"- Draft line count: `{draft_summary.get('draft_line_count')}`",
        f"- Stressed VaR95: `{mc_ref.get('stressed_var95_pct')}`",
        f"- Stressed ES95: `{mc_ref.get('stressed_es95_pct')}`",
        f"- Liquidity run probability: `{mc_ref.get('liquidity_run_probability_pct')}`",
        f"- Execution permission: `False`",
    ]) + "\n", encoding="utf-8")

    print(f"Wrote {DAILY_JSON}")
    print(f"Wrote {DAILY_MD}")
    print(f"Wrote {MC_JSON}")
    print(f"Wrote {MC_MD}")
    print(f"Daily reference source: {row_source}")
    print(f"Monte Carlo reference available: {mc_ref.get('available')}")
    print(f"Synthetic risk available: {synthetic_ref.get('available')}")
    print(f"Reference check status: {check_status}")
    print("Execution permission: False")


if __name__ == "__main__":
    main()
