# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-14T05:49:00+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.278% | 13.321% | 10.785% | 8.141% | 3.732% | GLDM UP 1.619pp; BOXX UP 1.45pp; BTC-USD DOWN -1.441pp; 00981A DOWN -1.395pp; USMV UP 1.115pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.074% | 15.576% | 10.838% | 8.748% | 3.848% | BOXX UP 3.705pp; GLDM UP 1.735pp; BTC-USD DOWN -1.404pp; QQQ DOWN -1.347pp; USMV UP 0.955pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.741% | 20.612% | 9.87% | 7.956% | 3.113% | BOXX UP 8.741pp; USMV UP 2.0pp; BTC-USD DOWN -1.973pp; QQQ DOWN -1.782pp; 00981A DOWN -1.58pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.686% | 20.557% | 4.103% | 9.536% | 3.113% | BOXX UP 8.686pp; BTC-USD DOWN -8.686pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.977% | 22.848% | 12.789% | 9.536% | 3.113% | BOXX UP 10.977pp; QQQ DOWN -10.977pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.343% | 16.214% | 8.446% | 9.536% | 3.113% | BOXX UP 4.343pp; BTC-USD DOWN -4.343pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.536% | 21.407% | 12.789% | 0.0% | 3.113% | 00981A DOWN -9.536pp; BOXX UP 9.536pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.103% | 15.974% | 8.686% | 9.536% | 3.113% | BOXX UP 4.103pp; ETH-USD DOWN -4.103pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.488% | 17.359% | 12.789% | 9.536% | 3.113% | BOXX UP 5.488pp; QQQ DOWN -5.488pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.768% | 16.639% | 12.789% | 4.768% | 3.113% | 00981A DOWN -4.768pp; BOXX UP 4.768pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.171% | 14.042% | 10.618% | 9.536% | 3.113% | BOXX UP 2.171pp; BTC-USD DOWN -2.171pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
