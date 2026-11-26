# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-11-26T11:35:02+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_candidate_review` | 14.807% | 17.006% | 10.258% | 11.861% | 5.0% | BOXX UP 6.508pp; BTC-USD DOWN -3.499pp; QQQ DOWN -2.789pp; 00981A DOWN -2.7pp; VOO DOWN -2.489pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 17.551% | 22.707% | 10.175% | 13.488% | 5.0% | BOXX UP 12.209pp; QQQ DOWN -3.877pp; BTC-USD DOWN -3.545pp; VOO DOWN -3.38pp; AVUV DOWN -2.531pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.94% | 19.513% | 12.152% | 11.585% | 5.0% | BOXX UP 9.015pp; VOO DOWN -2.644pp; BTC-USD DOWN -2.0pp; QQQ DOWN -2.0pp; 00981A DOWN -1.666pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.152% | 20.651% | 5.156% | 13.742% | 5.0% | BOXX UP 10.153pp; BTC-USD DOWN -10.153pp; GLDM UP 0.999pp; VOO DOWN -0.999pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 13.269% | 22.768% | 15.0% | 13.742% | 5.0% | BOXX UP 12.27pp; QQQ DOWN -11.961pp; GLDM UP 0.999pp; VOO DOWN -0.999pp; BTC-USD DOWN -0.205pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.076% | 15.575% | 10.232% | 13.742% | 5.0% | BOXX UP 5.077pp; BTC-USD DOWN -5.077pp; GLDM UP 0.999pp; VOO DOWN -0.999pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.155% | 15.654% | 10.153% | 13.742% | 5.0% | BOXX UP 5.156pp; ETH-USD DOWN -5.156pp; GLDM UP 0.999pp; VOO DOWN -0.999pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.848% | 19.347% | 15.0% | 5.202% | 5.0% | BOXX UP 8.849pp; 00981A DOWN -8.54pp; GLDM UP 0.999pp; VOO DOWN -0.999pp; BTC-USD DOWN -0.205pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 7.289% | 16.788% | 15.0% | 13.742% | 5.0% | BOXX UP 6.29pp; QQQ DOWN -5.981pp; GLDM UP 0.999pp; VOO DOWN -0.999pp; BTC-USD DOWN -0.205pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.537% | 13.036% | 12.771% | 13.742% | 5.0% | BOXX UP 2.538pp; BTC-USD DOWN -2.538pp; GLDM UP 0.999pp; VOO DOWN -0.999pp |
| `v2_3_from_v2_2_trim_ETH_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.577% | 13.076% | 12.731% | 13.742% | 5.0% | BOXX UP 2.578pp; ETH-USD DOWN -2.578pp; GLDM UP 0.999pp; VOO DOWN -0.999pp |
