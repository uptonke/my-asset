# v10.0 Human-Confirmed Trade Ticket

v10.0 is the final manual-review ticket layer. It can only prepare a human-confirmed manual-entry ticket when upstream formal draft, manual approval, sizing diagnostics, real-world prices, cash constraints, and explicit human confirmation inputs all pass.

It is not a broker order, not automatic execution, and not buy/sell advice.

## Inputs

- `data/alpha/manual_trade_ticket_latest.json`
- `data/alpha/trade_sizing_diagnostics_latest.json`
- `data/alpha/trade_ticket_explainability_latest.json`
- `data/alpha/manual_approval_console_latest.json`
- `data/alpha/formal_rebalance_draft_gate_latest.json`
- `data/alpha/trading_constraints_snapshot_latest.json`
- `config/manual_approval_override.json`

## Manual confirmation fields

Optional fields in `config/manual_approval_override.json`:

```json
{
  "human_final_confirmation_enabled": false,
  "human_confirmed_ticket_ids": [],
  "human_confirmed_candidate_ids": [],
  "human_confirmation_note": ""
}
```

Defaults should remain disabled unless the user is intentionally preparing a manual-entry review ticket.

## Output

- `data/alpha/human_confirmed_trade_ticket_latest.json`
- `data/alpha/human_confirmed_trade_ticket_summary.md`

## Safety boundary

v10.0 must always keep:

```json
{
  "not_trade_order": true,
  "trade_signal_enabled": false,
  "execution_permission": false,
  "broker_submission_enabled": false,
  "official_rebalance_enabled": false,
  "auto_trade_enabled": false
}
```

If any upstream gate, sizing rule, real-world price check, cash balance, or explicit human confirmation input is missing, v10.0 outputs zero confirmed tickets.
