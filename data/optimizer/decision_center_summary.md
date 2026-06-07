# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-07T06:09:37+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.567% | 10.94% | -25.241% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 16.19 | 1.374% | 9.26% | -20.711% | 22.47% | 穩定 | ES95 較目前改善 0.193 個百分點。；年化波動較目前降低 1.68 個百分點。；最差壓力情境較目前改善 4.53 個百分點。；跨樣本穩健性標記為穩定。；需要 22.47% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -8.84 | 0.751% | 5.07% | -4.074% | 77.5% | 穩定 | ES95 較目前改善 0.816 個百分點。；年化波動較目前降低 5.87 個百分點。；最差壓力情境較目前改善 21.17 個百分點。；跨樣本穩健性標記為穩定。；需要 77.50% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -8.94 | 0.754% | 5.07% | -3.831% | 76.66% | 穩定 | ES95 較目前改善 0.813 個百分點。；年化波動較目前降低 5.87 個百分點。；最差壓力情境較目前改善 21.41 個百分點。；跨樣本穩健性標記為穩定。；需要 76.66% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -3.27 | 0.716% | 5.69% | -8.42% | 67.22% | 可觀察 | ES95 較目前改善 0.851 個百分點。；年化波動較目前降低 5.25 個百分點。；最差壓力情境較目前改善 16.82 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.22% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -8.97 | 0.755% | 5.07% | -3.829% | 76.65% | 穩定 | ES95 較目前改善 0.812 個百分點。；年化波動較目前降低 5.87 個百分點。；最差壓力情境較目前改善 21.41 個百分點。；跨樣本穩健性標記為穩定。；需要 76.65% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -3.27 | 0.716% | 5.69% | -8.42% | 67.22% | 可觀察 | ES95 較目前改善 0.851 個百分點。；年化波動較目前降低 5.25 個百分點。；最差壓力情境較目前改善 16.82 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.22% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 14.73 | 1.185% | 8.28% | -19.666% | 28.13% | 可觀察 | ES95 較目前改善 0.382 個百分點。；年化波動較目前降低 2.66 個百分點。；最差壓力情境較目前改善 5.57 個百分點。；跨樣本穩健性僅為可觀察。；需要 28.13% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 7.97 | 1.048% | 7.02% | -14.425% | 38.75% | 可觀察 | ES95 較目前改善 0.519 個百分點。；年化波動較目前降低 3.92 個百分點。；最差壓力情境較目前改善 10.82 個百分點。；跨樣本穩健性僅為可觀察。；需要 38.75% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
