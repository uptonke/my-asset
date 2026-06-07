#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else default
    except Exception:
        return default


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


SCENARIOS = [
    {
        "key": "rate_hike_2022_like",
        "label": "2022 升息 / 股債齊跌近似",
        "description": "高估值科技、加密、利率敏感資產同步承壓；現金防守。",
        "bucket_shocks": {
            "cash": 0.2,
            "gold": -8.0,
            "crypto": -55.0,
            "taiwan_tech": -28.0,
            "us_tech": -32.0,
            "us_equity": -22.0,
            "us_small_value": -24.0,
            "developed_ex_us": -20.0,
            "emerging_vietnam": -30.0,
            "infrastructure_theme": -24.0,
            "commodity_equity": -16.0,
            "other_risk": -20.0,
        },
    },
    {
        "key": "crypto_crash",
        "label": "加密崩盤",
        "description": "BTC / ETH 大跌並拖累風險偏好。",
        "bucket_shocks": {
            "cash": 0.0,
            "gold": 4.0,
            "crypto": -70.0,
            "taiwan_tech": -10.0,
            "us_tech": -12.0,
            "us_equity": -8.0,
            "us_small_value": -10.0,
            "developed_ex_us": -7.0,
            "emerging_vietnam": -12.0,
            "infrastructure_theme": -8.0,
            "commodity_equity": -8.0,
            "other_risk": -8.0,
        },
    },
    {
        "key": "taiwan_tech_correction",
        "label": "台股科技修正",
        "description": "台股科技與半導體權重承壓，全球科技同步回檔。",
        "bucket_shocks": {
            "cash": 0.0,
            "gold": 3.0,
            "crypto": -25.0,
            "taiwan_tech": -35.0,
            "us_tech": -15.0,
            "us_equity": -10.0,
            "us_small_value": -12.0,
            "developed_ex_us": -8.0,
            "emerging_vietnam": -14.0,
            "infrastructure_theme": -10.0,
            "commodity_equity": -8.0,
            "other_risk": -10.0,
        },
    },
    {
        "key": "risk_off_usd_squeeze",
        "label": "美元擠壓 / 全球 risk-off",
        "description": "全球股市與新興市場下跌；黃金小幅防守，現金穩定。",
        "bucket_shocks": {
            "cash": 0.0,
            "gold": 5.0,
            "crypto": -40.0,
            "taiwan_tech": -22.0,
            "us_tech": -22.0,
            "us_equity": -18.0,
            "us_small_value": -22.0,
            "developed_ex_us": -20.0,
            "emerging_vietnam": -32.0,
            "infrastructure_theme": -18.0,
            "commodity_equity": -20.0,
            "other_risk": -18.0,
        },
    },
    {
        "key": "gold_hedge_failure",
        "label": "黃金避險失效",
        "description": "黃金與風險資產同跌，檢查 GLDM 避險失靈情境。",
        "bucket_shocks": {
            "cash": 0.0,
            "gold": -18.0,
            "crypto": -30.0,
            "taiwan_tech": -14.0,
            "us_tech": -16.0,
            "us_equity": -12.0,
            "us_small_value": -14.0,
            "developed_ex_us": -12.0,
            "emerging_vietnam": -18.0,
            "infrastructure_theme": -12.0,
            "commodity_equity": -14.0,
            "other_risk": -12.0,
        },
    },
    {
        "key": "theme_etf_liquidity_shock",
        "label": "主題 ETF 流動性折價",
        "description": "主題、基建、資料中心、礦業 ETF 同步折價。",
        "bucket_shocks": {
            "cash": 0.0,
            "gold": 2.0,
            "crypto": -25.0,
            "taiwan_tech": -16.0,
            "us_tech": -18.0,
            "us_equity": -12.0,
            "us_small_value": -16.0,
            "developed_ex_us": -10.0,
            "emerging_vietnam": -18.0,
            "infrastructure_theme": -32.0,
            "commodity_equity": -30.0,
            "other_risk": -12.0,
        },
    },
]


