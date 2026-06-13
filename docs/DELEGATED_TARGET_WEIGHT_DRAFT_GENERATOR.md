# v10.1 Delegated Target Weight & Draft Generator

v10.1 產生「機器委任目標權重與交易草案」。它不是 Human-Confirmed Trade Ticket，也不是券商委託單。

## 設計規則

- 所有目前資產都進 eligible pool，最多 50 檔。
- 不需要 asset class 分類。
- 系統於本輪產生 `machine_target_weights`。
- 入選資產最低 2%。
- 單一資產最高 40%。
- 未入選資產可以是 0%。
- 現金比例等於流動性緩衝比例，預設 5%。
- 不設單筆最高金額。
- 不槓桿、不放空。
- 美股不接受 fractional shares。
- 台股接受零股，以 1 股為最小單位。
- 加密資產不允許小數交易。

## 邊界

v10.1 固定保持：

- `trade_signal_enabled: false`
- `execution_permission: false`
- `broker_submission_enabled: false`
- `official_rebalance_enabled: false`
- `auto_trade_enabled: false`
- `not_trade_order: true`

它可以自己算目標權重與草案，但不能自動交易、不能送單，也不能冒充人工確認。
