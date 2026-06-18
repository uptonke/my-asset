# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `387`
- Period: `2025-05-28 → 2026-06-18`
- Asset count: `14`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.4% | 1.016% | 1.618% | -5.52% | 0.0% |
| inverse_vol_baseline | OK | 9.66% | 0.92% | 1.422% | -4.54% | 22.26% |
| scipy_min_variance_fallback | OK | 5.07% | 0.373% | 0.751% | -2.73% | 76.29% |
| riskfolio_min_variance | OK | 5.07% | 0.375% | 0.752% | -2.75% | 75.88% |
| riskfolio_cvar_minimize | OK | 5.15% | 0.375% | 0.742% | -2.62% | 68.74% |
| riskfolio_risk_parity_mv | OK | 8.51% | 0.716% | 1.239% | -3.63% | 25.07% |
| riskfolio_hrp_mv | OK | 6.71% | 0.635% | 1.011% | -2.99% | 43.74% |