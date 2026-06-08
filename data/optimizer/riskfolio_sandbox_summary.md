# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `377`
- Period: `2025-05-28 → 2026-06-08`
- Asset count: `16`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.09% | 0.98% | 1.6% | -5.4% | 0.0% |
| inverse_vol_baseline | OK | 9.27% | 0.821% | 1.386% | -4.99% | 22.89% |
| scipy_min_variance_fallback | OK | 5.07% | 0.352% | 0.756% | -2.63% | 77.7% |
| riskfolio_min_variance | OK | 5.07% | 0.372% | 0.756% | -2.67% | 77.09% |
| riskfolio_cvar_minimize | OK | 5.66% | 0.397% | 0.724% | -2.54% | 69.59% |
| riskfolio_risk_parity_mv | OK | 8.3% | 0.711% | 1.198% | -4.1% | 28.29% |
| riskfolio_hrp_mv | OK | 7.03% | 0.654% | 1.06% | -3.21% | 39.06% |