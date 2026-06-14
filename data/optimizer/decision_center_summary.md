# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-14T16:41:15+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.615% | 11.35% | -24.939% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.08 | 1.421% | 9.65% | -19.922% | 22.02% | 穩定 | ES95 較目前改善 0.194 個百分點。；年化波動較目前降低 1.70 個百分點。；最差壓力情境較目前改善 5.02 個百分點。；跨樣本穩健性標記為穩定。；需要 22.02% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -6.45 | 0.751% | 5.1% | -3.438% | 75.77% | 穩定 | ES95 較目前改善 0.864 個百分點。；年化波動較目前降低 6.25 個百分點。；最差壓力情境較目前改善 21.50 個百分點。；跨樣本穩健性標記為穩定。；需要 75.77% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -6.46 | 0.752% | 5.09% | -3.345% | 75.53% | 穩定 | ES95 較目前改善 0.863 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.59 個百分點。；跨樣本穩健性標記為穩定。；需要 75.53% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 2.88 | 0.743% | 5.17% | -4.675% | 69.1% | 可觀察 | ES95 較目前改善 0.872 個百分點。；年化波動較目前降低 6.18 個百分點。；最差壓力情境較目前改善 20.26 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.10% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -6.46 | 0.752% | 5.09% | -3.342% | 75.52% | 穩定 | ES95 較目前改善 0.863 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.60 個百分點。；跨樣本穩健性標記為穩定。；需要 75.52% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 2.88 | 0.743% | 5.17% | -4.675% | 69.1% | 可觀察 | ES95 較目前改善 0.872 個百分點。；年化波動較目前降低 6.18 個百分點。；最差壓力情境較目前改善 20.26 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.10% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 17.62 | 1.236% | 8.51% | -18.502% | 25.14% | 可觀察 | ES95 較目前改善 0.379 個百分點。；年化波動較目前降低 2.84 個百分點。；最差壓力情境較目前改善 6.44 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.14% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 11.61 | 1.012% | 6.73% | -12.744% | 43.32% | 可觀察 | ES95 較目前改善 0.603 個百分點。；年化波動較目前降低 4.62 個百分點。；最差壓力情境較目前改善 12.20 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.32% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
