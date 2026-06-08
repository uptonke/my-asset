# Rebalance Candidate Generator v2.1

Generated at: `2026-06-08T05:19:04+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.657% | 00981A DOWN -1.432pp; BTC-USD DOWN -1.405pp; BOXX UP 1.324pp; QQQ DOWN -0.913pp; USMV UP 0.901pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 6.65% | BOXX UP 2.0pp; 2330 UP 1.468pp; BTC-USD DOWN -1.381pp; QQQ DOWN -1.375pp; VOO DOWN -1.028pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.11% | BOXX UP 2.0pp; BTC-USD DOWN -1.698pp; QQQ DOWN -1.667pp; 00981A DOWN -1.588pp; AVUV DOWN -1.395pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.833 個百分點。；年化波動較目前降低 5.96 個百分點。；最差壓力情境較目前改善 21.38 個百分點。；跨樣本穩健性標記為穩定。；需要 77.93% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.833 個百分點。；年化波動較目前降低 5.97 個百分點。；最差壓力情境較目前改善 21.63 個百分點。；跨樣本穩健性標記為穩定。；需要 77.06% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.864 個百分點。；年化波動較目前降低 5.24 個百分點。；最差壓力情境較目前改善 17.20 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.92% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.833 個百分點。；年化波動較目前降低 5.97 個百分點。；最差壓力情境較目前改善 21.61 個百分點。；跨樣本穩健性標記為穩定。；需要 77.12% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.864 個百分點。；年化波動較目前降低 5.24 個百分點。；最差壓力情境較目前改善 17.20 個百分點。；跨樣本穩健性僅為可觀察。；需要 70.92% 換手率。 |
