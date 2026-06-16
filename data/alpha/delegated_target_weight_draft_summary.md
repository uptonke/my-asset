# v10.4 Delegated Target Weight & Draft Generator

- Generated: `2026-06-15T15:11:47+00:00`
- Delegated draft status: **machine_delegated_draft_available**
- Pool asset count: `16`
- Selected asset count: `16`
- Liquidity buffer: `0.0`%
- Liquidity buffer source: `portfolio_settings.liquidity_buffer_ratio_pct`
- Target asset weight sum: `100.0001`%
- Draft line count: `4`
- Price-quality excluded lines: `0 `
- Blockers: `0`
- Warnings: `23`
- Trade signal enabled: `False`
- Execution permission: `False`
- Broker submission enabled: `False`

## Boundary
- v10.4 is a delegated machine draft, not a broker order and not a human-confirmed ticket.
- The target weights are generated this run from current assets, ranking priors, alpha research scores, liquidity buffer and unit constraints. Holdings-table current prices may be used for delegated sizing; missing prices cannot generate BUY/SELL draft lines. Internal sells may fund buys even when explicit cash balance is missing.
