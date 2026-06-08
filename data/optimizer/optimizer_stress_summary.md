# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.336% | -17.628% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -20.693% | -14.164% | 22.58% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -19.692% | -13.623% | 28.12% |
| riskfolio_hrp_mv | Riskfolio-Lib | -14.384% | -9.805% | 38.88% |
| skfolio_cvar_minimize | skfolio/baseline | -6.473% | -4.785% | 71.79% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -6.473% | -4.785% | 71.79% |
| scipy_min_variance_fallback | skfolio/baseline | -3.922% | -2.961% | 77.92% |
| skfolio_min_variance | skfolio/baseline | -3.691% | -2.806% | 77.24% |
| riskfolio_min_variance | Riskfolio-Lib | -3.687% | -2.804% | 77.24% |