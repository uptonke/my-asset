# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-08-10T04:03:12+00:00`

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
- High-turnover review count: `4`
- Verdict: 有通過約束的觀察草案，但仍不得執行；下一步才是 Human Approval Layer。

## Drafts

| Draft | Source | Status | Turnover | Cash | Crypto | Taiwan | Gold | Top adjustments |
|---|---|---|---:|---:|---:|---:|---:|---|
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.455% | 15.082% | 12.549% | 8.075% | 4.057% | BOXX UP 1.78pp; BTC-USD DOWN -1.637pp; GLDM UP 1.63pp; SRVR UP 1.565pp; 00981A DOWN -1.472pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 8.102% | 16.711% | 12.596% | 9.547% | 4.178% | BOXX UP 3.409pp; VOO DOWN -2.254pp; GLDM UP 1.751pp; QQQ DOWN -1.675pp; BTC-USD DOWN -1.607pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.695% | 19.582% | 11.814% | 7.95% | 3.811% | BOXX UP 6.28pp; BTC-USD DOWN -2.0pp; QQQ DOWN -2.0pp; AVUV DOWN -1.774pp; 00981A DOWN -1.597pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.761% | 23.063% | 5.22% | 9.547% | 3.427% | BOXX UP 9.761pp; BTC-USD DOWN -9.761pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_violation_unresolved` | 13.252% | 25.554% | 14.981% | 9.547% | 3.427% | BOXX UP 12.252pp; QQQ DOWN -12.252pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.88% | 18.182% | 10.101% | 9.547% | 3.427% | BOXX UP 4.88pp; BTC-USD DOWN -4.88pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.22% | 18.522% | 9.761% | 9.547% | 3.427% | BOXX UP 5.22pp; ETH-USD DOWN -5.22pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.547% | 22.849% | 14.981% | 0.0% | 3.427% | 00981A DOWN -9.547pp; BOXX UP 9.547pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 7.126% | 19.428% | 14.981% | 9.547% | 3.427% | BOXX UP 6.126pp; QQQ DOWN -6.126pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.44% | 15.742% | 12.541% | 9.547% | 3.427% | BOXX UP 2.44pp; BTC-USD DOWN -2.44pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.61% | 15.912% | 12.371% | 9.547% | 3.427% | BOXX UP 2.61pp; ETH-USD DOWN -2.61pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
