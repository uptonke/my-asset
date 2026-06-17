# v10.5 Supabase Cloud Target Weight + Daily Quant Risk-Adjusted Delegated Engine

- Generated: `2026-06-17T13:26:32+00:00`
- Delegated draft status: **machine_delegated_draft_available**
- Pool asset count: `15`
- Selected asset count: `13`
- Liquidity buffer: `0.0`%
- Liquidity buffer source: `portfolio_settings.liquidity_buffer_ratio_pct`
- Daily Quant reference source: `supabase_live`
- Base target source: `stock_meta[ticker].target_weight`
- Front-end MC% target used: `False`
- Cloud target available count: `14`
- Cloud target missing count: `1`
- Daily Quant / MC risk mode: `high_tail_pressure`
- Synthetic risk available: `True`
- Monte Carlo reference available: `True`
- MC fragile nodes: `3`
- Target asset weight sum: `99.9998`%
- Draft line count: `12`
- Price-quality excluded lines: `0 `
- Blockers: `0`
- Warnings: `17`
- Trade signal enabled: `False`
- Execution permission: `False`
- Broker submission enabled: `False`

## Boundary
- v10.5 is an integrated delegated machine draft, not a broker order and not a human-confirmed ticket.
- Target weights use Supabase stock_meta[ticker].target_weight / 雲端% as base target weights.
- Daily Quant / Monte Carlo are risk-adjustment references only; this version does not consume the browser-only MC% target column.
- Holdings-table current prices may be used for delegated sizing; missing prices cannot generate BUY/SELL draft lines. Internal sells may fund buys even when explicit cash balance is missing.
