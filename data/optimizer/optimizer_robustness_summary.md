# Optimizer Robustness v1.4

- Status: `OK`
- Strict sample: `548`
- Period: `2025-05-28 → 2026-11-26`
- Asset count: `15`

## Windows

| Window | Status | Sample | Period / Reason |
|---|---:|---:|---|
| 6M | OK | 126 | 2026-07-24 → 2026-11-26 |
| 1Y | OK | 252 | 2026-03-20 → 2026-11-26 |
| FULL_STRICT | OK | 548 | 2025-05-28 → 2026-11-26 |
| 2Y | OK | 504 | 2025-07-11 → 2026-11-26 |
| 3Y | OK | 548 | 2025-05-28 → 2026-11-26 |

## Method stability

| Method | Verdict | Available windows | Avg pairwise turnover | Max weight range | ES95 range | Ann vol range |
|---|---:|---:|---:|---:|---:|---:|
| current_weight | 穩定 | 5 | 0.0% | 0.0% | 0.505% | 1.79% |
| inverse_vol_baseline | 穩定 | 5 | 5.29% | 6.89% | 0.159% | 0.55% |
| riskfolio_cvar_minimize | 可觀察 | 5 | 11.22% | 17.06% | 0.217% | 1.34% |
| riskfolio_hrp_mv | 不穩定 | 5 | 19.64% | 31.96% | 0.469% | 2.74% |
| riskfolio_min_variance | 穩定 | 5 | 4.53% | 4.32% | 0.205% | 1.37% |
| riskfolio_risk_parity_mv | 可觀察 | 5 | 12.56% | 20.8% | 0.258% | 2.16% |
| scipy_min_variance_fallback | 穩定 | 5 | 4.52% | 3.79% | 0.204% | 1.37% |
| skfolio_cvar_minimize | 可觀察 | 5 | 11.22% | 17.06% | 0.217% | 1.34% |
| skfolio_min_variance | 穩定 | 5 | 4.55% | 4.33% | 0.205% | 1.37% |