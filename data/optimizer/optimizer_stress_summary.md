# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -24.917% | -17.28% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.934% | -13.57% | 21.55% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.621% | -12.805% | 24.43% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.817% | -8.514% | 42.38% |
| skfolio_cvar_minimize | skfolio/baseline | -4.6% | -3.282% | 70.55% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.6% | -3.282% | 70.55% |
| scipy_min_variance_fallback | skfolio/baseline | -3.323% | -2.503% | 75.44% |
| riskfolio_min_variance | Riskfolio-Lib | -3.261% | -2.495% | 75.24% |
| skfolio_min_variance | skfolio/baseline | -3.254% | -2.492% | 75.25% |