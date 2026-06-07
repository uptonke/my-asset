# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-07T06:48:50+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 5.962% | 12.468% | 10.153% | 10.075% | 2.695% | GLDM UP 1.846pp; 00981A DOWN -1.433pp; BTC-USD DOWN -1.385pp; VOO DOWN -1.0pp; QQQ DOWN -0.914pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.639% | 14.56% | 10.178% | 11.875% | 2.785% | BOXX UP 2.932pp; QQQ DOWN -2.379pp; GLDM UP 1.936pp; 2330 UP 1.46pp; BTC-USD DOWN -1.364pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.128% | 18.753% | 9.588% | 9.799% | 2.253% | BOXX UP 7.125pp; VOO DOWN -1.883pp; BTC-USD DOWN -1.678pp; QQQ DOWN -1.667pp; 00981A DOWN -1.59pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.217% | 19.845% | 3.866% | 10.906% | 1.849% | BOXX UP 8.217pp; BTC-USD DOWN -8.217pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.515% | 22.143% | 12.083% | 10.906% | 1.849% | BOXX UP 10.515pp; QQQ DOWN -10.515pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.417% | 21.045% | 12.083% | 1.489% | 1.849% | 00981A DOWN -9.417pp; BOXX UP 9.417pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.109% | 15.737% | 7.974% | 10.906% | 1.849% | BOXX UP 4.109pp; BTC-USD DOWN -4.109pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 4.866% | 15.494% | 8.217% | 10.906% | 1.849% | BOXX UP 3.866pp; ETH-USD DOWN -3.866pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.258% | 16.886% | 12.083% | 10.906% | 1.849% | BOXX UP 5.258pp; QQQ DOWN -5.258pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.708% | 16.336% | 12.083% | 6.198% | 1.849% | 00981A DOWN -4.708pp; BOXX UP 4.708pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.054% | 13.682% | 10.029% | 10.906% | 1.849% | BOXX UP 2.054pp; BTC-USD DOWN -2.054pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
