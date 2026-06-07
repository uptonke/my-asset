# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `376`
- Period: `2025-05-28 → 2026-06-07`
- Asset count: `16`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 10.94% | 0.966% | 1.568% | -5.27% | 0.0% |
| inverse_vol_baseline | OK | 9.25% | 0.823% | 1.374% | -4.99% | 22.48% |
| scipy_min_variance_fallback | OK | 5.07% | 0.342% | 0.751% | -2.61% | 77.5% |
| riskfolio_min_variance | OK | 5.06% | 0.353% | 0.755% | -2.66% | 76.66% |
| riskfolio_cvar_minimize | OK | 5.68% | 0.389% | 0.716% | -2.48% | 67.23% |
| riskfolio_risk_parity_mv | OK | 8.26% | 0.71% | 1.185% | -4.09% | 28.14% |
| riskfolio_hrp_mv | OK | 7.01% | 0.657% | 1.048% | -3.21% | 38.76% |