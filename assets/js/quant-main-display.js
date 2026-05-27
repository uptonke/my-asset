(() => {
  "use strict";

  const PANEL_ID = "quant-meta-inline-panel-v2";
  const STYLE_ID = "quant-meta-inline-style-v2";
  const SUPABASE_URL = "https://yrccanqxzrcoknzabifz.supabase.co";
  const SUPABASE_KEY = "sb_publishable_lDfwRDxgMhzRwVk0-Qu3vg_9HTmTFZy";
  const TABLE = "portfolio_db";
  const ROW_ID = 1;

  let cache = {
    stockMeta: null,
    ledgerData: null,
    lastFetch: 0,
    error: null
  };

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      #${PANEL_ID}{margin-bottom:16px;border:1px solid rgba(255,255,255,.12);border-radius:18px;background:rgba(15,23,42,.78);backdrop-filter:blur(18px);box-shadow:0 18px 45px rgba(0,0,0,.24);overflow:hidden}
      #${PANEL_ID} .qmp-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:16px 18px;border-bottom:1px solid rgba(255,255,255,.10);background:linear-gradient(135deg,rgba(250,204,21,.08),rgba(56,189,248,.05))}
      #${PANEL_ID} .qmp-title{color:#fff;font-weight:900;letter-spacing:.02em;font-size:15px}
      #${PANEL_ID} .qmp-sub{color:rgba(203,213,225,.78);font-size:11px;line-height:1.6;margin-top:5px}
      #${PANEL_ID} .qmp-meta{color:rgba(148,163,184,.9);font-size:10px;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;text-align:right;white-space:nowrap}
      #${PANEL_ID} .qmp-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
      #${PANEL_ID} table{width:max-content;min-width:100%;border-collapse:collapse;font-size:12px;color:#e2e8f0}
      #${PANEL_ID} th{position:sticky;top:0;z-index:1;background:rgba(15,23,42,.96);color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:.08em;font-weight:800;padding:10px;border-bottom:1px solid rgba(255,255,255,.10);text-align:right;white-space:nowrap}
      #${PANEL_ID} td{padding:10px;border-bottom:1px solid rgba(255,255,255,.06);text-align:right;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;white-space:nowrap}
      #${PANEL_ID} th:first-child,#${PANEL_ID} td:first-child{text-align:left;position:sticky;left:0;background:rgba(15,23,42,.98);z-index:2}
      #${PANEL_ID} tr:hover td{background:rgba(255,255,255,.045)}
      #${PANEL_ID} .ticker{color:#fff;font-weight:900}
      #${PANEL_ID} .badge{display:inline-flex;align-items:center;justify-content:center;min-width:42px;padding:3px 7px;border-radius:999px;border:1px solid rgba(255,255,255,.10);background:rgba(255,255,255,.04);font-weight:800}
      #${PANEL_ID} .good{color:#f87171;background:rgba(239,68,68,.10);border-color:rgba(239,68,68,.18)}
      #${PANEL_ID} .mid{color:#facc15;background:rgba(250,204,21,.10);border-color:rgba(250,204,21,.18)}
      #${PANEL_ID} .bad{color:#4ade80;background:rgba(34,197,94,.10);border-color:rgba(34,197,94,.18)}
      #${PANEL_ID} .risk-high{color:#f87171;background:rgba(239,68,68,.10);border-color:rgba(239,68,68,.18)}
      #${PANEL_ID} .risk-mid{color:#facc15;background:rgba(250,204,21,.10);border-color:rgba(250,204,21,.18)}
      #${PANEL_ID} .risk-low{color:#4ade80;background:rgba(34,197,94,.10);border-color:rgba(34,197,94,.18)}
      #${PANEL_ID} .quality-ok{color:#4ade80}
      #${PANEL_ID} .quality-thin{color:#facc15}
      #${PANEL_ID} .quality-stale{color:#fb7185}
      #${PANEL_ID} .src{max-width:190px;overflow:hidden;text-overflow:ellipsis;display:inline-block;vertical-align:bottom;color:#93c5fd}
      #${PANEL_ID} .qmp-empty{padding:16px 18px;color:#94a3b8;font-size:12px;line-height:1.7}
      @media(max-width:768px){#${PANEL_ID}{border-radius:14px;margin:0 6px 14px}#${PANEL_ID} .qmp-head{flex-direction:column;padding:14px}#${PANEL_ID} .qmp-meta{text-align:left}#${PANEL_ID} th,#${PANEL_ID} td{padding:9px 8px;font-size:11px}}
    `;
    document.head.appendChild(style);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function num(value, digits = 2) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toFixed(digits) : "N/A";
  }

  function scoreClass(value, inverse = false) {
    const n = Number(value);
    if (!Number.isFinite(n)) return "";
    if (!inverse) return n >= 7 ? "good" : n >= 4 ? "mid" : "bad";
    return n >= 7 ? "risk-high" : n >= 4 ? "risk-mid" : "risk-low";
  }

  function qualityClass(value) {
    const q = String(value || "").toLowerCase();
    if (q === "ok") return "quality-ok";
    if (q === "thin") return "quality-thin";
    if (q === "stale") return "quality-stale";
    return "";
  }

  function sourceLabel(value) {
    return String(value || "N/A")
      .replace("YahooChart:", "YC:")
      .replace("yfinance:", "YF:")
      .replace("FinMind", "FinMind");
  }

  function ensurePanel() {
    let panel = document.getElementById(PANEL_ID);
    if (panel) return panel;

    const section = document.querySelector(".holdings-terminal-view");
    if (!section) return null;

    panel = document.createElement("div");
    panel.id = PANEL_ID;
    section.insertBefore(panel, section.firstChild);
    return panel;
  }

  function getTickersFromLedger(ledgerData) {
    const map = new Map();
    (ledgerData || []).forEach((tx) => {
      const ticker = String(tx?.ticker || "").trim().toUpperCase();
      if (!ticker) return;
      const type = String(tx?.type || "");
      if (type !== "Buy" && type !== "Sell") return;
      const shares = Number(tx?.shares) || 0;
      map.set(ticker, (map.get(ticker) || 0) + (type === "Buy" ? shares : -shares));
    });
    return Array.from(map.entries())
      .filter(([, shares]) => shares > 0.0001)
      .map(([ticker]) => ticker)
      .sort();
  }

  async function fetchSupabaseData(force = false) {
    const now = Date.now();
    if (!force && cache.stockMeta && now - cache.lastFetch < 60000) return cache;

    if (!window.supabase?.createClient) {
      cache.error = "Supabase JS library not loaded.";
      return cache;
    }

    try {
      const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
      const { data, error } = await client
        .from(TABLE)
        .select("stock_meta, ledger_data")
        .eq("id", ROW_ID)
        .single();

      if (error) throw error;

      cache.stockMeta = data?.stock_meta || {};
      cache.ledgerData = data?.ledger_data || [];
      cache.lastFetch = now;
      cache.error = null;
      window.__quantMetaDisplayCache = cache;
      return cache;
    } catch (err) {
      cache.error = err?.message || String(err);
      window.__quantMetaDisplayCache = cache;
      return cache;
    }
  }

  function buildRow(ticker, meta) {
    return `
      <tr>
        <td><span class="ticker">${escapeHtml(ticker)}</span></td>
        <td><span class="badge">${num(meta.beta, 2)}</span></td>
        <td><span class="badge ${scoreClass(meta.trend_score)}">${num(meta.trend_score, 2)}</span></td>
        <td><span class="badge ${scoreClass(meta.momentum_score)}">${num(meta.momentum_score, 2)}</span></td>
        <td><span class="badge ${scoreClass(meta.risk_score, true)}">${num(meta.risk_score, 2)}</span></td>
        <td><span class="badge ${scoreClass(meta.technical_score)}">${num(meta.technical_score, 2)}</span></td>
        <td><span class="badge ${scoreClass(meta.valuation_score)}">${num(meta.valuation_score, 2)}</span></td>
        <td><span class="badge ${scoreClass(meta.chip_score)}">${num(meta.chip_score, 2)}</span></td>
        <td><span class="badge ${scoreClass(meta.quant_health_score)}">${num(meta.quant_health_score, 2)}</span></td>
        <td><span class="${qualityClass(meta.data_quality)}">${escapeHtml(meta.data_quality || "N/A")}</span></td>
        <td><span class="src" title="${escapeHtml(meta.source || "N/A")}">${escapeHtml(sourceLabel(meta.source))}</span></td>
        <td>${escapeHtml(meta.updated_at || "N/A")}</td>
      </tr>
    `;
  }

  async function render(force = false) {
    injectStyle();
    const panel = ensurePanel();
    if (!panel) return;

    const data = await fetchSupabaseData(force);
    const stockMeta = data.stockMeta || {};
    const tickersFromLedger = getTickersFromLedger(data.ledgerData || []);
    const tickers = tickersFromLedger.length ? tickersFromLedger : Object.keys(stockMeta).sort();

    const latestUpdated = tickers
      .map((t) => stockMeta?.[t]?.updated_at)
      .filter(Boolean)
      .sort()
      .slice(-1)[0] || "N/A";

    if (data.error) {
      panel.innerHTML = `
        <div class="qmp-head">
          <div>
            <div class="qmp-title">量化因子總覽 <span style="color:#fb7185">Load failed</span></div>
            <div class="qmp-sub">讀取 Supabase stock_meta 失敗。原因：${escapeHtml(data.error)}</div>
          </div>
        </div>
      `;
      return;
    }

    if (!tickers.length) {
      panel.innerHTML = `
        <div class="qmp-head">
          <div>
            <div class="qmp-title">量化因子總覽 <span style="color:#facc15">Quant Meta</span></div>
            <div class="qmp-sub">尚未讀到 stock_meta。請先確認 GitHub Actions dry_run=false 已成功寫入 Supabase。</div>
          </div>
        </div>
      `;
      return;
    }

    panel.innerHTML = `
      <div class="qmp-head">
        <div>
          <div class="qmp-title">量化因子總覽 <span style="color:#facc15">Quant Meta</span></div>
          <div class="qmp-sub">直接讀 Supabase portfolio_db.stock_meta。Beta 顯示小數點後兩位；Risk 越高代表風險越高，其餘 score 越高通常越佳。</div>
        </div>
        <div class="qmp-meta">holdings=${tickers.length}<br>latest=${escapeHtml(latestUpdated)}</div>
      </div>
      <div class="qmp-wrap">
        <table>
          <thead>
            <tr>
              <th>Ticker</th><th>Beta</th><th>Trend</th><th>Momentum</th><th>Risk</th><th>Technical</th><th>Valuation</th><th>Chip</th><th>Health</th><th>Quality</th><th>Source</th><th>Updated</th>
            </tr>
          </thead>
          <tbody>
            ${tickers.map((ticker) => buildRow(ticker, stockMeta[ticker] || {})).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function boot() {
    let tries = 0;
    const timer = setInterval(() => {
      tries += 1;
      render(false);
      if (tries >= 12 && document.querySelector(".holdings-terminal-view")) clearInterval(timer);
    }, 800);

    document.addEventListener("click", () => setTimeout(() => render(false), 250), true);
    document.addEventListener("change", () => setTimeout(() => render(true), 300), true);
    setInterval(() => render(true), 120000);
  }

  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", boot) : boot();
})();
