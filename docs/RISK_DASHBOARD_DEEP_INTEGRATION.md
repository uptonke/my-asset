# Risk Dashboard Deep Integration v1.2

## Purpose

This release replaces the risk tab's previous stacked reading-order cards and separate core/attribution cards with a single integrated risk command center.

## Design boundary

The risk tab answers: current portfolio risk, benchmark-relative behavior, factor exposure, sample/source quality.

The optimizer tab answers: candidate rebalance reviewability, blocking reasons, watch-only status, and manual-ticket boundaries.

## What changed

- Core risk, benchmark attribution, payoff / recovery, factor exposure, and source guard now live in one integrated dashboard surface.
- The old reading-order card and separate core / benchmark sections are removed from the primary flow.
- EWMA, Component ES, and HRP-lite remain as diagnostic appendix details, not the main page structure.
- No calculation logic, target weights, trade tickets, or execution permissions are changed.

## Safety boundary

This release is display-only. It does not generate orders, target weights, or trading signals.
