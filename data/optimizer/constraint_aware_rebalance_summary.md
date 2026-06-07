# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-07T07:58:51+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 5.968% | 12.468% | 10.174% | 10.073% | 2.695% | GLDM UP 1.846pp; 00981A DOWN -1.432pp; BTC-USD DOWN -1.394pp; VOO DOWN -1.0pp; QQQ DOWN -0.913pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.642% | 14.559% | 10.201% | 11.872% | 2.785% | BOXX UP 2.935pp; QQQ DOWN -2.378pp; GLDM UP 1.936pp; 2330 UP 1.46pp; BTC-USD DOWN -1.371pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.133% | 18.754% | 9.611% | 9.795% | 2.253% | BOXX UP 7.13pp; VOO DOWN -1.882pp; BTC-USD DOWN -1.686pp; QQQ DOWN -1.666pp; 00981A DOWN -1.59pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.247% | 19.871% | 3.866% | 10.902% | 1.849% | BOXX UP 8.247pp; BTC-USD DOWN -8.247pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.511% | 22.135% | 12.113% | 10.902% | 1.849% | BOXX UP 10.511pp; QQQ DOWN -10.511pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.414% | 21.038% | 12.113% | 1.488% | 1.849% | 00981A DOWN -9.414pp; BOXX UP 9.414pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.124% | 15.748% | 7.989% | 10.902% | 1.849% | BOXX UP 4.124pp; BTC-USD DOWN -4.124pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 4.866% | 15.49% | 8.247% | 10.902% | 1.849% | BOXX UP 3.866pp; ETH-USD DOWN -3.866pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.256% | 16.88% | 12.113% | 10.902% | 1.849% | BOXX UP 5.256pp; QQQ DOWN -5.256pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.707% | 16.331% | 12.113% | 6.195% | 1.849% | 00981A DOWN -4.707pp; BOXX UP 4.707pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.062% | 13.686% | 10.051% | 10.902% | 1.849% | BOXX UP 2.062pp; BTC-USD DOWN -2.062pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
