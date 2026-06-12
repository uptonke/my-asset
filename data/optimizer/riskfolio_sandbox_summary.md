# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `381`
- Period: `2025-05-28 → 2026-06-12`
- Asset count: `14`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.37% | 1.012% | 1.612% | -5.48% | 0.0% |
| inverse_vol_baseline | OK | 9.69% | 0.913% | 1.42% | -4.54% | 21.96% |
| scipy_min_variance_fallback | OK | 5.11% | 0.373% | 0.751% | -2.72% | 75.2% |
| riskfolio_min_variance | OK | 5.11% | 0.376% | 0.752% | -2.75% | 75.3% |
| riskfolio_cvar_minimize | OK | 5.17% | 0.394% | 0.743% | -2.56% | 68.99% |
| riskfolio_risk_parity_mv | OK | 8.54% | 0.691% | 1.235% | -3.63% | 25.02% |
| riskfolio_hrp_mv | OK | 6.75% | 0.628% | 1.011% | -2.98% | 43.3% |