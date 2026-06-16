# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `385`
- Period: `2025-05-28 → 2026-06-16`
- Asset count: `14`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-02-11 → 2026-06-16 |
| 1Y | OK | 252 | 2025-10-08 → 2026-06-16 |
| FULL_STRICT | OK | 385 | 2025-05-28 → 2026-06-16 |
| 2Y | OK | 385 | 2025-05-28 → 2026-06-16 |
| 3Y | UNAVAILABLE | 385 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.29% | 1.27% |
| inverse_vol_baseline | 穩定 | 4 | 5.4% | 6.7% | 0.131% | 0.5% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 10.82% | 12.11% | 0.251% | 1.15% |
| riskfolio_hrp_mv | 可觀察 | 4 | 12.17% | 20.49% | 0.277% | 1.75% |
| riskfolio_min_variance | 穩定 | 4 | 5.25% | 4.51% | 0.238% | 1.16% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 8.6% | 14.29% | 0.119% | 0.69% |
| scipy_min_variance_fallback | 穩定 | 4 | 5.92% | 5.46% | 0.234% | 1.15% |
| skfolio_cvar_minimize | 可觀察 | 4 | 10.82% | 12.11% | 0.251% | 1.15% |
| skfolio_min_variance | 穩定 | 4 | 5.24% | 4.51% | 0.238% | 1.16% |