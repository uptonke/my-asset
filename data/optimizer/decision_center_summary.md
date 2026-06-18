# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-18T12:01:30+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.618% | 11.41% | -25.006% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.26 | 1.422% | 9.66% | -19.897% | 22.26% | 穩定 | ES95 較目前改善 0.196 個百分點。；年化波動較目前降低 1.75 個百分點。；最差壓力情境較目前改善 5.11 個百分點。；跨樣本穩健性標記為穩定。；需要 22.26% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -6.14 | 0.751% | 5.07% | -3.331% | 76.29% | 穩定 | ES95 較目前改善 0.867 個百分點。；年化波動較目前降低 6.34 個百分點。；最差壓力情境較目前改善 21.68 個百分點。；跨樣本穩健性標記為穩定。；需要 76.29% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -6.17 | 0.752% | 5.07% | -3.281% | 75.9% | 穩定 | ES95 較目前改善 0.866 個百分點。；年化波動較目前降低 6.34 個百分點。；最差壓力情境較目前改善 21.73 個百分點。；跨樣本穩健性標記為穩定。；需要 75.90% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 3.39 | 0.742% | 5.15% | -4.727% | 68.74% | 可觀察 | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 20.28 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.74% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -6.17 | 0.752% | 5.07% | -3.279% | 75.88% | 穩定 | ES95 較目前改善 0.866 個百分點。；年化波動較目前降低 6.34 個百分點。；最差壓力情境較目前改善 21.73 個百分點。；跨樣本穩健性標記為穩定。；需要 75.88% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 3.39 | 0.742% | 5.15% | -4.727% | 68.74% | 可觀察 | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 20.28 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.74% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 17.99 | 1.239% | 8.51% | -18.42% | 25.07% | 可觀察 | ES95 較目前改善 0.379 個百分點。；年化波動較目前降低 2.90 個百分點。；最差壓力情境較目前改善 6.59 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.07% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 11.92 | 1.011% | 6.71% | -12.648% | 43.74% | 可觀察 | ES95 較目前改善 0.607 個百分點。；年化波動較目前降低 4.70 個百分點。；最差壓力情境較目前改善 12.36 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.74% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
