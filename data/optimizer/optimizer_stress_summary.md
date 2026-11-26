# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -26.194% | -18.046% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.373% | -13.196% | 27.64% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -16.706% | -11.508% | 34.69% |
| riskfolio_hrp_mv | Riskfolio-Lib | -11.901% | -7.902% | 46.4% |
| skfolio_cvar_minimize | skfolio/baseline | -4.359% | -3.287% | 77.97% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.359% | -3.287% | 77.97% |
| scipy_min_variance_fallback | skfolio/baseline | -2.55% | -1.901% | 80.21% |
| riskfolio_min_variance | Riskfolio-Lib | -2.537% | -1.951% | 80.14% |
| skfolio_min_variance | skfolio/baseline | -2.532% | -1.946% | 80.14% |