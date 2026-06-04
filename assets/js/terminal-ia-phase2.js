(() => {
  "use strict";

  const SUMMARY_PANEL_ID = "terminal-ia-summary-panel";
  const META_PANEL_ID = "terminal-ia-kpi-metadata-panel";
  const HOLDINGS_PANEL_ID = "terminal-ia-holdings-market-list";

  let currentTabLabel = "總覽";

  const esc = (v) =>
    String(v ?? "").replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#039;"
    }[ch]));

  const num = (v, d = 1) => {
    const n = Number(v);
    return Number.isFinite(n) ? n.toFixed(d) : "N/A";
  };

  const scoreClass = (v, inverse = false) => {
    const n = Number(v);
    if (!Number.isFinite(n)) return "ia-muted";

    if (inverse) {
      if (n >= 7 切到其他分頁時，DOM 會真的消失
5. 不產生「庫存｜市場列表視圖」
