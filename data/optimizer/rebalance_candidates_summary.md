# Rebalance Candidate Generator v2.1

Generated at: `2026-11-26T11:35:02+00:00`

## Safety Boundary

- This is not a BUY / SELL list.
- execution_permission is always false in v2.1.
- No Supabase write.
- No official portfolio weight update.
- Human approval is mandatory before any real-world action.

## Summary

- Approved candidate count: `2`
- Watchlist draft count: `1`
- Rejected source count: `5`
- Verdict: 已有候選草案，但仍需人工批准。

## Approved Candidates

| Proposal | Gate | Source model | Proposed turnover | Top material changes |
|---|---|---|---:|---|
| `v2_1_inverse_vol_baseline` | `approved_candidate` | inverse_vol_baseline | 13.103% | BOXX UP 4.0pp; BTC-USD DOWN -3.5pp; QQQ DOWN -2.789pp; 00981A DOWN -2.7pp; IFRA UP 2.345pp |
| `v2_1_riskfolio_risk_parity_mv` | `approved_candidate` | riskfolio_risk_parity_mv | 13.615% | BOXX UP 4.0pp; QQQ DOWN -3.877pp; BTC-USD DOWN -3.545pp; VOO DOWN -3.381pp; AVUV DOWN -2.531pp |

## Watchlist Drafts

| Proposal | Gate | Source model | Proposed turnover | Top material changes |
|---|---|---|---:|---|
| `v2_1_riskfolio_hrp_mv` | `watch_review_only` | riskfolio_hrp_mv | 7.657% | BOXX UP 2.0pp; QQQ DOWN -2.0pp; BTC-USD DOWN -2.0pp; 00981A DOWN -1.666pp; VOO DOWN -1.645pp |

## Rejected Sources

| Source | Reason |
|---|---|
| `scipy_min_variance_fallback` | ES95 較目前改善 1.137 個百分點。；年化波動較目前降低 7.46 個百分點。；最差壓力情境較目前改善 23.62 個百分點。；跨樣本穩健性標記為穩定。；需要 80.19% 換手率。 |
| `skfolio_min_variance` | ES95 較目前改善 1.138 個百分點。；年化波動較目前降低 7.46 個百分點。；最差壓力情境較目前改善 23.64 個百分點。；跨樣本穩健性標記為穩定。；需要 80.13% 換手率。 |
| `skfolio_cvar_minimize` | ES95 較目前改善 1.148 個百分點。；年化波動較目前降低 7.32 個百分點。；最差壓力情境較目前改善 21.82 個百分點。；跨樣本穩健性僅為可觀察。；需要 77.96% 換手率。 |
| `riskfolio_min_variance` | ES95 較目前改善 1.138 個百分點。；年化波動較目前降低 7.46 個百分點。；最差壓力情境較目前改善 23.64 個百分點。；跨樣本穩健性標記為穩定。；需要 80.13% 換手率。 |
| `riskfolio_cvar_minimize` | ES95 較目前改善 1.148 個百分點。；年化波動較目前降低 7.32 個百分點。；最差壓力情境較目前改善 21.82 個百分點。；跨樣本穩健性僅為可觀察。；需要 77.96% 換手率。 |
