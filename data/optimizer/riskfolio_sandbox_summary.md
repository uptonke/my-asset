# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `386`
- Period: `2025-05-28 → 2026-06-17`
- Asset count: `14`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.43% | 1.02% | 1.626% | -5.56% | 0.0% |
| inverse_vol_baseline | OK | 9.64% | 0.898% | 1.42% | -4.54% | 22.28% |
| scipy_min_variance_fallback | OK | 5.08% | 0.373% | 0.751% | -2.73% | 75.87% |
| riskfolio_min_variance | OK | 5.08% | 0.378% | 0.752% | -2.76% | 76.08% |
| riskfolio_cvar_minimize | OK | 5.15% | 0.375% | 0.742% | -2.62% | 68.85% |
| riskfolio_risk_parity_mv | OK | 8.51% | 0.696% | 1.235% | -3.64% | 25.32% |
| riskfolio_hrp_mv | OK | 6.71% | 0.616% | 1.011% | -2.99% | 43.7% |