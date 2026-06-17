# Risk Reduction Simulator v2.2

Generated at: `2026-06-17T14:47:04+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.704% | 4.805pp | 2.831pp | -0.182pp | -1.282pp | 11.952 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.05% | 3.558pp | 1.2pp | -0.135pp | -0.948pp | 7.809 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.352% | 2.402pp | 1.415pp | -0.137pp | -0.963pp | 6.204 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.538% | 2.69pp | 1.195pp | -0.108pp | -0.757pp | 6.054 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.255% | 2.349pp | 1.384pp | -0.04pp | -0.284pp | 5.598 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.525% | 1.779pp | 0.6pp | -0.103pp | -0.726pp | 4.084 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.769% | 1.345pp | 0.597pp | -0.083pp | -0.581pp | 3.171 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.176% | 1.201pp | 0.708pp | -0.079pp | -0.554pp | 3.155 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.127% | 1.175pp | 0.692pp | -0.031pp | -0.218pp | 2.854 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.763% | 0.89pp | 0.3pp | -0.06pp | -0.421pp | 2.085 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.385% | 0.673pp | 0.298pp | -0.048pp | -0.338pp | 1.62 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.064% | 0.587pp | 0.346pp | -0.018pp | -0.128pp | 1.44 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
