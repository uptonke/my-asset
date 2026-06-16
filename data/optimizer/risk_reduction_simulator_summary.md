# Risk Reduction Simulator v2.2

Generated at: `2026-06-16T15:11:59+00:00`

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
| `v2_2_trim_BTC_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 8.771% | 4.842pp | 2.853pp | -0.185pp | -1.3pp | 12.05 |
| `v2_2_trim_QQQ_100pct_to_BOXX` | `risk_reduction_candidate` | 11.094% | 3.572pp | 1.205pp | -0.136pp | -0.954pp | 7.841 |
| `v2_2_trim_BTC_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 4.386% | 2.421pp | 1.426pp | -0.139pp | -0.976pp | 6.257 |
| `v2_2_trim_00981A_100pct_to_BOXX` | `risk_reduction_candidate` | 9.517% | 2.684pp | 1.192pp | -0.107pp | -0.752pp | 6.037 |
| `v2_2_trim_ETH_USD_100pct_to_BOXX` | `risk_reduction_candidate` | 4.31% | 2.379pp | 1.402pp | -0.041pp | -0.291pp | 5.672 |
| `v2_2_trim_QQQ_50pct_to_BOXX` | `risk_reduction_candidate` | 5.547% | 1.786pp | 0.602pp | -0.104pp | -0.73pp | 4.101 |
| `v2_2_trim_BTC_USD_25pct_to_BOXX` | `risk_reduction_candidate` | 2.193% | 1.211pp | 0.713pp | -0.08pp | -0.561pp | 3.182 |
| `v2_2_trim_00981A_50pct_to_BOXX` | `risk_reduction_candidate` | 4.759% | 1.342pp | 0.596pp | -0.082pp | -0.577pp | 3.162 |
| `v2_2_trim_ETH_USD_50pct_to_BOXX` | `risk_reduction_candidate` | 2.155% | 1.19pp | 0.701pp | -0.032pp | -0.224pp | 2.893 |
| `v2_2_trim_QQQ_25pct_to_BOXX` | `tradeoff_review` | 2.774% | 0.893pp | 0.301pp | -0.06pp | -0.424pp | 2.092 |
| `v2_2_trim_00981A_25pct_to_BOXX` | `tradeoff_review` | 2.379% | 0.671pp | 0.298pp | -0.048pp | -0.336pp | 1.615 |
| `v2_2_trim_ETH_USD_25pct_to_BOXX` | `tradeoff_review` | 1.078% | 0.595pp | 0.35pp | -0.019pp | -0.131pp | 1.46 |

## Method Notes

- Each simulation trims a fraction of one focus position and reallocates the trimmed weight to BOXX / cash equivalent.
- Stress improvements are deterministic scenario deltas, not forecasts.
- ES / volatility / MDD changes are proxy estimates, not a full covariance recomputation.
