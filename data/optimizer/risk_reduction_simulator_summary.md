# Risk Reduction Simulator v2.2

Generated at: `2026-06-07T07:15:53+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.217% | 4.536pp | 2.673pp | -0.166pp | -1.16pp | 11.248 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.515% | 3.386pp | 1.142pp | -0.125pp | -0.873pp | 7.411 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.417% | 2.656pp | 1.18pp | -0.108pp | -0.754pp | 5.982 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.109% | 2.268pp | 1.336pp | -0.125pp | -0.873pp | 5.833 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 3.866% | 2.134pp | 1.257pp | -0.034pp | -0.238pp | 5.071 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.258% | 1.693pp | 0.571pp | -0.096pp | -0.669pp | 3.872 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.708% | 1.328pp | 0.59pp | -0.083pp | -0.578pp | 3.135 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.054% | 1.134pp | 0.668pp | -0.072pp | -0.503pp | 2.964 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 1.933% | 1.067pp | 0.629pp | -0.026pp | -0.183pp | 2.582 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.629% | 0.847pp | 0.285pp | -0.056pp | -0.388pp | 1.975 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.354% | 0.664pp | 0.295pp | -0.048pp | -0.336pp | 1.601 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 0.967% | 0.534pp | 0.314pp | -0.015pp | -0.107pp | 1.302 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
