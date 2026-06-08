# Risk Reduction Simulator v2.2

Generated at: `2026-06-08T14:36:10+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.392% | 4.632pp | 2.73pp | -0.176pp | -1.221pp | 11.514 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.649% | 3.428pp | 1.157pp | -0.13pp | -0.902pp | 7.517 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.196% | 2.316pp | 1.365pp | -0.132pp | -0.918pp | 5.976 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.098% | 2.565pp | 1.14pp | -0.102pp | -0.705pp | 5.762 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.02% | 2.219pp | 1.308pp | -0.037pp | -0.26pp | 5.283 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.324% | 1.714pp | 0.578pp | -0.1pp | -0.691pp | 3.93 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.098% | 1.158pp | 0.682pp | -0.076pp | -0.528pp | 3.037 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.549% | 1.282pp | 0.57pp | -0.078pp | -0.541pp | 3.015 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.01% | 1.109pp | 0.654pp | -0.029pp | -0.2pp | 2.691 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.662% | 0.857pp | 0.289pp | -0.058pp | -0.401pp | 2.005 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.274% | 0.641pp | 0.285pp | -0.045pp | -0.315pp | 1.539 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.005% | 0.554pp | 0.327pp | -0.017pp | -0.117pp | 1.357 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
