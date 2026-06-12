# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-12T12:48:58+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.273% | 13.39% | 10.724% | 8.178% | 3.74% | GLDM UP 1.616pp; BOXX UP 1.449pp; BTC-USD DOWN -1.421pp; 00981A DOWN -1.406pp; USMV UP 1.113pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.033% | 15.611% | 10.775% | 8.806% | 3.853% | BOXX UP 3.67pp; GLDM UP 1.729pp; BTC-USD DOWN -1.386pp; QQQ DOWN -1.351pp; USMV UP 0.956pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.726% | 20.668% | 9.808% | 7.992% | 3.124% | BOXX UP 8.727pp; USMV UP 1.999pp; BTC-USD DOWN -1.954pp; QQQ DOWN -1.788pp; 00981A DOWN -1.592pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.61% | 20.551% | 4.096% | 9.584% | 3.124% | BOXX UP 8.61pp; BTC-USD DOWN -8.61pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.981% | 22.922% | 12.706% | 9.584% | 3.124% | BOXX UP 10.981pp; QQQ DOWN -10.981pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.305% | 16.246% | 8.401% | 9.584% | 3.124% | BOXX UP 4.305pp; BTC-USD DOWN -4.305pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.584% | 21.525% | 12.706% | 0.0% | 3.124% | 00981A DOWN -9.584pp; BOXX UP 9.584pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.096% | 16.037% | 8.61% | 9.584% | 3.124% | BOXX UP 4.096pp; ETH-USD DOWN -4.096pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.49% | 17.431% | 12.706% | 9.584% | 3.124% | BOXX UP 5.49pp; QQQ DOWN -5.49pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.792% | 16.733% | 12.706% | 4.792% | 3.124% | 00981A DOWN -4.792pp; BOXX UP 4.792pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.152% | 14.093% | 10.554% | 9.584% | 3.124% | BOXX UP 2.152pp; BTC-USD DOWN -2.152pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
