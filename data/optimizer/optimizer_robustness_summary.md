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
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.29% | 1.34% |
| inverse_vol_baseline | 穩定 | 4 | 5.4% | 6.75% | 0.131% | 0.52% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 10.89% | 12.11% | 0.251% | 1.15% |
| riskfolio_hrp_mv | 可觀察 | 4 | 12.52% | 20.73% | 0.28% | 1.76% |
| riskfolio_min_variance | 穩定 | 4 | 5.56% | 3.94% | 0.237% | 1.17% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 8.79% | 14.62% | 0.124% | 0.71% |
| scipy_min_variance_fallback | 穩定 | 4 | 5.91% | 4.43% | 0.228% | 1.16% |
| skfolio_cvar_minimize | 可觀察 | 4 | 10.89% | 12.11% | 0.251% | 1.15% |
| skfolio_min_variance | 穩定 | 4 | 5.59% | 3.99% | 0.237% | 1.17% |