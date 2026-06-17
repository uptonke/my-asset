# Rebalance Candidate Generator v2.1

Generated at: `2026-06-17T13:26:15+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.576% | BOXX UP 1.716pp; BTC-USD DOWN -1.443pp; 00981A DOWN -1.406pp; USMV UP 1.137pp; SRVR UP 1.051pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 5.544% | BOXX UP 2.0pp; BTC-USD DOWN -1.406pp; QQQ DOWN -1.38pp; USMV UP 0.963pp; VOO DOWN -0.932pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.523% | BOXX UP 2.0pp; USMV UP 2.0pp; BTC-USD DOWN -1.977pp; QQQ DOWN -1.811pp; 00981A DOWN -1.596pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.874 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.69 個百分點。；跨樣本穩健性標記為穩定。；需要 75.91% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.873 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.79 個百分點。；跨樣本穩健性標記為穩定。；需要 76.17% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.883 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 20.30 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.83% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.873 個百分點。；年化波動較目前降低 6.35 個百分點。；最差壓力情境較目前改善 21.79 個百分點。；跨樣本穩健性標記為穩定。；需要 76.15% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.883 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 20.30 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.83% 換手率。 |
