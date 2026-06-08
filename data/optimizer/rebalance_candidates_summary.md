# Rebalance Candidate Generator v2.1

Generated at: `2026-06-08T05:38:20+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.653% | 00981A DOWN -1.433pp; BTC-USD DOWN -1.401pp; BOXX UP 1.323pp; QQQ DOWN -0.913pp; USMV UP 0.901pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 6.647% | BOXX UP 2.0pp; 2330 UP 1.467pp; BTC-USD DOWN -1.377pp; QQQ DOWN -1.376pp; VOO DOWN -1.03pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.108% | BOXX UP 2.0pp; BTC-USD DOWN -1.692pp; QQQ DOWN -1.668pp; 00981A DOWN -1.589pp; AVUV DOWN -1.395pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.832 個百分點。；年化波動較目前降低 5.95 個百分點。；最差壓力情境較目前改善 21.37 個百分點。；跨樣本穩健性標記為穩定。；需要 77.92% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.832 個百分點。；年化波動較目前降低 5.96 個百分點。；最差壓力情境較目前改善 21.62 個百分點。；跨樣本穩健性標記為穩定。；需要 77.05% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.863 個百分點。；年化波動較目前降低 5.23 個百分點。；最差壓力情境較目前改善 17.19 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.92% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.832 個百分點。；年化波動較目前降低 5.96 個百分點。；最差壓力情境較目前改善 21.60 個百分點。；跨樣本穩健性標記為穩定。；需要 77.11% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.863 個百分點。；年化波動較目前降低 5.23 個百分點。；最差壓力情境較目前改善 17.19 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.92% 換手率。 |
