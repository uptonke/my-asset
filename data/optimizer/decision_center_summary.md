# Portfolio Optimizer Decision Center v2.0

- Status: `OK`
- Generated: `2026-06-12T12:48:58+00:00`
- Verdict: `僅供觀察`
- Candidate for v2.1: `-`
- Safety: no Supabase write, no holdings change, no execution instruction.

## Decision table

| Candidate | Source | Decision | Score | ES95 | Vol | Worst stress | Turnover | Robustness | Key reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| current_weight | skfolio/baseline | baseline | 0.0 | 1.612% | 11.37% | -24.913% | 0.0% | 穩定 | 目前投組，只作為比較基準。 |
| inverse_vol_baseline | skfolio/baseline | watch | 16.98 | 1.42% | 9.69% | -19.917% | 21.96% | 穩定 | ES95 較目前改善 0.192 個百分點。；年化波動較目前降低 1.68 個百分點。；最差壓力情境較目前改善 5.00 個百分點。；跨樣本穩健性標記為穩定。；需要 21.96% 換手率。 |
| scipy_min_variance_fallback | skfolio/baseline | reject | -6.52 | 0.751% | 5.11% | -3.392% | 75.2% | 穩定 | ES95 較目前改善 0.861 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.52 個百分點。；跨樣本穩健性標記為穩定。；需要 75.20% 換手率。 |
| skfolio_min_variance | skfolio/baseline | reject | -6.55 | 0.752% | 5.11% | -3.287% | 75.32% | 穩定 | ES95 較目前改善 0.860 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.63 個百分點。；跨樣本穩健性標記為穩定。；需要 75.32% 換手率。 |
| skfolio_cvar_minimize | skfolio/baseline | reject | 2.86 | 0.743% | 5.17% | -4.675% | 68.99% | 可觀察 | ES95 較目前改善 0.869 個百分點。；年化波動較目前降低 6.20 個百分點。；最差壓力情境較目前改善 20.24 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.99% 換手率。 |
| riskfolio_min_variance | Riskfolio-Lib | reject | -6.55 | 0.752% | 5.11% | -3.3% | 75.3% | 穩定 | ES95 較目前改善 0.860 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.61 個百分點。；跨樣本穩健性標記為穩定。；需要 75.30% 換手率。 |
| riskfolio_cvar_minimize | Riskfolio-Lib | reject | 2.86 | 0.743% | 5.17% | -4.675% | 68.99% | 可觀察 | ES95 較目前改善 0.869 個百分點。；年化波動較目前降低 6.20 個百分點。；最差壓力情境較目前改善 20.24 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.99% 換手率。 |
| riskfolio_risk_parity_mv | Riskfolio-Lib | watch | 17.54 | 1.235% | 8.54% | -18.529% | 25.02% | 可觀察 | ES95 較目前改善 0.377 個百分點。；年化波動較目前降低 2.83 個百分點。；最差壓力情境較目前改善 6.38 個百分點。；跨樣本穩健性僅為可觀察。；需要 25.02% 換手率。 |
| riskfolio_hrp_mv | Riskfolio-Lib | watch | 11.55 | 1.011% | 6.75% | -12.726% | 43.3% | 可觀察 | ES95 較目前改善 0.601 個百分點。；年化波動較目前降低 4.62 個百分點。；最差壓力情境較目前改善 12.19 個百分點。；跨樣本穩健性僅為可觀察。；需要 43.30% 換手率。 |

## Governance guardrails

- v2.0 is a decision-support aggregation layer only.
- Candidates marked `candidate` only mean eligible for v2.1 candidate generation review.
- `watch` means useful information but not executable enough.
- `reject` means the model failed turnover, concentration, robustness, or constraint checks.
