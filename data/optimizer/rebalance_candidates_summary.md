# Rebalance Candidate Generator v2.1

Generated at: `2026-06-16T15:11:58+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.58% | BOXX UP 1.726pp; BTC-USD DOWN -1.461pp; 00981A DOWN -1.393pp; USMV UP 1.147pp; SRVR UP 1.047pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 5.565% | BOXX UP 2.0pp; BTC-USD DOWN -1.425pp; QQQ DOWN -1.394pp; USMV UP 0.983pp; VOO DOWN -0.911pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.516% | BOXX UP 2.0pp; USMV UP 2.0pp; BTC-USD DOWN -1.994pp; QQQ DOWN -1.828pp; 00981A DOWN -1.583pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.878 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.83 個百分點。；跨樣本穩健性標記為穩定。；需要 77.07% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.878 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.76 個百分點。；跨樣本穩健性標記為穩定。；需要 76.11% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.888 個百分點。；年化波動較目前降低 6.29 個百分點。；最差壓力情境較目前改善 20.36 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.88% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.878 個百分點。；年化波動較目前降低 6.36 個百分點。；最差壓力情境較目前改善 21.76 個百分點。；跨樣本穩健性標記為穩定。；需要 76.11% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.888 個百分點。；年化波動較目前降低 6.29 個百分點。；最差壓力情境較目前改善 20.36 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.88% 換手率。 |
