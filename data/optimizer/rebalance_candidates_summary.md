# Rebalance Candidate Generator v2.1

Generated at: `2026-06-08T04:57:19+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.663% | 00981A DOWN -1.43pp; BTC-USD DOWN -1.413pp; BOXX UP 1.326pp; QQQ DOWN -0.911pp; USMV UP 0.902pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 6.654% | BOXX UP 2.0pp; 2330 UP 1.468pp; BTC-USD DOWN -1.389pp; QQQ DOWN -1.374pp; VOO DOWN -1.027pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.114% | BOXX UP 2.0pp; BTC-USD DOWN -1.705pp; QQQ DOWN -1.665pp; 00981A DOWN -1.586pp; AVUV DOWN -1.394pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.834 個百分點。；年化波動較目前降低 5.97 個百分點。；最差壓力情境較目前改善 21.40 個百分點。；跨樣本穩健性標記為穩定。；需要 77.94% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.834 個百分點。；年化波動較目前降低 5.98 個百分點。；最差壓力情境較目前改善 21.64 個百分點。；跨樣本穩健性標記為穩定。；需要 77.07% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 5.25 個百分點。；最差壓力情境較目前改善 17.22 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.93% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.834 個百分點。；年化波動較目前降低 5.98 個百分點。；最差壓力情境較目前改善 21.63 個百分點。；跨樣本穩健性標記為穩定。；需要 77.13% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.865 個百分點。；年化波動較目前降低 5.25 個百分點。；最差壓力情境較目前改善 17.22 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.93% 換手率。 |
