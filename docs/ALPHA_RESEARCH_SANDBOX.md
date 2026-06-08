# v5.0–v5.1 Forecast / Alpha Research Boundary

## Scope

- v5.0 builds a research-only forecast feature store.
- v5.1 builds a research-only alpha proxy ranking sandbox.

## Non-goals

- No BUY / SELL output.
- No official alpha model.
- No maximum Sharpe rebalance.
- No automatic execution.
- No Supabase write.
- No official portfolio weight update.

## Interpretation

`further_research` means the row passed a preliminary research screen. It does not mean the asset is attractive, bullish, or suitable for purchase.

## Safety invariants

All v5 outputs must keep:

- `research_only: true`
- `trade_signal_enabled: false`
- `execution_permission: false`
- `not_trade_order: true`
- `alpha_model_enabled: false`
- `maximum_sharpe_optimization_enabled: false`
