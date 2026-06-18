# v1.1.2 Risk / Optimizer Boundary Cleanup

## Purpose

Clarify the functional boundary between the Risk tab and Optimizer tab.

- Risk tab answers: **What is the current portfolio risk state?**
- Optimizer tab answers: **Are candidate rebalancing drafts reviewable, blocked, or watch-only?**

## UI changes

- Renamed the Risk toolbar headline to `風控｜投組風險診斷`.
- Renamed the Optimizer toolbar headline to `最佳化實驗室｜候選方案與交易邊界`.
- Risk toolbar now shows synthetic risk data availability and sample confidence.
- Optimizer toolbar now shows candidate draft count and a watch-only/non-trade status.
- Optimizer reading order now emphasizes candidate boundaries, formal draft blockers, alpha/constraint validation, and trade-ticket safety.
- Added an explicit boundary note inside the Optimizer tab.

## Boundary

This patch changes UI copy and card hierarchy only.

It does not change:

- Risk calculations
- v10.5 target weights
- v10.5.3 target thesis
- Trade-ticket generation
- Execution permission
- Broker submission

Execution remains disabled.
