# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.241% | -17.557% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -20.711% | -14.176% | 22.47% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -19.666% | -13.606% | 28.13% |
| riskfolio_hrp_mv | Riskfolio-Lib | -14.425% | -9.833% | 38.75% |
| skfolio_cvar_minimize | skfolio/baseline | -8.42% | -6.007% | 67.22% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -8.42% | -6.007% | 67.22% |
| scipy_min_variance_fallback | skfolio/baseline | -4.074% | -3.057% | 77.5% |
| skfolio_min_variance | skfolio/baseline | -3.831% | -2.896% | 76.66% |
| riskfolio_min_variance | Riskfolio-Lib | -3.829% | -2.896% | 76.65% |