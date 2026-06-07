# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.252% | -17.566% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -20.711% | -14.176% | 22.48% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -19.666% | -13.606% | 28.14% |
| riskfolio_hrp_mv | Riskfolio-Lib | -14.425% | -9.833% | 38.76% |
| skfolio_cvar_minimize | skfolio/baseline | -8.42% | -6.007% | 67.23% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -8.42% | -6.007% | 67.23% |
| scipy_min_variance_fallback | skfolio/baseline | -4.073% | -3.057% | 77.5% |
| skfolio_min_variance | skfolio/baseline | -3.831% | -2.896% | 76.67% |
| riskfolio_min_variance | Riskfolio-Lib | -3.828% | -2.895% | 76.66% |