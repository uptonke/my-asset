# Constraint-Aware Rebalance Sandbox v2.3

Generated at: `2026-06-08T06:35:02+00:00`

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
| `v2_3_v2_1_inverse_vol_baseline` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 5.981% | 12.48% | 10.352% | 9.848% | 2.696% | GLDM UP 1.847pp; BTC-USD DOWN -1.426pp; 00981A DOWN -1.372pp; VOO DOWN -1.0pp; QQQ DOWN -0.918pp |
| `v2_3_v2_1_riskfolio_risk_parity_mv` | v2.1_rebalance_candidate_generator | `constraint_pass_watch_only` | 7.646% | 14.557% | 10.382% | 11.639% | 2.789% | BOXX UP 2.927pp; QQQ DOWN -2.379pp; GLDM UP 1.94pp; 2330 UP 1.464pp; BTC-USD DOWN -1.401pp |
| `v2_3_v2_1_riskfolio_hrp_mv` | v2.1_rebalance_candidate_generator | `turnover_too_high_review_only` | 10.164% | 18.793% | 9.788% | 9.565% | 2.255% | BOXX UP 7.163pp; VOO DOWN -1.891pp; BTC-USD DOWN -1.718pp; QQQ DOWN -1.672pp; 00981A DOWN -1.532pp |
| `v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 9.358% | 19.988% | 4.002% | 10.611% | 1.849% | BOXX UP 8.358pp; BTC-USD DOWN -8.358pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 11.517% | 22.147% | 12.36% | 10.611% | 1.849% | BOXX UP 10.517pp; QQQ DOWN -10.517pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.179% | 15.809% | 8.181% | 10.611% | 1.849% | BOXX UP 4.179pp; BTC-USD DOWN -4.179pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `turnover_too_high_review_only` | 10.162% | 20.792% | 12.36% | 1.449% | 1.849% | 00981A DOWN -9.162pp; BOXX UP 9.162pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.002% | 15.632% | 8.358% | 10.611% | 1.849% | BOXX UP 4.002pp; ETH-USD DOWN -4.002pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_QQQ_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 6.259% | 16.889% | 12.36% | 10.611% | 1.849% | BOXX UP 5.259pp; QQQ DOWN -5.259pp; GLDM UP 1.0pp; VOO DOWN -1.0pp |
| `v2_3_from_v2_2_trim_00981A_50pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 5.581% | 16.211% | 12.36% | 6.03% | 1.849% | 00981A DOWN -4.581pp; BOXX UP 4.581pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
| `v2_3_from_v2_2_trim_BTC_USD_25pct_to_BOXX` | v2.2_risk_reduction_simulator | `constraint_pass_watch_only` | 3.09% | 13.72% | 10.27% | 10.611% | 1.849% | BOXX UP 2.09pp; BTC-USD DOWN -2.09pp; GLDM UP 1.0pp; QQQ DOWN -1.0pp |
