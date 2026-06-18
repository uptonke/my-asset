# Risk / Optimizer Card Layout v1

## Purpose

Consolidates the Risk and Optimizer pages into a clearer reading order without changing the underlying calculation logic, target-weight logic, or execution boundary.

## Risk page grouping

1. Core risk overview
   - Volatility
   - VaR / ES
   - Maximum drawdown
   - Sample quality
   - QuantStats-style metrics

2. Benchmark attribution and factor evidence
   - Release Guard
   - Benchmark attribution
   - Tracking Error / Information Ratio
   - Payoff ratio
   - Drawdown recovery
   - Factor exposure snapshot

3. Technical details
   - EWMA covariance and correlation regime
   - Component ES
   - HRP-lite risk budgeting

4. Legacy quant sandbox
   - Sharpe / PSR
   - SML / CML
   - Jump Diffusion
   - Kelly exposure
   - Conditional / crisis correlation

## Optimizer page grouping

1. Target weights and human-readable thesis
   - v10.0 human-confirmed ticket boundary
   - v10.5.3 target thesis
   - v10.5.1 delegated draft / dual-source target weights

2. Decision summary
   - Governance verdict
   - Further-research counts
   - Regime
   - Audit counts
   - Execution disabled boundary

3. Technical diagnostics and sandbox
   - Dependency checks
   - skfolio / Riskfolio sandboxes
   - Robustness
   - Constraint policy
   - Stress tests
   - Explainability

4. Decision / approval history chain
   - v2.4 through v9 cards
   - Approval, audit, regime, BL, walk-forward, alpha gate, formal gate, paper tracker, manual ticket and explainability history

## Safety boundary

This change is UI-only. It does not enable execution, does not submit broker orders, does not change target-weight calculations, and does not change validation or data pipelines.
