# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `383`
- Period: `2025-05-28 → 2026-06-14`
- Asset count: `14`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.35% | 1.011% | 1.615% | -5.49% | 0.0% |
| inverse_vol_baseline | OK | 9.65% | 0.906% | 1.421% | -4.54% | 22.02% |
| scipy_min_variance_fallback | OK | 5.1% | 0.378% | 0.751% | -2.72% | 75.77% |
| riskfolio_min_variance | OK | 5.09% | 0.379% | 0.752% | -2.75% | 75.52% |
| riskfolio_cvar_minimize | OK | 5.17% | 0.393% | 0.743% | -2.56% | 69.1% |
| riskfolio_risk_parity_mv | OK | 8.51% | 0.692% | 1.236% | -3.63% | 25.14% |
| riskfolio_hrp_mv | OK | 6.73% | 0.624% | 1.012% | -2.98% | 43.32% |