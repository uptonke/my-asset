# Risk Reduction Simulator v2.2

Generated at: `2026-06-07T07:58:51+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.247% | 4.552pp | 2.683pp | -0.168pp | -1.168pp | 11.292 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.511% | 3.385pp | 1.142pp | -0.125pp | -0.871pp | 7.408 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.414% | 2.655pp | 1.18pp | -0.108pp | -0.753pp | 5.98 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.124% | 2.276pp | 1.342pp | -0.126pp | -0.879pp | 5.857 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 3.866% | 2.134pp | 1.258pp | -0.034pp | -0.238pp | 5.072 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.256% | 1.692pp | 0.571pp | -0.096pp | -0.667pp | 3.869 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.707% | 1.327pp | 0.59pp | -0.083pp | -0.577pp | 3.133 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.062% | 1.138pp | 0.671pp | -0.073pp | -0.506pp | 2.976 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 1.933% | 1.067pp | 0.629pp | -0.026pp | -0.183pp | 2.582 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.628% | 0.846pp | 0.286pp | -0.056pp | -0.388pp | 1.974 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.354% | 0.664pp | 0.295pp | -0.048pp | -0.336pp | 1.601 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 0.967% | 0.534pp | 0.315pp | -0.015pp | -0.107pp | 1.303 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
