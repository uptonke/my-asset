# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-08-10T04:03:12+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.656% | 11.62% | -25.316% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 12.91 | 1.358% | 9.23% | -19.374% | 26.27% | 可觀察 | ES95 較目前改善 0.298 個百分點。；年化波動較目前降低 2.39 個百分點。；最差壓力情境較目前改善 5.94 個百分點。；跨樣本穩健性僅為可觀察。；需要 26.27% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -3.91 | 0.743% | 4.94% | -2.226% | 77.92% | 穩定 | ES95 較目前改善 0.913 個百分點。；年化波動較目前降低 6.68 個百分點。；最差壓力情境較目前改善 23.09 個百分點。；跨樣本穩健性標記為穩定。；需要 77.92% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -3.91 | 0.743% | 4.94% | -2.265% | 77.48% | 穩定 | ES95 較目前改善 0.913 個百分點。；年化波動較目前降低 6.68 個百分點。；最差壓力情境較目前改善 23.05 個百分點。；跨樣本穩健性標記為穩定。；需要 77.48% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -3.94 | 0.739% | 5.0% | -3.407% | 75.29% | 穩定 | ES95 較目前改善 0.917 個百分點。；年化波動較目前降低 6.62 個百分點。；最差壓力情境較目前改善 21.91 個百分點。；跨樣本穩健性標記為穩定。；需要 75.29% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -3.91 | 0.743% | 4.94% | -2.267% | 77.44% | 穩定 | ES95 較目前改善 0.913 個百分點。；年化波動較目前降低 6.68 個百分點。；最差壓力情境較目前改善 23.05 個百分點。；跨樣本穩健性標記為穩定。；需要 77.44% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -3.94 | 0.739% | 5.0% | -3.407% | 75.29% | 穩定 | ES95 較目前改善 0.917 個百分點。；年化波動較目前降低 6.62 個百分點。；最差壓力情境較目前改善 21.91 個百分點。；跨樣本穩健性標記為穩定。；需要 75.29% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 2.97 | 1.234% | 8.35% | -17.937% | 29.44% | 不穩定 | ES95 較目前改善 0.422 個百分點。；年化波動較目前降低 3.27 個百分點。；最差壓力情境較目前改善 7.38 個百分點。；穩健性資料不足或不穩定。；需要 29.44% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | -3.64 | 1.046% | 6.99% | -13.613% | 41.11% | 不穩定 | ES95 較目前改善 0.610 個百分點。；年化波動較目前降低 4.63 個百分點。；最差壓力情境較目前改善 11.70 個百分點。；穩健性資料不足或不穩定。；需要 41.11% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
