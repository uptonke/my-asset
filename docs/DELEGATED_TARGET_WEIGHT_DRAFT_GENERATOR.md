# v10.5 Supabase Cloud Target Weight + Daily Quant Risk-Adjusted Delegated Engine

This component generates a delegated review draft from the portfolio's cloud target weights.

## Target weight source

v10.5 now uses:

1. `stock_meta[ticker].target_weight` from Supabase / backup as the base cloud target weight (`雲端%`).
2. Daily Quant / synthetic risk / Monte Carlo reference only as a risk-adjustment layer.
3. Holdings-table current price / current value for sizing and price quality checks.

It does **not** use the browser-only manual Monte Carlo `%` column as a target weight source, because that value is created in the front-end after the user manually runs Monte Carlo and is not materialized into Supabase or repo JSON for GitHub Actions.

## Current weight and drift

- Current weight comes from the current portfolio state in the constraints snapshot.
- v10.5 target weight is the risk-adjusted and normalized cloud target.
- Drift is `v10.5 target weight - current weight`.

## Risk adjustment

Daily Quant and Monte Carlo reference can:

- penalize fragile nodes,
- add warnings when synthetic risk / Monte Carlo data is missing,
- flag high tail-pressure regimes,
- reduce target weight raw scores before normalization.

They do not provide MC% target weights in this mode.

## Safety boundary

v10.5 remains review-only:

- `trade_signal_enabled: false`
- `execution_permission: false`
- `broker_submission_enabled: false`
- `official_rebalance_enabled: false`
- `auto_trade_enabled: false`
- `not_trade_order: true`
