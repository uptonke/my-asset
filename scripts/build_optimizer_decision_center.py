#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


OUT_DIR = Path("data/optimizer")
JSON_OUT = OUT_DIR / "decision_center_latest.json"
MD_OUT = OUT_DIR / "decision_center_summary.md"

SOURCE_FILES = {
    "skfolio": OUT_DIR / "skfolio_sandbox_latest.json",
    "riskfolio": OUT_DIR / "riskfolio_sandbox_latest.json",
    "robustness": OUT_DIR / "optimizer_robustness_latest.json",
    "stress": OUT_DIR / "optimizer_stress_latest.json",
    "riskfolio_dependency": OUT_DIR / "riskfolio_dependency_status.json",
}

RISK_BUCKETS = {
    "cash": {"BOXX", "CASH", "USD", "TWD"},
    "gold": {"GLDM", "GLD", "IAU"},
    "crypto": {"BTC-USD", "ETH-USD", "BTC", "ETH"},
    "taiwan": {"00981A", "2330"},
}


CONSTRAINTS = {
    "max_single_weight_pct": 25.0,
    "watch_cash_weight_pct": 35.0,
    "reject_cash_weight_pct": 60.0,
    "max_crypto_weight_pct": 15.0,
    "max_taiwan_weight_pct": 30.0,
    "min_cash_weight_pct": 0.0,
    "watch_turnover_pct": 35.0,
    "reject_turnover_pct": 70.0,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        v = float(value)
        if math.isfinite(v):
            return v
        return default
    except Exception:
        return default


def round_or_none(value: Any, ndigits: int = 3) -> Optional[float]:
    v = safe_float(value)
    return round(v, ndigits) if v is not None else None


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "READ_ERROR", "error": str(exc)[:500]}


def pct_from_weights(weights: Iterable[Dict[str, Any]], tickers: Iterable[str]) -> float:
    tickerset = {str(t).upper() for t in tickers}
    total = 0.0
    for row in weights or []:
        t = str(row.get("ticker", "")).upper()
        if t in tickerset:
            total += safe_float(row.get("weight_pct"), 0.0) or 0.0
    return round(total, 3)


def classify_ticker(ticker: str) -> str:
    t = str(ticker or "").upper()
    if t in RISK_BUCKETS["cash"] or "CASH" in t:
        return "cash"
    if t in RISK_BUCKETS["gold"] or "GOLD" in t:
        return "gold"
    if t in RISK_BUCKETS["crypto"] or "BTC" in t or "ETH" in t:
        return "crypto"
    if t in RISK_BUCKETS["taiwan"] or t.startswith("00") or t.isdigit():
        return "taiwan"
    return "other"


def group_weights(weights: List[Dict[str, Any]]) -> Dict[str, float]:
    groups = {"cash_pct": 0.0, "gold_pct": 0.0, "crypto_pct": 0.0, "taiwan_pct": 0.0, "other_pct": 0.0}
    for row in weights or []:
        bucket = classify_ticker(str(row.get("ticker", "")))
        value = safe_float(row.get("weight_pct"), 0.0) or 0.0
        key = f"{bucket}_pct" if bucket in {"cash", "gold", "crypto", "taiwan"} else "other_pct"
        groups[key] += value
    return {k: round(v, 3) for k, v in groups.items()}


