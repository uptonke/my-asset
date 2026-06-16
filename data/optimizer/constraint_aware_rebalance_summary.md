# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-16T15:11:59+00:00`

## Safety Boundary

- This is not a BUY / SELL list.
- execution_permission is always false in v2.3.
- No Supabase write.
- No official portfolio weight update.
- Human approval is mandatory before any real-world action.

## Summary

- Total draft count: `11`
- Rebalance draft count: `3`
- Risk-reduction draft count: `8`
- Constraint pass count: `7`
- High-turnover review count: `4`
- Verdict: 有通過約束的觀察草案，但仍不得執行；下一步才是 Human Approval Layer。

## Drafts

| Draft | Source | Status | Turnover | Cash | Crypto | Taiwan | Gold | Top adjustments |
|---|---|---|---:|---:|---:|---:|---:|---|
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.346% | 13.213% | 11.004% | 8.124% | 3.753% | GLDM UP 1.61pp; BOXX UP 1.491pp; BTC-USD DOWN -1.461pp; 00981A DOWN -1.393pp; USMV UP 1.147pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.338% | 15.476% | 11.054% | 9.517% | 3.862% | BOXX UP 3.754pp; QQQ DOWN -2.394pp; GLDM UP 1.719pp; BTC-USD DOWN -1.425pp; USMV UP 0.983pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.802% | 20.524% | 10.088% | 7.934% | 3.143% | BOXX UP 8.802pp; USMV UP 2.0pp; BTC-USD DOWN -1.994pp; QQQ DOWN -1.828pp; 00981A DOWN -1.583pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.771% | 20.493% | 4.31% | 9.517% | 3.143% | BOXX UP 8.771pp; BTC-USD DOWN -8.771pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 12.094% | 22.816% | 13.081% | 9.517% | 3.143% | BOXX UP 11.094pp; QQQ DOWN -11.094pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.386% | 16.108% | 8.695% | 9.517% | 3.143% | BOXX UP 4.386pp; BTC-USD DOWN -4.386pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.517% | 21.239% | 13.081% | 0.0% | 3.143% | 00981A DOWN -9.517pp; BOXX UP 9.517pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.31% | 16.032% | 8.771% | 9.517% | 3.143% | BOXX UP 4.31pp; ETH-USD DOWN -4.31pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.547% | 17.269% | 13.081% | 9.517% | 3.143% | BOXX UP 5.547pp; QQQ DOWN -5.547pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.193% | 13.915% | 10.888% | 9.517% | 3.143% | BOXX UP 2.193pp; BTC-USD DOWN -2.193pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.759% | 16.481% | 13.081% | 4.758% | 3.143% | 00981A DOWN -4.759pp; BOXX UP 4.759pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
