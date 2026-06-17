# v10.5.1 Dual Target Blend Engine

- Generated: `2026-06-17T13:42:40+00:00`
- Delegated draft status: **machine_delegated_draft_available**
- Pool asset count: `15`
- Selected asset count: `15`
- Liquidity buffer: `0.0`%
- Liquidity buffer source: `portfolio_settings.liquidity_buffer_ratio_pct`
- Daily Quant reference source: `supabase_live`
- Target source: `50% stock_meta[ticker].target_weight + 50% v10.5 native target`
- v10.5 native candidate: `v5_2_v2_3_from_v2_2_trim_BTC_USD_100pct_to_BOXX`
- Front-end MC% target used: `False`
- Cloud target available count: `14`
- Cloud target missing count: `1`
- Daily Quant / MC risk mode: `high_tail_pressure`
- Synthetic risk available: `True`
- Monte Carlo reference available: `True`
- MC fragile nodes: `3`
- Target asset weight sum: `99.9998`%
- Draft line count: `4`
- Price-quality excluded lines: `0 `
- Blockers: `0`
- Warnings: `30`
- Trade signal enabled: `False`
- Execution permission: `False`
- Broker submission enabled: `False`

## Boundary
- v10.5 is an integrated delegated machine draft, not a broker order and not a human-confirmed ticket.
- Final suggested weights blend Supabase stock_meta[ticker].target_weight / 雲端% and v10.5 native target weights at 50/50.
- Daily Quant / Monte Carlo are used inside the v10.5 native target and risk checks; this version still does not consume the browser-only MC% target column.
- Holdings-table current prices may be used for delegated sizing; missing prices cannot generate BUY/SELL draft lines. Internal sells may fund buys even when explicit cash balance is missing.
