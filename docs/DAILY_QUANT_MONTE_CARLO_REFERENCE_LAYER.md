# v10.5 Daily Quant + Monte Carlo Reference Layer

v10.5 讓 delegated draft layer 連接既有 Daily Quant Pipeline 與 Monte Carlo / chaos_meta 輸出。

## Purpose

- Treat `.github/workflows/daily_update.yml` as the data and risk foundation.
- Read Supabase / backup `stock_meta`, `settings`, and `chaos_meta`.
- Reference synthetic portfolio risk and Monte Carlo-style tail diagnostics.
- Provide inputs to the v10.5 integrated delegated target-weight engine.
- After delegated target weights are generated, check the latest draft against the same references.

## Relationship with target weights

This layer is no longer only a post-hoc card. The delegated target-weight generator reads `daily_quant_reference_latest.json` before generating target weights:

- Synthetic risk and Monte Carlo pressure determine the target-weight scoring blend.
- Monte Carlo fragile nodes receive raw-score penalties before weight normalization.
- The final reference check still remains diagnostic only.

## Boundary

v10.5 does not rerun Monte Carlo, does not replace Daily Quant Pipeline, and does not create broker orders. It only writes diagnostic/reference JSON files and supplies risk context to the delegated target-weight generator.

Safety flags must remain false:

- `trade_signal_enabled`
- `execution_permission`
- `broker_submission_enabled`
- `official_rebalance_enabled`
- `auto_trade_enabled`
- `supabase_write_enabled`
