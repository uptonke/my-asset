# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-16T15:11:58+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.63% | 11.45% | -25.083% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.88 | 1.42% | 9.64% | -19.904% | 22.32% | 穩定 | ES95 較目前改善 0.210 個百分點。；年化波動較目前降低 1.81 個百分點。；最差壓力情境較目前改善 5.18 個百分點。；跨樣本穩健性標記為穩定。；需要 22.32% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -5.76 | 0.752% | 5.09% | -3.256% | 77.07% | 穩定 | ES95 較目前改善 0.878 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.83 個百分點。；跨樣本穩健性標記為穩定。；需要 77.07% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -5.76 | 0.752% | 5.09% | -3.319% | 76.11% | 穩定 | ES95 較目前改善 0.878 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.76 個百分點。；跨樣本穩健性標記為穩定。；需要 76.11% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 3.85 | 0.742% | 5.16% | -4.727% | 68.88% | 可觀察 | ES95 較目前改善 0.888 個百分點。；年化波動較目前降低 6.29 個百分點。；最差壓力情境較目前改善 20.36 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.88% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -5.76 | 0.752% | 5.09% | -3.318% | 76.11% | 穩定 | ES95 較目前改善 0.878 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.76 個百分點。；跨樣本穩健性標記為穩定。；需要 76.11% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 3.85 | 0.742% | 5.16% | -4.727% | 68.88% | 可觀察 | ES95 較目前改善 0.888 個百分點。；年化波動較目前降低 6.29 個百分點。；最差壓力情境較目前改善 20.36 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.88% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 18.44 | 1.236% | 8.5% | -18.489% | 25.34% | 可觀察 | ES95 較目前改善 0.394 個百分點。；年化波動較目前降低 2.95 個百分點。；最差壓力情境較目前改善 6.59 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.34% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 12.39 | 1.012% | 6.71% | -12.726% | 43.65% | 可觀察 | ES95 較目前改善 0.618 個百分點。；年化波動較目前降低 4.74 個百分點。；最差壓力情境較目前改善 12.36 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.65% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
