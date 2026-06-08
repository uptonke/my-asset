# Risk Reduction Simulator v2.2

Generated at: `2026-06-08T06:35:02+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.358% | 4.613pp | 2.719pp | -0.175pp | -1.213pp | 11.464 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.517% | 3.386pp | 1.143pp | -0.127pp | -0.88pp | 7.417 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.179% | 2.306pp | 1.36pp | -0.131pp | -0.912pp | 5.95 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.162% | 2.583pp | 1.149pp | -0.103pp | -0.717pp | 5.807 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.002% | 2.209pp | 1.303pp | -0.037pp | -0.258pp | 5.259 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.259% | 1.693pp | 0.572pp | -0.097pp | -0.674pp | 3.876 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.581% | 1.292pp | 0.575pp | -0.079pp | -0.55pp | 3.042 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.09% | 1.153pp | 0.68pp | -0.076pp | -0.525pp | 3.025 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.001% | 1.104pp | 0.651pp | -0.029pp | -0.198pp | 2.678 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.629% | 0.846pp | 0.286pp | -0.056pp | -0.392pp | 1.976 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.291% | 0.646pp | 0.288pp | -0.046pp | -0.32pp | 1.554 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.001% | 0.552pp | 0.326pp | -0.017pp | -0.116pp | 1.352 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
