# Risk Reduction Simulator v2.2

Generated at: `2026-06-07T08:13:08+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.242% | 4.55pp | 2.681pp | -0.167pp | -1.167pp | 11.285 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.512% | 3.385pp | 1.142pp | -0.125pp | -0.872pp | 7.409 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.415% | 2.655pp | 1.18pp | -0.108pp | -0.753pp | 5.98 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.121% | 2.275pp | 1.34pp | -0.126pp | -0.878pp | 5.853 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 3.862% | 2.132pp | 1.256pp | -0.034pp | -0.237pp | 5.066 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.256% | 1.693pp | 0.571pp | -0.096pp | -0.668pp | 3.871 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.707% | 1.328pp | 0.59pp | -0.083pp | -0.578pp | 3.135 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.06% | 1.137pp | 0.67pp | -0.072pp | -0.505pp | 2.972 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 1.931% | 1.066pp | 0.628pp | -0.026pp | -0.182pp | 2.579 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.628% | 0.846pp | 0.285pp | -0.056pp | -0.388pp | 1.973 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.354% | 0.664pp | 0.294pp | -0.048pp | -0.336pp | 1.6 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 0.965% | 0.533pp | 0.314pp | -0.015pp | -0.107pp | 1.301 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
