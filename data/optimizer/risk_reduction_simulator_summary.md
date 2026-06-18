# Risk Reduction Simulator v2.2

Generated at: `2026-06-18T12:01:30+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.639% | 4.768pp | 2.81pp | -0.179pp | -1.259pp | 11.851 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.991% | 3.539pp | 1.194pp | -0.133pp | -0.935pp | 7.762 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.827% | 2.771pp | 1.231pp | -0.114pp | -0.805pp | 6.253 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.32% | 2.384pp | 1.405pp | -0.134pp | -0.946pp | 6.151 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.268% | 2.356pp | 1.388pp | -0.04pp | -0.285pp | 5.615 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.496% | 1.769pp | 0.597pp | -0.102pp | -0.716pp | 4.057 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.914% | 1.385pp | 0.615pp | -0.088pp | -0.617pp | 3.279 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.16% | 1.192pp | 0.702pp | -0.077pp | -0.544pp | 3.126 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.134% | 1.178pp | 0.694pp | -0.031pp | -0.219pp | 2.862 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.748% | 0.884pp | 0.298pp | -0.059pp | -0.416pp | 2.068 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.457% | 0.693pp | 0.308pp | -0.051pp | -0.359pp | 1.677 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.067% | 0.589pp | 0.347pp | -0.018pp | -0.128pp | 1.444 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
