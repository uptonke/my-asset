#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

OUT_DIR = Path("data/optimizer")
SKFOLIO = OUT_DIR / "skfolio_sandbox_latest.json"
RISKFOLIO = OUT_DIR / "riskfolio_sandbox_latest.json"
STRESS = OUT_DIR / "optimizer_stress_latest.json"
JSON_OUT = OUT_DIR / "risk_reduction_simulator_latest.json"
MD_OUT = OUT_DIR / "risk_reduction_simulator_summary.md"

VERSION = "v2.2"
CASH_TICKER = "BOXX"
FOCUS_TICKERS = ["00981A", "BTC-USD", "ETH-USD", "QQQ", "GLDM"]
TRIM_FRACTIONS = [0.25, 0.50, 1.00]

SAFE_MODE_NOTE = (
    "v2.2 只模擬降低特定風險來源並轉入現金等價部位的風險變化；"
    "不產生 BUY / SELL 指令，不寫入 Supabase，不修改正式持倉或正式權重。"
)

# Fallback copy of stress-test bucket logic so v2.2 remains robust even if the
# v1.7 stress module is temporarily unavailable.
def ticker_bucket(ticker: str) -> str:
    t = str(ticker or "").upper()
    if t == "BOXX" or "CASH" in t:
        return "cash"
    if t in {"GLDM", "GLD"} or "GOLD" in t:
        return "gold"
    if t in {"BTC-USD", "ETH-USD"} or "BTC" in t or "ETH" in t or "加密" in t:
        return "crypto"
    if t in {"00981A", "2330"} or t.startswith("00") or t.isdigit() or "台灣" in t:
        return "taiwan_tech"
    if t in {"QQQ"}:
        return "us_tech"
    if t in {"VOO", "VTI", "USMV"}:
        return "us_equity"
    if t in {"AVUV"}:
        return "us_small_value"
    if t in {"VEA"}:
        return "developed_ex_us"
    if t in {"VNM"}:
        return "emerging_vietnam"
    if t in {"GRID", "IFRA", "SRVR"}:
        return "infrastructure_theme"
    if t in {"PICK"}:
        return "commodity_equity"
    return "other_risk"


FALLBACK_SCENARIOS: List[Dict[str, Any]] = [
    {
        "key": "rate_hike_2022_like",
        "label": "2022 升息 / 股債齊跌近似",
        "description": "高估值科技、加密、利率敏感資產同步承壓；現金防守。",
        "bucket_shocks": {
            "cash": 0.2, "gold": -8.0, "crypto": -55.0, "taiwan_tech": -28.0,
            "us_tech": -32.0, "us_equity": -22.0, "us_small_value": -24.0,
            "developed_ex_us": -20.0, "emerging_vietnam": -30.0,
            "infrastructure_theme": -24.0, "commodity_equity": -16.0, "other_risk": -20.0,
        },
    },
    {
        "key": "crypto_crash",
        "label": "加密崩盤",
        "description": "BTC / ETH 大跌並拖累風險偏好。",
        "bucket_shocks": {
            "cash": 0.0, "gold": 4.0, "crypto": -70.0, "taiwan_tech": -10.0,
            "us_tech": -12.0, "us_equity": -8.0, "us_small_value": -10.0,
            "developed_ex_us": -7.0, "emerging_vietnam": -12.0,
            "infrastructure_theme": -8.0, "commodity_equity": -8.0, "other_risk": -8.0,
        },
    },
    {
        "key": "taiwan_tech_correction",
        "label": "台股科技修正",
        "description": "台股科技與半導體權重承壓，全球科技同步回檔。",
        "bucket_shocks": {
            "cash": 0.0, "gold": 3.0, "crypto": -25.0, "taiwan_tech": -35.0,
            "us_tech": -15.0, "us_equity": -10.0, "us_small_value": -12.0,
            "developed_ex_us": -8.0, "emerging_vietnam": -14.0,
            "infrastructure_theme": -10.0, "commodity_equity": -8.0, "other_risk": -10.0,
        },
    },
    {
        "key": "risk_off_usd_squeeze",
        "label": "美元擠壓 / 全球 risk-off",
        "description": "全球股市與新興市場下跌；黃金小幅防守，現金穩定。",
        "bucket_shocks": {
            "cash": 0.0, "gold": 5.0, "crypto": -40.0, "taiwan_tech": -22.0,
            "us_tech": -22.0, "us_equity": -18.0, "us_small_value": -22.0,
            "developed_ex_us": -20.0, "emerging_vietnam": -32.0,
            "infrastructure_theme": -18.0, "commodity_equity": -20.0, "other_risk": -18.0,
        },
    },
    {
        "key": "gold_hedge_failure",
        "label": "黃金避險失效",
        "description": "黃金與風險資產同跌，檢查 GLDM 避險失靈情境。",
        "bucket_shocks": {
            "cash": 0.0, "gold": -18.0, "crypto": -30.0, "taiwan_tech": -14.0,
            "us_tech": -16.0, "us_equity": -12.0, "us_small_value": -14.0,
            "developed_ex_us": -12.0, "emerging_vietnam": -18.0,
            "infrastructure_theme": -12.0, "commodity_equity": -14.0, "other_risk": -12.0,
        },
    },
    {
        "key": "theme_etf_liquidity_shock",
        "label": "主題 ETF 流動性折價",
        "description": "主題、基建、資料中心、礦業 ETF 同步折價。",
        "bucket_shocks": {
            "cash": 0.0, "gold": 2.0, "crypto": -25.0, "taiwan_tech": -16.0,
            "us_tech": -18.0, "us_equity": -12.0, "us_small_value": -16.0,
            "developed_ex_us": -10.0, "emerging_vietnam": -18.0,
            "infrastructure_theme": -32.0, "commodity_equity": -30.0, "other_risk": -12.0,
        },
    },
]

