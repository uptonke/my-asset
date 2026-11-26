# Risk Reduction Simulator v2.2

Generated at: `2026-11-26T08:50:59+00:00`

## Safety Boundary

- This is not a BUY / SELL list.
- execution_permission is always false in v2.2.
- No Supabase write.
- No official portfolio weight update.
- Human approval is mandatory before any real-world action.

## Summary

- Simulation count: `15`
- Risk reduction candidates: `5`
- Tradeoff reviews: `4`
- Best simulation: `v2_2_trim_BTC_USD_100pct_to_BOXX`
- Verdict: 有風險降低候選可進入 v2.3 約束檢查。

## Top Simulations

| Simulation | Verdict | Trim | Worst stress improvement | Avg stress improvement | ES proxy change | Vol proxy change | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 10.206% | 5.633pp | 3.32pp | -0.26pp | -1.702pp | 14.169 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.954% | 3.849pp | 1.299pp | -0.162pp | -1.06pp | 8.482 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 5.103% | 2.817pp | 1.66pp | -0.194pp | -1.27pp | 7.388 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 5.157% | 2.846pp | 1.677pp | -0.061pp | -0.402pp | 6.827 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 8.534% | 2.406pp | 1.069pp | -0.087pp | -0.567pp | 5.341 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.977% | 1.924pp | 0.649pp | -0.123pp | -0.808pp | 4.44 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.552% | 1.408pp | 0.829pp | -0.111pp | -0.727pp | 3.759 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.579% | 1.423pp | 0.838pp | -0.047pp | -0.307pp | 3.49 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.267% | 1.203pp | 0.534pp | -0.067pp | -0.436pp | 2.78 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.989% | 0.962pp | 0.324pp | -0.072pp | -0.468pp | 2.266 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.289% | 0.711pp | 0.419pp | -0.027pp | -0.179pp | 1.762 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.134% | 0.601pp | 0.267pp | -0.039pp | -0.255pp | 1.416 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
