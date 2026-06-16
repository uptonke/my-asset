# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-16T14:36:21+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.339% | 13.223% | 10.961% | 8.127% | 3.752% | GLDM UP 1.611pp; BOXX UP 1.493pp; BTC-USD DOWN -1.455pp; 00981A DOWN -1.395pp; USMV UP 1.14pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.323% | 15.472% | 11.012% | 9.522% | 3.861% | BOXX UP 3.742pp; QQQ DOWN -2.388pp; GLDM UP 1.72pp; BTC-USD DOWN -1.419pp; USMV UP 0.979pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.797% | 20.528% | 10.046% | 7.937% | 3.141% | BOXX UP 8.798pp; USMV UP 1.999pp; BTC-USD DOWN -1.988pp; QQQ DOWN -1.823pp; 00981A DOWN -1.585pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.741% | 20.471% | 4.287% | 9.522% | 3.141% | BOXX UP 8.741pp; BTC-USD DOWN -8.741pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 12.091% | 22.821% | 13.028% | 9.522% | 3.141% | BOXX UP 11.091pp; QQQ DOWN -11.091pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.37% | 16.1% | 8.658% | 9.522% | 3.141% | BOXX UP 4.37pp; BTC-USD DOWN -4.37pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.522% | 21.252% | 13.028% | 0.0% | 3.141% | 00981A DOWN -9.522pp; BOXX UP 9.522pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.287% | 16.017% | 8.741% | 9.522% | 3.141% | BOXX UP 4.287pp; ETH-USD DOWN -4.287pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.545% | 17.275% | 13.028% | 9.522% | 3.141% | BOXX UP 5.545pp; QQQ DOWN -5.545pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.185% | 13.915% | 10.843% | 9.522% | 3.141% | BOXX UP 2.185pp; BTC-USD DOWN -2.185pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.761% | 16.491% | 13.028% | 4.761% | 3.141% | 00981A DOWN -4.761pp; BOXX UP 4.761pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
