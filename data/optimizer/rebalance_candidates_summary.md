# Rebalance Candidate Generator v2.1

Generated at: `2026-06-07T06:23:36+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.62% | 00981A DOWN -1.434pp; BTC-USD DOWN -1.377pp; BOXX UP 1.306pp; QQQ DOWN -0.916pp; SRVR UP 0.897pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 6.633% | BOXX UP 2.0pp; 2330 UP 1.46pp; QQQ DOWN -1.381pp; BTC-USD DOWN -1.356pp; VOO DOWN -1.037pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.094% | BOXX UP 2.0pp; BTC-USD DOWN -1.67pp; QQQ DOWN -1.669pp; 00981A DOWN -1.592pp; AVUV DOWN -1.402pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.817 個百分點。；年化波動較目前降低 5.87 個百分點。；最差壓力情境較目前改善 21.18 個百分點。；跨樣本穩健性標記為穩定。；需要 77.50% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.814 個百分點。；年化波動較目前降低 5.88 個百分點。；最差壓力情境較目前改善 21.42 個百分點。；跨樣本穩健性標記為穩定。；需要 76.67% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.852 個百分點。；年化波動較目前降低 5.26 個百分點。；最差壓力情境較目前改善 16.83 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.23% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.813 個百分點。；年化波動較目前降低 5.88 個百分點。；最差壓力情境較目前改善 21.42 個百分點。；跨樣本穩健性標記為穩定。；需要 76.66% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.852 個百分點。；年化波動較目前降低 5.26 個百分點。；最差壓力情境較目前改善 16.83 個百分點。；跨樣本穩健性僅為可觀察。；需要 67.23% 換手率。 |
