# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -26.17% | -18.027% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.373% | -13.196% | 27.61% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -16.708% | -11.51% | 34.66% |
| riskfolio_hrp_mv | Riskfolio-Lib | -11.903% | -7.903% | 46.38% |
| skfolio_cvar_minimize | skfolio/baseline | -4.359% | -3.287% | 77.96% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.359% | -3.287% | 77.96% |
| scipy_min_variance_fallback | skfolio/baseline | -2.553% | -1.904% | 80.19% |
| riskfolio_min_variance | Riskfolio-Lib | -2.539% | -1.953% | 80.13% |
| skfolio_min_variance | skfolio/baseline | -2.534% | -1.948% | 80.13% |