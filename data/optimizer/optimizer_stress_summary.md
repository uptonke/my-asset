# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.347% | -17.641% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -20.698% | -14.168% | 22.65% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -19.7% | -13.63% | 28.17% |
| riskfolio_hrp_mv | Riskfolio-Lib | -14.397% | -9.816% | 38.92% |
| skfolio_cvar_minimize | skfolio/baseline | -8.128% | -5.818% | 70.93% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -8.128% | -5.818% | 70.93% |
| scipy_min_variance_fallback | skfolio/baseline | -3.948% | -2.983% | 77.94% |
| riskfolio_min_variance | Riskfolio-Lib | -3.721% | -2.828% | 77.13% |
| skfolio_min_variance | skfolio/baseline | -3.703% | -2.818% | 77.07% |