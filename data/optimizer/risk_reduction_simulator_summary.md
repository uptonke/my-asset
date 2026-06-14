# Risk Reduction Simulator v2.2

Generated at: `2026-06-14T05:49:00+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.686% | 4.795pp | 2.827pp | -0.181pp | -1.274pp | 11.925 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.977% | 3.534pp | 1.194pp | -0.132pp | -0.933pp | 7.751 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.343% | 2.397pp | 1.413pp | -0.136pp | -0.957pp | 6.189 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.536% | 2.689pp | 1.196pp | -0.107pp | -0.756pp | 6.051 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.103% | 2.265pp | 1.335pp | -0.037pp | -0.263pp | 5.39 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.488% | 1.767pp | 0.597pp | -0.101pp | -0.714pp | 4.052 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.768% | 1.344pp | 0.598pp | -0.082pp | -0.58pp | 3.169 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.171% | 1.199pp | 0.707pp | -0.078pp | -0.551pp | 3.148 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.051% | 1.132pp | 0.668pp | -0.029pp | -0.202pp | 2.745 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.744% | 0.884pp | 0.299pp | -0.059pp | -0.415pp | 2.069 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.384% | 0.672pp | 0.299pp | -0.048pp | -0.337pp | 1.618 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.026% | 0.566pp | 0.334pp | -0.017pp | -0.118pp | 1.385 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
