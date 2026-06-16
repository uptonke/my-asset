# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-16T08:33:30+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.631% | 11.47% | -25.122% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.98 | 1.42% | 9.64% | -19.906% | 22.37% | 穩定 | ES95 較目前改善 0.211 個百分點。；年化波動較目前降低 1.83 個百分點。；最差壓力情境較目前改善 5.22 個百分點。；跨樣本穩健性標記為穩定。；需要 22.37% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -5.68 | 0.752% | 5.09% | -3.359% | 76.42% | 穩定 | ES95 較目前改善 0.879 個百分點。；年化波動較目前降低 6.38 個百分點。；最差壓力情境較目前改善 21.76 個百分點。；跨樣本穩健性標記為穩定。；需要 76.42% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -5.68 | 0.752% | 5.09% | -3.257% | 76.31% | 穩定 | ES95 較目前改善 0.879 個百分點。；年化波動較目前降低 6.38 個百分點。；最差壓力情境較目前改善 21.86 個百分點。；跨樣本穩健性標記為穩定。；需要 76.31% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 3.99 | 0.742% | 5.16% | -4.727% | 68.85% | 可觀察 | ES95 較目前改善 0.889 個百分點。；年化波動較目前降低 6.31 個百分點。；最差壓力情境較目前改善 20.39 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -5.68 | 0.752% | 5.09% | -3.255% | 76.33% | 穩定 | ES95 較目前改善 0.879 個百分點。；年化波動較目前降低 6.38 個百分點。；最差壓力情境較目前改善 21.87 個百分點。；跨樣本穩健性標記為穩定。；需要 76.33% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 3.99 | 0.742% | 5.16% | -4.727% | 68.85% | 可觀察 | ES95 較目前改善 0.889 個百分點。；年化波動較目前降低 6.31 個百分點。；最差壓力情境較目前改善 20.39 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 18.53 | 1.236% | 8.5% | -18.483% | 25.42% | 可觀察 | ES95 較目前改善 0.395 個百分點。；年化波動較目前降低 2.97 個百分點。；最差壓力情境較目前改善 6.64 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.42% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 12.53 | 1.012% | 6.72% | -12.729% | 43.58% | 可觀察 | ES95 較目前改善 0.619 個百分點。；年化波動較目前降低 4.75 個百分點。；最差壓力情境較目前改善 12.39 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.58% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
