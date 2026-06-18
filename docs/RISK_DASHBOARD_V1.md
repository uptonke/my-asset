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


## v1.0.2 Factor Value Mapping Fix

- 多因子狀態不再只看 factor object 是否存在。
- 只有 alpha / market beta / R² 等核心欄位與至少 3 個 numeric factor values 成功映射時，才顯示 `OK`。
- 支援 top-level、`coefficients`、`betas`、`factor_loadings`、`regression` 等多種歷史 payload 結構。
- 若找到物件但值無法映射，會先嘗試以目前持倉合成日報酬計算後備 FF5 + Momentum + TW + Crypto 快照；後備失敗才顯示 `PARTIAL / UNAVAILABLE`。
- `Update Stock Quant Meta` log 會輸出 factor attribution status/source/mapped count，便於除錯。
