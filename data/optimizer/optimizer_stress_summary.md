# Optimizer Stress Test v1.7

- Status: `OK`
- Candidate count: `9`

| Candidate | Source | Worst scenario | Average scenario | Turnover vs current |
|---|---:|---:|---:|---:|
| current_weight | skfolio/baseline | -25.316% | -17.508% | 0.0% |
| inverse_vol_baseline | skfolio/baseline | -19.374% | -13.133% | 26.27% |
| riskfolio_risk_parity_mv | Riskfolio-Lib | -17.937% | -12.266% | 29.44% |
| riskfolio_hrp_mv | Riskfolio-Lib | -13.613% | -9.056% | 41.11% |
| skfolio_cvar_minimize | skfolio/baseline | -3.407% | -2.689% | 75.29% |
| riskfolio_cvar_minimize | Riskfolio-Lib | -3.407% | -2.689% | 75.29% |
| riskfolio_min_variance | Riskfolio-Lib | -2.267% | -1.809% | 77.44% |
| skfolio_min_variance | skfolio/baseline | -2.265% | -1.805% | 77.48% |
| scipy_min_variance_fallback | skfolio/baseline | -2.226% | -1.722% | 77.92% |