# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -24.913% | -17.277% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.917% | -13.558% | 21.96% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.529% | -12.743% | 25.02% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.726% | -8.451% | 43.3% |
| skfolio_cvar_minimize | skfolio/baseline | -4.675% | -3.325% | 68.99% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.675% | -3.325% | 68.99% |
| scipy_min_variance_fallback | skfolio/baseline | -3.392% | -2.546% | 75.2% |
| riskfolio_min_variance | Riskfolio-Lib | -3.3% | -2.519% | 75.3% |
| skfolio_min_variance | skfolio/baseline | -3.287% | -2.513% | 75.32% |