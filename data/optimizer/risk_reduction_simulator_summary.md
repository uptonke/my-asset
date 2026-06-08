# Risk Reduction Simulator v2.2

Generated at: `2026-06-08T06:40:44+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.347% | 4.607pp | 2.716pp | -0.174pp | -1.21pp | 11.448 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.519% | 3.387pp | 1.144pp | -0.127pp | -0.881pp | 7.421 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.174% | 2.304pp | 1.358pp | -0.131pp | -0.91pp | 5.943 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.164% | 2.584pp | 1.149pp | -0.103pp | -0.718pp | 5.81 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 3.998% | 2.207pp | 1.301pp | -0.037pp | -0.257pp | 5.254 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.26% | 1.693pp | 0.572pp | -0.097pp | -0.675pp | 3.877 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.582% | 1.292pp | 0.574pp | -0.079pp | -0.551pp | 3.042 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.087% | 1.152pp | 0.679pp | -0.075pp | -0.524pp | 3.021 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 1.999% | 1.103pp | 0.651pp | -0.028pp | -0.198pp | 2.676 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.63% | 0.847pp | 0.286pp | -0.056pp | -0.392pp | 1.978 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.291% | 0.646pp | 0.287pp | -0.046pp | -0.321pp | 1.553 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.0% | 0.551pp | 0.325pp | -0.017pp | -0.116pp | 1.349 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
