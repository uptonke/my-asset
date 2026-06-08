#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "trade_sizing_diagnostics_latest.json"
SUMMARY_MD = OUT_DIR / "trade_sizing_diagnostics_summary.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(rel: str, default: Any = None) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def num(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def add_issue(issues: List[Dict[str, Any]], layer: str, severity: str, code: str, title: str, detail: str, remediation: str) -> None:
    issues.append({
        "layer": layer,
        "severity": severity,
        "code": code,
        "title": title,
        "detail": detail,
        "remediation": remediation,
    })


def zh_gate_reason(code: Any) -> str:
    text = str(code or "")
    mapping = {
        "alpha_validation_not_passed": "Alpha 驗證閘門尚未通過",
        "no_further_research_candidates": "v5.2 沒有進一步研究候選",
        "manual_research_proposal_missing": "沒有人工研究提案可升級",
        "execution_ready_draft_missing": "v8.0 沒有預執行草案",
        "walk_forward_not_ok": "滾動樣本外驗證不足",
        "governance_watch_or_fail": "模型治理仍為觀察或警示狀態",
        "manual_override_disabled": "人工 override 未啟用",
        "missing_cash_balance": "現金餘額缺失",
        "incomplete_real_world_price_fetch": "部分價格不是即時真實抓取",
        "formal_rebalance_draft_gate_not_available": "正式再平衡草案閘門未通過",
        "no_formal_rebalance_draft_rows": "沒有正式草案列",
        "missing_explicit_trade_lines_or_target_weights": "缺少明確交易列或目標權重",
    }
    return mapping.get(text, text or "未提供原因")


