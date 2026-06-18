#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "native_target_thesis_latest.json"
SUMMARY_MD = OUT_DIR / "native_target_thesis_summary.md"


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


def maybe_num(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        x = float(v)
        if math.isfinite(x):
            return x
    except Exception:
        return None
    return None


def round4(v: Any) -> Optional[float]:
    x = maybe_num(v)
    if x is None:
        return None
    return round(x, 4)


def ticker_of(row: Dict[str, Any]) -> str:
    return str(row.get("ticker") or row.get("symbol") or row.get("asset") or "").strip()


def index_by_ticker(rows: List[Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in rows:
        d = as_dict(item)
        t = ticker_of(d)
        if t and t not in out:
            out[t] = d
    return out


def find_ranking_evidence(ticker: str, ranking_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    best: Optional[Dict[str, Any]] = None
    best_abs_delta = 0.0
    matched_adjustments: List[Dict[str, Any]] = []
    matched_alpha_contributors: List[Dict[str, Any]] = []
    for row in ranking_rows:
        for adj in as_list(row.get("top_adjustments")):
            adjd = as_dict(adj)
            if ticker_of(adjd) == ticker:
                matched_adjustments.append({
                    "ranking_id": row.get("ranking_id"),
                    "rank": row.get("rank"),
                    "ranking_status": row.get("ranking_status"),
                    "ranking_score": row.get("ranking_score"),
                    "delta_pct": round4(adjd.get("delta_pct")),
                    "direction": adjd.get("direction"),
                    "reason_codes": row.get("reason_codes", [])[:6],
                })
                ad = abs(num(adjd.get("delta_pct")))
                if best is None or ad > best_abs_delta:
                    best = row
                    best_abs_delta = ad
        for contrib in as_list(row.get("alpha_alignment_top_contributors")):
            cd = as_dict(contrib)
            if ticker_of(cd) == ticker:
                matched_alpha_contributors.append({
                    "ranking_id": row.get("ranking_id"),
                    "rank": row.get("rank"),
                    "delta_pct": round4(cd.get("delta_pct")),
                    "alpha_research_score": round4(cd.get("alpha_research_score")),
                    "alignment_contribution": round4(cd.get("alignment_contribution")),
                })
    return {
        "available": bool(matched_adjustments or matched_alpha_contributors),
        "best_rank": best.get("rank") if best else None,
        "best_ranking_status": best.get("ranking_status") if best else None,
        "best_ranking_score": round4(best.get("ranking_score")) if best else None,
        "matched_adjustments": matched_adjustments[:3],
        "matched_alpha_contributors": matched_alpha_contributors[:3],
    }


def direction_label(delta: Optional[float]) -> str:
    if delta is None:
        return "UNKNOWN"
    if delta > 0.05:
        return "UP"
    if delta < -0.05:
        return "DOWN"
    return "NEUTRAL"



def fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "缺值"
    return f"{v:.4f}%".rstrip("0").rstrip(".") + "%" if False else f"{v:.4f}%"


def signed_pp(v: Optional[float]) -> str:
    if v is None:
        return "缺值"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.4f}pp"


def classify_target_pressure(target: Optional[float], current: Optional[float]) -> str:
    if target is None or current is None:
        return "missing"
    diff = target - current
    if diff > 0.75:
        return "increase"
    if diff < -0.75:
        return "decrease"
    return "near_current"


def native_driver_summary(row: Dict[str, Any], alpha: Dict[str, Any], ranking: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    drivers: List[str] = []
    alpha_score = maybe_num(alpha.get("alpha_research_score"))
    alpha_disp = alpha.get("research_disposition") or alpha.get("alpha_research_band")
    if alpha_score is not None:
        if alpha_score >= 0.75:
            drivers.append(f"v5.1 alpha 分數偏正向（{alpha_score:.3f}），支持 v10.5 原生權重提高")
        elif alpha_score <= -0.75:
            drivers.append(f"v5.1 alpha 分數偏負向（{alpha_score:.3f}），壓低 v10.5 原生權重")
        else:
            drivers.append(f"v5.1 alpha 分數中性附近（{alpha_score:.3f}，{alpha_disp or 'N/A'}）")
    elif alpha_disp:
        drivers.append(f"v5.1 研究分層為 {alpha_disp}")

    matched = as_list(ranking.get("matched_adjustments"))
    if matched:
        ups = [m for m in matched if str(m.get("direction")).upper() == "UP"]
        downs = [m for m in matched if str(m.get("direction")).upper() == "DOWN"]
        top = as_dict(matched[0])
        if len(ups) > len(downs):
            drivers.append(f"v5.2 候選排序多數指向加碼；代表案例 rank {top.get('rank')}、delta {top.get('delta_pct')}pp")
        elif len(downs) > len(ups):
            drivers.append(f"v5.2 候選排序多數指向減碼；代表案例 rank {top.get('rank')}、delta {top.get('delta_pct')}pp")
        else:
            drivers.append(f"v5.2 候選排序有相關證據但方向不單一；代表案例 rank {top.get('rank')}")
    elif ranking.get("available"):
        drivers.append("v5.2 ranking / alpha alignment 有相關證據，但不是主要調整來源")
    else:
        drivers.append("v5.2 ranking 未提供明確單檔調整證據")

    risk_mode = context.get("risk_mode")
    if risk_mode:
        drivers.append(f"Daily Quant / Monte Carlo 風險模式：{risk_mode}")
    if row.get("mc_fragile_node"):
        drivers.append("該標的被 Monte Carlo / Daily Quant 標示為 fragile node，原生權重已受風險懲罰")
    mult = maybe_num(row.get("daily_quant_mc_multiplier"))
    if mult is not None and abs(mult - 1.0) > 1e-6:
        drivers.append(f"Daily Quant / MC multiplier={mult:.3f}，代表風險調整已作用於 v10.5 原生權重")
    return drivers[:5]


def build_target_origin_thesis(row: Dict[str, Any], alpha: Dict[str, Any], ranking: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    current = round4(row.get("current_weight_pct"))
    cloud = round4(row.get("cloud_target_weight_pct"))
    native = round4(row.get("v105_native_target_weight_pct"))
    final = round4(row.get("final_suggested_weight_pct", row.get("machine_target_weight_pct")))
    delta = round4(row.get("delta_weight_pct"))
    cloud_pressure = classify_target_pressure(cloud, current)
    native_pressure = classify_target_pressure(native, current)
    final_pressure = classify_target_pressure(final, current)
    final_blend = None if cloud is None or native is None else round((cloud + native) / 2.0, 4)
    conflict_factor = round4(row.get("conflict_adjustment_factor"))
    cloud_delta = None if cloud is None or current is None else round(cloud - current, 4)
    native_delta = None if native is None or current is None else round(native - current, 4)
    final_delta = None if final is None or current is None else round(final - current, 4)
    parts: List[str] = []
    cloud_line = "雲端%缺值，因此沒有採用 Supabase stock_meta 目標權重。"
    if cloud is not None:
        if cloud_pressure == "increase":
            cloud_line = f"雲端%={cloud:.4f}% 高於目前 {current:.4f}%（{signed_pp(cloud_delta)}），雲端 Daily Quant / stock_meta 來源支持加碼。"
        elif cloud_pressure == "decrease":
            cloud_line = f"雲端%={cloud:.4f}% 低於目前 {current:.4f}%（{signed_pp(cloud_delta)}），雲端 Daily Quant / stock_meta 來源支持減碼。"
        else:
            cloud_line = f"雲端%={cloud:.4f}% 接近目前 {current:.4f}%，雲端來源不支持大幅調整。"
    native_line = "v10.5 原生權重缺值，因此沒有 Optimizer Lab 原生目標可比較。"
    if native is not None:
        if native_pressure == "increase":
            native_line = f"v10.5 原生權重={native:.4f}% 高於目前 {current:.4f}%（{signed_pp(native_delta)}），Optimizer Lab 原生引擎支持加碼。"
        elif native_pressure == "decrease":
            native_line = f"v10.5 原生權重={native:.4f}% 低於目前 {current:.4f}%（{signed_pp(native_delta)}），Optimizer Lab 原生引擎支持減碼。"
        else:
            native_line = f"v10.5 原生權重={native:.4f}% 接近目前 {current:.4f}%，Optimizer Lab 原生引擎偏向維持。"
    parts.append(cloud_line)
    parts.append(native_line)
    if final_blend is not None:
        parts.append(f"雙來源初始混合=50%×雲端%+50%×v10.5%={final_blend:.4f}%。")
    if conflict_factor is not None and abs(conflict_factor - 1.0) > 1e-6:
        parts.append(f"因雲端%與 v10.5%分歧，套用衝突縮放係數 {conflict_factor:.4f}，只採納部分 drift。")
    if final is not None and current is not None:
        if final_pressure == "increase":
            parts.append(f"最終建議%={final:.4f}% 高於目前，形成加碼目標；差異 {signed_pp(final_delta)}。")
        elif final_pressure == "decrease":
            parts.append(f"最終建議%={final:.4f}% 低於目前，形成減碼目標；差異 {signed_pp(final_delta)}。")
        else:
            parts.append(f"最終建議%={final:.4f}% 接近目前，目標權重依據偏向觀察或小幅調整。")
    drivers = native_driver_summary(row, alpha, ranking, context)
    if drivers:
        parts.append("v10.5% 原生來源：" + "；".join(drivers) + "。")
    return {
        "cloud_target_pressure": cloud_pressure,
        "v105_native_target_pressure": native_pressure,
        "final_target_pressure": final_pressure,
        "dual_blend_pre_conflict_pct": final_blend,
        "cloud_delta_vs_current_pct": cloud_delta,
        "native_delta_vs_current_pct": native_delta,
        "final_delta_vs_current_pct": final_delta,
        "target_origin_thesis": " ".join(parts),
        "target_origin_bullets": parts,
        "v105_native_driver_bullets": drivers,
    }


def build_thesis(row: Dict[str, Any], alpha: Dict[str, Any], ranking: Dict[str, Any], constraints: Dict[str, Any], context: Dict[str, Any], governance: Dict[str, Any], walk_forward: Dict[str, Any]) -> Dict[str, Any]:
    ticker = ticker_of(row)
    current = round4(row.get("current_weight_pct"))
    cloud = round4(row.get("cloud_target_weight_pct"))
    native = round4(row.get("v105_native_target_weight_pct"))
    final = round4(row.get("final_suggested_weight_pct", row.get("machine_target_weight_pct")))
    delta = round4(row.get("delta_weight_pct"))
    cloud_gap = None if cloud is None or native is None else round(abs(cloud - native), 4)
    direction = row.get("direction") or direction_label(delta)
    alpha_score = round4(alpha.get("alpha_research_score"))
    alpha_band = alpha.get("alpha_research_band")
    alpha_disposition = alpha.get("research_disposition")
    price_status = constraints.get("price_quality_status")
    price_provider = constraints.get("price_provider")
    sizing_allowed = constraints.get("trade_sizing_allowed")
    fragile = bool(row.get("mc_fragile_node"))
    multiplier = round4(row.get("daily_quant_mc_multiplier"))
    reasons: List[str] = []
    if cloud is None:
        reasons.append("cloud_target_missing")
    else:
        reasons.append("cloud_target_available")
    if native is not None:
        reasons.append("v105_native_target_available")
    if alpha_score is not None:
        reasons.append(f"alpha_score:{alpha_score}")
    if alpha_disposition:
        reasons.append(f"alpha:{alpha_disposition}")
    if ranking.get("available"):
        reasons.append("v5_2_ranking_evidence_available")
    if context.get("risk_mode"):
        reasons.append(f"risk_mode:{context.get('risk_mode')}")
    if fragile:
        reasons.append("monte_carlo_fragile_node_penalty")
    if row.get("dual_target_direction_conflict"):
        reasons.append("dual_target_direction_conflict")
    if row.get("conflict_adjustment_factor") not in (None, 1, 1.0):
        reasons.append(f"conflict_adjustment_factor:{round4(row.get('conflict_adjustment_factor'))}")
    if price_status:
        reasons.append(f"price_quality:{price_status}")

    cloud_dir = direction_label(None if cloud is None or current is None else cloud - current)
    native_dir = direction_label(None if native is None or current is None else native - current)
    final_dir = direction_label(delta)
    agreement = "unknown"
    if cloud is not None and native is not None and cloud_dir != "NEUTRAL" and native_dir != "NEUTRAL":
        agreement = "aligned" if cloud_dir == native_dir else "conflict"
    elif cloud is not None and native is not None:
        agreement = "weak_or_neutral"

    thesis_parts: List[str] = []
    if final_dir == "UP":
        thesis_parts.append("最終建議權重高於現有權重，形成加碼草案依據。")
    elif final_dir == "DOWN":
        thesis_parts.append("最終建議權重低於現有權重，形成減碼草案依據。")
    else:
        thesis_parts.append("最終建議權重接近現有權重，偏向不動或僅小幅調整。")
    if cloud is not None and native is not None:
        thesis_parts.append(f"雲端目標 {cloud}% 與 v10.5 原生目標 {native}% 以 50/50 形成雙來源基礎；分歧約 {cloud_gap} 個百分點。")
    elif cloud is not None:
        thesis_parts.append(f"雲端目標 {cloud}% 可用；v10.5 原生目標不足時以可用資料保守處理。")
    elif native is not None:
        thesis_parts.append(f"雲端目標缺失；主要依 v10.5 原生目標 {native}% 形成研究草案。")
    if agreement == "conflict":
        thesis_parts.append("雲端%與 v10.5%方向相反或明顯分歧，已啟用衝突縮放或警示，不視為高一致性訊號。")
    elif agreement == "aligned":
        thesis_parts.append("雲端%與 v10.5%方向一致，訊號一致性較高。")
    if fragile:
        thesis_parts.append("Monte Carlo / Daily Quant 風險參考標示為 fragile node，因此 v10.5 原生權重已受風險懲罰。")
    if alpha_score is not None:
        thesis_parts.append(f"v5.1 alpha research score 約 {alpha_score}，研究分層為 {alpha_band or 'N/A'}。")
    if ranking.get("available"):
        thesis_parts.append("v5.2 candidate ranking 或 alpha alignment 中有該標的相關調整證據。")
    if price_status:
        thesis_parts.append(f"交易 sizing 價格來源為 {price_status}，provider={price_provider or 'N/A'}。")

    origin = build_target_origin_thesis(row, alpha, ranking, context)

    return {
        "ticker": ticker,
        "current_weight_pct": current,
        "cloud_target_weight_pct": cloud,
        "v105_native_target_weight_pct": native,
        "final_suggested_weight_pct": final,
        "delta_weight_pct": delta,
        "direction": direction,
        "target_origin_thesis": origin.get("target_origin_thesis"),
        "target_origin_bullets": origin.get("target_origin_bullets", []),
        "v105_native_driver_bullets": origin.get("v105_native_driver_bullets", []),
        "dual_blend_pre_conflict_pct": origin.get("dual_blend_pre_conflict_pct"),
        "cloud_delta_vs_current_pct": origin.get("cloud_delta_vs_current_pct"),
        "native_delta_vs_current_pct": origin.get("native_delta_vs_current_pct"),
        "final_delta_vs_current_pct": origin.get("final_delta_vs_current_pct"),
        "cloud_target_pressure": origin.get("cloud_target_pressure"),
        "v105_native_target_pressure": origin.get("v105_native_target_pressure"),
        "final_target_pressure": origin.get("final_target_pressure"),
        "cloud_vs_native_gap_pct": cloud_gap,
        "cloud_direction_vs_current": cloud_dir,
        "native_direction_vs_current": native_dir,
        "final_direction_vs_current": final_dir,
        "source_agreement": agreement,
        "conflict_adjustment_factor": round4(row.get("conflict_adjustment_factor")),
        "daily_quant_mc_multiplier": multiplier,
        "mc_fragile_node": fragile,
        "alpha_research_score": alpha_score,
        "alpha_research_band": alpha_band,
        "alpha_research_disposition": alpha_disposition,
        "ranking_evidence": ranking,
        "price_quality_status": price_status,
        "trade_sizing_allowed": sizing_allowed,
        "evidence_sources": {
            "v5_1_alpha_research": bool(alpha),
            "v5_2_rebalance_ranking": bool(ranking.get("available")),
            "v3_0_regime": bool(context.get("selected_regime")),
            "v3_3_walk_forward": bool(walk_forward),
            "v3_4_governance": bool(governance),
            "v10_5_daily_quant_mc": bool(context),
            "v8_1_trading_constraints": bool(constraints),
        },
        "reason_codes": reasons[:12],
        "thesis_summary": " ".join(thesis_parts),
    }


def main() -> None:
    delegated = as_dict(read_json("data/alpha/delegated_target_weight_draft_latest.json", {}))
    alpha_rows = index_by_ticker(as_list(read_json("data/alpha/alpha_research_sandbox_latest.json", {}).get("asset_alpha_research", [])))
    ranking_rows = [as_dict(x) for x in as_list(read_json("data/alpha/rebalance_candidate_ranking_latest.json", {}).get("ranking_rows", []))]
    constraints_rows = index_by_ticker(as_list(read_json("data/alpha/trading_constraints_snapshot_latest.json", {}).get("asset_rows", [])))
    daily_ref = as_dict(read_json("data/alpha/daily_quant_reference_latest.json", {}))
    mc_check = as_dict(read_json("data/alpha/delegated_draft_monte_carlo_check_latest.json", {}))
    regime = as_dict(read_json("data/optimizer/regime_aware_optimizer_latest.json", {}))
    walk_forward = as_dict(read_json("data/optimizer/walk_forward_backtest_latest.json", {}))
    governance = as_dict(read_json("data/optimizer/model_governance_dashboard_latest.json", {}))

    rows = [as_dict(x) for x in as_list(delegated.get("machine_target_rows"))]
    thesis_rows: List[Dict[str, Any]] = []
    for row in rows:
        t = ticker_of(row)
        if not t:
            continue
        ranking_evidence = find_ranking_evidence(t, ranking_rows)
        context = {
            "risk_mode": as_dict(delegated.get("daily_quant_monte_carlo_context")).get("risk_mode"),
            "selected_regime": as_dict(regime.get("regime")).get("selected_regime"),
            "governance_verdict": as_dict(governance.get("summary")).get("verdict"),
            "walk_forward_status": as_dict(walk_forward.get("summary")).get("verdict") or walk_forward.get("status"),
            "mc_reference_status": mc_check.get("reference_check_status"),
            "daily_reference_source": daily_ref.get("portfolio_source"),
        }
        thesis_rows.append(build_thesis(row, alpha_rows.get(t, {}), ranking_evidence, constraints_rows.get(t, {}), context, governance, walk_forward))

    # Prioritize rows with active draft lines, then large absolute drift.
    draft_line_tickers = {ticker_of(as_dict(x)) for x in as_list(delegated.get("delegated_draft_lines"))}
    thesis_rows.sort(key=lambda r: (0 if r["ticker"] in draft_line_tickers else 1, -abs(num(r.get("delta_weight_pct")))), reverse=False)

    agreement_counts: Dict[str, int] = {}
    for r in thesis_rows:
        agreement_counts[r.get("source_agreement") or "unknown"] = agreement_counts.get(r.get("source_agreement") or "unknown", 0) + 1

    summary = {
        "status": "thesis_available" if thesis_rows else "no_thesis_rows",
        "row_count": len(thesis_rows),
        "draft_line_related_count": sum(1 for r in thesis_rows if r["ticker"] in draft_line_tickers),
        "source_agreement_counts": agreement_counts,
        "delegated_draft_status": delegated.get("delegated_draft_status"),
        "target_weight_source": delegated.get("target_weight_source"),
        "cloud_target_source": delegated.get("cloud_target_weight_source"),
        "v105_native_target_source": delegated.get("v105_native_target_source"),
        "front_end_manual_mc_percent_target_used": bool(delegated.get("frontend_mc_percent_target_used")),
        "execution_permission": False,
    }

    output = {
        "version": "v10.5.3",
        "status": summary["status"],
        "generated_at": now_iso(),
        "mode": "target_weight_origin_thesis_aggregation",
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
        "not_buy_signal": True,
        "not_sell_signal": True,
        "summary": summary,
        "source_files": {
            "delegated_target_weight_draft": "data/alpha/delegated_target_weight_draft_latest.json",
            "alpha_research_sandbox": "data/alpha/alpha_research_sandbox_latest.json",
            "rebalance_candidate_ranking": "data/alpha/rebalance_candidate_ranking_latest.json",
            "regime_aware_optimizer": "data/optimizer/regime_aware_optimizer_latest.json",
            "walk_forward_backtest": "data/optimizer/walk_forward_backtest_latest.json",
            "model_governance_dashboard": "data/optimizer/model_governance_dashboard_latest.json",
            "daily_quant_reference": "data/alpha/daily_quant_reference_latest.json",
            "delegated_draft_monte_carlo_check": "data/alpha/delegated_draft_monte_carlo_check_latest.json",
            "trading_constraints_snapshot": "data/alpha/trading_constraints_snapshot_latest.json",
        },
        "thesis_policy": {
            "purpose": "Explain where each target weight comes from: cloud target, v10.5 native target, 50/50 blend, conflict scaling, and earlier optimizer evidence.",
            "does_not_recalculate_target_weights": True,
            "does_not_use_frontend_manual_mc_percent": True,
            "display_position": "between_v10_0_human_confirmed_ticket_and_v10_5_1_delegated_draft",
        },
        "thesis_rows": thesis_rows,
        "safety_boundary": [
            "This layer explains target-weight origin and v10.5 delegated target weights; it does not create orders.",
            "It does not enable execution_permission, trade_signal_enabled, broker_submission_enabled, or Supabase writes.",
            "Thesis text is explanatory and not investment advice.",
        ],
    }

    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# v10.5.3 Target Weight Origin Thesis Aggregator",
        "",
        f"Generated at: {output['generated_at']}",
        f"Status: {output['status']}",
        f"Rows: {len(thesis_rows)}",
        f"Draft-line related rows: {summary['draft_line_related_count']}",
        "",
        "This layer explains where the target weights come from: cloud%, v10.5 native%, blend, conflict scaling, and optimizer evidence. It does not create trade orders.",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Thesis status: {output['status']}")
    print(f"Thesis rows: {len(thesis_rows)}")
    print("Execution permission: False")


if __name__ == "__main__":
    main()
