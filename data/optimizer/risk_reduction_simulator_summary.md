# Risk Reduction Simulator v2.2

Generated at: `2026-06-16T14:36:21+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.741% | 4.825pp | 2.844pp | -0.184pp | -1.291pp | 12.006 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.091% | 3.571pp | 1.206pp | -0.136pp | -0.954pp | 7.84 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.37% | 2.412pp | 1.422pp | -0.138pp | -0.969pp | 6.233 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.522% | 2.685pp | 1.194pp | -0.107pp | -0.753pp | 6.041 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.287% | 2.366pp | 1.395pp | -0.041pp | -0.288pp | 5.641 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.545% | 1.785pp | 0.603pp | -0.104pp | -0.73pp | 4.1 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.185% | 1.206pp | 0.711pp | -0.079pp | -0.558pp | 3.168 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.761% | 1.342pp | 0.597pp | -0.082pp | -0.578pp | 3.163 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.143% | 1.183pp | 0.697pp | -0.031pp | -0.221pp | 2.875 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.773% | 0.892pp | 0.301pp | -0.06pp | -0.423pp | 2.09 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.38% | 0.671pp | 0.298pp | -0.048pp | -0.336pp | 1.615 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.072% | 0.591pp | 0.349pp | -0.018pp | -0.129pp | 1.45 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
