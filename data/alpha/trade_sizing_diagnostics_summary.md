# v9.3 Gate Failure & Trade Sizing Diagnostics

- Generated: `2026-06-18T12:01:46+00:00`
- Diagnostic status: **blocked**
- Blockers: `9`
- Watch items: `2`
- Formal pass status: `blocked`
- Alpha validation: `watch_only_validation`
- Further research candidates: `2`
- Cash balance available: `False` / `None` (missing_cash_balance)
- All prices real-world: `False`
- Formal draft count: `0`
- Manual ticket count: `0`

## Top issues
- **blocker** `alpha_validation_gate_not_passed` — alpha_validation：實際值：watch_only_validation；要求：pass_or_conditional_pass。alpha_validation_gate_not_passed
- **blocker** `no_manual_research_proposal` — manual_research_proposal：實際值：0；要求：>=1 manual research proposal。no_manual_research_proposal
- **blocker** `no_pre_execution_draft` — pre_execution_draft：實際值：0；要求：>=1 execution-ready draft shell。no_pre_execution_draft
- **blocker** `alpha_validation_not_passed` — Alpha 驗證仍未通過：目前 Alpha validation status = watch_only_validation。
- **watch** `governance_not_clean_pass` — 模型治理仍有觀察警示：Governance verdict = watch_only_with_governance_warnings；score = 92.0。
- **blocker** `manual_override_disabled` — 人工 override 未啟用：config/manual_approval_override.json 目前未允許升級正式草案。
- **blocker** `missing_cash_balance` — 現金餘額缺失：cash_balance_twd = None；source = missing_cash_balance。
- **blocker** `incomplete_real_world_price_fetch` — 部分資產價格不是即時真實抓取：未成功 real-world fetch 的標的：00981A, AVUV, BOXX, BTC-USD, ETH-USD, GLDM, GRID, IFRA, PICK, QQQ, SRVR, USMV。
- **blocker** `no_formal_rebalance_draft` — 沒有正式再平衡草案：Formal draft gate status = blocked_by_formal_pass_conditions；formal draft count = 0。
- **blocker** `no_manual_trade_ticket` — 沒有人工交易票據草案：Ticket status = blocked_by_formal_rebalance_draft_gate；manual ticket count = 0。
- **watch** `no_paper_trade_tracking_items` — 沒有紙上追蹤項目：因為沒有正式草案或票據，所以沒有建立 1W / 1M / 3M 追蹤。

## Next actions
- 在 config/manual_approval_override.json 補 cash_balance_twd 與 max_trade_budget_twd；manual_override_enabled 可維持 false。
- 若只想產生正式審閱草案，考慮開啟 review-only manual override；不得開啟交易或送單。
- 檢查 v6 Alpha Validation Gate 的 watch 條件；在通過前不要生成正式交易票據。

## Boundary
- 這是阻擋原因與 sizing 診斷，不是買賣建議、看多／看空訊號或交易指令。
