# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `385`
- Period: `2025-05-28 → 2026-06-16`
- Asset count: `14`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.45% | 1.022% | 1.63% | -5.59% | 0.0% |
| inverse_vol_baseline | OK | 9.64% | 0.901% | 1.42% | -4.54% | 22.32% |
| scipy_min_variance_fallback | OK | 5.09% | 0.377% | 0.752% | -2.74% | 77.06% |
| riskfolio_min_variance | OK | 5.09% | 0.377% | 0.752% | -2.74% | 76.11% |
| riskfolio_cvar_minimize | OK | 5.16% | 0.375% | 0.742% | -2.62% | 68.88% |
| riskfolio_risk_parity_mv | OK | 8.5% | 0.695% | 1.236% | -3.64% | 25.34% |
| riskfolio_hrp_mv | OK | 6.71% | 0.619% | 1.012% | -2.99% | 43.65% |