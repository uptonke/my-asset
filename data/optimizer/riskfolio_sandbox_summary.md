# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `380`
- Period: `2025-05-28 → 2026-06-11`
- Asset count: `14`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.3% | 1.0% | 1.658% | -5.52% | 0.0% |
| inverse_vol_baseline | OK | 9.64% | 0.911% | 1.467% | -4.55% | 21.55% |
| scipy_min_variance_fallback | OK | 5.13% | 0.391% | 0.776% | -2.74% | 75.44% |
| riskfolio_min_variance | OK | 5.13% | 0.388% | 0.776% | -2.77% | 75.24% |
| riskfolio_cvar_minimize | OK | 5.19% | 0.391% | 0.766% | -2.69% | 70.55% |
| riskfolio_risk_parity_mv | OK | 8.55% | 0.694% | 1.289% | -3.72% | 24.43% |
| riskfolio_hrp_mv | OK | 6.78% | 0.648% | 1.046% | -2.98% | 42.38% |