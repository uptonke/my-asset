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
