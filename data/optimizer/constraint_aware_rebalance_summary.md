# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-11-26T08:29:23+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_candidate_review` | 14.8% | 17.004% | 10.25% | 11.863% | 5.0% | BOXX UP 6.504pp; BTC-USD DOWN -3.506pp; QQQ DOWN -2.79pp; 00981A DOWN -2.7pp; VOO DOWN -2.489pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 17.548% | 22.709% | 10.167% | 13.488% | 5.0% | BOXX UP 12.209pp; QQQ DOWN -3.879pp; BTC-USD DOWN -3.552pp; VOO DOWN -3.381pp; AVUV DOWN -2.532pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.933% | 19.51% | 12.143% | 11.587% | 5.0% | BOXX UP 9.01pp; VOO DOWN -2.644pp; BTC-USD DOWN -2.0pp; QQQ DOWN -2.0pp; 00981A DOWN -1.666pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.164% | 20.666% | 5.127% | 13.744% | 5.0% | BOXX UP 10.166pp; BTC-USD DOWN -10.166pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 13.255% | 22.757% | 15.0% | 13.744% | 5.0% | BOXX UP 12.257pp; QQQ DOWN -11.964pp; GLDM UP 0.998pp; VOO DOWN -0.998pp; BTC-USD DOWN -0.195pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.081% | 15.583% | 10.21% | 13.744% | 5.0% | BOXX UP 5.083pp; BTC-USD DOWN -5.083pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.125% | 15.627% | 10.166% | 13.744% | 5.0% | BOXX UP 5.127pp; ETH-USD DOWN -5.127pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.832% | 19.334% | 15.0% | 5.203% | 5.0% | BOXX UP 8.834pp; 00981A DOWN -8.541pp; GLDM UP 0.998pp; VOO DOWN -0.998pp; BTC-USD DOWN -0.195pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 7.273% | 16.775% | 15.0% | 13.744% | 5.0% | BOXX UP 6.275pp; QQQ DOWN -5.982pp; GLDM UP 0.998pp; VOO DOWN -0.998pp; BTC-USD DOWN -0.195pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.54% | 13.042% | 12.751% | 13.744% | 5.0% | BOXX UP 2.542pp; BTC-USD DOWN -2.542pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
| `v2_3_from_v2_2_trim_ETH_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.561% | 13.063% | 12.73% | 13.744% | 5.0% | BOXX UP 2.563pp; ETH-USD DOWN -2.563pp; GLDM UP 0.998pp; VOO DOWN -0.998pp |
