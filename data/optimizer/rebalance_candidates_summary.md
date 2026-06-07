# Rebalance Candidate Generator v2.1

Generated at: `2026-06-07T06:48:50+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.626% | 00981A DOWN -1.433pp; BTC-USD DOWN -1.386pp; BOXX UP 1.307pp; QQQ DOWN -0.915pp; USMV UP 0.898pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 6.637% | BOXX UP 2.0pp; 2330 UP 1.46pp; QQQ DOWN -1.379pp; BTC-USD DOWN -1.365pp; VOO DOWN -1.035pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.097% | BOXX UP 2.0pp; BTC-USD DOWN -1.679pp; QQQ DOWN -1.667pp; 00981A DOWN -1.59pp; AVUV DOWN -1.401pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.819 個百分點。；年化波動較目前降低 5.88 個百分點。；最差壓力情境較目前改善 21.20 個百分點。；跨樣本穩健性標記為穩定。；需要 77.51% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.816 個百分點。；年化波動較目前降低 5.89 個百分點。；最差壓力情境較目前改善 21.44 個百分點。；跨樣本穩健性標記為穩定。；需要 76.68% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.854 個百分點。；年化波動較目前降低 5.27 個百分點。；最差壓力情境較目前改善 16.85 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.23% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.815 個百分點。；年化波動較目前降低 5.89 個百分點。；最差壓力情境較目前改善 21.44 個百分點。；跨樣本穩健性標記為穩定。；需要 76.67% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.854 個百分點。；年化波動較目前降低 5.27 個百分點。；最差壓力情境較目前改善 16.85 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.23% 換手率。 |
