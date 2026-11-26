# Risk Reduction Simulator v2.2

Generated at: `2026-11-26T11:35:02+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 10.153% | 5.605pp | 3.304pp | -0.257pp | -1.685pp | 14.092 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.961% | 3.852pp | 1.3pp | -0.162pp | -1.062pp | 8.489 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 5.077% | 2.802pp | 1.652pp | -0.192pp | -1.258pp | 7.345 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 5.156% | 2.846pp | 1.678pp | -0.062pp | -0.403pp | 6.829 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 8.54% | 2.408pp | 1.071pp | -0.087pp | -0.569pp | 5.347 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.981% | 1.926pp | 0.65pp | -0.124pp | -0.81pp | 4.446 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.538% | 1.401pp | 0.826pp | -0.11pp | -0.72pp | 3.738 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.578% | 1.423pp | 0.839pp | -0.047pp | -0.307pp | 3.491 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.27% | 1.204pp | 0.535pp | -0.067pp | -0.437pp | 2.783 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.99% | 0.963pp | 0.325pp | -0.072pp | -0.469pp | 2.27 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.289% | 0.712pp | 0.42pp | -0.027pp | -0.179pp | 1.765 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.135% | 0.602pp | 0.268pp | -0.039pp | -0.255pp | 1.418 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
