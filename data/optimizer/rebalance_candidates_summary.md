# Rebalance Candidate Generator v2.1

Generated at: `2026-06-12T12:48:58+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.49% | BOXX UP 1.666pp; BTC-USD DOWN -1.421pp; 00981A DOWN -1.406pp; USMV UP 1.114pp; SRVR UP 1.04pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 5.527% | BOXX UP 2.0pp; BTC-USD DOWN -1.385pp; QQQ DOWN -1.351pp; USMV UP 0.958pp; AVUV DOWN -0.941pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.471% | BOXX UP 2.0pp; USMV UP 2.0pp; BTC-USD DOWN -1.954pp; QQQ DOWN -1.788pp; 00981A DOWN -1.592pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.861 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.52 個百分點。；跨樣本穩健性標記為穩定。；需要 75.20% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.860 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.63 個百分點。；跨樣本穩健性標記為穩定。；需要 75.32% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.869 個百分點。；年化波動較目前降低 6.20 個百分點。；最差壓力情境較目前改善 20.24 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.99% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.860 個百分點。；年化波動較目前降低 6.26 個百分點。；最差壓力情境較目前改善 21.61 個百分點。；跨樣本穩健性標記為穩定。；需要 75.30% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.869 個百分點。；年化波動較目前降低 6.20 個百分點。；最差壓力情境較目前改善 20.24 個百分點。；跨樣本穩健性僅為可觀察。；需要 68.99% 換手率。 |
