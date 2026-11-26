# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-11-26T08:38:57+00:00`

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
- Constraint pass count: `6`
- High-turnover review count: `5`
- Verdict: 有通過約束的觀察草案，但仍不得執行；下一步才是 Human Approval Layer。

## Drafts

| Draft | Source | Status | Turnover | Cash | Crypto | Taiwan | Gold | Top adjustments |
|---|---|---|---:|---:|---:|---:|---:|---|
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_candidate_review` | 14.804% | 17.005% | 10.256% | 11.861% | 5.0% | BOXX UP 6.506pp; BTC-USD DOWN -3.507pp; QQQ DOWN -2.79pp; 00981A DOWN -2.7pp; VOO DOWN -2.489pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 17.55% | 22.708% | 10.172% | 13.488% | 5.0% | BOXX UP 12.209pp; QQQ DOWN -3.878pp; BTC-USD DOWN -3.554pp; VOO DOWN -3.381pp; AVUV DOWN -2.532pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.933% | 19.509% | 12.152% | 11.585% | 5.0% | BOXX UP 9.01pp; VOO DOWN -2.644pp; BTC-USD DOWN -2.0pp; QQQ DOWN -2.0pp; 00981A DOWN -1.666pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.167% | 20.668% | 5.134% | 13.742% | 5.0% | BOXX UP 10.169pp; BTC-USD DOWN -10.169pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 13.263% | 22.764% | 15.0% | 13.742% | 5.0% | BOXX UP 12.265pp; QQQ DOWN -11.962pp; GLDM UP 0.998pp; VOO DOWN -0.998pp; BTC-USD DOWN -0.201pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.083% | 15.584% | 10.218% | 13.742% | 5.0% | BOXX UP 5.085pp; BTC-USD DOWN -5.085pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.132% | 15.633% | 10.169% | 13.742% | 5.0% | BOXX UP 5.134pp; ETH-USD DOWN -5.134pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.841% | 19.342% | 15.0% | 5.202% | 5.0% | BOXX UP 8.843pp; 00981A DOWN -8.54pp; GLDM UP 0.998pp; VOO DOWN -0.998pp; BTC-USD DOWN -0.201pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 7.282% | 16.783% | 15.0% | 13.742% | 5.0% | BOXX UP 6.284pp; QQQ DOWN -5.981pp; GLDM UP 0.998pp; VOO DOWN -0.998pp; BTC-USD DOWN -0.201pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.54% | 13.041% | 12.761% | 13.742% | 5.0% | BOXX UP 2.542pp; BTC-USD DOWN -2.542pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
| `v2_3_from_v2_2_trim_ETH_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.565% | 13.066% | 12.736% | 13.742% | 5.0% | BOXX UP 2.567pp; ETH-USD DOWN -2.567pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
