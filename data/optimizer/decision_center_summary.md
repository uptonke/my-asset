# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-07T07:15:53+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.57% | 10.95% | -25.268% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 16.35 | 1.374% | 9.25% | -20.71% | 22.5% | 穩定 | ES95 較目前改善 0.196 個百分點。；年化波動較目前降低 1.70 個百分點。；最差壓力情境較目前改善 4.56 個百分點。；跨樣本穩健性標記為穩定。；需要 22.50% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -8.73 | 0.751% | 5.07% | -4.073% | 77.51% | 穩定 | ES95 較目前改善 0.819 個百分點。；年化波動較目前降低 5.88 個百分點。；最差壓力情境較目前改善 21.20 個百分點。；跨樣本穩健性標記為穩定。；需要 77.51% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -8.8 | 0.754% | 5.06% | -3.831% | 76.68% | 穩定 | ES95 較目前改善 0.816 個百分點。；年化波動較目前降低 5.89 個百分點。；最差壓力情境較目前改善 21.44 個百分點。；跨樣本穩健性標記為穩定。；需要 76.68% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -3.1 | 0.716% | 5.68% | -8.42% | 67.23% | 可觀察 | ES95 較目前改善 0.854 個百分點。；年化波動較目前降低 5.27 個百分點。；最差壓力情境較目前改善 16.85 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.23% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -8.82 | 0.755% | 5.06% | -3.829% | 76.67% | 穩定 | ES95 較目前改善 0.815 個百分點。；年化波動較目前降低 5.89 個百分點。；最差壓力情境較目前改善 21.44 個百分點。；跨樣本穩健性標記為穩定。；需要 76.67% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -3.1 | 0.716% | 5.68% | -8.42% | 67.23% | 可觀察 | ES95 較目前改善 0.854 個百分點。；年化波動較目前降低 5.27 個百分點。；最差壓力情境較目前改善 16.85 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.23% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 14.92 | 1.185% | 8.26% | -19.666% | 28.15% | 可觀察 | ES95 較目前改善 0.385 個百分點。；年化波動較目前降低 2.69 個百分點。；最差壓力情境較目前改善 5.60 個百分點。；跨樣本穩健性僅為可觀察。；需要 28.15% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 8.13 | 1.048% | 7.01% | -14.424% | 38.78% | 可觀察 | ES95 較目前改善 0.522 個百分點。；年化波動較目前降低 3.94 個百分點。；最差壓力情境較目前改善 10.84 個百分點。；跨樣本穩健性僅為可觀察。；需要 38.78% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
