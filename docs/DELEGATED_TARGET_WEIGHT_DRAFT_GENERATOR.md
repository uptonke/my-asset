# v10.5 Integrated Delegated Target Weight + Daily Quant / Monte Carlo Engine

v10.5 產生「整合式機器委任目標權重與交易草案」。這一版不再把 Daily Quant / Monte Carlo 只當成事後參考卡，而是把它們納入目標權重生成前的 scoring input。

## 目標

- 所有目前資產都進 eligible pool。
- 不需要 asset class 分類。
- 系統本輪自行產生 machine target weights。
- 入選資產最少 2%。
- 單一資產最多 40%。
- 未入選資產可以是 0%。
- 現金目標等於流動性緩衝比例；`0` 是有效設定。
- 不設單筆最高金額。
- 美股不允許 fractional shares。
- 台股允許零股，以 1 股為最小單位。
- 加密允許小數交易，最小 sizing 單位為 0.00000001 顆。

## v10.5 如何把 Daily Quant / Monte Carlo 加入目標權重

目標權重生成前會讀取：

- `data/alpha/daily_quant_reference_latest.json`
- `stock_meta.__synthetic_portfolio_risk__`
- `chaos_meta` / Monte Carlo 參考值
- Monte Carlo fragile nodes
- Daily Quant tail pressure metrics

然後先調整 raw score，再做 2%～40% 的目標權重正規化：

- 高尾部壓力時，提高目前持倉權重錨定，降低 ranking / alpha 權重。
- Monte Carlo fragile nodes 會先被扣 raw score，再進權重正規化。
- Daily Quant / Monte Carlo 只影響草案分數與風險標記，不會啟用交易。

## 價格品質與 holdings source guard

交易 sizing 允許使用「庫存頁現價(TWD)」或 real-world price fetch 成功的資產。

- 庫存頁現價(TWD) 可用：可產生 BUY / SELL 草案列。
- real-world price 成功：可產生 BUY / SELL 草案列。
- missing price：不得產生 BUY / SELL 草案列。
- 本地基金或中文名稱資產優先使用庫存頁現價(TWD)，避免把 TWD 價格誤當 USD 後乘上 USD/TWD。

## Workflow 順序

`optimizer-lab.yml.yml` 會先產生 Daily Quant / Monte Carlo reference input，再產生整合式 delegated target weights，最後再重跑 reference check：

1. Build Daily Quant + Monte Carlo Reference Inputs v10.5
2. Build Integrated Delegated Target Weight Draft v10.5
3. Build Daily Quant + Monte Carlo Reference Check v10.5

## 安全邊界

v10.5 固定保持：

```json
{
  "trade_signal_enabled": false,
  "execution_permission": false,
  "broker_submission_enabled": false,
  "official_rebalance_enabled": false,
  "auto_trade_enabled": false,
  "not_trade_order": true
}
```

v10.5 是委任草案引擎，不是券商委託單，也不是 human-confirmed ticket。
