# Rebalance Candidate Generator v2.1

Generated at: `2026-06-17T13:53:51+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.573% | BOXX UP 1.72pp; BTC-USD DOWN -1.448pp; 00981A DOWN -1.397pp; USMV UP 1.144pp; SRVR UP 1.051pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 5.547% | BOXX UP 2.0pp; BTC-USD DOWN -1.411pp; QQQ DOWN -1.389pp; USMV UP 0.968pp; VOO DOWN -0.931pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.526% | BOXX UP 2.0pp; USMV UP 2.0pp; BTC-USD DOWN -1.982pp; QQQ DOWN -1.819pp; 00981A DOWN -1.587pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.72 個百分點。；跨樣本穩健性標記為穩定。；需要 75.81% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.874 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.81 個百分點。；跨樣本穩健性標記為穩定。；需要 76.04% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.885 個百分點。；年化波動較目前降低 6.29 個百分點。；最差壓力情境較目前改善 20.32 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.874 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.82 個百分點。；跨樣本穩健性標記為穩定。；需要 76.01% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.885 個百分點。；年化波動較目前降低 6.29 個百分點。；最差壓力情境較目前改善 20.32 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.85% 換手率。 |
