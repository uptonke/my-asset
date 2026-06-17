# Risk Reduction Simulator v2.2

Generated at: `2026-06-17T13:26:15+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.699% | 4.802pp | 2.83pp | -0.182pp | -1.28pp | 11.944 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.015% | 3.547pp | 1.197pp | -0.134pp | -0.941pp | 7.782 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.349% | 2.401pp | 1.415pp | -0.137pp | -0.961pp | 6.202 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.572% | 2.7pp | 1.2pp | -0.108pp | -0.763pp | 6.078 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.266% | 2.355pp | 1.388pp | -0.041pp | -0.286pp | 5.614 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.508% | 1.774pp | 0.599pp | -0.102pp | -0.72pp | 4.07 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.786% | 1.35pp | 0.6pp | -0.083pp | -0.585pp | 3.185 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.175% | 1.201pp | 0.708pp | -0.079pp | -0.553pp | 3.154 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.133% | 1.178pp | 0.694pp | -0.031pp | -0.219pp | 2.862 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.754% | 0.887pp | 0.3pp | -0.059pp | -0.418pp | 2.077 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.393% | 0.675pp | 0.3pp | -0.048pp | -0.34pp | 1.626 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.067% | 0.589pp | 0.347pp | -0.018pp | -0.128pp | 1.444 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
