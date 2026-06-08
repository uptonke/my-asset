# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.319% | -17.619% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -20.7% | -14.17% | 22.62% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -19.701% | -13.631% | 28.14% |
| riskfolio_hrp_mv | Riskfolio-Lib | -14.399% | -9.817% | 38.89% |
| skfolio_cvar_minimize | skfolio/baseline | -8.128% | -5.818% | 70.92% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -8.128% | -5.818% | 70.92% |
| scipy_min_variance_fallback | skfolio/baseline | -3.947% | -2.982% | 77.92% |
| riskfolio_min_variance | Riskfolio-Lib | -3.72% | -2.828% | 77.11% |
| skfolio_min_variance | skfolio/baseline | -3.703% | -2.818% | 77.05% |