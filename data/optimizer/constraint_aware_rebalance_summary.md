# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-08T06:40:44+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 5.977% | 12.48% | 10.343% | 9.849% | 2.696% | GLDM UP 1.846pp; BTC-USD DOWN -1.421pp; 00981A DOWN -1.373pp; VOO DOWN -1.0pp; QQQ DOWN -0.919pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.641% | 14.554% | 10.375% | 11.64% | 2.789% | BOXX UP 2.922pp; QQQ DOWN -2.38pp; GLDM UP 1.939pp; 2330 UP 1.464pp; BTC-USD DOWN -1.395pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.16% | 18.792% | 9.78% | 9.566% | 2.255% | BOXX UP 7.16pp; VOO DOWN -1.892pp; BTC-USD DOWN -1.713pp; QQQ DOWN -1.673pp; 00981A DOWN -1.533pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.347% | 19.979% | 3.998% | 10.613% | 1.85% | BOXX UP 8.347pp; BTC-USD DOWN -8.347pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.519% | 22.151% | 12.345% | 10.613% | 1.85% | BOXX UP 10.519pp; QQQ DOWN -10.519pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.174% | 15.806% | 8.171% | 10.613% | 1.85% | BOXX UP 4.174pp; BTC-USD DOWN -4.174pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.164% | 20.796% | 12.345% | 1.449% | 1.85% | 00981A DOWN -9.164pp; BOXX UP 9.164pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 4.998% | 15.63% | 8.347% | 10.613% | 1.85% | BOXX UP 3.998pp; ETH-USD DOWN -3.998pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.26% | 16.892% | 12.345% | 10.613% | 1.85% | BOXX UP 5.26pp; QQQ DOWN -5.26pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.582% | 16.214% | 12.345% | 6.031% | 1.85% | 00981A DOWN -4.582pp; BOXX UP 4.582pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.087% | 13.719% | 10.258% | 10.613% | 1.85% | BOXX UP 2.087pp; BTC-USD DOWN -2.087pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
