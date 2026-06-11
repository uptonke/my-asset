# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-11T13:23:31+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.658% | 11.3% | -24.917% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 17.08 | 1.467% | 9.64% | -19.934% | 21.55% | 穩定 | ES95 較目前改善 0.191 個百分點。；年化波動較目前降低 1.66 個百分點。；最差壓力情境較目前改善 4.98 個百分點。；跨樣本穩健性標記為穩定。；需要 21.55% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -6.12 | 0.776% | 5.13% | -3.323% | 75.44% | 穩定 | ES95 較目前改善 0.882 個百分點。；年化波動較目前降低 6.17 個百分點。；最差壓力情境較目前改善 21.59 個百分點。；跨樣本穩健性標記為穩定。；需要 75.44% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -6.12 | 0.776% | 5.13% | -3.254% | 75.25% | 穩定 | ES95 較目前改善 0.882 個百分點。；年化波動較目前降低 6.17 個百分點。；最差壓力情境較目前改善 21.66 個百分點。；跨樣本穩健性標記為穩定。；需要 75.25% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | -6.58 | 0.766% | 5.19% | -4.6% | 70.55% | 穩定 | ES95 較目前改善 0.892 個百分點。；年化波動較目前降低 6.11 個百分點。；最差壓力情境較目前改善 20.32 個百分點。；跨樣本穩健性標記為穩定。；需要 70.55% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -6.12 | 0.776% | 5.13% | -3.261% | 75.24% | 穩定 | ES95 較目前改善 0.882 個百分點。；年化波動較目前降低 6.17 個百分點。；最差壓力情境較目前改善 21.66 個百分點。；跨樣本穩健性標記為穩定。；需要 75.24% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | -6.58 | 0.766% | 5.19% | -4.6% | 70.55% | 穩定 | ES95 較目前改善 0.892 個百分點。；年化波動較目前降低 6.11 個百分點。；最差壓力情境較目前改善 20.32 個百分點。；跨樣本穩健性標記為穩定。；需要 70.55% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 17.29 | 1.289% | 8.55% | -18.621% | 24.43% | 可觀察 | ES95 較目前改善 0.369 個百分點。；年化波動較目前降低 2.75 個百分點。；最差壓力情境較目前改善 6.30 個百分點。；跨樣本穩健性僅為可觀察。；需要 24.43% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 11.99 | 1.046% | 6.78% | -12.817% | 42.38% | 可觀察 | ES95 較目前改善 0.612 個百分點。；年化波動較目前降低 4.52 個百分點。；最差壓力情境較目前改善 12.10 個百分點。；跨樣本穩健性僅為可觀察。；需要 42.38% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
