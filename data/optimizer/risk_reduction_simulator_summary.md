# Risk Reduction Simulator v2.2

Generated at: `2026-06-08T05:38:20+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.275% | 4.568pp | 2.692pp | -0.17pp | -1.183pp | 11.339 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.494% | 3.379pp | 1.14pp | -0.126pp | -0.873pp | 7.398 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.423% | 2.658pp | 1.181pp | -0.109pp | -0.759pp | 5.991 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.137% | 2.284pp | 1.345pp | -0.128pp | -0.89pp | 5.882 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 3.953% | 2.182pp | 1.286pp | -0.036pp | -0.25pp | 5.191 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.247% | 1.69pp | 0.57pp | -0.096pp | -0.669pp | 3.866 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.711% | 1.329pp | 0.59pp | -0.084pp | -0.582pp | 3.14 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.069% | 1.142pp | 0.672pp | -0.074pp | -0.512pp | 2.989 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 1.976% | 1.091pp | 0.643pp | -0.028pp | -0.192pp | 2.644 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.623% | 0.845pp | 0.284pp | -0.056pp | -0.388pp | 1.971 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.356% | 0.665pp | 0.295pp | -0.049pp | -0.338pp | 1.605 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 0.988% | 0.546pp | 0.321pp | -0.016pp | -0.113pp | 1.334 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
