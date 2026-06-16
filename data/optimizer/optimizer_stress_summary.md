# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.083% | -17.404% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.904% | -13.551% | 22.32% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.489% | -12.714% | 25.34% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.726% | -8.452% | 43.65% |
| skfolio_cvar_minimize | skfolio/baseline | -4.727% | -3.374% | 68.88% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.727% | -3.374% | 68.88% |
| skfolio_min_variance | skfolio/baseline | -3.319% | -2.535% | 76.11% |
| riskfolio_min_variance | Riskfolio-Lib | -3.318% | -2.534% | 76.11% |
| scipy_min_variance_fallback | skfolio/baseline | -3.256% | -2.482% | 77.07% |