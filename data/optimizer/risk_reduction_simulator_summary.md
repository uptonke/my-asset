# Risk Reduction Simulator v2.2

Generated at: `2026-06-12T12:48:58+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.61% | 4.753pp | 2.801pp | -0.178pp | -1.253pp | 11.812 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.981% | 3.536pp | 1.193pp | -0.133pp | -0.936pp | 7.756 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.305% | 2.377pp | 1.401pp | -0.134pp | -0.942pp | 6.133 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.584% | 2.703pp | 1.201pp | -0.109pp | -0.766pp | 6.087 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.096% | 2.261pp | 1.333pp | -0.037pp | -0.263pp | 5.381 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.49% | 1.768pp | 0.597pp | -0.102pp | -0.717pp | 4.056 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.792% | 1.352pp | 0.601pp | -0.083pp | -0.587pp | 3.19 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.152% | 1.189pp | 0.7pp | -0.077pp | -0.542pp | 3.118 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.048% | 1.131pp | 0.666pp | -0.029pp | -0.202pp | 2.742 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.745% | 0.884pp | 0.298pp | -0.059pp | -0.416pp | 2.069 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.396% | 0.676pp | 0.3pp | -0.048pp | -0.342pp | 1.629 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.024% | 0.566pp | 0.333pp | -0.017pp | -0.118pp | 1.384 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
