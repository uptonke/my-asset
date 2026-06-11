# Rebalance Candidate Generator v2.1

Generated at: `2026-06-11T13:23:31+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.386% | BOXX UP 1.58pp; BTC-USD DOWN -1.458pp; 00981A DOWN -1.395pp; USMV UP 1.069pp; SRVR UP 1.026pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 5.46% | BOXX UP 2.0pp; BTC-USD DOWN -1.41pp; QQQ DOWN -1.29pp; AVUV DOWN -0.933pp; USMV UP 0.92pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.358% | BOXX UP 2.0pp; USMV UP 2.0pp; BTC-USD DOWN -1.985pp; QQQ DOWN -1.725pp; 00981A DOWN -1.58pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.882 個百分點。；年化波動較目前降低 6.17 個百分點。；最差壓力情境較目前改善 21.59 個百分點。；跨樣本穩健性標記為穩定。；需要 75.44% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.882 個百分點。；年化波動較目前降低 6.17 個百分點。；最差壓力情境較目前改善 21.66 個百分點。；跨樣本穩健性標記為穩定。；需要 75.25% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.892 個百分點。；年化波動較目前降低 6.11 個百分點。；最差壓力情境較目前改善 20.32 個百分點。；跨樣本穩健性標記為穩定。；需要 70.55% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.882 個百分點。；年化波動較目前降低 6.17 個百分點。；最差壓力情境較目前改善 21.66 個百分點。；跨樣本穩健性標記為穩定。；需要 75.24% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.892 個百分點。；年化波動較目前降低 6.11 個百分點。；最差壓力情境較目前改善 20.32 個百分點。；跨樣本穩健性標記為穩定。；需要 70.55% 換手率。 |
