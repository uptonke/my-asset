# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-14T07:03:09+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.276% | 13.322% | 10.774% | 8.143% | 3.733% | GLDM UP 1.619pp; BOXX UP 1.449pp; BTC-USD DOWN -1.439pp; 00981A DOWN -1.395pp; USMV UP 1.115pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.073% | 15.577% | 10.829% | 8.75% | 3.849% | BOXX UP 3.704pp; GLDM UP 1.735pp; BTC-USD DOWN -1.402pp; QQQ DOWN -1.348pp; USMV UP 0.955pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.739% | 20.612% | 9.86% | 7.957% | 3.114% | BOXX UP 8.739pp; USMV UP 2.0pp; BTC-USD DOWN -1.971pp; QQQ DOWN -1.782pp; 00981A DOWN -1.581pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.677% | 20.55% | 4.1% | 9.538% | 3.114% | BOXX UP 8.677pp; BTC-USD DOWN -8.677pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.979% | 22.852% | 12.777% | 9.538% | 3.114% | BOXX UP 10.979pp; QQQ DOWN -10.979pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.338% | 16.211% | 8.439% | 9.538% | 3.114% | BOXX UP 4.338pp; BTC-USD DOWN -4.338pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.538% | 21.411% | 12.777% | 0.0% | 3.114% | 00981A DOWN -9.538pp; BOXX UP 9.538pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.1% | 15.973% | 8.677% | 9.538% | 3.114% | BOXX UP 4.1pp; ETH-USD DOWN -4.1pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.489% | 17.362% | 12.777% | 9.538% | 3.114% | BOXX UP 5.489pp; QQQ DOWN -5.489pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.769% | 16.642% | 12.777% | 4.769% | 3.114% | 00981A DOWN -4.769pp; BOXX UP 4.769pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.169% | 14.042% | 10.608% | 9.538% | 3.114% | BOXX UP 2.169pp; BTC-USD DOWN -2.169pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
