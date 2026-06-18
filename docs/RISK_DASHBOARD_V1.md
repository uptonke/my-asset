# v1.0 Risk Dashboard Release Guard

This release freezes the Risk tab into a stable diagnostic surface.

## Scope

- Synthetic portfolio risk
- QuantStats-style risk report
- Benchmark-relative attribution
- Win rate and payoff diagnostics
- Drawdown recovery diagnostics
- Factor attribution snapshot from the existing `macro_meta.fama_french`
- Source guard for benchmark alignment and FX handling

## Non-goals

- No target-weight generation
- No trade draft generation
- No Supabase writes beyond the existing Stock Quant Meta workflow
- No broker submission
- No execution permission

## Source-of-truth rules

1. Portfolio returns come from the current-weight synthetic portfolio return engine.
2. Benchmark attribution aligns portfolio and benchmark returns on common daily dates.
3. Benchmark FX conversion uses historical USD/TWD where available; otherwise it is explicitly marked as static FX.
4. Factor exposure is not rebuilt here. It references the existing `macro_meta.fama_french` output.
5. Missing benchmark or factor data is displayed as unavailable or warning, never silently imputed.

## v1.0.1 Factor Attribution Source Binding Fix

- `factor_attribution_snapshot` now searches multiple known factor-exposure locations before reporting unavailable:
  - `macro_meta.fama_french`
  - `macro_meta.factor_attribution`
  - top-level `fama_french`
  - `stock_meta.__macro_meta__.fama_french`
  - previous synthetic-risk attribution diagnostics, when present
- If no existing factor payload is found, the risk update script can compute a fallback weekly 8-factor snapshot from current-weight synthetic portfolio returns using FF5, Momentum, Taiwan market, and BTC crypto proxy factors.
- This remains a risk-tab diagnostic only. It does not create target weights, trade drafts, execution permission, broker submission, or Supabase trading instructions.
