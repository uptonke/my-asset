# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `376`
- Period: `2025-05-28 → 2026-06-08`
- Asset count: `16`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.05% | 0.972% | 1.589% | -5.34% | 0.0% |
| inverse_vol_baseline | OK | 9.28% | 0.822% | 1.386% | -4.99% | 22.65% |
| scipy_min_variance_fallback | OK | 5.08% | 0.353% | 0.755% | -2.62% | 77.94% |
| riskfolio_min_variance | OK | 5.07% | 0.371% | 0.755% | -2.67% | 77.13% |
| riskfolio_cvar_minimize | OK | 5.8% | 0.415% | 0.724% | -2.55% | 70.93% |
| riskfolio_risk_parity_mv | OK | 8.31% | 0.711% | 1.198% | -4.1% | 28.17% |
| riskfolio_hrp_mv | OK | 7.03% | 0.655% | 1.059% | -3.2% | 38.92% |