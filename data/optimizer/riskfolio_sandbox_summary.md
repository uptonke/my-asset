# Riskfolio-Lib Sandbox v1.2

- Status: `OK`
- Mode: `sandbox_only`
- Strict sample: `386`
- Period: `2025-05-28 → 2026-06-17`
- Asset count: `14`

| Portfolio | Status | Ann Vol | VaR95 | ES95 | MDD | Turnover vs Current |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | OK | 11.43% | 1.019% | 1.625% | -5.56% | 0.0% |
| inverse_vol_baseline | OK | 9.64% | 0.898% | 1.42% | -4.54% | 22.3% |
| scipy_min_variance_fallback | OK | 5.08% | 0.373% | 0.751% | -2.73% | 75.91% |
| riskfolio_min_variance | OK | 5.08% | 0.377% | 0.752% | -2.76% | 76.15% |
| riskfolio_cvar_minimize | OK | 5.15% | 0.375% | 0.742% | -2.62% | 68.83% |
| riskfolio_risk_parity_mv | OK | 8.5% | 0.696% | 1.235% | -3.64% | 25.33% |
| riskfolio_hrp_mv | OK | 6.71% | 0.616% | 1.011% | -2.99% | 43.69% |