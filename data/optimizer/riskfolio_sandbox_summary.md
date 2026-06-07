# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `375`
- Period: `2025-05-28 → 2026-06-07`
- Asset count: `16`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 10.94% | 0.966% | 1.567% | -5.26% | 0.0% |
| inverse_vol_baseline | OK | 9.26% | 0.824% | 1.374% | -4.99% | 22.47% |
| scipy_min_variance_fallback | OK | 5.07% | 0.342% | 0.751% | -2.61% | 77.5% |
| riskfolio_min_variance | OK | 5.07% | 0.354% | 0.755% | -2.66% | 76.65% |
| riskfolio_cvar_minimize | OK | 5.69% | 0.389% | 0.716% | -2.48% | 67.22% |
| riskfolio_risk_parity_mv | OK | 8.28% | 0.71% | 1.185% | -4.09% | 28.13% |
| riskfolio_hrp_mv | OK | 7.02% | 0.658% | 1.048% | -3.21% | 38.75% |