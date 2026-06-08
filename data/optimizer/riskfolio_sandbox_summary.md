# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `377`
- Period: `2025-05-28 → 2026-06-08`
- Asset count: `16`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.07% | 0.972% | 1.594% | -5.37% | 0.0% |
| inverse_vol_baseline | OK | 9.28% | 0.822% | 1.386% | -4.99% | 22.58% |
| scipy_min_variance_fallback | OK | 5.08% | 0.354% | 0.756% | -2.63% | 77.92% |
| riskfolio_min_variance | OK | 5.07% | 0.372% | 0.756% | -2.67% | 77.24% |
| riskfolio_cvar_minimize | OK | 5.37% | 0.385% | 0.729% | -2.53% | 71.79% |
| riskfolio_risk_parity_mv | OK | 8.32% | 0.71% | 1.199% | -4.1% | 28.12% |
| riskfolio_hrp_mv | OK | 7.03% | 0.655% | 1.06% | -3.21% | 38.88% |