# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `439`
- Period: `2025-05-28 → 2026-08-10`
- Asset count: `13`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-04-06 → 2026-08-10 |
| 1Y | OK | 252 | 2025-12-01 → 2026-08-10 |
| FULL_STRICT | OK | 439 | 2025-05-28 → 2026-08-10 |
| 2Y | OK | 439 | 2025-05-28 → 2026-08-10 |
| 3Y | UNAVAILABLE | 439 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.123% | 1.21% |
| inverse_vol_baseline | 可觀察 | 4 | 7.88% | 11.26% | 0.367% | 2.36% |
| riskfolio_cvar_minimize | 穩定 | 4 | 5.26% | 4.46% | 0.454% | 2.42% |
| riskfolio_hrp_mv | 不穩定 | 4 | 25.01% | 43.09% | 0.698% | 4.32% |
| riskfolio_min_variance | 穩定 | 4 | 4.9% | 3.74% | 0.428% | 2.46% |
| riskfolio_risk_parity_mv | 不穩定 | 4 | 16.81% | 29.76% | 0.624% | 4.12% |
| scipy_min_variance_fallback | 穩定 | 4 | 5.52% | 3.97% | 0.42% | 2.46% |
| skfolio_cvar_minimize | 穩定 | 4 | 5.26% | 4.46% | 0.454% | 2.42% |
| skfolio_min_variance | 穩定 | 4 | 4.86% | 3.74% | 0.428% | 2.46% |