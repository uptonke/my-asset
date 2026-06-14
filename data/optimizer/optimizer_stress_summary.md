# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -24.939% | -17.3% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.922% | -13.56% | 22.02% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.502% | -12.723% | 25.14% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.744% | -8.462% | 43.32% |
| skfolio_cvar_minimize | skfolio/baseline | -4.675% | -3.325% | 69.1% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.675% | -3.325% | 69.1% |
| scipy_min_variance_fallback | skfolio/baseline | -3.438% | -2.582% | 75.77% |
| skfolio_min_variance | skfolio/baseline | -3.345% | -2.55% | 75.53% |
| riskfolio_min_variance | Riskfolio-Lib | -3.342% | -2.549% | 75.52% |