# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `381`
- Period: `2025-05-28 → 2026-06-12`
- Asset count: `14`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-02-07 → 2026-06-12 |
| 1Y | OK | 252 | 2025-10-04 → 2026-06-12 |
| FULL_STRICT | OK | 381 | 2025-05-28 → 2026-06-12 |
| 2Y | OK | 381 | 2025-05-28 → 2026-06-12 |
| 3Y | UNAVAILABLE | 381 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.289% | 1.24% |
| inverse_vol_baseline | 穩定 | 4 | 5.41% | 6.75% | 0.13% | 0.48% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 11.22% | 11.96% | 0.252% | 1.18% |
| riskfolio_hrp_mv | 可觀察 | 4 | 12.54% | 20.71% | 0.278% | 1.78% |
| riskfolio_min_variance | 穩定 | 4 | 5.71% | 3.83% | 0.238% | 1.21% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 8.57% | 14.23% | 0.121% | 0.67% |
| scipy_min_variance_fallback | 穩定 | 4 | 5.66% | 4.1% | 0.234% | 1.21% |
| skfolio_cvar_minimize | 可觀察 | 4 | 11.22% | 11.96% | 0.252% | 1.18% |
| skfolio_min_variance | 穩定 | 4 | 5.72% | 3.84% | 0.238% | 1.21% |