def extract_portfolios(data: Dict[str, Any], allowed_prefixes: List[str], source: str) -> List[Dict[str, Any]]:
    out = []
    portfolios = data.get("portfolios", {}) if isinstance(data, dict) else {}
    for key, p in portfolios.items():
        if not any(key == prefix or key.startswith(prefix) for prefix in allowed_prefixes):
            continue
        if not isinstance(p, dict) or p.get("status") != "OK":
            continue
        weights = {}
        for row in p.get("weights", []) or []:
            ticker = row.get("ticker")
            if not ticker:
                continue
            weights[str(ticker)] = safe_float(row.get("weight_pct")) / 100.0
        if not weights:
            continue
        out.append({
            "key": key,
            "label": key,
            "source": source,
            "weights": weights,
            "turnover_vs_current_pct": p.get("turnover_vs_current_pct"),
            "metrics": p.get("metrics", {}),
        })
    return out


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, safe_float(v)) for v in weights.values())
    if total <= 0:
        return {}
    return {k: max(0.0, safe_float(v)) / total for k, v in weights.items()}


def stress_return(weights: Dict[str, float], scenario: Dict[str, Any]) -> Dict[str, Any]:
    w = normalize_weights(weights)
    shocks = scenario["bucket_shocks"]
    contributions = []
    total = 0.0
    for ticker, weight in w.items():
        bucket = ticker_bucket(ticker)
        shock_pct = safe_float(shocks.get(bucket, shocks.get("other_risk", -10.0)))
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
    return {
        "return_pct": round(total, 3),
        "top_contributors": contributions[:5],
    }


def main() -> None:
    out_dir = Path("data/optimizer")
    skfolio = load_json(out_dir / "skfolio_sandbox_latest.json")
    riskfolio = load_json(out_dir / "riskfolio_sandbox_latest.json")

    candidates = []
    candidates.extend(extract_portfolios(skfolio, ["current_weight", "inverse_vol_baseline", "scipy_min_variance_fallback", "skfolio_"], "skfolio/baseline"))
    candidates.extend(extract_portfolios(riskfolio, ["riskfolio_"], "Riskfolio-Lib"))

    # Deduplicate by key/source.
    seen = set()
    clean = []
    for c in candidates:
        ident = (c["source"], c["key"])
        if ident in seen:
            continue
        seen.add(ident)
        clean.append(c)

    rows = []
    for c in clean:
        scenario_returns = {}
        returns = []
        for s in SCENARIOS:
            sr = stress_return(c["weights"], s)
            scenario_returns[s["key"]] = sr
            returns.append(sr["return_pct"])
        rows.append({
            "key": c["key"],
            "label": c["label"],
            "source": c["source"],
            "status": "OK",
            "turnover_vs_current_pct": c.get("turnover_vs_current_pct"),
            "worst_scenario_return_pct": round(min(returns), 3) if returns else None,
            "avg_scenario_return_pct": round(sum(returns) / len(returns), 3) if returns else None,
            "best_scenario_return_pct": round(max(returns), 3) if returns else None,
            "scenario_returns": scenario_returns,
        })

    rows.sort(key=lambda x: safe_float(x.get("worst_scenario_return_pct"), 999.0))

    result = {
        "version": "v1.7",
        "status": "OK" if rows else "NO_CANDIDATES",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "scenario_stress_sandbox",
        "safe_mode": True,
        "safe_mode_note": "Deterministic scenario shocks only. No Supabase write, no holdings change, no BUY/SELL.",
        "scenarios": [{k: v for k, v in s.items() if k != "bucket_shocks"} for s in SCENARIOS],
        "comparison_rows": rows,
        "warnings": [
            "Scenario shocks are deterministic approximations, not forecasts.",
            "FX, taxes, liquidity and execution are not fully modeled.",
            "This is a sandbox stress diagnostic, not a rebalance instruction.",
        ],
    }

    latest = out_dir / "optimizer_stress_latest.json"
    latest.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Optimizer Stress Test v1.7",
        "",
        f"- Status: `{result['status']}`",
        f"- Candidate count: `{len(rows)}`",
        "",
        "| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['label']} | {row['source']} | {row.get('worst_scenario_return_pct')}% | "
            f"{row.get('avg_scenario_return_pct')}% | {row.get('turnover_vs_current_pct', 'N/A')}% |"
        )
    (out_dir / "optimizer_stress_summary.md").write_text("\n".join(lines), encoding="utf-8")

    github_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if github_summary:
        Path(github_summary).write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "version": result["version"],
        "status": result["status"],
        "candidate_count": len(rows),
        "scenario_count": len(SCENARIOS),
        "output": str(latest),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
