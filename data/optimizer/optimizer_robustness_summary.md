# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `386`
- Period: `2025-05-28 → 2026-06-17`
- Asset count: `14`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-02-12 → 2026-06-17 |
| 1Y | OK | 252 | 2025-10-09 → 2026-06-17 |
| FULL_STRICT | OK | 386 | 2025-05-28 → 2026-06-17 |
| 2Y | OK | 386 | 2025-05-28 → 2026-06-17 |
| 3Y | UNAVAILABLE | 386 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.29% | 1.33% |
| inverse_vol_baseline | 穩定 | 4 | 5.41% | 6.77% | 0.131% | 0.52% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 10.89% | 12.11% | 0.251% | 1.16% |
| riskfolio_hrp_mv | 可觀察 | 4 | 12.55% | 20.8% | 0.28% | 1.77% |
| riskfolio_min_variance | 穩定 | 4 | 5.52% | 4.0% | 0.238% | 1.18% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 8.82% | 14.71% | 0.125% | 0.73% |
| scipy_min_variance_fallback | 穩定 | 4 | 5.94% | 4.48% | 0.229% | 1.16% |
| skfolio_cvar_minimize | 可觀察 | 4 | 10.89% | 12.11% | 0.251% | 1.16% |
| skfolio_min_variance | 穩定 | 4 | 5.55% | 4.02% | 0.238% | 1.18% |