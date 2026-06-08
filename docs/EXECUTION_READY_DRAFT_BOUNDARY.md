# v6-v8 Alpha Validation / Manual Proposal / Execution-Ready Draft Boundary

This repository uses a strict research-only execution boundary.

## v6.0 Alpha Validation Gate

Purpose: validate whether v5 alpha research and rebalance ranking outputs are mature enough to be reviewed.

It checks feature coverage, alpha research rows, rebalance ranking rows, walk-forward evidence, governance status, and safety flags.

A v6 pass/watch label is not a buy signal, sell signal, bullish signal, or allocation recommendation.

## v7.0 Manual Rebalance Proposal

Purpose: convert ranked research candidates into a manual research review queue.

The output is a checklist-oriented proposal, not a trade order. It does not modify holdings, write Supabase, enable broker execution, or authorize any transaction.

## v8.0 Execution-Ready Draft

Purpose: package manually reviewable proposals into pre-execution checklists.

The name means the draft is formatted for human review before any possible manual action. It does not mean the system can submit orders or approve trades.

Required safety flags remain:

- `execution_permission: false`
- `trade_signal_enabled: false`
- `broker_submission_enabled: false`
- `official_rebalance_enabled: false`
- `not_trade_order: true`

## Wording rule

Do not label any v6-v8 output as:

- buy recommendation
- sell recommendation
- bullish signal
- best allocation
- approved trade
- automatic rebalance

Use:

- validation status
- manual research proposal
- pre-execution checklist draft
- blocked / watch-only / further research
