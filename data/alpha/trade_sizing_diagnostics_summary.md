# v9.3 Gate Failure & Trade Sizing Diagnostics

- Generated: `2026-06-08T14:23:17+00:00`
- Diagnostic status: **blocked**
- Blockers: `11`
- Watch items: `3`
- Formal pass status: `blocked`
- Alpha validation: `watch_only_validation`
- Further research candidates: `0`
- Cash balance available: `False` / `None` (missing_cash_balance)
- All prices real-world: `False`
- Formal draft count: `0`
- Manual ticket count: `0`

## Top issues
- **blocker** `alpha_validation_gate_not_passed` — alpha_validation：實際值：watch_only_validation；要求：pass_or_conditional_pass。alpha_validation_gate_not_passed
- **blocker** `no_rebalance_candidate_cleared_research_threshold` — rebalance_ranking：實際值：0；要求：>=1 further research candidate。no_rebalance_candidate_cleared_research_threshold
- **blocker** `no_manual_research_proposal` — manual_research_proposal：實際值：0；要求：>=1 manual research proposal。no_manual_research_proposal
- **blocker** `no_pre_execution_draft` — pre_execution_draft：實際值：0；要求：>=1 execution-ready draft shell。no_pre_execution_draft
- **blocker** `alpha_validation_not_passed` — Alpha 驗證仍未通過：目前 Alpha validation status = watch_only_validation。
- **blocker** `no_further_research_candidates` — 沒有進一步研究候選：v5.2 調倉研究候選排序沒有任何草案進入進一步研究。
- **watch** `governance_not_clean_pass` — 模型治理仍有觀察警示：Governance verdict = watch_only_with_governance_warnings；score = 92.0。
- **blocker** `manual_override_disabled` — 人工 override 未啟用：config/manual_approval_override.json 目前未允許升級正式草案。
- **blocker** `missing_cash_balance` — 現金餘額缺失：cash_balance_twd = None；source = missing_cash_balance。
- **blocker** `incomplete_real_world_price_fetch` — 部分資產價格不是即時真實抓取：未成功 real-world fetch 的標的：00981A, 2330, AVUV, BOXX, BTC-USD, ETH-USD, GRID, IFRA, PICK, QQQ, SRVR, USMV。
- **watch** `minimum_trade_unit_not_met` — 部分部位低於最小交易單位：共有 2 檔不符合最小單位檢查。
- **blocker** `no_formal_rebalance_draft` — 沒有正式再平衡草案：Formal draft gate status = blocked_by_formal_pass_conditions；formal draft count = 0。

## Next actions
- 在 config/manual_approval_override.json 補 cash_balance_twd 與 max_trade_budget_twd；manual_override_enabled 可維持 false。
- 若只想產生正式審閱草案，考慮開啟 review-only manual override；不得開啟交易或送單。
- 檢查 v5.2 排名為何沒有進一步研究候選；避免放寬門檻到產生假訊號。
- 檢查 v6 Alpha Validation Gate 的 watch 條件；在通過前不要生成正式交易票據。

## Boundary
- 這是阻擋原因與 sizing 診斷，不是買賣建議、看多／看空訊號或交易指令。
