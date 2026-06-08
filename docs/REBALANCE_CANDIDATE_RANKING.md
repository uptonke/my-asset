# v5.2 Rebalance Candidate Ranking Engine

v5.2 只做「調倉研究候選排序」，不是買入建議、不是賣出建議、不是最佳配置，也不是交易指令。

## Inputs

- `data/optimizer/constraint_aware_rebalance_latest.json`
- `data/optimizer/regime_aware_optimizer_latest.json`
- `data/optimizer/walk_forward_backtest_latest.json`
- `data/optimizer/model_governance_dashboard_latest.json`
- `data/alpha/alpha_research_sandbox_latest.json`

## Output

- `data/alpha/rebalance_candidate_ranking_latest.json`
- `data/alpha/rebalance_candidate_ranking_summary.md`

## Ranking logic

The ranking combines bounded research-only components:

- risk reduction evidence
- alpha research alignment
- constraint status
- turnover friction
- regime overlay
- sample/governance quality
- cash-disguise penalty

## Safety boundary

- `research_only = true`
- `trade_signal_enabled = false`
- `execution_permission = false`
- `not_trade_order = true`
- `official_alpha_enabled = false`
- `maximum_sharpe_optimization_enabled = false`
- `official_rebalance_enabled = false`

`further_research` means only that a candidate deserves more research. It does not mean buy, sell, bullish, approved, optimal, or execution-ready.
