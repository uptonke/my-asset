# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.166% | -17.498% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -20.711% | -14.177% | 22.38% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -19.665% | -13.605% | 28.05% |
| riskfolio_hrp_mv | Riskfolio-Lib | -14.425% | -9.833% | 38.68% |
| skfolio_cvar_minimize | skfolio/baseline | -8.42% | -6.007% | 67.19% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -8.42% | -6.007% | 67.19% |
| scipy_min_variance_fallback | skfolio/baseline | -4.071% | -3.055% | 77.46% |
| skfolio_min_variance | skfolio/baseline | -3.83% | -2.895% | 76.62% |
| riskfolio_min_variance | Riskfolio-Lib | -3.827% | -2.894% | 76.61% |