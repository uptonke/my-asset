# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-07T06:34:51+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 5.909% | 12.475% | 9.93% | 10.103% | 2.697% | GLDM UP 1.845pp; 00981A DOWN -1.442pp; BTC-USD DOWN -1.338pp; VOO DOWN -1.0pp; QQQ DOWN -0.924pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.605% | 14.577% | 9.954% | 11.903% | 2.787% | BOXX UP 2.909pp; QQQ DOWN -2.389pp; GLDM UP 1.935pp; 2330 UP 1.459pp; BTC-USD DOWN -1.317pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.098% | 18.772% | 9.366% | 9.825% | 2.255% | BOXX UP 7.104pp; VOO DOWN -1.892pp; QQQ DOWN -1.677pp; BTC-USD DOWN -1.63pp; 00981A DOWN -1.6pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.042% | 19.71% | 3.739% | 10.944% | 1.852% | BOXX UP 8.042pp; BTC-USD DOWN -8.042pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.551% | 22.219% | 11.781% | 10.944% | 1.852% | BOXX UP 10.551pp; QQQ DOWN -10.551pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.45% | 21.118% | 11.781% | 1.494% | 1.852% | 00981A DOWN -9.45pp; BOXX UP 9.45pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.021% | 15.689% | 7.76% | 10.944% | 1.852% | BOXX UP 4.021pp; BTC-USD DOWN -4.021pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 4.739% | 15.407% | 8.042% | 10.944% | 1.852% | BOXX UP 3.739pp; ETH-USD DOWN -3.739pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.276% | 16.944% | 11.781% | 10.944% | 1.852% | BOXX UP 5.276pp; QQQ DOWN -5.276pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.725% | 16.393% | 11.781% | 6.219% | 1.852% | 00981A DOWN -4.725pp; BOXX UP 4.725pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.011% | 13.679% | 9.77% | 10.944% | 1.852% | BOXX UP 2.011pp; BTC-USD DOWN -2.011pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
