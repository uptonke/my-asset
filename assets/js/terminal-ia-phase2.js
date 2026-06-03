(() => {
  "use strict";

  const SUMMARY_PANEL_ID = "terminal-ia-summary-panel";
  const HOLDINGS_PANEL_ID = "terminal-ia-holdings-market-list";
  const META_PANEL_ID = "terminal-ia-kpi-metadata-panel";

  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (m) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;"
  }[m]));

  const num = (v, d = 1) => Number.isFinite(Number(v)) ? Number(v).toFixed(d) : "N/A";

  const scoreClass = (v, inverse = false) => {
    const x = Number(v);
    if (!Number.isFinite(x)) return "ia-muted";
    if (inverse) return x >= 7 ? "ia-bad" : x >= 4 ? "ia-warn" : "ia-ok";
    return x >= 7 ? "ia-ok" : x >= 4 ? "ia-warn" : "ia-bad";
  };

  const qualityClass = (v) => {
    const s = String(v || "").toUpperCase();
    if (["OK", "ON", "FULL", "NORMAL"].includes(s)) return "ia-ok";
    if (["FAILED", "INVALID", "OFF", "ERROR"].includes(s)) return "ia-bad";
    return "ia-warn";
  };

  function cache() {
    return window.__quantMetaDisplayCache || {};
  }

  function activeTickers(ledger) {
    const m = new Map();
    (ledger || []).forEach((tx) => {
      const t = String(tx?.ticker || "").trim().toUpperCase();
      const type = String(tx?.type || "");
      if (!t || !["Buy", "Sell"].includes(type)) return;
      const sh = Number(tx?.shares) || 0;
      m.set(t, (m.get(t) || 0) + (type === "Buy" ? sh : -sh));
    });
    return [...m.entries()].filter(([, v]) => v > 0.0001).map(([t]) => t).sort();
  }

  function summaryAnchor() {
    return document.querySelector("#market-intelligence-summary-panel-v2") ||
      document.querySelector(".overview-dashboard") ||
      document.querySelector(".dashboard-overview") ||
      document.querySelector(".portfolio-overview") ||
      document.querySelector("#overview") ||
      document.querySelector("main");
  }

  function holdingsAnchor() {
    return document.querySelector(".holdings-terminal-view") ||
      document.querySelector("#quant-meta-inline-panel-v10")?.parentElement ||
      document.querySelector("main");
  }

  function ensureBefore(id, anchor) {
    if (!anchor?.parentNode) return null;
    let panel = document.getElementById(id);
    if (panel) return panel;
    panel = document.createElement("div");
    panel.id = id;
    anchor.parentNode.insertBefore(panel, anchor);
    return panel;
  }

  function ensureInsideTop(id, anchor) {
    if (!anchor) return null;
    let panel = document.getElementById(id);
    if (panel) return panel;
    panel = document.createElement("div");
    panel.id = id;
    anchor.insertBefore(panel, anchor.firstChild);
    return panel;
  }

  function makeAlerts(marketCompass, stockMeta, tickers) {
    const out = [];
    const dq = marketCompass?.data_quality || {};
    const add = (sev, title, detail, tag) => out.push({ sev, title, detail, tag });

    (marketCompass?.penalties || []).slice(0, 3).forEach((p) => {
      add("WARN", "市場環境扣分", p?.reason || String(p), "Market");
    });

    if (dq.overall && dq.overall !== "OK") add("WARN", "資料品質不是完全 OK", `overall=${dq.overall}`, "Data");
    if (marketCompass?.fred_status && !["ON", "OK"].includes(String(marketCompass.fred_status).toUpperCase())) {
      add("WARN", "FRED 資料源非 ON", `FRED=${marketCompass.fred_status}`, "Data");
    }

    tickers.map((t) => [t, stockMeta?.[t]])
      .filter(([, x]) => Number(x?.quant_health_score) < 4)
      .slice(0, 3)
      .forEach(([t, x]) => add("BAD", `${t} 量化健康度偏弱`, `健康度=${num(x?.quant_health_score, 2)}；風險=${num(x?.risk_score, 2)}`, "Holding"));

    if (Number(marketCompass?.adjusted_score) < 45) {
      add("BAD", "市場調整後分數偏弱", `Adjusted Score=${num(marketCompass.adjusted_score, 1)}/100`, "Market");
    }

    if (!out.length) add("OK", "目前沒有高優先級警報", "資料品質與主要風險訊號沒有觸發紅燈；仍需檢查資料更新時間。", "OK");
    return out.slice(0, 8);
  }

  function renderSummary() {
    const data = cache();
    const marketCompass = data?.macroMeta?.market_compass || {};
    const stockMeta = data?.stockMeta || {};
    const tickers = activeTickers(data?.ledgerData || []);
    const panel = ensureBefore(SUMMARY_PANEL_ID, summaryAnchor());
    if (!panel) return false;

    const dq = marketCompass?.data_quality || {};
    const alertRows = makeAlerts(marketCompass, stockMeta, tickers);
    const topRisk = tickers
      .map((t) => ({ ticker: t, risk: Number(stockMeta?.[t]?.risk_score), health: Number(stockMeta?.[t]?.quant_health_score), quality: stockMeta?.[t]?.data_quality || "N/A" }))
      .filter((x) => Number.isFinite(x.risk))
      .sort((a, b) => b.risk - a.risk)
      .slice(0, 4);

    panel.innerHTML = `
      <section class="ia-panel">
        <div class="ia-head">
          <div>
            <div class="ia-title">總覽｜市場狀態與優先檢查</div>
            <div class="ia-subtitle">首頁只保留可行動訊號：市場環境、資料品質、警報佇列與主要風險來源。</div>
          </div>
          <div class="ia-meta">updated=${esc(marketCompass?.date || "N/A")}<br>phase=ia2-passive</div>
        </div>
        <div class="ia-body">
          <div class="ia-grid">
            <div class="ia-kpi"><div class="ia-k">調整後分數</div><div class="ia-v ${scoreClass(marketCompass?.adjusted_score)}">${num(marketCompass?.adjusted_score, 1)}/100</div><div class="ia-note">來源：macro_meta.market_compass｜品質：${esc(dq?.overall || "N/A")}</div></div>
            <div class="ia-kpi"><div class="ia-k">原始分數</div><div class="ia-v ${scoreClass(marketCompass?.raw_score)}">${num(marketCompass?.raw_score, 1)}/100</div><div class="ia-note">算法：Market Compass raw modules</div></div>
            <div class="ia-kpi"><div class="ia-k">市場環境</div><div class="ia-v" style="font-size:13px">${esc(marketCompass?.regime || marketCompass?.label || "N/A")}</div><div class="ia-note">不輸出操作結論，只描述資料狀態。</div></div>
            <div class="ia-kpi"><div class="ia-k">資料品質</div><div class="ia-v ${qualityClass(dq?.overall || marketCompass?.fred_status)}">${esc(dq?.overall || "N/A")}</div><div class="ia-note">FRED=${esc(marketCompass?.fred_status || dq?.fred_status || "N/A")}｜Credit=${esc(dq?.credit_quality || "N/A")}</div></div>
          </div>

          <div class="ia-grid-3">
            <div class="ia-panel" style="margin:0">
              <div class="ia-head"><div><div class="ia-title">警報佇列</div><div class="ia-subtitle">依資料品質、扣分原因、單檔風險自動整理。</div></div></div>
              <div class="ia-body"><div class="ia-alert-list">
                ${alertRows.map((a) => `<div class="ia-alert"><div class="ia-alert-sev ${a.sev === "BAD" ? "ia-bad" : a.sev === "WARN" ? "ia-warn" : "ia-ok"}">${esc(a.sev)}</div><div><div class="ia-alert-title">${esc(a.title)}</div><div class="ia-alert-detail">${esc(a.detail)}</div></div><span class="ia-chip">${esc(a.tag)}</span></div>`).join("")}
              </div></div>
            </div>

            <div class="ia-panel" style="margin:0">
              <div class="ia-head"><div><div class="ia-title">主要風險來源</div><div class="ia-subtitle">以單檔 risk_score 排序，非完整風險貢獻模型。</div></div></div>
              <div class="ia-body">
                ${topRisk.length ? topRisk.map((x) => `<div class="ia-alert"><div class="ia-alert-sev ${scoreClass(x.risk, true)}">${num(x.risk, 1)}</div><div><div class="ia-alert-title">${esc(x.ticker)}</div><div class="ia-alert-detail">健康度=${num(x.health, 2)}｜品質=${esc(x.quality)}</div></div><span class="ia-chip">Risk</span></div>`).join("") : `<div class="ia-note">尚無可排序的 risk_score。</div>`}
              </div>
            </div>

            <div class="ia-panel" style="margin:0">
              <div class="ia-head"><div><div class="ia-title">資料口徑</div><div class="ia-subtitle">核心 KPI 來源與可信度。</div></div></div>
              <div class="ia-body"><div class="ia-metadata-grid" style="grid-template-columns:1fr">
                <div class="ia-source-card"><div class="ia-source-label">Market Compass</div><div class="ia-source-value">${esc(dq?.overall || "N/A")}</div></div>
                <div class="ia-source-card"><div class="ia-source-label">Stock Meta</div><div class="ia-source-value">${tickers.length} 檔</div></div>
                <div class="ia-source-card"><div class="ia-source-label">Ledger</div><div class="ia-source-value">${(data?.ledgerData || []).length} 筆</div></div>
              </div></div>
            </div>
          </div>
        </div>
      </section>
    `;
    return true;
  }

  function renderHoldings() {
    const data = cache();
    const stockMeta = data?.stockMeta || {};
    const tickers = activeTickers(data?.ledgerData || []);
    const panel = ensureInsideTop(HOLDINGS_PANEL_ID, holdingsAnchor());
    if (!panel) return false;

    const list = tickers.length ? tickers : Object.keys(stockMeta).sort();
    const latest = Object.values(stockMeta).map((x) => x?.updated_at).filter(Boolean).sort().slice(-1)[0] || "N/A";
    const rows = list.map((t) => {
      const x = stockMeta?.[t] || {};
      const signal = x.pivot_signal || "N/A";
      const signalClass = signal.includes("偏多") ? "ia-ok" : signal.includes("偏弱") ? "ia-bad" : "ia-warn";
      return `<tr><td><span class="ia-ticker">${esc(t)}</span><span class="ia-name">${esc(x.source || "N/A")}</span></td><td>${num(x.beta, 2)}</td><td><span class="ia-chip ${scoreClass(x.trend_score)}">${num(x.trend_score, 1)}</span></td><td><span class="ia-chip ${scoreClass(x.momentum_score)}">${num(x.momentum_score, 1)}</span></td><td><span class="ia-chip ${scoreClass(x.risk_score, true)}">${num(x.risk_score, 1)}</span></td><td><span class="ia-chip ${scoreClass(x.quant_health_score)}">${num(x.quant_health_score, 1)}</span></td><td>${esc(x.pivot_position_plain || x.pivot_status || "N/A")}</td><td><span class="ia-chip ${signalClass}">${esc(signal)}</span></td><td><span class="ia-chip ${qualityClass(x.data_quality)}">${esc(x.data_quality || "N/A")}</span></td><td>${esc(x.updated_at || "N/A")}</td></tr>`;
    }).join("");

    panel.innerHTML = `
      <section class="ia-panel">
        <div class="ia-head"><div><div class="ia-title">庫存｜市場列表視圖</div><div class="ia-subtitle">代號、Beta、趨勢、動能、風險、健康度、月線位置、綜合訊號、品質與更新。</div></div><div class="ia-meta">holdings=${list.length}<br>latest=${esc(latest)}</div></div>
        <div class="ia-table-wrap">
          <table class="ia-table">
            <thead><tr><th>代號</th><th>Beta</th><th>趨勢</th><th>動能</th><th>風險</th><th>健康度</th><th>月線位置</th><th>綜合訊號</th><th>品質</th><th>更新</th></tr></thead>
            <tbody>${rows || `<tr><td colspan="10">尚無 stock_meta / ledger 資料。</td></tr>`}</tbody>
          </table>
        </div>
      </section>
    `;
    return true;
  }

  function renderMetadata() {
    const anchor = document.getElementById(SUMMARY_PANEL_ID);
    if (!anchor) return false;
    let panel = document.getElementById(META_PANEL_ID);
    if (!panel) {
      panel = document.createElement("div");
      panel.id = META_PANEL_ID;
      anchor.insertAdjacentElement("afterend", panel);
    }

    panel.innerHTML = `
      <section class="ia-panel">
        <div class="ia-head"><div><div class="ia-title">KPI 來源與品質字典</div><div class="ia-subtitle">先建立統一口徑；後續再把每個原生 KPI 逐一掛上 tooltip。</div></div><div class="ia-meta">scope=frontend display</div></div>
        <div class="ia-body"><div class="ia-metadata-grid">
          <div class="ia-source-card"><div class="ia-source-label">NAV / TWR / MWR</div><div class="ia-source-value">Supabase ledger / frontend</div><div class="ia-note">品質取決於交易紀錄完整性。</div></div>
          <div class="ia-source-card"><div class="ia-source-label">Alpha / Beta</div><div class="ia-source-value">frontend / stock_meta</div><div class="ia-note">需標明 CAPM 假設或持倉加權。</div></div>
          <div class="ia-source-card"><div class="ia-source-label">MDD / VaR / CVaR</div><div class="ia-source-value">NAV history</div><div class="ia-note">需看樣本數與頻率。</div></div>
          <div class="ia-source-card"><div class="ia-source-label">Market Compass</div><div class="ia-source-value">macro_meta.market_compass</div><div class="ia-note">FRED / Yahoo / credit quality。</div></div>
          <div class="ia-source-card"><div class="ia-source-label">月線位置</div><div class="ia-source-value">stock_meta pivot</div><div class="ia-note">位置判讀，不是買賣建議。</div></div>
        </div></div>
      </section>
    `;
    return true;
  }

  function renderOnce() {
    renderSummary();
    renderHoldings();
    renderMetadata();
  }

  function boot() {
    let tries = 0;
    const timer = setInterval(() => {
      tries += 1;
      renderOnce();
      if (tries >= 10) clearInterval(timer);
    }, 1000);
  }

  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", boot) : boot();
})();
