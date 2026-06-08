# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-08T05:38:20+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 5.995% | 12.466% | 10.258% | 10.084% | 2.695% | GLDM UP 1.847pp; 00981A DOWN -1.433pp; BTC-USD DOWN -1.403pp; VOO DOWN -1.0pp; QQQ DOWN -0.913pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.649% | 14.534% | 10.286% | 11.892% | 2.785% | BOXX UP 2.929pp; QQQ DOWN -2.376pp; GLDM UP 1.937pp; 2330 UP 1.467pp; BTC-USD DOWN -1.379pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.164% | 18.769% | 9.695% | 9.811% | 2.252% | BOXX UP 7.164pp; VOO DOWN -1.887pp; BTC-USD DOWN -1.694pp; QQQ DOWN -1.668pp; 00981A DOWN -1.588pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.275% | 19.88% | 3.953% | 10.913% | 1.848% | BOXX UP 8.275pp; BTC-USD DOWN -8.275pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.494% | 22.099% | 12.228% | 10.913% | 1.848% | BOXX UP 10.494pp; QQQ DOWN -10.494pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.423% | 21.028% | 12.228% | 1.49% | 1.848% | 00981A DOWN -9.423pp; BOXX UP 9.423pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.137% | 15.742% | 8.091% | 10.913% | 1.848% | BOXX UP 4.137pp; BTC-USD DOWN -4.137pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 4.953% | 15.558% | 8.275% | 10.913% | 1.848% | BOXX UP 3.953pp; ETH-USD DOWN -3.953pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.247% | 16.852% | 12.228% | 10.913% | 1.848% | BOXX UP 5.247pp; QQQ DOWN -5.247pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.711% | 16.316% | 12.228% | 6.202% | 1.848% | 00981A DOWN -4.711pp; BOXX UP 4.711pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.069% | 13.674% | 10.159% | 10.913% | 1.848% | BOXX UP 2.069pp; BTC-USD DOWN -2.069pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
