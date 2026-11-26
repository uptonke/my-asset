# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-11-26T08:38:57+00:00`
- Verdict: `候選觀察`
- Candidate for v2.1: `inverse_vol_baseline, riskfolio_risk_parity_mv`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.854% | 12.14% | -26.174% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | candidate | 24.44 | 1.483% | 9.36% | -19.373% | 27.61% | 穩定 | ES95 較目前改善 0.371 個百分點。；年化波動較目前降低 2.78 個百分點。；最差壓力情境較目前改善 6.80 個百分點。；跨樣本穩健性標記為穩定。；需要 27.61% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | 4.73 | 0.718% | 4.68% | -2.553% | 80.19% | 穩定 | ES95 較目前改善 1.136 個百分點。；年化波動較目前降低 7.46 個百分點。；最差壓力情境較目前改善 23.62 個百分點。；跨樣本穩健性標記為穩定。；需要 80.19% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | 4.76 | 0.717% | 4.68% | -2.534% | 80.13% | 穩定 | ES95 較目前改善 1.137 個百分點。；年化波動較目前降低 7.46 個百分點。；最差壓力情境較目前改善 23.64 個百分點。；跨樣本穩健性標記為穩定。；需要 80.13% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -3.29 | 0.707% | 4.82% | -4.359% | 77.96% | 可觀察 | ES95 較目前改善 1.147 個百分點。；年化波動較目前降低 7.32 個百分點。；最差壓力情境較目前改善 21.81 個百分點。；跨樣本穩健性僅為可觀察。；需要 77.96% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | 4.76 | 0.717% | 4.68% | -2.538% | 80.13% | 穩定 | ES95 較目前改善 1.137 個百分點。；年化波動較目前降低 7.46 個百分點。；最差壓力情境較目前改善 23.64 個百分點。；跨樣本穩健性標記為穩定。；需要 80.13% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -3.29 | 0.707% | 4.82% | -4.359% | 77.96% | 可觀察 | ES95 較目前改善 1.147 個百分點。；年化波動較目前降低 7.32 個百分點。；最差壓力情境較目前改善 21.81 個百分點。；跨樣本穩健性僅為可觀察。；需要 77.96% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | candidate | 24.25 | 1.311% | 8.17% | -16.707% | 34.66% | 可觀察 | ES95 較目前改善 0.543 個百分點。；年化波動較目前降低 3.97 個百分點。；最差壓力情境較目前改善 9.47 個百分點。；跨樣本穩健性僅為可觀察。；需要 34.66% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 6.27 | 1.017% | 6.45% | -11.903% | 46.38% | 不穩定 | ES95 較目前改善 0.837 個百分點。；年化波動較目前降低 5.69 個百分點。；最差壓力情境較目前改善 14.27 個百分點。；穩健性資料不足或不穩定。；需要 46.38% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
