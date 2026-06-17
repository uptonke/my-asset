# v10.5.2 Native Target Thesis Aggregator

This layer explains the evidence behind v10.5.1 delegated target weights.

It reads existing optimizer outputs, including v5.1 alpha research, v5.2 rebalance ranking, v3.0 regime-aware optimizer, v3.3 walk-forward backtest, v3.4 governance, v10.5 Daily Quant / Monte Carlo reference, and trading constraints.

It does not recalculate target weights, does not use front-end manual MC%, does not create orders, and does not enable execution.

Output files:

- `data/alpha/native_target_thesis_latest.json`
- `data/alpha/native_target_thesis_summary.md`

Safety flags remain false:

- `trade_signal_enabled`
- `execution_permission`
- `broker_submission_enabled`
- `official_rebalance_enabled`
- `auto_trade_enabled`
- `supabase_write_enabled`
