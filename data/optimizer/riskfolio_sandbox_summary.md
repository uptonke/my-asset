# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `548`
- Period: `2025-05-28 → 2026-11-26`
- Asset count: `15`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 12.14% | 1.044% | 1.855% | -15.09% | 0.0% |
| inverse_vol_baseline | OK | 9.36% | 0.864% | 1.483% | -9.81% | 27.62% |
| scipy_min_variance_fallback | OK | 4.68% | 0.365% | 0.718% | -2.97% | 80.19% |
| riskfolio_min_variance | OK | 4.68% | 0.357% | 0.717% | -2.97% | 80.13% |
| riskfolio_cvar_minimize | OK | 4.82% | 0.34% | 0.707% | -2.84% | 77.96% |
| riskfolio_risk_parity_mv | OK | 8.17% | 0.75% | 1.311% | -8.91% | 34.67% |
| riskfolio_hrp_mv | OK | 6.45% | 0.596% | 1.017% | -5.14% | 46.38% |