# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -26.176% | -18.032% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.373% | -13.196% | 27.62% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -16.707% | -11.51% | 34.67% |
| riskfolio_hrp_mv | Riskfolio-Lib | -11.903% | -7.903% | 46.38% |
| skfolio_cvar_minimize | skfolio/baseline | -4.359% | -3.287% | 77.96% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.359% | -3.287% | 77.96% |
| scipy_min_variance_fallback | skfolio/baseline | -2.554% | -1.905% | 80.19% |
| riskfolio_min_variance | Riskfolio-Lib | -2.539% | -1.954% | 80.13% |
| skfolio_min_variance | skfolio/baseline | -2.534% | -1.949% | 80.13% |