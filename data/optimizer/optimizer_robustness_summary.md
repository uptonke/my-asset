# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `383`
- Period: `2025-05-28 → 2026-06-14`
- Asset count: `14`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-02-09 → 2026-06-14 |
| 1Y | OK | 252 | 2025-10-06 → 2026-06-14 |
| FULL_STRICT | OK | 383 | 2025-05-28 → 2026-06-14 |
| 2Y | OK | 383 | 2025-05-28 → 2026-06-14 |
| 3Y | UNAVAILABLE | 383 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.289% | 1.24% |
| inverse_vol_baseline | 穩定 | 4 | 5.39% | 6.67% | 0.13% | 0.5% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 11.22% | 11.96% | 0.252% | 1.17% |
| riskfolio_hrp_mv | 可觀察 | 4 | 12.49% | 20.61% | 0.277% | 1.78% |
| riskfolio_min_variance | 穩定 | 4 | 5.69% | 4.0% | 0.238% | 1.18% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 8.73% | 14.58% | 0.123% | 0.72% |
| scipy_min_variance_fallback | 穩定 | 4 | 5.71% | 4.44% | 0.235% | 1.19% |
| skfolio_cvar_minimize | 可觀察 | 4 | 11.22% | 11.96% | 0.252% | 1.17% |
| skfolio_min_variance | 穩定 | 4 | 5.69% | 4.01% | 0.238% | 1.18% |