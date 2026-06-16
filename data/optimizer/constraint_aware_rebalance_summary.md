# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-16T08:33:30+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.388% | 13.268% | 11.089% | 8.127% | 3.756% | GLDM UP 1.608pp; BOXX UP 1.511pp; BTC-USD DOWN -1.484pp; 00981A DOWN -1.395pp; USMV UP 1.142pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.351% | 15.505% | 11.142% | 9.522% | 3.867% | BOXX UP 3.748pp; QQQ DOWN -2.423pp; GLDM UP 1.719pp; BTC-USD DOWN -1.447pp; USMV UP 0.982pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.802% | 20.56% | 10.197% | 7.937% | 3.148% | BOXX UP 8.803pp; USMV UP 1.999pp; BTC-USD DOWN -1.994pp; QQQ DOWN -1.858pp; 00981A DOWN -1.585pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.879% | 20.636% | 4.309% | 9.522% | 3.148% | BOXX UP 8.879pp; BTC-USD DOWN -8.879pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 12.214% | 22.971% | 13.188% | 9.522% | 3.148% | BOXX UP 11.214pp; QQQ DOWN -11.214pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.439% | 16.196% | 8.749% | 9.522% | 3.148% | BOXX UP 4.439pp; BTC-USD DOWN -4.439pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.522% | 21.279% | 13.188% | 0.0% | 3.148% | 00981A DOWN -9.522pp; BOXX UP 9.522pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.309% | 16.066% | 8.879% | 9.522% | 3.148% | BOXX UP 4.309pp; ETH-USD DOWN -4.309pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.607% | 17.364% | 13.188% | 9.522% | 3.148% | BOXX UP 5.607pp; QQQ DOWN -5.607pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.22% | 13.977% | 10.968% | 9.522% | 3.148% | BOXX UP 2.22pp; BTC-USD DOWN -2.22pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.761% | 16.518% | 13.188% | 4.761% | 3.148% | 00981A DOWN -4.761pp; BOXX UP 4.761pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
