# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-14T07:03:09+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.616% | 11.36% | -24.947% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.12 | 1.421% | 9.66% | -19.922% | 22.02% | 穩定 | ES95 較目前改善 0.195 個百分點。；年化波動較目前降低 1.70 個百分點。；最差壓力情境較目前改善 5.02 個百分點。；跨樣本穩健性標記為穩定。；需要 22.02% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -6.4 | 0.751% | 5.1% | -3.43% | 75.94% | 穩定 | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.52 個百分點。；跨樣本穩健性標記為穩定。；需要 75.94% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -6.43 | 0.752% | 5.1% | -3.339% | 75.65% | 穩定 | ES95 較目前改善 0.864 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.61 個百分點。；跨樣本穩健性標記為穩定。；需要 75.65% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 2.94 | 0.743% | 5.17% | -4.675% | 69.11% | 可觀察 | ES95 較目前改善 0.873 個百分點。；年化波動較目前降低 6.19 個百分點。；最差壓力情境較目前改善 20.27 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.11% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -6.43 | 0.752% | 5.1% | -3.336% | 75.64% | 穩定 | ES95 較目前改善 0.864 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.61 個百分點。；跨樣本穩健性標記為穩定。；需要 75.64% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 2.94 | 0.743% | 5.17% | -4.675% | 69.11% | 可觀察 | ES95 較目前改善 0.873 個百分點。；年化波動較目前降低 6.19 個百分點。；最差壓力情境較目前改善 20.27 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.11% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 17.68 | 1.236% | 8.51% | -18.507% | 25.14% | 可觀察 | ES95 較目前改善 0.380 個百分點。；年化波動較目前降低 2.85 個百分點。；最差壓力情境較目前改善 6.44 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.14% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 11.68 | 1.012% | 6.73% | -12.745% | 43.31% | 可觀察 | ES95 較目前改善 0.604 個百分點。；年化波動較目前降低 4.63 個百分點。；最差壓力情境較目前改善 12.20 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.31% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
