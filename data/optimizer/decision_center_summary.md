# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-08T04:57:19+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.589% | 11.05% | -25.347% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 16.77 | 1.386% | 9.28% | -20.698% | 22.65% | 穩定 | ES95 較目前改善 0.203 個百分點。；年化波動較目前降低 1.77 個百分點。；最差壓力情境較目前改善 4.65 個百分點。；跨樣本穩健性標記為穩定。；需要 22.65% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -8.06 | 0.755% | 5.08% | -3.948% | 77.94% | 穩定 | ES95 較目前改善 0.834 個百分點。；年化波動較目前降低 5.97 個百分點。；最差壓力情境較目前改善 21.40 個百分點。；跨樣本穩健性標記為穩定。；需要 77.94% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -8.03 | 0.755% | 5.07% | -3.703% | 77.07% | 穩定 | ES95 較目前改善 0.834 個百分點。；年化波動較目前降低 5.98 個百分點。；最差壓力情境較目前改善 21.64 個百分點。；跨樣本穩健性標記為穩定。；需要 77.07% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -21.26 | 0.724% | 5.8% | -8.128% | 70.93% | 可觀察 | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 5.25 個百分點。；最差壓力情境較目前改善 17.22 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.93% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -8.03 | 0.755% | 5.07% | -3.721% | 77.13% | 穩定 | ES95 較目前改善 0.834 個百分點。；年化波動較目前降低 5.98 個百分點。；最差壓力情境較目前改善 21.63 個百分點。；跨樣本穩健性標記為穩定。；需要 77.13% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -21.26 | 0.724% | 5.8% | -8.128% | 70.93% | 可觀察 | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 5.25 個百分點。；最差壓力情境較目前改善 17.22 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.93% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 15.27 | 1.198% | 8.31% | -19.7% | 28.17% | 可觀察 | ES95 較目前改善 0.391 個百分點。；年化波動較目前降低 2.74 個百分點。；最差壓力情境較目前改善 5.65 個百分點。；跨樣本穩健性僅為可觀察。；需要 28.17% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 8.63 | 1.059% | 7.03% | -14.397% | 38.92% | 可觀察 | ES95 較目前改善 0.530 個百分點。；年化波動較目前降低 4.02 個百分點。；最差壓力情境較目前改善 10.95 個百分點。；跨樣本穩健性僅為可觀察。；需要 38.92% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
