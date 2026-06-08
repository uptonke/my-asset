# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-08T14:36:10+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.6% | 11.1% | -25.378% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.18 | 1.386% | 9.27% | -20.687% | 22.89% | 穩定 | ES95 較目前改善 0.214 個百分點。；年化波動較目前降低 1.83 個百分點。；最差壓力情境較目前改善 4.69 個百分點。；跨樣本穩健性標記為穩定。；需要 22.89% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -7.6 | 0.756% | 5.07% | -3.994% | 77.7% | 穩定 | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 6.03 個百分點。；最差壓力情境較目前改善 21.38 個百分點。；跨樣本穩健性標記為穩定。；需要 77.70% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -7.6 | 0.756% | 5.07% | -3.755% | 77.1% | 穩定 | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 6.03 個百分點。；最差壓力情境較目前改善 21.62 個百分點。；跨樣本穩健性標記為穩定。；需要 77.10% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -2.4 | 0.724% | 5.65% | -7.881% | 69.61% | 可觀察 | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 5.45 個百分點。；最差壓力情境較目前改善 17.50 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.61% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -7.6 | 0.756% | 5.07% | -3.752% | 77.09% | 穩定 | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 6.03 個百分點。；最差壓力情境較目前改善 21.63 個百分點。；跨樣本穩健性標記為穩定。；需要 77.09% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -2.43 | 0.724% | 5.66% | -7.894% | 69.59% | 可觀察 | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 5.44 個百分點。；最差壓力情境較目前改善 17.48 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.59% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 15.73 | 1.198% | 8.3% | -19.698% | 28.29% | 可觀察 | ES95 較目前改善 0.402 個百分點。；年化波動較目前降低 2.80 個百分點。；最差壓力情境較目前改善 5.68 個百分點。；跨樣本穩健性僅為可觀察。；需要 28.29% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 9.04 | 1.06% | 7.03% | -14.379% | 39.06% | 可觀察 | ES95 較目前改善 0.540 個百分點。；年化波動較目前降低 4.07 個百分點。；最差壓力情境較目前改善 11.00 個百分點。；跨樣本穩健性僅為可觀察。；需要 39.06% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
