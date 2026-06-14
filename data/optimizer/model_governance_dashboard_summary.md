# Model Governance Dashboard v3.4

Generated: `2026-06-14T05:49:05+00:00`

## Safety boundary

- 追蹤模型版本、失效條件、樣本品質、過度最佳化風險。
- 不是交易指令；不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。

## Summary

- Governance score: `92`
- Verdict: `watch_only_with_governance_warnings`
- Critical flags: `0`
- Warning flags: `1`
- Missing models: `0`

## Model registry

| Version | Model | Exists | Status | Safe mode | Governance |
|---|---|---:|---|---:|---|
| `v1.0` | skfolio Sandbox | True | `OK` | True | `ok` |
| `v1.1` | Riskfolio Dependency Sandbox | True | `OK` | True | `ok` |
| `v1.2` | Riskfolio Optimizer Sandbox | True | `OK` | True | `ok` |
| `v1.4` | Optimizer Robustness Check | True | `OK` | True | `ok` |
| `v1.7` | Stress Test Optimizer Weights | True | `OK` | True | `ok` |
| `v2.0` | Portfolio Optimizer Decision Center | True | `OK` | True | `ok` |
| `v2.1` | Rebalance Candidate Generator | True | `OK` | True | `ok` |
| `v2.2` | Risk Reduction Simulator | True | `OK` | True | `ok` |
| `v2.3` | Constraint-Aware Rebalance Sandbox | True | `OK` | True | `ok` |
| `v2.4` | Human Approval Layer | True | `OK` | True | `ok` |
| `v2.5` | Action Audit Trail | True | `OK` | True | `ok` |
| `v3.0` | Regime-Aware Optimizer | True | `OK` | True | `ok` |
| `v3.1` | Bayesian / Black-Litterman Sandbox | True | `OK` | True | `ok` |
| `v3.2` | Expected Return Model | True | `OK` | True | `ok` |
| `v3.3` | Walk-forward Backtest | True | `OK` | True | `ok` |

## Governance flags

- `warning` / `three_year_window_unavailable` — 樣本品質限制：three_year_window_unavailable

## Failure conditions

- Any execution_permission=true in sandbox outputs.
- Expected return absolute forecast or maximum Sharpe optimization becomes enabled before validation.
- Walk-forward backtest is proxy-only or fold count remains too low.
- 3Y robustness window unavailable while model is promoted beyond watch-only.
- Black-Litterman view engine accepts arbitrary subjective views.
- High-turnover drafts are promoted without explicit manual approval.
