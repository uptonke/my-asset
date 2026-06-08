# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-08T05:19:04+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.588% | 11.04% | -25.329% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 16.7 | 1.386% | 9.28% | -20.699% | 22.63% | 穩定 | ES95 較目前改善 0.202 個百分點。；年化波動較目前降低 1.76 個百分點。；最差壓力情境較目前改善 4.63 個百分點。；跨樣本穩健性標記為穩定。；需要 22.63% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -8.11 | 0.755% | 5.08% | -3.948% | 77.93% | 穩定 | ES95 較目前改善 0.833 個百分點。；年化波動較目前降低 5.96 個百分點。；最差壓力情境較目前改善 21.38 個百分點。；跨樣本穩健性標記為穩定。；需要 77.93% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -8.09 | 0.755% | 5.07% | -3.703% | 77.06% | 穩定 | ES95 較目前改善 0.833 個百分點。；年化波動較目前降低 5.97 個百分點。；最差壓力情境較目前改善 21.63 個百分點。；跨樣本穩健性標記為穩定。；需要 77.06% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -21.34 | 0.724% | 5.8% | -8.128% | 70.92% | 可觀察 | ES95 較目前改善 0.864 個百分點。；年化波動較目前降低 5.24 個百分點。；最差壓力情境較目前改善 17.20 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.92% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -8.09 | 0.755% | 5.07% | -3.72% | 77.12% | 穩定 | ES95 較目前改善 0.833 個百分點。；年化波動較目前降低 5.97 個百分點。；最差壓力情境較目前改善 21.61 個百分點。；跨樣本穩健性標記為穩定。；需要 77.12% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -21.34 | 0.724% | 5.8% | -8.128% | 70.92% | 可觀察 | ES95 較目前改善 0.864 個百分點。；年化波動較目前降低 5.24 個百分點。；最差壓力情境較目前改善 17.20 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.92% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 15.2 | 1.198% | 8.31% | -19.7% | 28.15% | 可觀察 | ES95 較目前改善 0.390 個百分點。；年化波動較目前降低 2.73 個百分點。；最差壓力情境較目前改善 5.63 個百分點。；跨樣本穩健性僅為可觀察。；需要 28.15% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 8.54 | 1.059% | 7.04% | -14.398% | 38.9% | 可觀察 | ES95 較目前改善 0.529 個百分點。；年化波動較目前降低 4.00 個百分點。；最差壓力情境較目前改善 10.93 個百分點。；跨樣本穩健性僅為可觀察。；需要 38.90% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
