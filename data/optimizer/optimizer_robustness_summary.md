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
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.292% | 1.26% |
| inverse_vol_baseline | 穩定 | 4 | 5.39% | 6.73% | 0.131% | 0.51% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 10.89% | 12.11% | 0.251% | 1.17% |
| riskfolio_hrp_mv | 可觀察 | 4 | 12.24% | 20.63% | 0.278% | 1.77% |
| riskfolio_min_variance | 穩定 | 4 | 5.5% | 3.9% | 0.238% | 1.18% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 8.66% | 14.4% | 0.12% | 0.71% |
| scipy_min_variance_fallback | 穩定 | 4 | 5.46% | 4.56% | 0.237% | 1.18% |
| skfolio_cvar_minimize | 可觀察 | 4 | 10.89% | 12.11% | 0.251% | 1.17% |
| skfolio_min_variance | 穩定 | 4 | 5.55% | 3.91% | 0.238% | 1.18% |