# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-14T16:41:15+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.276% | 13.324% | 10.756% | 8.151% | 3.733% | GLDM UP 1.619pp; BOXX UP 1.449pp; BTC-USD DOWN -1.437pp; 00981A DOWN -1.398pp; USMV UP 1.115pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.074% | 15.583% | 10.809% | 8.76% | 3.848% | BOXX UP 3.708pp; GLDM UP 1.734pp; BTC-USD DOWN -1.4pp; QQQ DOWN -1.349pp; USMV UP 0.954pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.74% | 20.615% | 9.842% | 7.965% | 3.114% | BOXX UP 8.74pp; USMV UP 2.0pp; BTC-USD DOWN -1.969pp; QQQ DOWN -1.783pp; 00981A DOWN -1.584pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.67% | 20.545% | 4.083% | 9.549% | 3.114% | BOXX UP 8.67pp; BTC-USD DOWN -8.67pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.981% | 22.856% | 12.753% | 9.549% | 3.114% | BOXX UP 10.981pp; QQQ DOWN -10.981pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.335% | 16.21% | 8.418% | 9.549% | 3.114% | BOXX UP 4.335pp; BTC-USD DOWN -4.335pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.549% | 21.424% | 12.753% | 0.0% | 3.114% | 00981A DOWN -9.549pp; BOXX UP 9.549pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.083% | 15.958% | 8.67% | 9.549% | 3.114% | BOXX UP 4.083pp; ETH-USD DOWN -4.083pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.49% | 17.365% | 12.753% | 9.549% | 3.114% | BOXX UP 5.49pp; QQQ DOWN -5.49pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.774% | 16.649% | 12.753% | 4.775% | 3.114% | 00981A DOWN -4.774pp; BOXX UP 4.774pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.167% | 14.042% | 10.586% | 9.549% | 3.114% | BOXX UP 2.167pp; BTC-USD DOWN -2.167pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