def extract_portfolios(data: Dict[str, Any], source: str, allowed: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    portfolios = data.get("portfolios", {}) if isinstance(data, dict) else {}
    rows: List[Dict[str, Any]] = []
    if not isinstance(portfolios, dict):
        return rows

    for key, p in portfolios.items():
        if allowed and key not in allowed and not any(key.startswith(prefix) for prefix in allowed if prefix.endswith("_")):
            continue
        if not isinstance(p, dict):
            continue
        metrics = p.get("metrics", {}) if isinstance(p.get("metrics"), dict) else {}
        weights = p.get("weights", []) if isinstance(p.get("weights"), list) else []
        risk_weights = [
            r for r in weights
            if classify_ticker(str(r.get("ticker", ""))) != "cash"
        ]
        max_single = max([safe_float(r.get("weight_pct"), 0.0) or 0.0 for r in risk_weights] or [0.0])
        max_single_ticker = "-"
        if risk_weights:
            max_row = max(risk_weights, key=lambda r: safe_float(r.get("weight_pct"), 0.0) or 0.0)
            max_single_ticker = str(max_row.get("ticker", "-"))
        grouped = group_weights(weights)

        rows.append({
            "id": str(key),
            "name": str(key).replace("_", " "),
            "source": source,
            "type": "baseline" if key in {"current_weight", "inverse_vol_baseline"} else "optimizer",
            "raw_status": p.get("status", "UNKNOWN"),
            "metrics": {
                "annual_return_pct": round_or_none(metrics.get("annual_return_pct")),
                "annual_vol_pct": round_or_none(metrics.get("annual_vol_pct")),
                "sharpe": round_or_none(metrics.get("sharpe")),
                "var95_pct": round_or_none(metrics.get("var95_pct")),
                "es95_pct": round_or_none(metrics.get("es95_pct")),
                "max_drawdown_pct": round_or_none(metrics.get("max_drawdown_pct")),
                "worst_day_pct": round_or_none(metrics.get("worst_day_pct")),
                "best_day_pct": round_or_none(metrics.get("best_day_pct")),
                "turnover_vs_current_pct": round_or_none(p.get("turnover_vs_current_pct")),
            },
            "exposure": {
                **grouped,
                "max_single_weight_pct": round(max_single, 3),
                "max_single_ticker": max_single_ticker,
            },
            "top_weights": [
                {
                    "ticker": str(r.get("ticker", "")),
                    "weight_pct": round_or_none(r.get("weight_pct")),
                    "delta_vs_current_pct": round_or_none(r.get("delta_vs_current_pct")),
                }
                for r in sorted(weights, key=lambda r: safe_float(r.get("weight_pct"), 0.0) or 0.0, reverse=True)[:8]
            ],
        })
    return rows


def merge_candidates(skfolio: Dict[str, Any], riskfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    rows.extend(extract_portfolios(
        skfolio,
        "skfolio/baseline",
        ["current_weight", "inverse_vol_baseline", "scipy_min_variance_fallback", "skfolio_"],
    ))
    rows.extend(extract_portfolios(
        riskfolio,
        "Riskfolio-Lib",
        ["riskfolio_"],
    ))

    seen: set[Tuple[str, str]] = set()
    clean: List[Dict[str, Any]] = []
    for row in rows:
        key = (row.get("source", ""), row.get("id", ""))
        if key in seen:
            continue
        seen.add(key)
        clean.append(row)
    return clean


def attach_robustness(candidates: List[Dict[str, Any]], robustness: Dict[str, Any]) -> None:
    stability = robustness.get("method_stability", {}) if isinstance(robustness, dict) else {}
    for c in candidates:
        s = stability.get(c["id"], {}) if isinstance(stability, dict) else {}
        c["robustness"] = {
            "status": s.get("status", "MISSING") if isinstance(s, dict) else "MISSING",
            "verdict": s.get("verdict", "缺資料") if isinstance(s, dict) else "缺資料",
            "available_windows": s.get("available_windows") if isinstance(s, dict) else None,
            "avg_pairwise_weight_turnover_pct": round_or_none(s.get("avg_pairwise_weight_turnover_pct") if isinstance(s, dict) else None),
            "max_asset_weight_range_pct": round_or_none(s.get("max_asset_weight_range_pct") if isinstance(s, dict) else None),
            "es95_range_pct": round_or_none(s.get("es95_range_pct") if isinstance(s, dict) else None),
            "annual_vol_range_pct": round_or_none(s.get("annual_vol_range_pct") if isinstance(s, dict) else None),
        }


def attach_stress(candidates: List[Dict[str, Any]], stress: Dict[str, Any]) -> None:
    rows = stress.get("comparison_rows", []) if isinstance(stress, dict) else []
    by_key: Dict[str, Dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict):
            by_key[str(row.get("key", ""))] = row
    for c in candidates:
        s = by_key.get(c["id"], {})
        c["stress"] = {
            "status": s.get("status", "MISSING") if s else "MISSING",
            "worst_scenario_return_pct": round_or_none(s.get("worst_scenario_return_pct") if s else None),
            "avg_scenario_return_pct": round_or_none(s.get("avg_scenario_return_pct") if s else None),
            "best_scenario_return_pct": round_or_none(s.get("best_scenario_return_pct") if s else None),
            "scenario_returns": s.get("scenario_returns", {}) if s else {},
        }


def constraint_flags(candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []
    metrics = candidate.get("metrics", {})
    exposure = candidate.get("exposure", {})
    turnover = safe_float(metrics.get("turnover_vs_current_pct"), 0.0) or 0.0

    def add(level: str, code: str, message: str) -> None:
        flags.append({"level": level, "code": code, "message": message})

    if turnover >= CONSTRAINTS["reject_turnover_pct"]:
        add("violation", "turnover_extreme", f"換手率 {turnover:.2f}% 過高，暫不適合作為候選調整。")
    elif turnover >= CONSTRAINTS["watch_turnover_pct"]:
        add("warning", "turnover_high", f"換手率 {turnover:.2f}% 偏高，需要摩擦成本與人工審查。")

    max_single = safe_float(exposure.get("max_single_weight_pct"), 0.0) or 0.0
    if max_single > CONSTRAINTS["max_single_weight_pct"]:
        add("violation", "single_position_cap", f"單一標的 {exposure.get('max_single_ticker', '-')} 權重 {max_single:.2f}% 超過上限。")

    crypto = safe_float(exposure.get("crypto_pct"), 0.0) or 0.0
    if crypto > CONSTRAINTS["max_crypto_weight_pct"]:
        add("violation", "crypto_cap", f"加密資產權重 {crypto:.2f}% 超過風險上限。")

    taiwan = safe_float(exposure.get("taiwan_pct"), 0.0) or 0.0
    if taiwan > CONSTRAINTS["max_taiwan_weight_pct"]:
        add("warning", "taiwan_concentration", f"台股 / 台灣科技權重 {taiwan:.2f}% 偏集中。")

    cash = safe_float(exposure.get("cash_pct"), 0.0) or 0.0
    if cash < CONSTRAINTS["min_cash_weight_pct"]:
        add("violation", "cash_negative", f"現金權重 {cash:.2f}% 小於下限。")
    elif cash >= CONSTRAINTS["reject_cash_weight_pct"]:
        add("violation", "cash_too_high", f"現金 / BOXX 權重 {cash:.2f}% 過高，像是降風險而非可執行配置。")
    elif cash >= CONSTRAINTS["watch_cash_weight_pct"]:
        add("warning", "cash_high", f"現金 / BOXX 權重 {cash:.2f}% 偏高，需要確認是否符合現金下限與機會成本。")

    return flags


def score_candidate(candidate: Dict[str, Any], current: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if candidate.get("id") == "current_weight":
        return {"status": "baseline", "score": 0.0, "reason": "目前投組，只作為比較基準。"}
    if candidate.get("raw_status") != "OK":
        return {"status": "missing_or_optional", "score": None, "reason": "模型輸出不存在或狀態非 OK。"}

    metrics = candidate.get("metrics", {})
    stress = candidate.get("stress", {})
    robust = candidate.get("robustness", {})
    flags = candidate.get("constraint_flags", [])

    violations = [f for f in flags if f.get("level") == "violation"]
    warnings = [f for f in flags if f.get("level") == "warning"]
    turnover = safe_float(metrics.get("turnover_vs_current_pct"), 0.0) or 0.0
    es = safe_float(metrics.get("es95_pct"))
    vol = safe_float(metrics.get("annual_vol_pct"))
    worst_stress = safe_float(stress.get("worst_scenario_return_pct"))
    robustness_verdict = str(robust.get("verdict", "缺資料"))

    current_metrics = current.get("metrics", {}) if current else {}
    current_stress = current.get("stress", {}) if current else {}
    current_es = safe_float(current_metrics.get("es95_pct"))
    current_vol = safe_float(current_metrics.get("annual_vol_pct"))
    current_worst = safe_float(current_stress.get("worst_scenario_return_pct"))

    score = 0.0
    reasons: List[str] = []

    if current_es is not None and es is not None:
        improvement = current_es - es
        if improvement > 0:
            score += min(improvement * 30.0, 35.0)
            reasons.append(f"ES95 較目前改善 {improvement:.3f} 個百分點。")
    if current_vol is not None and vol is not None:
        improvement = current_vol - vol
        if improvement > 0:
            score += min(improvement * 2.5, 20.0)
            reasons.append(f"年化波動較目前降低 {improvement:.2f} 個百分點。")
    if current_worst is not None and worst_stress is not None:
        improvement = worst_stress - current_worst
        if improvement > 0:
            score += min(improvement * 1.2, 25.0)
            reasons.append(f"最差壓力情境較目前改善 {improvement:.2f} 個百分點。")

    if robustness_verdict == "穩定":
        score += 12.0
        reasons.append("跨樣本穩健性標記為穩定。")
    elif robustness_verdict == "可觀察":
        score += 4.0
        reasons.append("跨樣本穩健性僅為可觀察。")
    else:
        score -= 12.0
        reasons.append("穩健性資料不足或不穩定。")

    score -= min(turnover / 2.0, 35.0)
    if turnover > 0:
        reasons.append(f"需要 {turnover:.2f}% 換手率。")

    score -= 25.0 * len(violations)
    score -= 7.5 * len(warnings)

    if violations:
        return {"status": "reject", "score": round(score, 2), "reason": "；".join(reasons[:5]) or "違反硬性限制。"}
    if turnover >= CONSTRAINTS["reject_turnover_pct"]:
        return {"status": "reject", "score": round(score, 2), "reason": "換手率過高。"}
    if score >= 20.0 and turnover <= CONSTRAINTS["watch_turnover_pct"] and robustness_verdict in {"穩定", "可觀察"}:
        return {"status": "candidate", "score": round(score, 2), "reason": "；".join(reasons[:5])}
    return {"status": "watch", "score": round(score, 2), "reason": "；".join(reasons[:5]) or "有參考價值，但尚不足以進入候選調整。"}


def rank_decisions(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    current = next((c for c in candidates if c.get("id") == "current_weight"), None)
    for c in candidates:
        c["constraint_flags"] = constraint_flags(c)
        c["decision"] = score_candidate(c, current)

    def valid_metric(name: str, reverse: bool = False) -> Optional[Dict[str, Any]]:
        rows = [c for c in candidates if c.get("raw_status") == "OK" and c.get("id") != "current_weight"]
        rows = [c for c in rows if safe_float(c.get("metrics", {}).get(name)) is not None]
        if not rows:
            return None
        return sorted(rows, key=lambda c: safe_float(c.get("metrics", {}).get(name), 0.0) or 0.0, reverse=reverse)[0]

    def valid_stress() -> Optional[Dict[str, Any]]:
        rows = [c for c in candidates if c.get("raw_status") == "OK" and c.get("id") != "current_weight"]
        rows = [c for c in rows if safe_float(c.get("stress", {}).get("worst_scenario_return_pct")) is not None]
        if not rows:
            return None
        return sorted(rows, key=lambda c: safe_float(c.get("stress", {}).get("worst_scenario_return_pct"), -999.0) or -999.0, reverse=True)[0]

    ranked = sorted(
        [c for c in candidates if c.get("decision", {}).get("status") in {"candidate", "watch"}],
        key=lambda c: safe_float(c.get("decision", {}).get("score"), -999.0) or -999.0,
        reverse=True,
    )

    candidate_ids = [c["id"] for c in candidates if c.get("decision", {}).get("status") == "candidate"]
    watch_ids = [c["id"] for c in candidates if c.get("decision", {}).get("status") == "watch"]
    rejected_ids = [c["id"] for c in candidates if c.get("decision", {}).get("status") == "reject"]

    best_es = valid_metric("es95_pct")
    lowest_turnover = valid_metric("turnover_vs_current_pct")
    best_stress = valid_stress()

    return {
        "verdict": "候選觀察" if candidate_ids else "僅供觀察",
        "safe_mode_note": "v2.0 只整合與分級模型輸出，不產生交易指令，不改正式持倉，不寫入 Supabase。",
        "candidate_for_v2_1": candidate_ids,
        "watch": watch_ids,
        "rejected": rejected_ids,
        "top_ranked": [c["id"] for c in ranked[:5]],
        "best_es95": best_es["id"] if best_es else None,
        "lowest_turnover": lowest_turnover["id"] if lowest_turnover else None,
        "best_worst_stress": best_stress["id"] if best_stress else None,
        "counts": {
            "total": len(candidates),
            "candidate": len(candidate_ids),
            "watch": len(watch_ids),
            "reject": len(rejected_ids),
            "missing_or_optional": len([c for c in candidates if c.get("decision", {}).get("status") == "missing_or_optional"]),
        },
    }


def build_markdown(report: Dict[str, Any]) -> str:
    rows = report.get("candidates", [])
    lines = [
        "# Portfolio Optimizer Decision Center v2.0",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Verdict: `{report.get('decision_summary', {}).get('verdict')}`",
        f"- Candidate for v2.1: `{', '.join(report.get('decision_summary', {}).get('candidate_for_v2_1', [])) or '-'}`",
        "- Safety: no Supabase write, no holdings change, no execution instruction.",
        "",
        "## Decision table",
        "",
        "| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for c in rows:
        m = c.get("metrics", {})
        s = c.get("stress", {})
        d = c.get("decision", {})
        r = c.get("robustness", {})
        reason = str(d.get("reason", "")).replace("|", "/")[:180]
        lines.append(
            f"| {c.get('id')} | {c.get('source')} | {d.get('status')} | {d.get('score')} | "
            f"{m.get('es95_pct')}% | {m.get('annual_vol_pct')}% | {s.get('worst_scenario_return_pct')}% | "
            f"{m.get('turnover_vs_current_pct')}% | {r.get('verdict')} | {reason} |"
        )

    lines.extend([
        "",
        "## Governance guardrails",
        "",
        "- v2.0 is a decision-support aggregation layer only.",
        "- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.",
        "- `watch` means useful information but not executable enough.",
        "- `reject` means the model failed turnover, concentration, robustness, or constraint checks.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    loaded = {name: load_json(path) for name, path in SOURCE_FILES.items()}
    candidates = merge_candidates(loaded["skfolio"], loaded["riskfolio"])
    attach_robustness(candidates, loaded["robustness"])
    attach_stress(candidates, loaded["stress"])
    decision_summary = rank_decisions(candidates)

    source_status = {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "status": loaded.get(name, {}).get("status") if isinstance(loaded.get(name), dict) else None,
            "version": loaded.get(name, {}).get("version") if isinstance(loaded.get(name), dict) else None,
        }
        for name, path in SOURCE_FILES.items()
    }

    report = {
        "version": "v2.0",
        "status": "OK" if candidates else "NO_CANDIDATES",
        "generated_at": now_utc(),
        "mode": "portfolio_optimizer_decision_center",
        "safe_mode": True,
        "safe_mode_note": "Aggregates sandbox optimizer outputs only. No Supabase write, no holdings change, no execution instruction.",
        "source_status": source_status,
        "constraints": CONSTRAINTS,
        "candidates": candidates,
        "decision_summary": decision_summary,
        "warnings": [] if candidates else ["No optimizer candidates were found. Run skfolio/riskfolio sandbox tasks first."],
    }

    JSON_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(report), encoding="utf-8")

    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    print(f"Candidate count: {len(candidates)}")
    print(f"v2.1 candidates: {', '.join(decision_summary.get('candidate_for_v2_1', [])) or '-'}")


if __name__ == "__main__":
    main()
