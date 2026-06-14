# Risk Reduction Simulator v2.2

Generated at: `2026-06-14T07:03:09+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.677% | 4.79pp | 2.824pp | -0.181pp | -1.27pp | 11.911 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.979% | 3.535pp | 1.194pp | -0.133pp | -0.932pp | 7.753 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.338% | 2.395pp | 1.412pp | -0.136pp | -0.954pp | 6.183 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.538% | 2.69pp | 1.196pp | -0.107pp | -0.755pp | 6.053 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.1% | 2.263pp | 1.334pp | -0.037pp | -0.262pp | 5.385 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.489% | 1.768pp | 0.597pp | -0.101pp | -0.713pp | 4.053 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.769% | 1.345pp | 0.598pp | -0.082pp | -0.579pp | 3.17 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.169% | 1.197pp | 0.706pp | -0.078pp | -0.549pp | 3.142 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.05% | 1.132pp | 0.668pp | -0.029pp | -0.202pp | 2.745 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.745% | 0.884pp | 0.299pp | -0.059pp | -0.414pp | 2.068 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.384% | 0.672pp | 0.299pp | -0.048pp | -0.337pp | 1.618 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.025% | 0.566pp | 0.334pp | -0.017pp | -0.118pp | 1.385 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
