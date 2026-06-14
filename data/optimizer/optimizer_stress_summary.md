# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -24.951% | -17.309% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.922% | -13.56% | 22.03% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -18.507% | -12.726% | 25.15% |
| riskfolio_hrp_mv | Riskfolio-Lib | -12.745% | -8.463% | 43.32% |
| skfolio_cvar_minimize | skfolio/baseline | -4.675% | -3.325% | 69.11% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -4.675% | -3.325% | 69.11% |
| scipy_min_variance_fallback | skfolio/baseline | -3.437% | -2.58% | 75.9% |
| skfolio_min_variance | skfolio/baseline | -3.339% | -2.546% | 75.65% |
| riskfolio_min_variance | Riskfolio-Lib | -3.336% | -2.544% | 75.64% |