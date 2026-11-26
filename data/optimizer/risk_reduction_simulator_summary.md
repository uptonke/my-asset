# Risk Reduction Simulator v2.2

Generated at: `2026-11-26T08:38:57+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 10.169% | 5.614pp | 3.309pp | -0.258pp | -1.69pp | 14.117 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.962% | 3.852pp | 1.3pp | -0.162pp | -1.062pp | 8.489 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 5.085% | 2.807pp | 1.654pp | -0.193pp | -1.262pp | 7.359 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 5.134% | 2.834pp | 1.67pp | -0.061pp | -0.399pp | 6.798 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 8.54% | 2.409pp | 1.07pp | -0.087pp | -0.569pp | 5.348 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.981% | 1.926pp | 0.65pp | -0.124pp | -0.81pp | 4.446 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.542% | 1.404pp | 0.827pp | -0.11pp | -0.722pp | 3.746 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.567% | 1.417pp | 0.835pp | -0.046pp | -0.304pp | 3.474 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.27% | 1.205pp | 0.536pp | -0.067pp | -0.437pp | 2.786 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.99% | 0.963pp | 0.325pp | -0.072pp | -0.469pp | 2.27 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.284% | 0.709pp | 0.418pp | -0.027pp | -0.178pp | 1.757 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.135% | 0.602pp | 0.268pp | -0.039pp | -0.255pp | 1.418 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
