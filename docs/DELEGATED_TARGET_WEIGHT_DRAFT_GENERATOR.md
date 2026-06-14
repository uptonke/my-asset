# v10.3 Delegated Target Weight & Draft Generator

v10.3 產生「機器委任目標權重與交易草案」，並加入 Price Quality + Holdings Source Guard。它不是 Human-Confirmed Trade Ticket，也不是券商委託單。

## 目標

- 所有目前資產都進 eligible pool。
- 不需要 asset class 分類。
- 系統本輪自行產生 machine target weights。
- 入選資產最少 2%。
- 單一資產最多 40%。
- 未入選資產可以是 0%。
- 現金目標等於流動性緩衝比例。
- 不設單筆最高金額。
- 美股不允許 fractional shares。
- 台股允許零股，以 1 股為最小單位。
- 加密允許小數交易，最小 sizing 單位為 0.00000001 顆。

## v10.3 價格品質防線

v10.3 的交易 sizing 允許使用「庫存頁現價(TWD)」或 real-world price fetch 成功的資產。

- 庫存頁現價(TWD) 可用：可產生 BUY / SELL 草案列。
- real-world price 成功：可產生 BUY / SELL 草案列。
- missing price：不得產生 BUY / SELL 草案列。
- 本地基金或中文名稱資產優先使用庫存頁現價(TWD)，避免把 TWD 價格誤當 USD 後乘上 USD/TWD。

這是為了讓委任草案與庫存頁一致，避免錯誤交易金額。

## Holdings source guard

trading constraints snapshot 會修正本地基金／中文名稱資產的 fallback 幣別：

- 中文基金與 category=基金 預設視為 TWD fallback price。
- 不再把這類 fallback price 當 USD 後乘上 USD/TWD。
- 庫存頁現價(TWD) 允許用於 delegated trade sizing；缺少庫存現價與 real-world 價格時才排除交易列。

## 安全邊界

v10.3 固定保持：

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

## v10.3 更新

- 加密資產允許小數交易，最小 sizing 單位為 0.00000001 顆。
- 委任草案可使用庫存頁「現價(TWD)」作為 sizing 價格來源。
- 明確允許先賣出舊有部位，賣出所得可作為買入資金來源；缺少現金餘額不再阻擋內部再平衡草案。
- 仍維持 execution_permission=false、broker_submission_enabled=false、not_trade_order=true。
