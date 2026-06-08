# Rebalance Candidate Generator v2.1

Generated at: `2026-06-08T14:36:10+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 5.723% | BTC-USD DOWN -1.429pp; 00981A DOWN -1.355pp; BOXX UP 1.343pp; QQQ DOWN -0.961pp; USMV UP 0.908pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 6.679% | BOXX UP 2.0pp; 2330 UP 1.476pp; QQQ DOWN -1.412pp; BTC-USD DOWN -1.405pp; VOO DOWN -1.036pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.138% | BOXX UP 2.0pp; BTC-USD DOWN -1.72pp; QQQ DOWN -1.717pp; 00981A DOWN -1.513pp; AVUV DOWN -1.417pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 6.03 個百分點。；最差壓力情境較目前改善 21.38 個百分點。；跨樣本穩健性標記為穩定。；需要 77.70% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 6.03 個百分點。；最差壓力情境較目前改善 21.62 個百分點。；跨樣本穩健性標記為穩定。；需要 77.10% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 5.45 個百分點。；最差壓力情境較目前改善 17.50 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.61% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.844 個百分點。；年化波動較目前降低 6.03 個百分點。；最差壓力情境較目前改善 21.63 個百分點。；跨樣本穩健性標記為穩定。；需要 77.09% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.876 個百分點。；年化波動較目前降低 5.44 個百分點。；最差壓力情境較目前改善 17.48 個百分點。；跨樣本穩健性僅為可觀察。；需要 69.59% 換手率。 |
