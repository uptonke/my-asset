# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-08T05:38:20+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.587% | 11.03% | -25.319% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 16.64 | 1.386% | 9.28% | -20.7% | 22.62% | 穩定 | ES95 較目前改善 0.201 個百分點。；年化波動較目前降低 1.75 個百分點。；最差壓力情境較目前改善 4.62 個百分點。；跨樣本穩健性標記為穩定。；需要 22.62% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -8.17 | 0.755% | 5.08% | -3.947% | 77.92% | 穩定 | ES95 較目前改善 0.832 個百分點。；年化波動較目前降低 5.95 個百分點。；最差壓力情境較目前改善 21.37 個百分點。；跨樣本穩健性標記為穩定。；需要 77.92% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -8.14 | 0.755% | 5.07% | -3.703% | 77.05% | 穩定 | ES95 較目前改善 0.832 個百分點。；年化波動較目前降低 5.96 個百分點。；最差壓力情境較目前改善 21.62 個百分點。；跨樣本穩健性標記為穩定。；需要 77.05% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -21.41 | 0.724% | 5.8% | -8.128% | 70.92% | 可觀察 | ES95 較目前改善 0.863 個百分點。；年化波動較目前降低 5.23 個百分點。；最差壓力情境較目前改善 17.19 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.92% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -8.14 | 0.755% | 5.07% | -3.72% | 77.11% | 穩定 | ES95 較目前改善 0.832 個百分點。；年化波動較目前降低 5.96 個百分點。；最差壓力情境較目前改善 21.60 個百分點。；跨樣本穩健性標記為穩定。；需要 77.11% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -21.41 | 0.724% | 5.8% | -8.128% | 70.92% | 可觀察 | ES95 較目前改善 0.863 個百分點。；年化波動較目前降低 5.23 個百分點。；最差壓力情境較目前改善 17.19 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.92% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 15.14 | 1.198% | 8.31% | -19.701% | 28.14% | 可觀察 | ES95 較目前改善 0.389 個百分點。；年化波動較目前降低 2.72 個百分點。；最差壓力情境較目前改善 5.62 個百分點。；跨樣本穩健性僅為可觀察。；需要 28.14% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 8.47 | 1.059% | 7.04% | -14.399% | 38.89% | 可觀察 | ES95 較目前改善 0.528 個百分點。；年化波動較目前降低 3.99 個百分點。；最差壓力情境較目前改善 10.92 個百分點。；跨樣本穩健性僅為可觀察。；需要 38.89% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
