# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.378% | -17.654% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -20.687% | -14.161% | 22.89% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -19.698% | -13.628% | 28.29% |
| riskfolio_hrp_mv | Riskfolio-Lib | -14.379% | -9.804% | 39.06% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -7.894% | -5.657% | 69.59% |
| skfolio_cvar_minimize | skfolio/baseline | -7.881% | -5.649% | 69.61% |
| scipy_min_variance_fallback | skfolio/baseline | -3.994% | -3.003% | 77.7% |
| skfolio_min_variance | skfolio/baseline | -3.755% | -2.84% | 77.1% |
| riskfolio_min_variance | Riskfolio-Lib | -3.752% | -2.838% | 77.09% |