# Risk Reduction Simulator v2.2

Generated at: `2026-06-17T13:53:51+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.722% | 4.815pp | 2.838pp | -0.183pp | -1.287pp | 11.979 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.047% | 3.557pp | 1.201pp | -0.135pp | -0.947pp | 7.807 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.361% | 2.407pp | 1.419pp | -0.137pp | -0.967pp | 6.219 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.538% | 2.69pp | 1.195pp | -0.108pp | -0.757pp | 6.054 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.275% | 2.36pp | 1.391pp | -0.041pp | -0.287pp | 5.626 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.523% | 1.779pp | 0.6pp | -0.103pp | -0.725pp | 4.084 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.769% | 1.345pp | 0.598pp | -0.083pp | -0.581pp | 3.172 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.18% | 1.204pp | 0.71pp | -0.079pp | -0.556pp | 3.163 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.137% | 1.18pp | 0.695pp | -0.031pp | -0.22pp | 2.867 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.762% | 0.889pp | 0.3pp | -0.06pp | -0.421pp | 2.083 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.384% | 0.672pp | 0.299pp | -0.048pp | -0.338pp | 1.619 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.069% | 0.59pp | 0.348pp | -0.018pp | -0.129pp | 1.447 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
