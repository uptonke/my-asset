# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.122% | -17.434% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.906% | -13.552% | 22.37% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.483% | -12.71% | 25.42% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.729% | -8.453% | 43.58% |
| skfolio_cvar_minimize | skfolio/baseline | -4.727% | -3.374% | 68.85% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.727% | -3.374% | 68.85% |
| scipy_min_variance_fallback | skfolio/baseline | -3.359% | -2.541% | 76.42% |
| skfolio_min_variance | skfolio/baseline | -3.257% | -2.507% | 76.31% |
| riskfolio_min_variance | Riskfolio-Lib | -3.255% | -2.504% | 76.33% |