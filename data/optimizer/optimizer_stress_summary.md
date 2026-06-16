# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.065% | -17.39% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.903% | -13.551% | 22.29% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.489% | -12.714% | 25.31% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.724% | -8.45% | 43.63% |
| skfolio_cvar_minimize | skfolio/baseline | -4.727% | -3.374% | 68.87% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.727% | -3.374% | 68.87% |
| riskfolio_min_variance | Riskfolio-Lib | -3.317% | -2.533% | 76.08% |
| skfolio_min_variance | skfolio/baseline | -3.316% | -2.532% | 76.11% |
| scipy_min_variance_fallback | skfolio/baseline | -3.258% | -2.483% | 77.02% |