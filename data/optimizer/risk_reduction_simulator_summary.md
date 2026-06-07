# Risk Reduction Simulator v2.2

Generated at: `2026-06-07T06:34:48+00:00`

## Safety Boundary

- This is not a BUY / SELL list.
- execution_permission is always false in v2.2.
- No Supabase write.
- No official portfolio weight update.
- Human approval is mandatory before any real-world action.

## Summary

- Simulation count: `15`
- Risk reduction candidates: `5`
- Tradeoff reviews: `5`
- Best simulation: `v2_2_trim_BTC_USD_100pct_to_BOXX`
- Verdict: 有風險降低候選可進入 v2.3 約束檢查。

## Top Simulations

| Simulation | Verdict | Trim | Worst stress improvement | Avg stress improvement | ES proxy change | Vol proxy change | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.042% | 4.44pp | 2.617pp | -0.159pp | -1.11pp | 10.993 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.551% | 3.398pp | 1.147pp | -0.126pp | -0.88pp | 7.441 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.45% | 2.665pp | 1.185pp | -0.109pp | -0.761pp | 6.007 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.021% | 2.22pp | 1.309pp | -0.12pp | -0.835pp | 5.697 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 3.739% | 2.064pp | 1.217pp | -0.032pp | -0.222pp | 4.9 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.276% | 1.699pp | 0.573pp | -0.097pp | -0.674pp | 3.888 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.725% | 1.333pp | 0.593pp | -0.084pp | -0.583pp | 3.15 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.011% | 1.11pp | 0.654pp | -0.069pp | -0.481pp | 2.893 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 1.87% | 1.032pp | 0.609pp | -0.024pp | -0.171pp | 2.493 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.638% | 0.85pp | 0.287pp | -0.056pp | -0.392pp | 1.984 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.363% | 0.667pp | 0.297pp | -0.049pp | -0.339pp | 1.61 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 0.935% | 0.516pp | 0.305pp | -0.014pp | -0.1pp | 1.257 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
