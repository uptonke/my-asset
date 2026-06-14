# Risk Reduction Simulator v2.2

Generated at: `2026-06-14T16:41:15+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.67% | 4.785pp | 2.821pp | -0.18pp | -1.266pp | 11.896 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.981% | 3.535pp | 1.194pp | -0.133pp | -0.932pp | 7.753 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.335% | 2.392pp | 1.41pp | -0.135pp | -0.951pp | 6.173 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.549% | 2.692pp | 1.197pp | -0.108pp | -0.756pp | 6.058 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.083% | 2.253pp | 1.328pp | -0.037pp | -0.26pp | 5.361 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.49% | 1.767pp | 0.597pp | -0.101pp | -0.713pp | 4.051 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.774% | 1.346pp | 0.599pp | -0.083pp | -0.58pp | 3.174 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.167% | 1.196pp | 0.705pp | -0.078pp | -0.547pp | 3.138 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.041% | 1.126pp | 0.664pp | -0.028pp | -0.2pp | 2.729 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.745% | 0.884pp | 0.298pp | -0.059pp | -0.414pp | 2.067 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.387% | 0.673pp | 0.299pp | -0.048pp | -0.338pp | 1.62 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.021% | 0.563pp | 0.332pp | -0.017pp | -0.117pp | 1.377 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
