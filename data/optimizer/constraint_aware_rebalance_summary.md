# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-17T13:53:51+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.34% | 13.241% | 10.94% | 8.141% | 3.764% | GLDM UP 1.608pp; BOXX UP 1.487pp; BTC-USD DOWN -1.449pp; 00981A DOWN -1.397pp; USMV UP 1.143pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.335% | 15.715% | 10.992% | 9.538% | 3.874% | BOXX UP 3.961pp; QQQ DOWN -2.388pp; GLDM UP 1.718pp; BTC-USD DOWN -1.413pp; USMV UP 0.967pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 11.796% | 20.551% | 10.022% | 7.951% | 3.156% | BOXX UP 8.797pp; USMV UP 1.999pp; BTC-USD DOWN -1.984pp; QQQ DOWN -1.818pp; 00981A DOWN -1.587pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.722% | 20.476% | 4.275% | 9.538% | 3.156% | BOXX UP 8.722pp; BTC-USD DOWN -8.722pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 12.047% | 22.801% | 12.997% | 9.538% | 3.156% | BOXX UP 11.047pp; QQQ DOWN -11.047pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.361% | 16.115% | 8.636% | 9.538% | 3.156% | BOXX UP 4.361pp; BTC-USD DOWN -4.361pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.538% | 21.292% | 12.997% | 0.0% | 3.156% | 00981A DOWN -9.538pp; BOXX UP 9.538pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.275% | 16.029% | 8.722% | 9.538% | 3.156% | BOXX UP 4.275pp; ETH-USD DOWN -4.275pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.523% | 17.277% | 12.997% | 9.538% | 3.156% | BOXX UP 5.523pp; QQQ DOWN -5.523pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.769% | 16.523% | 12.997% | 4.769% | 3.156% | 00981A DOWN -4.769pp; BOXX UP 4.769pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.18% | 13.934% | 10.817% | 9.538% | 3.156% | BOXX UP 2.18pp; BTC-USD DOWN -2.18pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
