# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.028% | -17.364% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.901% | -13.55% | 22.28% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.449% | -12.69% | 25.32% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.702% | -8.437% | 43.7% |
| skfolio_cvar_minimize | skfolio/baseline | -4.727% | -3.374% | 68.85% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.727% | -3.374% | 68.85% |
| scipy_min_variance_fallback | skfolio/baseline | -3.331% | -2.521% | 75.86% |
| skfolio_min_variance | skfolio/baseline | -3.235% | -2.498% | 76.09% |
| riskfolio_min_variance | Riskfolio-Lib | -3.232% | -2.495% | 76.08% |