RISK_PROXY = {
    "cash": 0.05,
    "gold": 0.85,
    "crypto": 5.00,
    "taiwan_tech": 2.60,
    "us_tech": 2.40,
    "us_equity": 1.55,
    "us_small_value": 2.00,
    "developed_ex_us": 1.70,
    "emerging_vietnam": 3.00,
    "infrastructure_theme": 2.10,
    "commodity_equity": 2.30,
    "other_risk": 1.80,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "READ_ERROR", "error": str(exc)[:800]}


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def round_or_none(value: Any, ndigits: int = 3) -> Optional[float]:
    v = safe_float(value)
    return round(v, ndigits) if v is not None else None


def normalize(weights: Dict[str, float]) -> Dict[str, float]:
    clean = {str(k): max(0.0, safe_float(v, 0.0) or 0.0) for k, v in weights.items() if str(k)}
    total = sum(clean.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in clean.items()}


def weight_map_from_rows(rows: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip()
        if not ticker:
            continue
        out[ticker] = (safe_float(row.get("weight_pct"), 0.0) or 0.0) / 100.0
    return normalize(out)


def current_portfolio_payload() -> Tuple[Dict[str, float], Dict[str, Any], str]:
    skfolio = load_json(SKFOLIO)
    riskfolio = load_json(RISKFOLIO)
    for source, payload in (("skfolio", skfolio), ("riskfolio", riskfolio)):
        p = ((payload.get("portfolios") or {}).get("current_weight") or {}) if isinstance(payload, dict) else {}
        weights = weight_map_from_rows(p.get("weights", [])) if isinstance(p, dict) else {}
        if weights:
            return weights, p, source
    return {}, {}, "missing"


def load_scenarios() -> List[Dict[str, Any]]:
    # Prefer the maintained v1.7 module, but use fallback constants if import fails.
    try:
        from run_optimizer_stress_tests import SCENARIOS as scenarios  # type: ignore
        if isinstance(scenarios, list) and scenarios:
            return scenarios
    except Exception:
        pass
    return FALLBACK_SCENARIOS


def stress_return(weights: Dict[str, float], scenario: Dict[str, Any]) -> Dict[str, Any]:
    w = normalize(weights)
    shocks = scenario.get("bucket_shocks", {}) or {}
    contributions = []
    total = 0.0
    for ticker, weight in w.items():
        bucket = ticker_bucket(ticker)
        shock_pct = safe_float(shocks.get(bucket, shocks.get("other_risk", -10.0)), -10.0) or -10.0
        contribution_pct = weight * shock_pct
        total += contribution_pct
        contributions.append({
            "ticker": ticker,
            "bucket": bucket,
            "weight_pct": round(weight * 100.0, 3),
            "shock_pct": round(shock_pct, 2),
            "contribution_pct": round(contribution_pct, 3),
        })
    contributions.sort(key=lambda x: x["contribution_pct"])
    return {"return_pct": round(total, 3), "top_contributors": contributions[:5]}


def stress_profile(weights: Dict[str, float], scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_scenario = {}
    returns = []
    for s in scenarios:
        sr = stress_return(weights, s)
        by_scenario[s["key"]] = sr
        returns.append(sr["return_pct"])
    return {
        "worst_scenario_return_pct": round(min(returns), 3) if returns else None,
        "avg_scenario_return_pct": round(sum(returns) / len(returns), 3) if returns else None,
        "best_scenario_return_pct": round(max(returns), 3) if returns else None,
        "scenario_returns": by_scenario,
    }


def risk_proxy_score(weights: Dict[str, float]) -> float:
    w = normalize(weights)
    return math.sqrt(sum((weight ** 2) * RISK_PROXY.get(ticker_bucket(ticker), 1.8) for ticker, weight in w.items()))


def proxy_metrics(base_metrics: Dict[str, Any], base_stress: Dict[str, Any], current: Dict[str, float], proposed: Dict[str, float]) -> Dict[str, Any]:
    cur_score = risk_proxy_score(current)
    new_score = risk_proxy_score(proposed)
    ratio = new_score / cur_score if cur_score > 0 else 1.0

    vol = safe_float(base_metrics.get("annual_vol_pct"))
    es = safe_float(base_metrics.get("es95_pct"))
    mdd = safe_float(base_metrics.get("max_drawdown_pct"))
    cur_worst = safe_float(base_stress.get("worst_scenario_return_pct"))
    new_worst = safe_float(stress_profile(proposed, load_scenarios()).get("worst_scenario_return_pct"))

    mdd_ratio = 1.0
    if cur_worst is not None and new_worst is not None and cur_worst < 0:
        mdd_ratio = abs(new_worst / cur_worst)

    return {
        "metric_source": "proxy_diagonal_bucket_risk",
        "annual_vol_pct": round(vol * ratio, 3) if vol is not None else None,
        "es95_pct": round(es * ratio, 3) if es is not None else None,
        "max_drawdown_pct": round(mdd * mdd_ratio, 3) if mdd is not None else None,
        "risk_proxy_ratio_vs_current": round(ratio, 4),
        "warning": "No covariance/return-matrix recomputation is used here; this is a conservative proxy layer derived from current metrics and deterministic stress buckets.",
    }


def trim_to_cash(weights: Dict[str, float], ticker: str, trim_fraction: float) -> Tuple[Dict[str, float], float]:
    w = normalize(weights)
    if ticker not in w or w[ticker] <= 0:
        return w, 0.0
    trim_amount = w[ticker] * trim_fraction
    w[ticker] = max(0.0, w[ticker] - trim_amount)
    w[CASH_TICKER] = w.get(CASH_TICKER, 0.0) + trim_amount
    return normalize(w), trim_amount


def exposure(weights: Dict[str, float]) -> Dict[str, Any]:
    w = normalize(weights)
    out = {"cash_pct": 0.0, "gold_pct": 0.0, "crypto_pct": 0.0, "taiwan_pct": 0.0, "other_pct": 0.0}
    max_ticker = None
    max_weight = -1.0
    for ticker, weight in w.items():
        bucket = ticker_bucket(ticker)
        if bucket == "cash":
            out["cash_pct"] += weight * 100.0
        elif bucket == "gold":
            out["gold_pct"] += weight * 100.0
        elif bucket == "crypto":
            out["crypto_pct"] += weight * 100.0
        elif bucket == "taiwan_tech":
            out["taiwan_pct"] += weight * 100.0
        else:
            out["other_pct"] += weight * 100.0
        if weight > max_weight:
            max_weight = weight
            max_ticker = ticker
    return {
        **{k: round(v, 3) for k, v in out.items()},
        "max_single_weight_pct": round(max_weight * 100.0, 3) if max_weight >= 0 else None,
        "max_single_ticker": max_ticker,
    }


def score_candidate(row: Dict[str, Any]) -> float:
    d = row.get("improvement_vs_current", {}) or {}
    worst = safe_float(d.get("worst_scenario_return_improvement_pp"), 0.0) or 0.0
    avg = safe_float(d.get("avg_scenario_return_improvement_pp"), 0.0) or 0.0
    vol = -(safe_float(d.get("annual_vol_change_pp"), 0.0) or 0.0)
    es = -(safe_float(d.get("es95_change_pp"), 0.0) or 0.0)
    turnover = safe_float(row.get("turnover_to_cash_pct"), 0.0) or 0.0
    return round(2.0 * worst + 0.75 * avg + 0.6 * vol + 0.8 * es - 0.08 * turnover, 3)


def verdict(row: Dict[str, Any]) -> str:
    d = row.get("improvement_vs_current", {}) or {}
    worst = safe_float(d.get("worst_scenario_return_improvement_pp"), 0.0) or 0.0
    avg = safe_float(d.get("avg_scenario_return_improvement_pp"), 0.0) or 0.0
    es = safe_float(d.get("es95_change_pp"), 0.0) or 0.0
    vol = safe_float(d.get("annual_vol_change_pp"), 0.0) or 0.0
    target = row.get("target_ticker")
    if worst >= 1.0 and avg >= 0.2 and es <= 0.05 and vol <= 0.05:
        return "risk_reduction_candidate"
    if worst > 0.0 and avg >= -0.1:
        return "tradeoff_review"
    if target == "GLDM" and worst < 0:
        return "hedge_trim_risk_warning"
    return "not_effective"


def build() -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    current, current_payload, source = current_portfolio_payload()
    scenarios = load_scenarios()
    current_stress = stress_profile(current, scenarios) if current else {}
    base_metrics = (current_payload.get("metrics") or {}) if isinstance(current_payload, dict) else {}
    base_proxy = proxy_metrics(base_metrics, current_stress, current, current) if current else {}

    simulations: List[Dict[str, Any]] = []
    for ticker in FOCUS_TICKERS:
        if ticker not in current or current[ticker] <= 0:
            continue
        for frac in TRIM_FRACTIONS:
            proposed, trimmed = trim_to_cash(current, ticker, frac)
            proposed_stress = stress_profile(proposed, scenarios)
            proposed_metrics = proxy_metrics(base_metrics, current_stress, current, proposed)

            improvements = {
                "worst_scenario_return_improvement_pp": round_or_none(
                    (safe_float(proposed_stress.get("worst_scenario_return_pct"), 0.0) or 0.0)
                    - (safe_float(current_stress.get("worst_scenario_return_pct"), 0.0) or 0.0)
                ),
                "avg_scenario_return_improvement_pp": round_or_none(
                    (safe_float(proposed_stress.get("avg_scenario_return_pct"), 0.0) or 0.0)
                    - (safe_float(current_stress.get("avg_scenario_return_pct"), 0.0) or 0.0)
                ),
                "annual_vol_change_pp": round_or_none(
                    (safe_float(proposed_metrics.get("annual_vol_pct"), 0.0) or 0.0)
                    - (safe_float(base_proxy.get("annual_vol_pct"), 0.0) or 0.0)
                ),
                "es95_change_pp": round_or_none(
                    (safe_float(proposed_metrics.get("es95_pct"), 0.0) or 0.0)
                    - (safe_float(base_proxy.get("es95_pct"), 0.0) or 0.0)
                ),
                "max_drawdown_change_pp": round_or_none(
                    (safe_float(proposed_metrics.get("max_drawdown_pct"), 0.0) or 0.0)
                    - (safe_float(base_proxy.get("max_drawdown_pct"), 0.0) or 0.0)
                ),
            }

            scenario_deltas = []
            for s in scenarios:
                key = s["key"]
                before = ((current_stress.get("scenario_returns") or {}).get(key) or {}).get("return_pct")
                after = ((proposed_stress.get("scenario_returns") or {}).get(key) or {}).get("return_pct")
                scenario_deltas.append({
                    "scenario_key": key,
                    "scenario_label": s.get("label"),
                    "current_return_pct": round_or_none(before),
                    "simulated_return_pct": round_or_none(after),
                    "improvement_pp": round_or_none((safe_float(after, 0.0) or 0.0) - (safe_float(before, 0.0) or 0.0)),
                })

            row: Dict[str, Any] = {
                "simulation_id": f"v2_2_trim_{ticker.replace('-', '_')}_{int(frac * 100)}pct_to_{CASH_TICKER}",
                "target_ticker": ticker,
                "trim_fraction_of_position": frac,
                "current_weight_pct": round(current.get(ticker, 0.0) * 100.0, 3),
                "trimmed_weight_pct": round(trimmed * 100.0, 3),
                "turnover_to_cash_pct": round(trimmed * 100.0, 3),
                "reallocation_ticker": CASH_TICKER,
                "current_stress": current_stress,
                "simulated_stress": proposed_stress,
                "current_proxy_metrics": base_proxy,
                "simulated_proxy_metrics": proposed_metrics,
                "improvement_vs_current": improvements,
                "scenario_deltas": scenario_deltas,
                "exposure_after": exposure(proposed),
                "execution_permission": False,
                "not_trade_order": True,
                "requires_manual_approval": True,
            }
            row["risk_reduction_score"] = score_candidate(row)
            row["verdict"] = verdict(row)
            simulations.append(row)

    simulations.sort(key=lambda r: safe_float(r.get("risk_reduction_score"), -9999.0) or -9999.0, reverse=True)
    top_candidates = [r for r in simulations if r.get("verdict") == "risk_reduction_candidate"][:5]
    tradeoffs = [r for r in simulations if r.get("verdict") == "tradeoff_review"][:5]
    warnings = [r for r in simulations if r.get("verdict") == "hedge_trim_risk_warning"][:5]

    payload = {
        "version": VERSION,
        "status": "OK" if current else "MISSING_CURRENT_WEIGHTS",
        "generated_at": now_utc(),
        "mode": "risk_reduction_simulator",
        "safe_mode": True,
        "safe_mode_note": SAFE_MODE_NOTE,
        "source_files": {
            "skfolio": str(SKFOLIO),
            "riskfolio": str(RISKFOLIO),
            "stress": str(STRESS),
        },
        "baseline_source": source,
        "policy": {
            "focus_tickers": FOCUS_TICKERS,
            "trim_fractions": TRIM_FRACTIONS,
            "reallocation_ticker": CASH_TICKER,
            "output_is_not_trade_order": True,
        },
        "baseline": {
            "weights": {k: round(v * 100.0, 3) for k, v in sorted(current.items())},
            "exposure": exposure(current) if current else {},
            "stress": current_stress,
            "proxy_metrics": base_proxy,
        },
        "simulations": simulations,
        "summary": {
            "simulation_count": len(simulations),
            "risk_reduction_candidate_count": len(top_candidates),
            "tradeoff_review_count": len(tradeoffs),
            "hedge_trim_warning_count": len(warnings),
            "top_risk_reduction_candidates": [r["simulation_id"] for r in top_candidates],
            "top_tradeoff_reviews": [r["simulation_id"] for r in tradeoffs],
            "top_warning_cases": [r["simulation_id"] for r in warnings],
            "best_simulation_id": simulations[0]["simulation_id"] if simulations else None,
            "verdict": "有風險降低候選可進入 v2.3 約束檢查。" if top_candidates else "沒有明確風險降低候選；僅供觀察。",
        },
        "warnings": [
            "v2.2 uses deterministic stress scenarios and proxy risk metrics; it is not a return forecast.",
            "Trim-to-cash simulations are diagnostics only and may ignore tax, liquidity, spread and minimum unit constraints.",
            "GLDM trimming can improve gold-hedge-failure scenario but may worsen risk-off hedge behavior; review scenario deltas, not only score.",
        ],
    }
    return payload


def write_md(payload: Dict[str, Any]) -> str:
    s = payload.get("summary", {}) or {}
    lines = [
        "# Risk Reduction Simulator v2.2",
        "",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Safety Boundary",
        "",
        "- This is not a BUY / SELL list.",
        "- execution_permission is always false in v2.2.",
        "- No Supabase write.",
        "- No official portfolio weight update.",
        "- Human approval is mandatory before any real-world action.",
        "",
        "## Summary",
        "",
        f"- Simulation count: `{s.get('simulation_count')}`",
        f"- Risk reduction candidates: `{s.get('risk_reduction_candidate_count')}`",
        f"- Tradeoff reviews: `{s.get('tradeoff_review_count')}`",
        f"- Best simulation: `{s.get('best_simulation_id')}`",
        f"- Verdict: {s.get('verdict')}",
        "",
        "## Top Simulations",
        "",
        "| Simulation | Verdict | Trim | Worst stress improvement | Avg stress improvement | ES proxy change | Vol proxy change | Score |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in (payload.get("simulations") or [])[:12]:
        d = r.get("improvement_vs_current", {}) or {}
        lines.append(
            f"| `{r.get('simulation_id')}` | `{r.get('verdict')}` | {r.get('trimmed_weight_pct')}% | "
            f"{d.get('worst_scenario_return_improvement_pp')}pp | {d.get('avg_scenario_return_improvement_pp')}pp | "
            f"{d.get('es95_change_pp')}pp | {d.get('annual_vol_change_pp')}pp | {r.get('risk_reduction_score')} |"
        )
    lines.extend([
        "",
        "## Method Notes",
        "",
        "- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.",
        "- Stress improvements are deterministic scenario deltas, not forecasts.",
        "- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    payload = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(write_md(payload), encoding="utf-8")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Simulation count: {payload['summary']['simulation_count']}")
    print(f"Risk reduction candidates: {payload['summary']['risk_reduction_candidate_count']}")


if __name__ == "__main__":
    main()
