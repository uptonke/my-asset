# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-07T06:23:36+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.568% | 10.94% | -25.252% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 16.25 | 1.374% | 9.25% | -20.711% | 22.48% | 穩定 | ES95 較目前改善 0.194 個百分點。；年化波動較目前降低 1.69 個百分點。；最差壓力情境較目前改善 4.54 個百分點。；跨樣本穩健性標記為穩定。；需要 22.48% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -8.81 | 0.751% | 5.07% | -4.073% | 77.5% | 穩定 | ES95 較目前改善 0.817 個百分點。；年化波動較目前降低 5.87 個百分點。；最差壓力情境較目前改善 21.18 個百分點。；跨樣本穩健性標記為穩定。；需要 77.50% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -8.88 | 0.754% | 5.06% | -3.831% | 76.67% | 穩定 | ES95 較目前改善 0.814 個百分點。；年化波動較目前降低 5.88 個百分點。；最差壓力情境較目前改善 21.42 個百分點。；跨樣本穩健性標記為穩定。；需要 76.67% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -3.21 | 0.716% | 5.68% | -8.42% | 67.23% | 可觀察 | ES95 較目前改善 0.852 個百分點。；年化波動較目前降低 5.26 個百分點。；最差壓力情境較目前改善 16.83 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.23% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -8.91 | 0.755% | 5.06% | -3.828% | 76.66% | 穩定 | ES95 較目前改善 0.813 個百分點。；年化波動較目前降低 5.88 個百分點。；最差壓力情境較目前改善 21.42 個百分點。；跨樣本穩健性標記為穩定。；需要 76.66% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -3.21 | 0.716% | 5.68% | -8.42% | 67.23% | 可觀察 | ES95 較目前改善 0.852 個百分點。；年化波動較目前降低 5.26 個百分點。；最差壓力情境較目前改善 16.83 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.23% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 14.82 | 1.185% | 8.26% | -19.666% | 28.14% | 可觀察 | ES95 較目前改善 0.383 個百分點。；年化波動較目前降低 2.68 個百分點。；最差壓力情境較目前改善 5.59 個百分點。；跨樣本穩健性僅為可觀察。；需要 28.14% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 8.04 | 1.048% | 7.01% | -14.425% | 38.76% | 可觀察 | ES95 較目前改善 0.520 個百分點。；年化波動較目前降低 3.93 個百分點。；最差壓力情境較目前改善 10.83 個百分點。；跨樣本穩健性僅為可觀察。；需要 38.76% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
