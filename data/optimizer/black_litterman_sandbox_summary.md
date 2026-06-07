# Bayesian / Black-Litterman Sandbox v3.1

Generated: `2026-06-07T07:25:46+00:00`

## Safety boundary

- Rules-based view engine only; no arbitrary subjective views.
- Posterior tilt is a proxy sandbox, not a production Black-Litterman optimizer.
- 不是 BUY / SELL 指令，不自動交易，不寫入 Supabase，不修改正式持倉或正式權重。

## Summary

- Regime: `risk_off_liquidity_pressure`
- View engine status: `rules_based_stable`
- Views: 4
- Posterior candidates: 2

## Views

- `cash` overweight `2.5`pp, confidence `0.85` — Risk-off regime raises liquidity buffer.
- `crypto` underweight `2.0`pp, confidence `0.85` — Crypto tail risk is penalized under liquidity pressure.
- `us_tech` underweight `1.0`pp, confidence `0.85` — High-duration tech is stress-sensitive.
- `gold` overweight `0.8`pp, confidence `0.85` — Small hedge allocation; not treated as guaranteed hedge.

## Posterior candidates

### v3_1_current_prior_posterior_tilt

- Prior: `current_weight`
- Method: `rules_based_bl_tilt_proxy`
- Turnover vs prior: `1.874`%
- Status: `watch_only_bl_proxy_requires_review`

### v3_1_v3_0_v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX_posterior_tilt

- Prior: `v3_0_v2_3_from_v2_2_trim_ETH_USD_100pct_to_BOXX`
- Method: `rules_based_bl_tilt_proxy_on_regime_draft`
- Turnover vs prior: `1.071`%
- Status: `watch_only_bl_proxy_requires_review`
