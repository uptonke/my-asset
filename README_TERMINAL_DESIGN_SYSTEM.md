# Frontend Terminal Design System Patch

目標：把前端從「AI 拼裝 dashboard」收斂成更像正式金融工具的 **Dark Institutional Brokerage Terminal**。

## 這包做什麼

1. 統一卡片、表格、KPI、badge 的視覺語言
2. 降低 glassmorphism、backdrop blur、neon、gradient、巨大 shadow
3. 強化表格密度與金融數字可讀性
4. 所有金額 / 百分比 / Beta / 分數盡量使用 monospace + tabular numbers
5. 保留既有 00–60 CSS，不一次廢棄，避免前端爆炸
6. 不碰 Supabase singleton
7. 不改 Python 資料管線
8. 不做 .vue / Vite 重構

## 內含檔案

```text
.github/workflows/apply_terminal_design_system.yml
scripts/apply_terminal_design_system.py
scripts/rollback_terminal_design_system.py
assets/css/70-terminal-design-system.css
assets/js/terminal-ui-polish.js
```

## 使用方式

把本 zip 內檔案照路徑上傳到 repo 並 commit 到 main。

然後執行：

```text
GitHub → Actions → Apply Terminal Design System → Run workflow
```

成功後會自動 commit 回 main。

## 成功後檢查

F12 / Elements 應看到：

```html
<link rel="stylesheet" href="assets/css/70-terminal-design-system.css?v=terminal-ds-1">
<script src="assets/js/terminal-ui-polish.js?v=terminal-ds-1"></script>
```

## 回滾

若不喜歡這版樣式，執行：

```bash
python scripts/rollback_terminal_design_system.py
```

再 commit index.html 即可。
