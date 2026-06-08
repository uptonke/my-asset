# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `376`
- Period: `2025-05-28 → 2026-06-08`
- Asset count: `16`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.03% | 0.97% | 1.587% | -5.32% | 0.0% |
| inverse_vol_baseline | OK | 9.28% | 0.822% | 1.386% | -4.99% | 22.61% |
| scipy_min_variance_fallback | OK | 5.08% | 0.353% | 0.755% | -2.62% | 77.92% |
| riskfolio_min_variance | OK | 5.07% | 0.371% | 0.755% | -2.67% | 77.11% |
| riskfolio_cvar_minimize | OK | 5.8% | 0.415% | 0.724% | -2.55% | 70.92% |
| riskfolio_risk_parity_mv | OK | 8.31% | 0.711% | 1.198% | -4.1% | 28.14% |
| riskfolio_hrp_mv | OK | 7.04% | 0.655% | 1.059% | -3.2% | 38.89% |