# v10.2 Delegated Target Weight & Draft Generator

v10.2 產生「機器委任目標權重與交易草案」，並加入 Price Quality + Holdings Source Guard。它不是 Human-Confirmed Trade Ticket，也不是券商委託單。

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
- 加密不允許小數交易。

## v10.2 價格品質防線

v10.2 的交易 sizing 只允許使用 real-world price fetch 成功的資產。

- real-world price 成功：可產生 BUY / SELL 草案列。
- stored fallback price：可進入 target weight pool，但不得產生 BUY / SELL 草案列。
- missing price：不得產生 BUY / SELL 草案列。
- 本地基金或中文名稱資產若只能用 stored fallback，會被保留在 pool，但交易列會被 Price Quality Guard 擋下。

這是為了避免把非即時 fallback 價格誤當成可交易價格，產生錯誤交易金額。

## Holdings source guard

trading constraints snapshot 會修正本地基金／中文名稱資產的 fallback 幣別：

- 中文基金與 category=基金 預設視為 TWD fallback price。
- 不再把這類 fallback price 當 USD 後乘上 USD/TWD。
- fallback price 仍然標記為 non-real-time，不允許用於 delegated trade sizing。

## 安全邊界

v10.2 固定保持：

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
