# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-17T14:47:04+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.626% | 11.43% | -25.028% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.67 | 1.42% | 9.64% | -19.901% | 22.28% | 穩定 | ES95 較目前改善 0.206 個百分點。；年化波動較目前降低 1.79 個百分點。；最差壓力情境較目前改善 5.13 個百分點。；跨樣本穩健性標記為穩定。；需要 22.28% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -5.88 | 0.751% | 5.08% | -3.331% | 75.86% | 穩定 | ES95 較目前改善 0.875 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.70 個百分點。；跨樣本穩健性標記為穩定。；需要 75.86% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -5.91 | 0.752% | 5.08% | -3.235% | 76.09% | 穩定 | ES95 較目前改善 0.874 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.79 個百分點。；跨樣本穩健性標記為穩定。；需要 76.09% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 3.66 | 0.742% | 5.15% | -4.727% | 68.85% | 可觀察 | ES95 較目前改善 0.884 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 20.30 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -5.91 | 0.752% | 5.08% | -3.232% | 76.08% | 穩定 | ES95 較目前改善 0.874 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.80 個百分點。；跨樣本穩健性標記為穩定。；需要 76.08% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 3.66 | 0.742% | 5.15% | -4.727% | 68.85% | 可觀察 | ES95 較目前改善 0.884 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 20.30 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 18.26 | 1.235% | 8.51% | -18.449% | 25.32% | 可觀察 | ES95 較目前改善 0.391 個百分點。；年化波動較目前降低 2.92 個百分點。；最差壓力情境較目前改善 6.58 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.32% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 12.19 | 1.011% | 6.71% | -12.702% | 43.7% | 可觀察 | ES95 較目前改善 0.615 個百分點。；年化波動較目前降低 4.72 個百分點。；最差壓力情境較目前改善 12.33 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.70% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
