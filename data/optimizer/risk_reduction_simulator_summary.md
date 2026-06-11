# Risk Reduction Simulator v2.2

Generated at: `2026-06-11T13:23:31+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.739% | 4.824pp | 2.844pp | -0.189pp | -1.286pp | 12.005 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.838% | 3.49pp | 1.178pp | -0.133pp | -0.904pp | 7.645 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.369% | 2.412pp | 1.422pp | -0.142pp | -0.966pp | 6.234 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.527% | 2.687pp | 1.195pp | -0.11pp | -0.751pp | 6.047 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.155% | 2.294pp | 1.352pp | -0.039pp | -0.269pp | 5.462 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.419% | 1.745pp | 0.589pp | -0.102pp | -0.693pp | 3.996 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.185% | 1.206pp | 0.711pp | -0.082pp | -0.556pp | 3.17 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.763% | 1.344pp | 0.598pp | -0.085pp | -0.576pp | 3.169 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.077% | 1.147pp | 0.676pp | -0.03pp | -0.207pp | 2.783 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.709% | 0.873pp | 0.295pp | -0.059pp | -0.402pp | 2.039 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.382% | 0.672pp | 0.299pp | -0.049pp | -0.335pp | 1.618 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.039% | 0.574pp | 0.339pp | -0.018pp | -0.121pp | 1.406 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
