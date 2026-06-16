# v10.4 Delegated Target Weight & Draft Generator

- Generated: `2026-06-16T08:33:45+00:00`
- Delegated draft status: **machine_delegated_draft_available**
- Pool asset count: `15`
- Selected asset count: `15`
- Liquidity buffer: `0.0`%
- Liquidity buffer source: `portfolio_settings.liquidity_buffer_ratio_pct`
- Target asset weight sum: `100.0`%
- Draft line count: `3`
- Price-quality excluded lines: `0 `
- Blockers: `0`
- Warnings: `22`
- Trade signal enabled: `False`
- Execution permission: `False`
- Broker submission enabled: `False`

## Boundary
- v10.4 is a delegated machine draft, not a broker order and not a human-confirmed ticket.
- The target weights are generated this run from current assets, ranking priors, alpha research scores, liquidity buffer and unit constraints. Holdings-table current prices may be used for delegated sizing; missing prices cannot generate BUY/SELL draft lines. Internal sells may fund buys even when explicit cash balance is missing.
