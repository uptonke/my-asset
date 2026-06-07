# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-07T08:13:08+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 5.966% | 12.467% | 10.166% | 10.074% | 2.695% | GLDM UP 1.846pp; 00981A DOWN -1.432pp; BTC-USD DOWN -1.394pp; VOO DOWN -1.0pp; QQQ DOWN -0.913pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.64% | 14.558% | 10.192% | 11.874% | 2.785% | BOXX UP 2.933pp; QQQ DOWN -2.378pp; GLDM UP 1.936pp; 2330 UP 1.46pp; BTC-USD DOWN -1.372pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.131% | 18.752% | 9.602% | 9.797% | 2.253% | BOXX UP 7.128pp; VOO DOWN -1.883pp; BTC-USD DOWN -1.686pp; QQQ DOWN -1.666pp; 00981A DOWN -1.59pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.242% | 19.867% | 3.862% | 10.904% | 1.849% | BOXX UP 8.242pp; BTC-USD DOWN -8.242pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.512% | 22.137% | 12.104% | 10.904% | 1.849% | BOXX UP 10.512pp; QQQ DOWN -10.512pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.415% | 21.04% | 12.104% | 1.489% | 1.849% | 00981A DOWN -9.415pp; BOXX UP 9.415pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.121% | 15.746% | 7.983% | 10.904% | 1.849% | BOXX UP 4.121pp; BTC-USD DOWN -4.121pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 4.862% | 15.487% | 8.242% | 10.904% | 1.849% | BOXX UP 3.862pp; ETH-USD DOWN -3.862pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.256% | 16.881% | 12.104% | 10.904% | 1.849% | BOXX UP 5.256pp; QQQ DOWN -5.256pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.707% | 16.332% | 12.104% | 6.197% | 1.849% | 00981A DOWN -4.707pp; BOXX UP 4.707pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.06% | 13.685% | 10.044% | 10.904% | 1.849% | BOXX UP 2.06pp; BTC-USD DOWN -2.06pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
