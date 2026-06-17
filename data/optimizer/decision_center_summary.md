# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-17T13:53:51+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.627% | 11.44% | -25.043% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.74 | 1.42% | 9.64% | -19.901% | 22.29% | 穩定 | ES95 較目前改善 0.207 個百分點。；年化波動較目前降低 1.80 個百分點。；最差壓力情境較目前改善 5.14 個百分點。；跨樣本穩健性標記為穩定。；需要 22.29% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -5.82 | 0.751% | 5.08% | -3.324% | 75.81% | 穩定 | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.72 個百分點。；跨樣本穩健性標記為穩定。；需要 75.81% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -5.88 | 0.753% | 5.08% | -3.231% | 76.04% | 穩定 | ES95 較目前改善 0.874 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.81 個百分點。；跨樣本穩健性標記為穩定。；需要 76.04% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 3.73 | 0.742% | 5.15% | -4.727% | 68.85% | 可觀察 | ES95 較目前改善 0.885 個百分點。；年化波動較目前降低 6.29 個百分點。；最差壓力情境較目前改善 20.32 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -5.88 | 0.753% | 5.08% | -3.227% | 76.01% | 穩定 | ES95 較目前改善 0.874 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.82 個百分點。；跨樣本穩健性標記為穩定。；需要 76.01% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 3.73 | 0.742% | 5.15% | -4.727% | 68.85% | 可觀察 | ES95 較目前改善 0.885 個百分點。；年化波動較目前降低 6.29 個百分點。；最差壓力情境較目前改善 20.32 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 18.33 | 1.235% | 8.51% | -18.449% | 25.34% | 可觀察 | ES95 較目前改善 0.392 個百分點。；年化波動較目前降低 2.93 個百分點。；最差壓力情境較目前改善 6.59 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.34% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 12.25 | 1.011% | 6.71% | -12.704% | 43.72% | 可觀察 | ES95 較目前改善 0.616 個百分點。；年化波動較目前降低 4.73 個百分點。；最差壓力情境較目前改善 12.34 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.72% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
