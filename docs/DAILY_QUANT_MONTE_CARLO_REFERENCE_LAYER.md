# v10.5 Daily Quant + Monte Carlo Reference Layer

v10.5 connects the delegated draft layer to the existing Daily Quant Pipeline and Monte Carlo / chaos_meta outputs.

## Purpose

- Treat `.github/workflows/daily_update.yml` as the data and risk foundation.
- Read Supabase / backup `stock_meta`, `settings`, and `chaos_meta`.
- Reference synthetic portfolio risk and Monte Carlo-style tail diagnostics.
- Check the latest v10.x delegated draft against those references.

## Boundary

v10.5 does not rerun Monte Carlo, does not replace Daily Quant Pipeline, and does not create broker orders. It only writes diagnostic/reference JSON files.

Safety flags must remain false:

- `trade_signal_enabled`
- `execution_permission`
- `broker_submission_enabled`
- `official_rebalance_enabled`
- `auto_trade_enabled`
- `supabase_write_enabled`
