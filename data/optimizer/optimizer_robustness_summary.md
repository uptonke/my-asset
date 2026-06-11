# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `380`
- Period: `2025-05-28 → 2026-06-11`
- Asset count: `14`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-02-06 → 2026-06-11 |
| 1Y | OK | 252 | 2025-10-03 → 2026-06-11 |
| FULL_STRICT | OK | 380 | 2025-05-28 → 2026-06-11 |
| 2Y | OK | 380 | 2025-05-28 → 2026-06-11 |
| 3Y | UNAVAILABLE | 380 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.264% | 1.68% |
| inverse_vol_baseline | 穩定 | 4 | 5.42% | 7.18% | 0.111% | 0.5% |
| riskfolio_cvar_minimize | 穩定 | 4 | 9.25% | 9.98% | 0.275% | 1.2% |
| riskfolio_hrp_mv | 可觀察 | 4 | 13.2% | 22.02% | 0.321% | 1.78% |
| riskfolio_min_variance | 穩定 | 4 | 5.63% | 4.35% | 0.261% | 1.22% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 8.6% | 14.62% | 0.114% | 0.54% |
| scipy_min_variance_fallback | 穩定 | 4 | 5.61% | 4.47% | 0.26% | 1.22% |
| skfolio_cvar_minimize | 穩定 | 4 | 9.25% | 9.98% | 0.275% | 1.2% |
| skfolio_min_variance | 穩定 | 4 | 5.63% | 4.34% | 0.261% | 1.22% |