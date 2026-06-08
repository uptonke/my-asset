# Risk Reduction Simulator v2.2

Generated at: `2026-06-08T04:57:19+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.323% | 4.594pp | 2.708pp | -0.172pp | -1.198pp | 11.41 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.484% | 3.376pp | 1.14pp | -0.125pp | -0.871pp | 7.391 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.414% | 2.655pp | 1.18pp | -0.109pp | -0.757pp | 5.983 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.162% | 2.297pp | 1.354pp | -0.129pp | -0.9pp | 5.92 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 3.989% | 2.202pp | 1.298pp | -0.037pp | -0.255pp | 5.241 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.242% | 1.688pp | 0.57pp | -0.096pp | -0.667pp | 3.861 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.707% | 1.327pp | 0.59pp | -0.083pp | -0.58pp | 3.134 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.081% | 1.149pp | 0.677pp | -0.075pp | -0.518pp | 3.01 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 1.995% | 1.101pp | 0.649pp | -0.028pp | -0.196pp | 2.669 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.621% | 0.844pp | 0.285pp | -0.056pp | -0.388pp | 1.97 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.353% | 0.664pp | 0.296pp | -0.049pp | -0.338pp | 1.604 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 0.997% | 0.55pp | 0.325pp | -0.017pp | -0.115pp | 1.347 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
