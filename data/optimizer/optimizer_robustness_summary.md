# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `376`
- Period: `2025-05-28 → 2026-06-08`
- Asset count: `16`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-02-02 → 2026-06-08 |
| 1Y | OK | 252 | 2025-09-29 → 2026-06-08 |
| FULL_STRICT | OK | 376 | 2025-05-28 → 2026-06-08 |
| 2Y | OK | 376 | 2025-05-28 → 2026-06-08 |
| 3Y | UNAVAILABLE | 376 | strict sample too short for this window |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 4 | 0.0% | 0.0% | 0.372% | 2.25% |
| inverse_vol_baseline | 穩定 | 4 | 5.06% | 6.47% | 0.138% | 0.8% |
| riskfolio_cvar_minimize | 可觀察 | 4 | 14.85% | 19.11% | 0.241% | 1.72% |
| riskfolio_hrp_mv | 可觀察 | 4 | 14.76% | 18.08% | 0.255% | 1.45% |
| riskfolio_min_variance | 穩定 | 4 | 6.01% | 4.31% | 0.241% | 1.16% |
| riskfolio_risk_parity_mv | 可觀察 | 4 | 9.14% | 15.87% | 0.057% | 0.38% |
| scipy_min_variance_fallback | 穩定 | 4 | 6.42% | 5.48% | 0.247% | 1.17% |
| skfolio_cvar_minimize | 可觀察 | 4 | 14.85% | 19.11% | 0.241% | 1.72% |
| skfolio_min_variance | 穩定 | 4 | 6.04% | 4.33% | 0.241% | 1.16% |