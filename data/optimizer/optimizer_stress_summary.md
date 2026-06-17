# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.027% | -17.366% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.9% | -13.55% | 22.3% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.445% | -12.687% | 25.33% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.701% | -8.436% | 43.69% |
| skfolio_cvar_minimize | skfolio/baseline | -4.727% | -3.374% | 68.83% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.727% | -3.374% | 68.83% |
| scipy_min_variance_fallback | skfolio/baseline | -3.341% | -2.524% | 75.91% |
| skfolio_min_variance | skfolio/baseline | -3.24% | -2.499% | 76.17% |
| riskfolio_min_variance | Riskfolio-Lib | -3.237% | -2.496% | 76.15% |