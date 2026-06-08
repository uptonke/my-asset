# v9.3 Gate Failure & Trade Sizing Diagnostics

This module explains why formal rebalance drafts or manual trade ticket drafts are blocked.

It reads:

- `data/alpha/formal_draft_pass_conditions_latest.json`
- `data/alpha/manual_approval_input_latest.json`
- `data/alpha/trading_constraints_snapshot_latest.json`
- `data/alpha/formal_rebalance_draft_gate_latest.json`
- `data/alpha/manual_trade_ticket_latest.json`
- `data/alpha/paper_trade_tracker_latest.json`

It outputs:

- `data/alpha/trade_sizing_diagnostics_latest.json`
- `data/alpha/trade_sizing_diagnostics_summary.md`

## Boundary

v9.3 is diagnostic-only. It does not approve trades, does not create buy/sell signals, does not submit broker orders, and does not enable execution.
