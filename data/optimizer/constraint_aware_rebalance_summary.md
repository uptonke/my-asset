# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-11T13:23:31+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.208% | 13.587% | 10.858% | 8.131% | 3.721% | GLDM UP 1.618pp; BTC-USD DOWN -1.456pp; BOXX UP 1.402pp; 00981A DOWN -1.396pp; USMV UP 1.068pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.105% | 15.72% | 10.926% | 9.527% | 3.849% | BOXX UP 3.535pp; QQQ DOWN -2.29pp; GLDM UP 1.746pp; BTC-USD DOWN -1.409pp; AVUV DOWN -0.933pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.513% | 20.699% | 9.951% | 7.946% | 3.103% | BOXX UP 8.514pp; USMV UP 1.999pp; BTC-USD DOWN -1.984pp; QQQ DOWN -1.725pp; 00981A DOWN -1.581pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.739% | 20.924% | 4.155% | 9.527% | 3.103% | BOXX UP 8.739pp; BTC-USD DOWN -8.739pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.838% | 23.023% | 12.894% | 9.527% | 3.103% | BOXX UP 10.838pp; QQQ DOWN -10.838pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.369% | 16.554% | 8.525% | 9.527% | 3.103% | BOXX UP 4.369pp; BTC-USD DOWN -4.369pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.527% | 21.712% | 12.894% | 0.0% | 3.103% | 00981A DOWN -9.527pp; BOXX UP 9.527pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.155% | 16.34% | 8.739% | 9.527% | 3.103% | BOXX UP 4.155pp; ETH-USD DOWN -4.155pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.419% | 17.604% | 12.894% | 9.527% | 3.103% | BOXX UP 5.419pp; QQQ DOWN -5.419pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.185% | 14.37% | 10.709% | 9.527% | 3.103% | BOXX UP 2.185pp; BTC-USD DOWN -2.185pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.763% | 16.948% | 12.894% | 4.764% | 3.103% | 00981A DOWN -4.763pp; BOXX UP 4.763pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
