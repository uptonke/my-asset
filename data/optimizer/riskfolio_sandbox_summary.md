# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `382`
- Period: `2025-05-28 → 2026-06-14`
- Asset count: `14`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.38% | 1.013% | 1.616% | -5.51% | 0.0% |
| inverse_vol_baseline | OK | 9.67% | 0.909% | 1.421% | -4.54% | 22.03% |
| scipy_min_variance_fallback | OK | 5.1% | 0.377% | 0.751% | -2.72% | 75.9% |
| riskfolio_min_variance | OK | 5.1% | 0.378% | 0.752% | -2.75% | 75.64% |
| riskfolio_cvar_minimize | OK | 5.18% | 0.394% | 0.743% | -2.56% | 69.11% |
| riskfolio_risk_parity_mv | OK | 8.52% | 0.692% | 1.236% | -3.64% | 25.15% |
| riskfolio_hrp_mv | OK | 6.74% | 0.626% | 1.012% | -2.98% | 43.32% |