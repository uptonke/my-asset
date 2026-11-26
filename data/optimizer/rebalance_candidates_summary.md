# Rebalance Candidate Generator v2.1

Generated at: `2026-11-26T08:50:59+00:00`

## Safety Boundary

- This is not a BUY / SELL list.
- execution_permission is always false in v2.1.
- No Supabase write.
- No official portfolio weight update.
- Human approval is mandatory before any real-world action.

## Summary

- Approved candidate count: `2`
- Watchlist draft count: `1`
- Rejected source count: `5`
- Verdict: 已有候選草案，但仍需人工批准。

## Approved Candidates

| Proposal | Gate | Source model | Proposed turnover | Top material changes |
|---|---|---|---:|---|
| `v2_1_inverse_vol_baseline` | `approved_candidate` | inverse_vol_baseline | 13.114% | BOXX UP 4.0pp; BTC-USD DOWN -3.526pp; QQQ DOWN -2.786pp; 00981A DOWN -2.697pp; IFRA UP 2.346pp |
| `v2_1_riskfolio_risk_parity_mv` | `approved_candidate` | riskfolio_risk_parity_mv | 13.626% | BOXX UP 4.0pp; QQQ DOWN -3.874pp; BTC-USD DOWN -3.573pp; VOO DOWN -3.376pp; AVUV DOWN -2.527pp |

## Watchlist Drafts

| Proposal | Gate | Source model | Proposed turnover | Top material changes |
|---|---|---|---:|---|
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.656% | BOXX UP 2.0pp; QQQ DOWN -2.0pp; BTC-USD DOWN -2.0pp; 00981A DOWN -1.665pp; VOO DOWN -1.643pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 1.138 個百分點。；年化波動較目前降低 7.47 個百分點。；最差壓力情境較目前改善 23.64 個百分點。；跨樣本穩健性標記為穩定。；需要 80.21% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 1.139 個百分點。；年化波動較目前降低 7.47 個百分點。；最差壓力情境較目前改善 23.66 個百分點。；跨樣本穩健性標記為穩定。；需要 80.14% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 1.149 個百分點。；年化波動較目前降低 7.33 個百分點。；最差壓力情境較目前改善 21.84 個百分點。；跨樣本穩健性僅為可觀察。；需要 77.97% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 1.139 個百分點。；年化波動較目前降低 7.47 個百分點。；最差壓力情境較目前改善 23.66 個百分點。；跨樣本穩健性標記為穩定。；需要 80.14% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 1.149 個百分點。；年化波動較目前降低 7.33 個百分點。；最差壓力情境較目前改善 21.84 個百分點。；跨樣本穩健性僅為可觀察。；需要 77.97% 換手率。 |
