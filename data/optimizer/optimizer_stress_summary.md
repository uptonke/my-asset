# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.006% | -17.353% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.897% | -13.548% | 22.26% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.42% | -12.672% | 25.07% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.648% | -8.402% | 43.74% |
| skfolio_cvar_minimize | skfolio/baseline | -4.727% | -3.374% | 68.74% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.727% | -3.374% | 68.74% |
| scipy_min_variance_fallback | skfolio/baseline | -3.331% | -2.526% | 76.29% |
| skfolio_min_variance | skfolio/baseline | -3.281% | -2.517% | 75.9% |
| riskfolio_min_variance | Riskfolio-Lib | -3.279% | -2.515% | 75.88% |