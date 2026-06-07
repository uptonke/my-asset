# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.275% | -17.584% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -20.71% | -14.175% | 22.51% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -19.665% | -13.605% | 28.16% |
| riskfolio_hrp_mv | Riskfolio-Lib | -14.424% | -9.832% | 38.78% |
| skfolio_cvar_minimize | skfolio/baseline | -8.42% | -6.007% | 67.24% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -8.42% | -6.007% | 67.24% |
| scipy_min_variance_fallback | skfolio/baseline | -4.074% | -3.057% | 77.51% |
| skfolio_min_variance | skfolio/baseline | -3.831% | -2.897% | 76.68% |
| riskfolio_min_variance | Riskfolio-Lib | -3.829% | -2.896% | 76.67% |