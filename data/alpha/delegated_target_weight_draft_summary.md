# v10.5 Integrated Delegated Target Weight + Daily Quant / Monte Carlo Engine

- Generated: `2026-06-16T15:12:15+00:00`
- Delegated draft status: **machine_delegated_draft_available**
- Pool asset count: `15`
- Selected asset count: `15`
- Liquidity buffer: `0.0`%
- Liquidity buffer source: `portfolio_settings.liquidity_buffer_ratio_pct`
- Daily Quant reference source: `supabase_live`
- Daily Quant / MC risk mode: `high_tail_pressure`
- Synthetic risk available: `True`
- Monte Carlo reference available: `True`
- MC fragile nodes: `3`
- Target asset weight sum: `100.0`%
- Draft line count: `7`
- Price-quality excluded lines: `0 `
- Blockers: `0`
- Warnings: `19`
- Trade signal enabled: `False`
- Execution permission: `False`
- Broker submission enabled: `False`

## Boundary
- v10.5 is an integrated delegated machine draft, not a broker order and not a human-confirmed ticket.
- Target weights are generated this run from current assets, ranking priors, alpha research scores, Daily Quant synthetic risk context, Monte Carlo fragile-node penalties, liquidity buffer and unit constraints.
- Daily Quant / Monte Carlo now influence target weights before normalization; they are not only a post-hoc reference card.
- Holdings-table current prices may be used for delegated sizing; missing prices cannot generate BUY/SELL draft lines. Internal sells may fund buys even when explicit cash balance is missing.
