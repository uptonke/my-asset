# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `439`
- Period: `2025-05-28 → 2026-08-10`
- Asset count: `13`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.62% | 1.048% | 1.656% | -6.27% | 0.0% |
| inverse_vol_baseline | OK | 9.23% | 0.857% | 1.358% | -4.51% | 26.27% |
| scipy_min_variance_fallback | OK | 4.94% | 0.344% | 0.743% | -3.0% | 77.92% |
| riskfolio_min_variance | OK | 4.94% | 0.346% | 0.743% | -3.01% | 77.44% |
| riskfolio_cvar_minimize | OK | 5.0% | 0.357% | 0.739% | -3.07% | 75.29% |
| riskfolio_risk_parity_mv | OK | 8.35% | 0.757% | 1.234% | -3.75% | 29.44% |
| riskfolio_hrp_mv | OK | 6.99% | 0.61% | 1.046% | -3.33% | 41.11% |