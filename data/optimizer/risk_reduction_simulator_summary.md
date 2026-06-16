# Risk Reduction Simulator v2.2

Generated at: `2026-06-16T08:33:30+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.879% | 4.902pp | 2.888pp | -0.189pp | -1.329pp | 12.208 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.214% | 3.611pp | 1.218pp | -0.138pp | -0.972pp | 7.932 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.439% | 2.451pp | 1.444pp | -0.142pp | -0.998pp | 6.342 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.522% | 2.686pp | 1.193pp | -0.107pp | -0.75pp | 6.041 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.309% | 2.379pp | 1.402pp | -0.041pp | -0.29pp | 5.672 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.607% | 1.806pp | 0.609pp | -0.106pp | -0.744pp | 4.151 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.22% | 1.226pp | 0.722pp | -0.082pp | -0.574pp | 3.226 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.761% | 1.343pp | 0.597pp | -0.082pp | -0.575pp | 3.163 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.155% | 1.19pp | 0.7pp | -0.032pp | -0.223pp | 2.892 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.804% | 0.903pp | 0.304pp | -0.061pp | -0.431pp | 2.117 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.381% | 0.672pp | 0.298pp | -0.048pp | -0.335pp | 1.616 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.077% | 0.595pp | 0.35pp | -0.019pp | -0.13pp | 1.46 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
