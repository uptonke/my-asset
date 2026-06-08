# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.329% | -17.626% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -20.699% | -14.169% | 22.63% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -19.7% | -13.631% | 28.15% |
| riskfolio_hrp_mv | Riskfolio-Lib | -14.398% | -9.817% | 38.9% |
| skfolio_cvar_minimize | skfolio/baseline | -8.128% | -5.818% | 70.92% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -8.128% | -5.818% | 70.92% |
| scipy_min_variance_fallback | skfolio/baseline | -3.948% | -2.983% | 77.93% |
| riskfolio_min_variance | Riskfolio-Lib | -3.72% | -2.828% | 77.12% |
| skfolio_min_variance | skfolio/baseline | -3.703% | -2.818% | 77.06% |