# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-08T04:57:19+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.011% | 12.467% | 10.319% | 10.076% | 2.694% | GLDM UP 1.847pp; 00981A DOWN -1.431pp; BTC-USD DOWN -1.416pp; VOO DOWN -1.0pp; QQQ DOWN -0.91pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.66% | 14.529% | 10.348% | 11.884% | 2.785% | BOXX UP 2.935pp; QQQ DOWN -2.373pp; GLDM UP 1.938pp; 2330 UP 1.468pp; BTC-USD DOWN -1.392pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.175% | 18.765% | 9.756% | 9.803% | 2.252% | BOXX UP 7.171pp; VOO DOWN -1.885pp; BTC-USD DOWN -1.708pp; QQQ DOWN -1.665pp; 00981A DOWN -1.586pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.323% | 19.917% | 3.989% | 10.902% | 1.847% | BOXX UP 8.323pp; BTC-USD DOWN -8.323pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.484% | 22.078% | 12.312% | 10.902% | 1.847% | BOXX UP 10.484pp; QQQ DOWN -10.484pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.414% | 21.008% | 12.312% | 1.488% | 1.847% | 00981A DOWN -9.414pp; BOXX UP 9.414pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.162% | 15.756% | 8.15% | 10.902% | 1.847% | BOXX UP 4.162pp; BTC-USD DOWN -4.162pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 4.989% | 15.583% | 8.323% | 10.902% | 1.847% | BOXX UP 3.989pp; ETH-USD DOWN -3.989pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.242% | 16.836% | 12.312% | 10.902% | 1.847% | BOXX UP 5.242pp; QQQ DOWN -5.242pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.707% | 16.301% | 12.312% | 6.195% | 1.847% | 00981A DOWN -4.707pp; BOXX UP 4.707pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.081% | 13.675% | 10.231% | 10.902% | 1.847% | BOXX UP 2.081pp; BTC-USD DOWN -2.081pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
