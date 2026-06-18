# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-18T12:01:30+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.348% | 13.348% | 10.873% | 8.359% | 3.739% | GLDM UP 1.615pp; BOXX UP 1.483pp; 00981A DOWN -1.468pp; BTC-USD DOWN -1.428pp; USMV UP 1.136pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.272% | 15.586% | 10.924% | 8.827% | 3.842% | BOXX UP 3.721pp; GLDM UP 1.718pp; BTC-USD DOWN -1.392pp; QQQ DOWN -1.373pp; 00981A DOWN -1.0pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.802% | 20.666% | 9.954% | 8.168% | 3.124% | BOXX UP 8.801pp; USMV UP 2.001pp; BTC-USD DOWN -1.963pp; QQQ DOWN -1.807pp; 00981A DOWN -1.659pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.639% | 20.504% | 4.268% | 9.827% | 3.124% | BOXX UP 8.639pp; BTC-USD DOWN -8.639pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.991% | 22.856% | 12.907% | 9.827% | 3.124% | BOXX UP 10.991pp; QQQ DOWN -10.991pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.827% | 21.692% | 12.907% | 0.0% | 3.124% | 00981A DOWN -9.827pp; BOXX UP 9.827pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.32% | 16.185% | 8.587% | 9.827% | 3.124% | BOXX UP 4.32pp; BTC-USD DOWN -4.32pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.268% | 16.133% | 8.639% | 9.827% | 3.124% | BOXX UP 4.268pp; ETH-USD DOWN -4.268pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.496% | 17.361% | 12.907% | 9.827% | 3.124% | BOXX UP 5.496pp; QQQ DOWN -5.496pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.914% | 16.779% | 12.907% | 4.913% | 3.124% | 00981A DOWN -4.914pp; BOXX UP 4.914pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.16% | 14.025% | 10.747% | 9.827% | 3.124% | BOXX UP 2.16pp; BTC-USD DOWN -2.16pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
