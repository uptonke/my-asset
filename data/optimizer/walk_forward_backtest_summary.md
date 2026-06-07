# Walk-forward Backtest v3.3

Generated: `2026-06-07T08:05:09+00:00`

## Safety boundary

- 用於模型驗證，不是交易指令。
- 不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。

## Summary

- Status: `PROXY_ONLY`
- Mode detail: `proxy_from_robustness_windows_not_true_walk_forward`
- Method count: `9`
- Fold count: `4`
- Likely better than current: `-`
- Verdict: `proxy_only_insufficient_for_model_promotion`

## Aggregate results

| Method | Folds | Avg ES95 | Avg Vol | Avg Turnover | Risk win rate | Decision |
|---|---:|---:|---:|---:|---:|---|
| `riskfolio_cvar_minimize` | 4 | 0.631 | 5.13 | 71.727 | - | `proxy_only_no_out_of_sample_claim` |
| `skfolio_cvar_minimize` | 4 | 0.631 | 5.13 | 71.727 | - | `proxy_only_no_out_of_sample_claim` |
| `scipy_min_variance_fallback` | 4 | 0.662 | 4.605 | 78.83 | - | `proxy_only_no_out_of_sample_claim` |
| `skfolio_min_variance` | 4 | 0.665 | 4.605 | 78.58 | - | `proxy_only_no_out_of_sample_claim` |
| `riskfolio_min_variance` | 4 | 0.666 | 4.605 | 78.56 | - | `proxy_only_no_out_of_sample_claim` |
| `riskfolio_hrp_mv` | 4 | 0.936 | 6.37 | 46.705 | - | `proxy_only_no_out_of_sample_claim` |
| `riskfolio_risk_parity_mv` | 4 | 1.17 | 8.127 | 31.703 | - | `proxy_only_no_out_of_sample_claim` |
| `inverse_vol_baseline` | 4 | 1.43 | 9.535 | 24.133 | - | `proxy_only_no_out_of_sample_claim` |
| `current_weight` | 4 | 1.71 | 11.69 | 0.0 | - | `baseline` |

## Warnings

- True walk-forward unavailable; fallback proxy used. Reason: No module named 'run_skfolio_sandbox'
- This is not a true out-of-sample walk-forward backtest; it uses robustness windows as proxy.
