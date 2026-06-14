# v10.3 Delegated Target Weight & Draft Generator

- Generated: `2026-06-14T16:41:30+00:00`
- Delegated draft status: **machine_delegated_draft_available**
- Pool asset count: `15`
- Selected asset count: `15`
- Liquidity buffer: `5.0`%
- Target asset weight sum: `94.9999`%
- Draft line count: `5`
- Price-quality excluded lines: `0 `
- Blockers: `0`
- Warnings: `18`
- Trade signal enabled: `False`
- Execution permission: `False`
- Broker submission enabled: `False`

## Boundary
- v10.3 is a delegated machine draft, not a broker order and not a human-confirmed ticket.
- The target weights are generated this run from current assets, ranking priors, alpha research scores, liquidity buffer and unit constraints. Holdings-table current prices may be used for delegated sizing; missing prices cannot generate BUY/SELL draft lines. Internal sells may fund buys even when explicit cash balance is missing.
