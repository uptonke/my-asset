# Walk-forward Backtest v3.3

Generated: `2026-11-26T08:39:06+00:00`

## Safety boundary

- 用於模型驗證，不是交易指令。
- 不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。

## Summary

- Status: `OK`
- Mode detail: `true_walk_forward_from_price_returns`
- Method count: `3`
- Fold count: `20`
- Likely better than current: `-`
- Verdict: `needs_more_out_of_sample_evidence`

## Aggregate results

| Method | Folds | Avg ES95 | Avg Vol | Avg Turnover | Risk win rate | Decision |
|---|---:|---:|---:|---:|---:|---|
| `inverse_vol_baseline` | 20 | 0.0 | 0.0 | 28.464 | 0.0 | `watch_only_validation` |
| `scipy_min_variance_fallback` | 20 | 0.0 | 0.0 | 78.381 | 0.0 | `watch_only_validation` |
| `current_weight` | 20 | 0.0 | 0.0 | 0.0 | None | `baseline` |

## Warnings

