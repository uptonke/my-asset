# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `375`
- Period: `2025-05-28 → 2026-06-07`
- Asset count: `16`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-02-01 → 2026-06-07 |
| 1Y | OK | 252 | 2025-09-28 → 2026-06-07 |
| FULL_STRICT | OK | 375 | 2025-05-28 → 2026-06-07 |
| 2Y | OK | 375 | 2025-05-28 → 2026-06-07 |
| 3Y | UNAVAILABLE | 375 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.352% | 2.19% |
| inverse_vol_baseline | 穩定 | 4 | 5.02% | 6.36% | 0.119% | 0.74% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 13.78% | 20.38% | 0.233% | 1.63% |
| riskfolio_hrp_mv | 可觀察 | 4 | 14.76% | 17.94% | 0.277% | 1.49% |
| riskfolio_min_variance | 穩定 | 4 | 6.01% | 4.3% | 0.24% | 1.17% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 9.46% | 16.51% | 0.081% | 0.52% |
| scipy_min_variance_fallback | 穩定 | 4 | 6.56% | 5.55% | 0.243% | 1.17% |
| skfolio_cvar_minimize | 可觀察 | 4 | 13.78% | 20.38% | 0.233% | 1.63% |
| skfolio_min_variance | 穩定 | 4 | 6.02% | 4.34% | 0.239% | 1.17% |