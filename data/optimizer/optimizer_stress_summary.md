# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.043% | -17.375% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.901% | -13.55% | 22.29% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.449% | -12.69% | 25.34% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.704% | -8.438% | 43.72% |
| skfolio_cvar_minimize | skfolio/baseline | -4.727% | -3.374% | 68.85% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.727% | -3.374% | 68.85% |
| scipy_min_variance_fallback | skfolio/baseline | -3.324% | -2.518% | 75.81% |
| skfolio_min_variance | skfolio/baseline | -3.231% | -2.496% | 76.04% |
| riskfolio_min_variance | Riskfolio-Lib | -3.227% | -2.492% | 76.01% |