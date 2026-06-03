# Frontend migration bundle

這包做四件事：

1. 移除 Tailwind CDN runtime，改成 Tailwind CLI 產生 `assets/css/tailwind-built.css`。
2. 保留既有 `00–50` CSS，不一次廢棄。
3. 新增 `60-design-token-denoise.css`，降低玻璃擬態 / 毛玻璃 / heavy shadow，但不完全刪除風格。
4. 套用 no-chip 前端：量化因子表移除「籌碼」欄，不動 Supabase singleton。

## 不需要本機 terminal 的用法

1. 在 GitHub 網頁上傳這包內的檔案到對應路徑。
2. 到 Actions，執行：`Apply Frontend Tailwind Migration`。
3. 等 action 自動 commit 完成。
4. 等 GitHub Pages 更新後，強制刷新頁面。

## 為什麼要跑 Actions？

因為 Tailwind production CSS 必須由 Node/Tailwind CLI 掃描 `index.html` 與 JS 後產生。這樣才不是 CDN runtime，也不會把整包未使用 CSS 全塞進頁面。

## 這包不做什麼

- 不導入 Vite。
- 不改成 `.vue` SFC。
- 不刪除 `00–50` CSS。
- 不修 Supabase Multiple GoTrueClient warning。

這是 Phase 1：先讓 Tailwind production 化、畫面降噪、前端不顯示籌碼欄。
