# Rebalance Candidate Generator v2.1

Generated at: `2026-06-07T06:17:30+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.594% | 00981A DOWN -1.441pp; BTC-USD DOWN -1.343pp; BOXX UP 1.297pp; QQQ DOWN -0.924pp; SRVR UP 0.895pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 6.616% | BOXX UP 2.0pp; 2330 UP 1.459pp; QQQ DOWN -1.388pp; BTC-USD DOWN -1.322pp; VOO DOWN -1.044pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.079% | BOXX UP 2.0pp; QQQ DOWN -1.676pp; BTC-USD DOWN -1.635pp; 00981A DOWN -1.599pp; AVUV DOWN -1.408pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.809 個百分點。；年化波動較目前降低 5.82 個百分點。；最差壓力情境較目前改善 21.09 個百分點。；跨樣本穩健性標記為穩定。；需要 77.46% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.806 個百分點。；年化波動較目前降低 5.82 個百分點。；最差壓力情境較目前改善 21.34 個百分點。；跨樣本穩健性標記為穩定。；需要 76.62% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 5.20 個百分點。；最差壓力情境較目前改善 16.75 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.19% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.805 個百分點。；年化波動較目前降低 5.82 個百分點。；最差壓力情境較目前改善 21.34 個百分點。；跨樣本穩健性標記為穩定。；需要 76.61% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 5.20 個百分點。；最差壓力情境較目前改善 16.75 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.19% 換手率。 |
