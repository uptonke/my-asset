# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `377`
- Period: `2025-05-28 → 2026-06-08`
- Asset count: `16`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-02-03 → 2026-06-08 |
| 1Y | OK | 252 | 2025-09-30 → 2026-06-08 |
| FULL_STRICT | OK | 377 | 2025-05-28 → 2026-06-08 |
| 2Y | OK | 377 | 2025-05-28 → 2026-06-08 |
| 3Y | UNAVAILABLE | 377 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.371% | 2.2% |
| inverse_vol_baseline | 穩定 | 4 | 5.27% | 6.86% | 0.13% | 0.7% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 11.88% | 13.88% | 0.246% | 1.41% |
| riskfolio_hrp_mv | 可觀察 | 4 | 15.2% | 19.21% | 0.269% | 1.62% |
| riskfolio_min_variance | 穩定 | 4 | 6.09% | 4.13% | 0.259% | 1.25% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 9.62% | 16.82% | 0.072% | 0.52% |
| scipy_min_variance_fallback | 穩定 | 4 | 6.53% | 5.44% | 0.256% | 1.25% |
| skfolio_cvar_minimize | 可觀察 | 4 | 11.88% | 13.88% | 0.246% | 1.41% |
| skfolio_min_variance | 穩定 | 4 | 6.09% | 4.14% | 0.259% | 1.25% |