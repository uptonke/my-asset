# Rebalance Candidate Generator v2.1

Generated at: `2026-06-16T08:33:30+00:00`

## Safety Boundary

- This is not a BUY / SELL list.
- execution_permission is always false in v2.1.
- No Supabase write.
- No official portfolio weight update.
- Human approval is mandatory before any real-world action.

## Summary

- Approved candidate count: `0`
- Watchlist draft count: `3`
- Rejected source count: `5`
- Verdict: 無可直接進入人工批准的候選；僅產生觀察草案。

## Approved Candidates

None.

## Watchlist Drafts

| Proposal | Gate | Source model | Proposed turnover | Top material changes |
|---|---|---|---:|---|
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.594% | BOXX UP 1.715pp; BTC-USD DOWN -1.49pp; 00981A DOWN -1.395pp; USMV UP 1.143pp; SRVR UP 1.049pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 5.585% | BOXX UP 2.0pp; BTC-USD DOWN -1.453pp; QQQ DOWN -1.421pp; USMV UP 0.983pp; AVUV DOWN -0.896pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.497% | BOXX UP 2.0pp; USMV UP 2.0pp; BTC-USD DOWN -2.0pp; QQQ DOWN -1.857pp; 00981A DOWN -1.586pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.879 個百分點。；年化波動較目前降低 6.38 個百分點。；最差壓力情境較目前改善 21.76 個百分點。；跨樣本穩健性標記為穩定。；需要 76.42% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.879 個百分點。；年化波動較目前降低 6.38 個百分點。；最差壓力情境較目前改善 21.86 個百分點。；跨樣本穩健性標記為穩定。；需要 76.31% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.889 個百分點。；年化波動較目前降低 6.31 個百分點。；最差壓力情境較目前改善 20.39 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.879 個百分點。；年化波動較目前降低 6.38 個百分點。；最差壓力情境較目前改善 21.87 個百分點。；跨樣本穩健性標記為穩定。；需要 76.33% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.889 個百分點。；年化波動較目前降低 6.31 個百分點。；最差壓力情境較目前改善 20.39 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
