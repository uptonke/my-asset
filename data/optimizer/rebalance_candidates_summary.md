# Rebalance Candidate Generator v2.1

Generated at: `2026-06-14T05:49:00+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.507% | BOXX UP 1.678pp; BTC-USD DOWN -1.441pp; 00981A DOWN -1.395pp; USMV UP 1.115pp; SRVR UP 1.042pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 5.541% | BOXX UP 2.0pp; BTC-USD DOWN -1.403pp; QQQ DOWN -1.347pp; USMV UP 0.955pp; AVUV DOWN -0.952pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.477% | BOXX UP 2.0pp; USMV UP 2.0pp; BTC-USD DOWN -1.973pp; QQQ DOWN -1.782pp; 00981A DOWN -1.58pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 21.51 個百分點。；跨樣本穩健性標記為穩定。；需要 75.90% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.864 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 21.61 個百分點。；跨樣本穩健性標記為穩定。；需要 75.65% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.873 個百分點。；年化波動較目前降低 6.20 個百分點。；最差壓力情境較目前改善 20.28 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.11% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.864 個百分點。；年化波動較目前降低 6.28 個百分點。；最差壓力情境較目前改善 21.62 個百分點。；跨樣本穩健性標記為穩定。；需要 75.64% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.873 個百分點。；年化波動較目前降低 6.20 個百分點。；最差壓力情境較目前改善 20.28 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.11% 換手率。 |
