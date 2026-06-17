# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-17T13:26:15+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.327% | 13.239% | 10.919% | 8.166% | 3.76% | GLDM UP 1.609pp; BOXX UP 1.467pp; BTC-USD DOWN -1.442pp; 00981A DOWN -1.406pp; USMV UP 1.138pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.329% | 15.536% | 10.972% | 9.572% | 3.87% | BOXX UP 3.764pp; QQQ DOWN -2.38pp; GLDM UP 1.719pp; BTC-USD DOWN -1.405pp; USMV UP 0.963pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.782% | 20.554% | 10.002% | 7.976% | 3.151% | BOXX UP 8.782pp; USMV UP 2.0pp; BTC-USD DOWN -1.976pp; QQQ DOWN -1.811pp; 00981A DOWN -1.596pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.699% | 20.471% | 4.266% | 9.572% | 3.151% | BOXX UP 8.699pp; BTC-USD DOWN -8.699pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 12.015% | 22.787% | 12.965% | 9.572% | 3.151% | BOXX UP 11.015pp; QQQ DOWN -11.015pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.349% | 16.121% | 8.616% | 9.572% | 3.151% | BOXX UP 4.349pp; BTC-USD DOWN -4.349pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.572% | 21.344% | 12.965% | 0.0% | 3.151% | 00981A DOWN -9.572pp; BOXX UP 9.572pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.266% | 16.038% | 8.699% | 9.572% | 3.151% | BOXX UP 4.266pp; ETH-USD DOWN -4.266pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.508% | 17.28% | 12.965% | 9.572% | 3.151% | BOXX UP 5.508pp; QQQ DOWN -5.508pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.786% | 16.558% | 12.965% | 4.786% | 3.151% | 00981A DOWN -4.786pp; BOXX UP 4.786pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.175% | 13.947% | 10.79% | 9.572% | 3.151% | BOXX UP 2.175pp; BTC-USD DOWN -2.175pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
