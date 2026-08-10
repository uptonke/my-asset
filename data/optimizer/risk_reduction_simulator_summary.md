# Risk Reduction Simulator v2.2

Generated at: `2026-08-10T04:03:12+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 9.761% | 5.388pp | 3.176pp | -0.208pp | -1.46pp | 13.42 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 12.252% | 3.945pp | 1.331pp | -0.15pp | -1.051pp | 8.659 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.88% | 2.694pp | 1.588pp | -0.156pp | -1.094pp | 6.97 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 5.22% | 2.881pp | 1.698pp | -0.055pp | -0.388pp | 6.895 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.547% | 2.692pp | 1.197pp | -0.096pp | -0.675pp | 6.0 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 6.126% | 1.972pp | 0.666pp | -0.115pp | -0.804pp | 4.528 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.44% | 1.347pp | 0.794pp | -0.09pp | -0.628pp | 3.543 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.61% | 1.44pp | 0.849pp | -0.042pp | -0.297pp | 3.52 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.774% | 1.346pp | 0.598pp | -0.074pp | -0.519pp | 3.129 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 3.063% | 0.986pp | 0.333pp | -0.066pp | -0.466pp | 2.309 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.305% | 0.72pp | 0.424pp | -0.025pp | -0.174pp | 1.778 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.387% | 0.673pp | 0.299pp | -0.043pp | -0.303pp | 1.595 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
