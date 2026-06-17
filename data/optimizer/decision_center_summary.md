# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-17T13:26:15+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.625% | 11.43% | -25.027% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.63 | 1.42% | 9.64% | -19.9% | 22.3% | 穩定 | ES95 較目前改善 0.205 個百分點。；年化波動較目前降低 1.79 個百分點。；最差壓力情境較目前改善 5.13 個百分點。；跨樣本穩健性標記為穩定。；需要 22.30% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -5.91 | 0.751% | 5.08% | -3.341% | 75.91% | 穩定 | ES95 較目前改善 0.874 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.69 個百分點。；跨樣本穩健性標記為穩定。；需要 75.91% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -5.94 | 0.752% | 5.08% | -3.24% | 76.17% | 穩定 | ES95 較目前改善 0.873 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.79 個百分點。；跨樣本穩健性標記為穩定。；需要 76.17% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 3.63 | 0.742% | 5.15% | -4.727% | 68.83% | 可觀察 | ES95 較目前改善 0.883 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 20.30 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.83% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -5.94 | 0.752% | 5.08% | -3.237% | 76.15% | 穩定 | ES95 較目前改善 0.873 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.79 個百分點。；跨樣本穩健性標記為穩定。；需要 76.15% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 3.63 | 0.742% | 5.15% | -4.727% | 68.83% | 可觀察 | ES95 較目前改善 0.883 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 20.30 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.83% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 18.26 | 1.235% | 8.5% | -18.445% | 25.33% | 可觀察 | ES95 較目前改善 0.390 個百分點。；年化波動較目前降低 2.93 個百分點。；最差壓力情境較目前改善 6.58 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.33% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 12.17 | 1.011% | 6.71% | -12.701% | 43.69% | 可觀察 | ES95 較目前改善 0.614 個百分點。；年化波動較目前降低 4.72 個百分點。；最差壓力情境較目前改善 12.33 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.69% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
