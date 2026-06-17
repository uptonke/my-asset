# Expected Return Model v3.2

Generated: `2026-06-17T13:26:15+00:00`

## Safety boundary

- Relative prior only; absolute expected-return forecast is disabled.
- Maximum Sharpe optimization is disabled.
- 不是 BUY / SELL 指令，不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。

## Summary

- Asset priors: `14`
- Positive prior buckets: `2`
- Negative prior buckets: `3`
- Verdict: `relative_prior_only_no_max_sharpe`

## Bucket priors

| Bucket | Score | Band | Confidence | Regime adj | BL adj |
|---|---:|---|---:|---:|---:|
| `cash` | 2.05 | `relative_overweight_prior` | 0.75 | 0.8 | 0.85 |
| `gold` | 0.622 | `neutral_or_no_edge_prior` | 0.75 | 0.25 | 0.272 |
| `global_equity` | 0.0 | `neutral_or_no_edge_prior` | 0.75 | 0.0 | 0.0 |
| `other` | 0.0 | `neutral_or_no_edge_prior` | 0.75 | 0.0 | 0.0 |
| `us_equity` | 0.0 | `neutral_or_no_edge_prior` | 0.75 | 0.0 | 0.0 |
| `commodity_equity` | -0.1 | `neutral_or_no_edge_prior` | 0.75 | 0.0 | 0.0 |
| `emerging_market` | -0.35 | `neutral_or_no_edge_prior` | 0.7 | -0.25 | 0.0 |
| `theme_etf` | -0.45 | `neutral_or_no_edge_prior` | 0.7 | -0.3 | 0.0 |
| `taiwan_tech` | -0.55 | `neutral_or_no_edge_prior` | 0.75 | -0.35 | 0.0 |
| `us_tech` | -0.94 | `relative_underweight_prior` | 0.75 | -0.45 | -0.34 |
| `crypto` | -1.98 | `relative_underweight_prior` | 0.7 | -0.9 | -0.68 |

## Top asset priors

| Ticker | Bucket | Score | Band | Confidence |
|---|---|---:|---|---:|
| `BOXX` | `cash` | 2.05 | `relative_overweight_prior` | 0.75 |
| `GLDM` | `gold` | 0.622 | `neutral_or_no_edge_prior` | 0.75 |
| `AVUV` | `other` | 0.0 | `neutral_or_no_edge_prior` | 0.75 |
| `PICK` | `other` | 0.0 | `neutral_or_no_edge_prior` | 0.75 |
| `USMV` | `other` | 0.0 | `neutral_or_no_edge_prior` | 0.75 |
| `VEA` | `other` | 0.0 | `neutral_or_no_edge_prior` | 0.75 |
| `VOO` | `us_equity` | 0.0 | `neutral_or_no_edge_prior` | 0.75 |
| `GRID` | `theme_etf` | -0.45 | `neutral_or_no_edge_prior` | 0.7 |
| `IFRA` | `theme_etf` | -0.45 | `neutral_or_no_edge_prior` | 0.7 |
| `SRVR` | `theme_etf` | -0.45 | `neutral_or_no_edge_prior` | 0.7 |
| `00981A` | `taiwan_tech` | -0.55 | `neutral_or_no_edge_prior` | 0.75 |
| `QQQ` | `us_tech` | -0.94 | `relative_underweight_prior` | 0.75 |
| `BTC-USD` | `crypto` | -1.98 | `relative_underweight_prior` | 0.7 |
| `ETH-USD` | `crypto` | -1.98 | `relative_underweight_prior` | 0.7 |

## Warnings

- 3Y robustness window unavailable; expected return confidence capped.
- Absolute expected return forecast is disabled by design.
- Maximum Sharpe optimization is disabled; no alpha model is trusted enough.
