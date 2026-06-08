# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-08T06:35:02+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.594% | 11.07% | -25.341% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.0 | 1.386% | 9.28% | -20.693% | 22.59% | 穩定 | ES95 較目前改善 0.208 個百分點。；年化波動較目前降低 1.79 個百分點。；最差壓力情境較目前改善 4.65 個百分點。；跨樣本穩健性標記為穩定。；需要 22.59% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -7.88 | 0.756% | 5.08% | -3.923% | 77.92% | 穩定 | ES95 較目前改善 0.838 個百分點。；年化波動較目前降低 5.99 個百分點。；最差壓力情境較目前改善 21.42 個百分點。；跨樣本穩健性標記為穩定。；需要 77.92% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -7.86 | 0.756% | 5.07% | -3.691% | 77.24% | 穩定 | ES95 較目前改善 0.838 個百分點。；年化波動較目前降低 6.00 個百分點。；最差壓力情境較目前改善 21.65 個百分點。；跨樣本穩健性標記為穩定。；需要 77.24% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -18.16 | 0.729% | 5.37% | -6.473% | 71.79% | 可觀察 | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 5.70 個百分點。；最差壓力情境較目前改善 18.87 個百分點。；跨樣本穩健性僅為可觀察。；需要 71.79% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -7.86 | 0.756% | 5.07% | -3.688% | 77.24% | 穩定 | ES95 較目前改善 0.838 個百分點。；年化波動較目前降低 6.00 個百分點。；最差壓力情境較目前改善 21.65 個百分點。；跨樣本穩健性標記為穩定。；需要 77.24% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -18.16 | 0.729% | 5.37% | -6.473% | 71.79% | 可觀察 | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 5.70 個百分點。；最差壓力情境較目前改善 18.87 個百分點。；跨樣本穩健性僅為可觀察。；需要 71.79% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 15.44 | 1.199% | 8.32% | -19.692% | 28.12% | 可觀察 | ES95 較目前改善 0.395 個百分點。；年化波動較目前降低 2.75 個百分點。；最差壓力情境較目前改善 5.65 個百分點。；跨樣本穩健性僅為可觀察。；需要 28.12% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 8.82 | 1.06% | 7.03% | -14.384% | 38.89% | 可觀察 | ES95 較目前改善 0.534 個百分點。；年化波動較目前降低 4.04 個百分點。；最差壓力情境較目前改善 10.96 個百分點。；跨樣本穩健性僅為可觀察。；需要 38.89% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
