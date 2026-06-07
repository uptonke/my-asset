# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-07T05:59:59+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.56% | 10.89% | -25.166% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 15.81 | 1.374% | 9.26% | -20.711% | 22.38% | 穩定 | ES95 較目前改善 0.186 個百分點。；年化波動較目前降低 1.63 個百分點。；最差壓力情境較目前改善 4.46 個百分點。；跨樣本穩健性標記為穩定。；需要 22.38% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -9.18 | 0.751% | 5.07% | -4.071% | 77.46% | 穩定 | ES95 較目前改善 0.809 個百分點。；年化波動較目前降低 5.82 個百分點。；最差壓力情境較目前改善 21.09 個百分點。；跨樣本穩健性標記為穩定。；需要 77.46% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -9.27 | 0.754% | 5.07% | -3.83% | 76.62% | 穩定 | ES95 較目前改善 0.806 個百分點。；年化波動較目前降低 5.82 個百分點。；最差壓力情境較目前改善 21.34 個百分點。；跨樣本穩健性標記為穩定。；需要 76.62% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -3.68 | 0.716% | 5.69% | -8.42% | 67.19% | 可觀察 | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 5.20 個百分點。；最差壓力情境較目前改善 16.75 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.19% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -9.3 | 0.755% | 5.07% | -3.827% | 76.61% | 穩定 | ES95 較目前改善 0.805 個百分點。；年化波動較目前降低 5.82 個百分點。；最差壓力情境較目前改善 21.34 個百分點。；跨樣本穩健性標記為穩定。；需要 76.61% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -3.68 | 0.716% | 5.69% | -8.42% | 67.19% | 可觀察 | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 5.20 個百分點。；最差壓力情境較目前改善 16.75 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.19% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 14.35 | 1.185% | 8.28% | -19.665% | 28.05% | 可觀察 | ES95 較目前改善 0.375 個百分點。；年化波動較目前降低 2.61 個百分點。；最差壓力情境較目前改善 5.50 個百分點。；跨樣本穩健性僅為可觀察。；需要 28.05% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 7.58 | 1.048% | 7.02% | -14.425% | 38.68% | 可觀察 | ES95 較目前改善 0.512 個百分點。；年化波動較目前降低 3.87 個百分點。；最差壓力情境較目前改善 10.74 個百分點。；跨樣本穩健性僅為可觀察。；需要 38.68% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
