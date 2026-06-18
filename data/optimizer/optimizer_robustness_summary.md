# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `387`
- Period: `2025-05-28 → 2026-06-18`
- Asset count: `14`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-02-13 → 2026-06-18 |
| 1Y | OK | 252 | 2025-10-10 → 2026-06-18 |
| FULL_STRICT | OK | 387 | 2025-05-28 → 2026-06-18 |
| 2Y | OK | 387 | 2025-05-28 → 2026-06-18 |
| 3Y | UNAVAILABLE | 387 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.29% | 1.24% |
| inverse_vol_baseline | 穩定 | 4 | 5.37% | 6.77% | 0.13% | 0.53% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 10.63% | 11.33% | 0.271% | 1.19% |
| riskfolio_hrp_mv | 可觀察 | 4 | 12.76% | 21.24% | 0.328% | 1.89% |
| riskfolio_min_variance | 穩定 | 4 | 5.76% | 4.14% | 0.266% | 1.23% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 9.28% | 15.72% | 0.175% | 0.95% |
| scipy_min_variance_fallback | 穩定 | 4 | 6.11% | 4.96% | 0.258% | 1.22% |
| skfolio_cvar_minimize | 可觀察 | 4 | 10.63% | 11.33% | 0.271% | 1.19% |
| skfolio_min_variance | 穩定 | 4 | 5.78% | 4.17% | 0.266% | 1.23% |