# Rebalance Candidate Generator v2.1

Generated at: `2026-06-08T06:35:02+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.646% | BTC-USD DOWN -1.421pp; 00981A DOWN -1.373pp; BOXX UP 1.319pp; QQQ DOWN -0.919pp; USMV UP 0.898pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 6.644% | BOXX UP 2.0pp; 2330 UP 1.465pp; BTC-USD DOWN -1.396pp; QQQ DOWN -1.38pp; VOO DOWN -1.033pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.106% | BOXX UP 2.0pp; BTC-USD DOWN -1.713pp; QQQ DOWN -1.673pp; 00981A DOWN -1.533pp; AVUV DOWN -1.4pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.838 個百分點。；年化波動較目前降低 5.99 個百分點。；最差壓力情境較目前改善 21.42 個百分點。；跨樣本穩健性標記為穩定。；需要 77.92% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.838 個百分點。；年化波動較目前降低 6.00 個百分點。；最差壓力情境較目前改善 21.65 個百分點。；跨樣本穩健性標記為穩定。；需要 77.24% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 5.70 個百分點。；最差壓力情境較目前改善 18.87 個百分點。；跨樣本穩健性僅為可觀察。；需要 71.79% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.838 個百分點。；年化波動較目前降低 6.00 個百分點。；最差壓力情境較目前改善 21.65 個百分點。；跨樣本穩健性標記為穩定。；需要 77.24% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 5.70 個百分點。；最差壓力情境較目前改善 18.87 個百分點。；跨樣本穩健性僅為可觀察。；需要 71.79% 換手率。 |
