# Risk Reduction Simulator v2.2

Generated at: `2026-06-08T05:19:04+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.292% | 4.577pp | 2.698pp | -0.171pp | -1.189pp | 11.364 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 10.491% | 3.378pp | 1.14pp | -0.126pp | -0.873pp | 7.396 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.42% | 2.657pp | 1.181pp | -0.109pp | -0.758pp | 5.988 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.146% | 2.289pp | 1.349pp | -0.129pp | -0.894pp | 5.898 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 3.965% | 2.189pp | 1.29pp | -0.036pp | -0.252pp | 5.208 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.245% | 1.689pp | 0.57pp | -0.096pp | -0.669pp | 3.864 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.71% | 1.329pp | 0.59pp | -0.084pp | -0.581pp | 3.139 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.073% | 1.145pp | 0.675pp | -0.074pp | -0.515pp | 2.999 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 1.982% | 1.095pp | 0.645pp | -0.028pp | -0.194pp | 2.654 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.623% | 0.845pp | 0.285pp | -0.056pp | -0.388pp | 1.972 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.355% | 0.664pp | 0.295pp | -0.049pp | -0.338pp | 1.603 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 0.991% | 0.548pp | 0.323pp | -0.016pp | -0.113pp | 1.34 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
