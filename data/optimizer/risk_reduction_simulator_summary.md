# Risk Reduction Simulator v2.2

Generated at: `2026-11-26T08:29:23+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 10.166% | 5.611pp | 3.307pp | -0.258pp | -1.69pp | 14.109 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.964% | 3.852pp | 1.3pp | -0.162pp | -1.063pp | 8.489 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 5.083% | 2.805pp | 1.653pp | -0.193pp | -1.261pp | 7.354 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 5.127% | 2.83pp | 1.668pp | -0.061pp | -0.398pp | 6.788 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 8.541% | 2.408pp | 1.07pp | -0.087pp | -0.569pp | 5.346 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.982% | 1.926pp | 0.65pp | -0.124pp | -0.81pp | 4.446 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.542% | 1.403pp | 0.827pp | -0.11pp | -0.722pp | 3.744 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.563% | 1.415pp | 0.834pp | -0.046pp | -0.304pp | 3.47 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.271% | 1.204pp | 0.535pp | -0.067pp | -0.437pp | 2.783 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.991% | 0.963pp | 0.325pp | -0.072pp | -0.469pp | 2.269 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.282% | 0.707pp | 0.417pp | -0.027pp | -0.177pp | 1.752 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.135% | 0.602pp | 0.268pp | -0.039pp | -0.255pp | 1.418 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
