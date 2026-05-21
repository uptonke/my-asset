# Stock Portfolio Dashboard v11.8 UI/UX Command Center

此版為 UI/UX 大改版：保留既有 Supabase schema 與核心計算邏輯，不新增風險模型。

## 分頁結構

1. 今日總覽：決策中心、核心 KPI、警報與資產配置。
2. 持倉配置：持倉表、權重、損益、再平衡狀態。
3. 績效回顧：TWR/MWR、Sharpe、MDD、快照歷史、NAV 趨勢、FIRE 進度。
4. 風險分析：相關性矩陣、尾部風險、SML/CML、FF 因子、MC/CRO、壓力測試。
5. 交易記帳：Ledger Wizard、交易流水帳、記帳 SOP。
6. 系統資料：同步狀態、資料新鮮度、快照/匯入/匯出維護操作。

## 部署

把本資料夾內容放在 GitHub Pages repo root，確保 `index.html` 位於最外層。

## 安全

本版輸出 zip 不包含 `backups/` 與舊的 `my-quant-dashboard/` scaffold，避免把真實資產備份誤上傳到公開 repo。
