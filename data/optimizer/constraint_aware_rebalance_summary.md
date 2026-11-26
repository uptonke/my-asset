# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-11-26T08:50:59+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_candidate_review` | 14.822% | 17.009% | 10.284% | 11.855% | 4.999% | BOXX UP 6.518pp; BTC-USD DOWN -3.527pp; QQQ DOWN -2.786pp; 00981A DOWN -2.697pp; VOO DOWN -2.486pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 17.563% | 22.709% | 10.2% | 13.482% | 4.999% | BOXX UP 12.218pp; QQQ DOWN -3.874pp; BTC-USD DOWN -3.573pp; VOO DOWN -3.376pp; AVUV DOWN -2.527pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.935% | 19.499% | 12.206% | 11.577% | 4.999% | BOXX UP 9.008pp; VOO DOWN -2.643pp; BTC-USD DOWN -2.0pp; QQQ DOWN -2.0pp; 00981A DOWN -1.665pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.206% | 20.697% | 5.157% | 13.733% | 4.999% | BOXX UP 10.206pp; BTC-USD DOWN -10.206pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 13.317% | 22.808% | 15.0% | 13.733% | 4.999% | BOXX UP 12.317pp; QQQ DOWN -11.954pp; GLDM UP 1.0pp; VOO DOWN -1.0pp; BTC-USD DOWN -0.241pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.103% | 15.594% | 10.26% | 13.733% | 4.999% | BOXX UP 5.103pp; BTC-USD DOWN -5.103pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.157% | 15.648% | 10.206% | 13.733% | 4.999% | BOXX UP 5.157pp; ETH-USD DOWN -5.157pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.897% | 19.388% | 15.0% | 5.199% | 4.999% | BOXX UP 8.897pp; 00981A DOWN -8.534pp; GLDM UP 1.0pp; VOO DOWN -1.0pp; BTC-USD DOWN -0.241pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 7.34% | 16.831% | 15.0% | 13.733% | 4.999% | BOXX UP 6.34pp; QQQ DOWN -5.977pp; GLDM UP 1.0pp; VOO DOWN -1.0pp; BTC-USD DOWN -0.241pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.552% | 13.043% | 12.811% | 13.733% | 4.999% | BOXX UP 2.552pp; BTC-USD DOWN -2.552pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.579% | 13.07% | 12.784% | 13.733% | 4.999% | BOXX UP 2.579pp; ETH-USD DOWN -2.579pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
