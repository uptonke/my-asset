# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-11-26T08:50:59+00:00`
- Verdict: `候選觀察`
- Candidate for v2.1: `inverse_vol_baseline, riskfolio_risk_parity_mv`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.856% | 12.15% | -26.194% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | candidate | 24.53 | 1.483% | 9.36% | -19.373% | 27.64% | 穩定 | ES95 較目前改善 0.373 個百分點。；年化波動較目前降低 2.79 個百分點。；最差壓力情境較目前改善 6.82 個百分點。；跨樣本穩健性標記為穩定。；需要 27.64% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | 4.81 | 0.718% | 4.68% | -2.55% | 80.21% | 穩定 | ES95 較目前改善 1.138 個百分點。；年化波動較目前降低 7.47 個百分點。；最差壓力情境較目前改善 23.64 個百分點。；跨樣本穩健性標記為穩定。；需要 80.21% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | 4.85 | 0.717% | 4.68% | -2.532% | 80.14% | 穩定 | ES95 較目前改善 1.139 個百分點。；年化波動較目前降低 7.47 個百分點。；最差壓力情境較目前改善 23.66 個百分點。；跨樣本穩健性標記為穩定。；需要 80.14% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -3.2 | 0.707% | 4.82% | -4.359% | 77.97% | 可觀察 | ES95 較目前改善 1.149 個百分點。；年化波動較目前降低 7.33 個百分點。；最差壓力情境較目前改善 21.84 個百分點。；跨樣本穩健性僅為可觀察。；需要 77.97% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | 4.85 | 0.717% | 4.68% | -2.537% | 80.14% | 穩定 | ES95 較目前改善 1.139 個百分點。；年化波動較目前降低 7.47 個百分點。；最差壓力情境較目前改善 23.66 個百分點。；跨樣本穩健性標記為穩定。；需要 80.14% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -3.2 | 0.707% | 4.82% | -4.359% | 77.97% | 可觀察 | ES95 較目前改善 1.149 個百分點。；年化波動較目前降低 7.33 個百分點。；最差壓力情境較目前改善 21.84 個百分點。；跨樣本穩健性僅為可觀察。；需要 77.97% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | candidate | 24.34 | 1.311% | 8.17% | -16.706% | 34.69% | 可觀察 | ES95 較目前改善 0.545 個百分點。；年化波動較目前降低 3.98 個百分點。；最差壓力情境較目前改善 9.49 個百分點。；跨樣本穩健性僅為可觀察。；需要 34.69% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 6.37 | 1.017% | 6.45% | -11.901% | 46.4% | 不穩定 | ES95 較目前改善 0.839 個百分點。；年化波動較目前降低 5.70 個百分點。；最差壓力情境較目前改善 14.29 個百分點。；穩健性資料不足或不穩定。；需要 46.40% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
