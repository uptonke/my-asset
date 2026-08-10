# Rebalance Candidate Generator v2.1

Generated at: `2026-08-10T04:03:12+00:00`

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
| `v2_1_inverse_vol_baseline` | `watch_review_only` | inverse_vol_baseline | 6.566% | BOXX UP 1.892pp; BTC-USD DOWN -1.637pp; SRVR UP 1.565pp; 00981A DOWN -1.472pp; QQQ DOWN -1.276pp |
| `v2_1_riskfolio_risk_parity_mv` | `watch_review_only` | riskfolio_risk_parity_mv | 6.527% | BOXX UP 2.0pp; QQQ DOWN -1.675pp; BTC-USD DOWN -1.607pp; VOO DOWN -1.254pp; SRVR UP 1.222pp |
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.685% | BOXX UP 2.0pp; QQQ DOWN -2.0pp; BTC-USD DOWN -2.0pp; AVUV DOWN -1.774pp; 00981A DOWN -1.598pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 0.913 個百分點。；年化波動較目前降低 6.68 個百分點。；最差壓力情境較目前改善 23.09 個百分點。；跨樣本穩健性標記為穩定。；需要 77.92% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 0.913 個百分點。；年化波動較目前降低 6.68 個百分點。；最差壓力情境較目前改善 23.05 個百分點。；跨樣本穩健性標記為穩定。；需要 77.48% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 0.917 個百分點。；年化波動較目前降低 6.62 個百分點。；最差壓力情境較目前改善 21.91 個百分點。；跨樣本穩健性標記為穩定。；需要 75.29% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 0.913 個百分點。；年化波動較目前降低 6.68 個百分點。；最差壓力情境較目前改善 23.05 個百分點。；跨樣本穩健性標記為穩定。；需要 77.44% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 0.917 個百分點。；年化波動較目前降低 6.62 個百分點。；最差壓力情境較目前改善 21.91 個百分點。；跨樣本穩健性標記為穩定。；需要 75.29% 換手率。 |