def main() -> None:
    formal_conditions = as_dict(read_json("data/alpha/formal_draft_pass_conditions_latest.json", {}))
    manual_input = as_dict(read_json("data/alpha/manual_approval_input_latest.json", {}))
    sizing = as_dict(read_json("data/alpha/trading_constraints_snapshot_latest.json", {}))
    formal_gate = as_dict(read_json("data/alpha/formal_rebalance_draft_gate_latest.json", {}))
    manual_ticket = as_dict(read_json("data/alpha/manual_trade_ticket_latest.json", {}))
    paper_tracker = as_dict(read_json("data/alpha/paper_trade_tracker_latest.json", {}))
    alpha_validation = as_dict(read_json("data/alpha/alpha_validation_gate_latest.json", {}))
    ranking = as_dict(read_json("data/alpha/rebalance_candidate_ranking_latest.json", {}))
    governance = as_dict(read_json("data/optimizer/model_governance_dashboard_latest.json", {}))
    walk_forward = as_dict(read_json("data/optimizer/walk_forward_backtest_latest.json", {}))

    issues: List[Dict[str, Any]] = []

    pass_summary = as_dict(formal_conditions.get("summary"))
    pass_status = str(formal_conditions.get("pass_status") or pass_summary.get("pass_status") or "missing")
    hard_fails = int(num(pass_summary.get("hard_fail_count"), len(as_list(formal_conditions.get("block_reasons")))))
    watch_fails = int(num(pass_summary.get("watch_fail_count"), len(as_list(formal_conditions.get("watch_reasons")))))
    gates = as_list(formal_conditions.get("gates"))
    for g in gates:
        gd = as_dict(g)
        if gd.get("passed") is False:
            sev = str(gd.get("severity") or "watch")
            add_issue(
                issues,
                "formal_pass_conditions",
                "blocker" if sev == "hard" else "watch",
                str(gd.get("reason_code") or gd.get("name") or "gate_failed"),
                str(gd.get("name") or "正式草案條件未通過"),
                f"實際值：{gd.get('actual')}；要求：{gd.get('required')}。{zh_gate_reason(gd.get('reason_code'))}",
                "若要產生正式草案，需先改善此 gate；不得用前端文字繞過。",
            )

    alpha_summary = as_dict(alpha_validation.get("summary"))
    alpha_status = str(alpha_summary.get("validation_status") or alpha_validation.get("validation_status") or "missing")
    if alpha_status not in {"pass", "conditional_pass", "conditional_pass_with_watch_items"}:
        add_issue(
            issues,
            "alpha_validation_gate",
            "blocker",
            "alpha_validation_not_passed",
            "Alpha 驗證仍未通過",
            f"目前 Alpha validation status = {alpha_status}。",
            "維持研究模式；待 walk-forward / governance / ranking 條件改善後再允許正式草案。",
        )

    ranking_summary = as_dict(ranking.get("summary"))
    further_research = int(num(ranking_summary.get("further_research_count") or ranking_summary.get("further_research"), 0))
    if further_research <= 0:
        add_issue(
            issues,
            "rebalance_ranking",
            "blocker",
            "no_further_research_candidates",
            "沒有進一步研究候選",
            "v5.2 調倉研究候選排序沒有任何草案進入進一步研究。",
            "不要產生交易票據；先改善 alpha / risk / constraint 條件。",
        )

    gov_summary = as_dict(governance.get("summary"))
    gov_verdict = str(gov_summary.get("verdict") or governance.get("verdict") or "missing")
    gov_score = num(gov_summary.get("governance_score") or governance.get("governance_score"), 0)
    if "watch" in gov_verdict.lower() or "fail" in gov_verdict.lower():
        add_issue(
            issues,
            "model_governance",
            "watch",
            "governance_not_clean_pass",
            "模型治理仍有觀察警示",
            f"Governance verdict = {gov_verdict}；score = {gov_score}。",
            "正式草案仍可被擋；先檢查樣本品質、過度最佳化與安全旗標。",
        )

    wf_summary = as_dict(walk_forward.get("summary"))
    wf_status = str(wf_summary.get("status") or walk_forward.get("status") or "missing")
    wf_folds = int(num(wf_summary.get("fold_count") or walk_forward.get("fold_count"), 0))
    if wf_status.upper() != "OK" or wf_folds < 6:
        add_issue(
            issues,
            "walk_forward",
            "watch",
            "walk_forward_evidence_limited",
            "樣本外驗證證據有限",
            f"Walk-forward status = {wf_status}；fold count = {wf_folds}。",
            "延長樣本或降低對 alpha 排序的信任度。",
        )

    manual_summary = as_dict(manual_input.get("summary"))
    override = as_dict(manual_input.get("manual_override")) or as_dict(manual_input.get("override"))
    override_enabled = bool(manual_input.get("manual_override_enabled") or manual_summary.get("manual_override_enabled") or override.get("manual_override_enabled"))
    if not override_enabled:
        add_issue(
            issues,
            "manual_approval_input",
            "blocker",
            "manual_override_disabled",
            "人工 override 未啟用",
            "config/manual_approval_override.json 目前未允許升級正式草案。",
            "若只想產生人工審閱草案，可手動開啟 review-only override；仍不得啟用交易或送單。",
        )

    sizing_summary = as_dict(sizing.get("summary"))
    cash = as_dict(sizing.get("cash_balance"))
    cash_available = bool(sizing_summary.get("cash_balance_available"))
    cash_balance_twd = cash.get("cash_balance_twd", sizing_summary.get("cash_balance_twd"))
    cash_source = str(cash.get("source") or "missing")
    if not cash_available:
        add_issue(
            issues,
            "trading_sizing",
            "blocker",
            "missing_cash_balance",
            "現金餘額缺失",
            f"cash_balance_twd = {cash_balance_twd}；source = {cash_source}。",
            "在 config/manual_approval_override.json 補 cash_balance_twd 與 max_trade_budget_twd；不等於允許交易。",
        )

    all_prices_real = bool(sizing_summary.get("all_prices_real_world"))
    asset_rows = [as_dict(r) for r in as_list(sizing.get("asset_rows"))]
    failed_price_rows = [r for r in asset_rows if not r.get("real_world_price_fetched")]
    if not all_prices_real:
        tickers = [str(r.get("ticker") or "?") for r in failed_price_rows[:12]]
        add_issue(
            issues,
            "trading_sizing",
            "blocker",
            "incomplete_real_world_price_fetch",
            "部分資產價格不是即時真實抓取",
            f"未成功 real-world fetch 的標的：{', '.join(tickers) if tickers else '未列出'}。",
            "重新跑 workflow 或檢查 ticker map；使用 stored fallback 時不應產生正式交易票據。",
        )

    unit_block_rows = []
    for r in asset_rows:
        if r.get("is_position_tradable_under_unit_rule") is False:
            unit_block_rows.append({
                "ticker": r.get("ticker"),
                "asset_kind": r.get("asset_kind"),
                "shares": r.get("shares"),
                "minimum_trade_unit": r.get("minimum_trade_unit"),
                "rule_note": r.get("trade_rule_note"),
            })
    if unit_block_rows:
        add_issue(
            issues,
            "trading_sizing",
            "watch",
            "minimum_trade_unit_not_met",
            "部分部位低於最小交易單位",
            f"共有 {len(unit_block_rows)} 檔不符合最小單位檢查。",
            "美股至少 1 股、台股零股 1 股、加密至少 1 顆；小於單位時不應產生票據。",
        )

    formal_summary = as_dict(formal_gate.get("summary"))
    formal_gate_status = str(formal_summary.get("formal_draft_gate_status") or formal_gate.get("formal_draft_gate_status") or "missing")
    formal_count = int(num(formal_summary.get("formal_draft_count"), len(as_list(formal_gate.get("formal_draft_rows")))))
    if formal_count <= 0:
        add_issue(
            issues,
            "formal_rebalance_draft_gate",
            "blocker",
            "no_formal_rebalance_draft",
            "沒有正式再平衡草案",
            f"Formal draft gate status = {formal_gate_status}；formal draft count = {formal_count}。",
            "需先通過正式草案條件與人工 review-only 設定，才可能產生草案。",
        )

    ticket_summary = as_dict(manual_ticket.get("summary"))
    ticket_status = str(ticket_summary.get("ticket_status") or manual_ticket.get("ticket_status") or "missing")
    ticket_count = int(num(ticket_summary.get("manual_ticket_count"), len(as_list(manual_ticket.get("manual_trade_tickets")) or as_list(manual_ticket.get("ticket_rows")))))
    if ticket_count <= 0:
        add_issue(
            issues,
            "manual_trade_ticket",
            "blocker",
            "no_manual_trade_ticket",
            "沒有人工交易票據草案",
            f"Ticket status = {ticket_status}；manual ticket count = {ticket_count}。",
            "若前置 gate 未通過，v9 必須輸出 0 張票據；不得捏造買賣明細。",
        )

    paper_summary = as_dict(paper_tracker.get("summary"))
    paper_count = int(num(paper_summary.get("paper_trade_count"), len(as_list(paper_tracker.get("paper_trades")) or as_list(paper_tracker.get("tracked_items")))))
    if paper_count <= 0:
        add_issue(
            issues,
            "paper_trade_tracker",
            "watch",
            "no_paper_trade_tracking_items",
            "沒有紙上追蹤項目",
            "因為沒有正式草案或票據，所以沒有建立 1W / 1M / 3M 追蹤。",
            "等 v8.1 / v9 產生 review-only 草案後再建立追蹤；不要用紙上追蹤當即時交易訊號。",
        )

    blocker_count = sum(1 for i in issues if i.get("severity") == "blocker")
    watch_count = sum(1 for i in issues if i.get("severity") == "watch")
    if blocker_count > 0:
        diagnostic_status = "blocked"
    elif watch_count > 0:
        diagnostic_status = "watch_items_only"
    else:
        diagnostic_status = "clear_for_review_only_draft_check"

    top_reasons = [i["code"] for i in issues if i.get("severity") == "blocker"][:8]
    next_actions = []
    if any(i["code"] == "missing_cash_balance" for i in issues):
        next_actions.append("在 config/manual_approval_override.json 補 cash_balance_twd 與 max_trade_budget_twd；manual_override_enabled 可維持 false。")
    if any(i["code"] == "manual_override_disabled" for i in issues):
        next_actions.append("若只想產生正式審閱草案，考慮開啟 review-only manual override；不得開啟交易或送單。")
    if any(i["code"] == "no_further_research_candidates" for i in issues):
        next_actions.append("檢查 v5.2 排名為何沒有進一步研究候選；避免放寬門檻到產生假訊號。")
    if any(i["code"] == "alpha_validation_not_passed" for i in issues):
        next_actions.append("檢查 v6 Alpha Validation Gate 的 watch 條件；在通過前不要生成正式交易票據。")
    if not next_actions:
        next_actions.append("目前沒有 blocker；仍只能產生人工審閱草案，不是交易指令。")

    output = {
        "version": "v9.3",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "gate_failure_and_trade_sizing_diagnostics",
        "safe_mode": True,
        "research_only": True,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "auto_trade_enabled": False,
        "supabase_write_enabled": False,
        "not_trade_order": True,
        "not_buy_signal": True,
        "not_sell_signal": True,
        "diagnostic_status": diagnostic_status,
        "summary": {
            "diagnostic_status": diagnostic_status,
            "blocker_count": blocker_count,
            "watch_count": watch_count,
            "formal_pass_status": pass_status,
            "formal_hard_fail_count": hard_fails,
            "formal_watch_fail_count": watch_fails,
            "alpha_validation_status": alpha_status,
            "further_research_count": further_research,
            "governance_score": gov_score,
            "governance_verdict": gov_verdict,
            "walk_forward_status": wf_status,
            "walk_forward_fold_count": wf_folds,
            "manual_override_enabled": override_enabled,
            "cash_balance_available": cash_available,
            "cash_balance_twd": cash_balance_twd,
            "cash_balance_source": cash_source,
            "all_prices_real_world": all_prices_real,
            "real_world_price_success_count": int(num(sizing_summary.get("real_world_price_success_count"), 0)),
            "asset_count": int(num(sizing_summary.get("asset_count"), len(asset_rows))),
            "formal_draft_gate_status": formal_gate_status,
            "formal_draft_count": formal_count,
            "manual_ticket_status": ticket_status,
            "manual_ticket_count": ticket_count,
            "paper_trade_count": paper_count,
            "top_block_reasons": top_reasons,
        },
        "source_files": {
            "formal_draft_pass_conditions": "data/alpha/formal_draft_pass_conditions_latest.json",
            "manual_approval_input": "data/alpha/manual_approval_input_latest.json",
            "trading_constraints_snapshot": "data/alpha/trading_constraints_snapshot_latest.json",
            "formal_rebalance_draft_gate": "data/alpha/formal_rebalance_draft_gate_latest.json",
            "manual_trade_ticket": "data/alpha/manual_trade_ticket_latest.json",
            "paper_trade_tracker": "data/alpha/paper_trade_tracker_latest.json",
        },
        "issues": issues,
        "trade_sizing_snapshot": {
            "cash_balance": {"available": cash_available, "cash_balance_twd": cash_balance_twd, "source": cash_source},
            "asset_count": len(asset_rows),
            "failed_price_rows": failed_price_rows,
            "unit_rule_watch_rows": unit_block_rows,
            "constraints_policy": sizing.get("constraints") or {},
        },
        "next_actions": next_actions,
        "safety_boundary": [
            "v9.3 only diagnoses why formal drafts or manual tickets are blocked.",
            "It does not approve trades, does not enable execution, and does not submit broker orders.",
            "A clear diagnostic status is not a buy/sell signal and not a bullish/bearish market view.",
        ],
    }

    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# v9.3 Gate Failure & Trade Sizing Diagnostics",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Diagnostic status: **{diagnostic_status}**",
        f"- Blockers: `{blocker_count}`",
        f"- Watch items: `{watch_count}`",
        f"- Formal pass status: `{pass_status}`",
        f"- Alpha validation: `{alpha_status}`",
        f"- Further research candidates: `{further_research}`",
        f"- Cash balance available: `{cash_available}` / `{cash_balance_twd}` ({cash_source})",
        f"- All prices real-world: `{all_prices_real}`",
        f"- Formal draft count: `{formal_count}`",
        f"- Manual ticket count: `{ticket_count}`",
        "",
        "## Top issues",
    ]
    if issues:
        for i in issues[:12]:
            lines.append(f"- **{i['severity']}** `{i['code']}` — {i['title']}：{i['detail']}")
    else:
        lines.append("- None")
    lines += ["", "## Next actions"]
    for action in next_actions:
        lines.append(f"- {action}")
    lines += ["", "## Boundary", "- 這是阻擋原因與 sizing 診斷，不是買賣建議、看多／看空訊號或交易指令。"]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Diagnostic status: {diagnostic_status}")
    print(f"Blockers: {blocker_count}")
    print(f"Watch items: {watch_count}")


if __name__ == "__main__":
    main()
