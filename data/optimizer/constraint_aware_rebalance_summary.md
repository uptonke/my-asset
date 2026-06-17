# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-17T14:47:04+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.332% | 13.239% | 10.911% | 8.142% | 3.769% | GLDM UP 1.606pp; BOXX UP 1.485pp; BTC-USD DOWN -1.445pp; 00981A DOWN -1.396pp; USMV UP 1.144pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.331% | 15.717% | 10.964% | 9.538% | 3.878% | BOXX UP 3.963pp; QQQ DOWN -2.391pp; GLDM UP 1.715pp; BTC-USD DOWN -1.408pp; USMV UP 0.969pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.796% | 20.55% | 9.993% | 7.951% | 3.163% | BOXX UP 8.796pp; USMV UP 2.0pp; BTC-USD DOWN -1.979pp; QQQ DOWN -1.821pp; 00981A DOWN -1.587pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.704% | 20.458% | 4.255% | 9.538% | 3.163% | BOXX UP 8.704pp; BTC-USD DOWN -8.704pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 12.05% | 22.804% | 12.959% | 9.538% | 3.163% | BOXX UP 11.05pp; QQQ DOWN -11.05pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.352% | 16.106% | 8.607% | 9.538% | 3.163% | BOXX UP 4.352pp; BTC-USD DOWN -4.352pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.538% | 21.292% | 12.959% | 0.0% | 3.163% | 00981A DOWN -9.538pp; BOXX UP 9.538pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.255% | 16.009% | 8.704% | 9.538% | 3.163% | BOXX UP 4.255pp; ETH-USD DOWN -4.255pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.525% | 17.279% | 12.959% | 9.538% | 3.163% | BOXX UP 5.525pp; QQQ DOWN -5.525pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.769% | 16.523% | 12.959% | 4.769% | 3.163% | 00981A DOWN -4.769pp; BOXX UP 4.769pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.176% | 13.93% | 10.783% | 9.538% | 3.163% | BOXX UP 2.176pp; BTC-USD DOWN -2.176pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
