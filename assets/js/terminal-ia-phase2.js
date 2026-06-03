(() => {
  "use strict";

  const SUMMARY_PANEL_ID = "terminal-ia-summary-panel";
  const META_PANEL_ID = "terminal-ia-kpi-metadata-panel";
  const OLD_HOLDINGS_PANEL_ID = "terminal-ia-holdings-market-list";

  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (m) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;"
  }[m]));

  const num = (v, d = 1) => Number.isFinite(Number(v)) ? Number(v).toFixed(d) : "N/A";

  const scoreClass = (v, inverse = false) => {
    const x = Number(v);
    if (!Number