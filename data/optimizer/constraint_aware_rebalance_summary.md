# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-08T14:36:10+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 6.032% | 12.42% | 10.393% | 9.794% | 2.693% | GLDM UP 1.848pp; BTC-USD DOWN -1.434pp; 00981A DOWN -1.355pp; VOO DOWN -1.0pp; QQQ DOWN -0.958pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.279% | 13.646% | 10.422% | 12.013% | 2.783% | QQQ DOWN -2.409pp; BOXX UP 2.095pp; GLDM UP 1.938pp; 2330 UP 1.476pp; BTC-USD DOWN -1.41pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.235% | 18.77% | 9.831% | 9.516% | 2.252% | BOXX UP 7.219pp; VOO DOWN -1.896pp; BTC-USD DOWN -1.725pp; QQQ DOWN -1.714pp; 00981A DOWN -1.513pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.392% | 19.944% | 4.02% | 10.537% | 1.845% | BOXX UP 8.392pp; BTC-USD DOWN -8.392pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.649% | 22.201% | 12.412% | 10.537% | 1.845% | BOXX UP 10.649pp; QQQ DOWN -10.649pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.196% | 15.748% | 8.216% | 10.537% | 1.845% | BOXX UP 4.196pp; BTC-USD DOWN -4.196pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.098% | 20.65% | 12.412% | 1.439% | 1.845% | 00981A DOWN -9.098pp; BOXX UP 9.098pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.02% | 15.572% | 8.392% | 10.537% | 1.845% | BOXX UP 4.02pp; ETH-USD DOWN -4.02pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.324% | 16.876% | 12.412% | 10.537% | 1.845% | BOXX UP 5.324pp; QQQ DOWN -5.324pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.098% | 13.65% | 10.314% | 10.537% | 1.845% | BOXX UP 2.098pp; BTC-USD DOWN -2.098pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.549% | 16.101% | 12.412% | 5.988% | 1.845% | 00981A DOWN -4.549pp; BOXX UP 4.549pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
