# Walk-forward Backtest v3.3

Generated: `2026-06-14T16:41:20+00:00`

## Safety boundary

- 用於模型驗證，不是交易指令。
- 不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。

## Summary

- Status: `OK`
- Mode detail: `true_walk_forward_from_price_returns`
- Method count: `3`
- Fold count: `12`
- Likely better than current: `-`
- Verdict: `needs_more_out_of_sample_evidence`

## Aggregate results

| Method | Folds | Avg ES95 | Avg Vol | Avg Turnover | Risk win rate | Decision |
|---|---:|---:|---:|---:|---:|---|
| `inverse_vol_baseline` | 12 | 0.0 | 0.0 | 22.747 | 0.0 | `watch_only_validation` |
| `scipy_min_variance_fallback` | 12 | 0.0 | 0.0 | 73.401 | 0.0 | `watch_only_validation` |
| `current_weight` | 12 | 0.0 | 0.0 | 0.0 | None | `baseline` |

## Warnings

