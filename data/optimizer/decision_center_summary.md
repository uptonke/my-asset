# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-16T14:36:21+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.628% | 11.44% | -25.065% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.79 | 1.42% | 9.64% | -19.903% | 22.29% | 穩定 | ES95 較目前改善 0.208 個百分點。；年化波動較目前降低 1.80 個百分點。；最差壓力情境較目前改善 5.16 個百分點。；跨樣本穩健性標記為穩定。；需要 22.29% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -5.84 | 0.752% | 5.09% | -3.258% | 77.02% | 穩定 | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.81 個百分點。；跨樣本穩健性標記為穩定。；需要 77.02% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -5.84 | 0.752% | 5.09% | -3.316% | 76.11% | 穩定 | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.75 個百分點。；跨樣本穩健性標記為穩定。；需要 76.11% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 3.75 | 0.742% | 5.16% | -4.727% | 68.87% | 可觀察 | ES95 較目前改善 0.886 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 20.34 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.87% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -5.84 | 0.752% | 5.09% | -3.317% | 76.08% | 穩定 | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.75 個百分點。；跨樣本穩健性標記為穩定。；需要 76.08% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 3.75 | 0.742% | 5.16% | -4.727% | 68.87% | 可觀察 | ES95 較目前改善 0.886 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 20.34 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.87% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 18.35 | 1.236% | 8.5% | -18.489% | 25.31% | 可觀察 | ES95 較目前改善 0.392 個百分點。；年化波動較目前降低 2.94 個百分點。；最差壓力情境較目前改善 6.58 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.31% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 12.3 | 1.012% | 6.71% | -12.724% | 43.63% | 可觀察 | ES95 較目前改善 0.616 個百分點。；年化波動較目前降低 4.73 個百分點。；最差壓力情境較目前改善 12.34 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.63% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
