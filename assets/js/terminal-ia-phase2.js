(() => {
  "use strict";

  const SUMMARY_PANEL_ID = "terminal-ia-summary-panel";
  const META_PANEL_ID = "terminal-ia-kpi-metadata-panel";
  const HOLDINGS_PANEL_ID = "terminal-ia-holdings-market-list";

  let currentTabLabel = "總覽";

  const esc = (value) =>
    String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#039;"
    }[char]));

  const num = (value, digits = 1) => {
    const n = Number(value);
    return Number.isFinite(n) ? n.toFixed(digits) : "N/A";
  };

  const scoreClass = (value, inverse = false) => {
    const n = Number(value);
    if (!Number.isFinite(n)) return "ia-muted";

    if (inverse) {
      if (n >= 7) return "ia-bad";
      if (n >= 4) return "ia-warn";
      return "ia-ok";
    }

    if (n >= 7) return "ia-ok";
    if (n >= 4) return "ia-warn";
    return "ia-bad";
  };

  const qualityClass = (value) => {
    const s = String(value || "").toUpperCase();
    if (["OK", "ON", "FULL", "NORMAL"].includes(s)) return "ia-ok";
    if (["FAILED", "INVALID", "OFF", "ERROR"].includes(s)) return "ia-bad";
    return "ia-warn";
  };

  function getCache() {
    return window.__quantMetaDisplayCache || {};
  }

  function removePanel(id) {
    document.querySelectorAll(`[id="${id}"]`).forEach((el) => el.remove());
  }

  function removeAllIaPanels() {
    removePanel(SUMMARY_PANEL_ID);
    removePanel(META_PANEL_ID);
    removePanel(HOLDINGS_PANEL_ID);
  }

  function getMainContainer() {
    return (
      document.querySelector("main > div") ||
      document.querySelector("main") ||
      document.body
    );
  }

  function getActiveNavText() {
    const buttons = [...document.querySelectorAll("nav button")];

    const activeButton = buttons.find((button) => {
      const cls = String(button.className || "");
      return cls.includes("bg-white") || cls.includes("text-slate-900");
    });

    return (activeButton?.textContent || currentTabLabel || "").trim();
  }

  function isSummaryActive() {
    const text = getActiveNavText();
    return text.includes("總覽");
  }

  function ensurePanel(id, afterId = null) {
    let panel = document.getElementById(id);
    if (panel) return panel;

    const main = getMainContainer();
    panel = document.createElement("div");
    panel.id = id;

    if (afterId) {
      const afterNode = document.getElementById(afterId);
      if (afterNode?.parentNode) {
        afterNode.insertAdjacentElement("afterend", panel);
        return panel;
      }
    }

    main.insertBefore(panel, main.firstChild);
    return panel;
  }

  function getActiveTickers(ledger) {
    const map = new Map();

    (ledger || []).forEach((tx) => {
      const ticker = String(tx?.ticker || "").trim().toUpperCase();
      const type = String(tx?.type || "");
      const shares = Number(tx?.shares) || 0;

      if (!ticker || !["Buy", "Sell"].includes(type)) return;

      map.set(ticker, (map.get(ticker) || 0) + (type === "Buy" ? shares : -shares));
    });

    return [...map.entries()]
      .filter(([, shares]) => shares > 0.0001)
      .map(([ticker]) => ticker)
      .sort();
  }

  function makeAlerts(marketCompass, stockMeta, tickers) {
    const alerts = [];
    const dataQuality = marketCompass?.data_quality || {};

    const add = (severity, title, detail, tag) => {
      alerts.push({ severity, title, detail, tag });
    };

    (marketCompass?.penalties || []).slice(0, 3).forEach((penalty) => {
      add("WARN", "市場環境扣分", penalty?.reason || String(penalty), "Market");
    });

    if (dataQuality.overall && dataQuality.overall !== "OK") {
      add("WARN", "資料品質不是完全 OK", `overall=${dataQuality.overall}`, "Data");
    }

    if (
      marketCompass?.fred_status &&
      !["ON", "OK"].includes(String(marketCompass.fred_status).toUpperCase())
    ) {
      add("WARN", "FRED 資料源非 ON", `FRED=${marketCompass.fred_status}`, "Data");
    }

    tickers
      .map((ticker) => [ticker, stockMeta?.[ticker]])
      .filter(([, meta]) => Number(meta?.quant_health_score) < 4)
      .slice(0, 3)
      .forEach(([ticker, meta]) => {
        add(
          "BAD",
          `${ticker} 量化健康度偏弱`,
          `健康度=${num(meta?.quant_health_score, 2)}；風險=${num(meta?.risk_score, 2)}`,
          "Holding"
        );
      });

    if (Number(marketCompass?.adjusted_score) < 45) {
      add(
        "BAD",
        "市場調整後分數偏弱",
        `Adjusted Score=${num(marketCompass.adjusted_score, 1)}/100`,
        "Market"
      );
    }

    if (!alerts.length) {
      add(
        "OK",
        "目前沒有高優先級警報",
        "資料品質與主要風險訊號沒有觸發紅燈；仍需檢查資料更新時間。",
        "OK"
      );
    }

    return alerts.slice(0, 8);
  }

  function renderSummaryPanel() {
    const data = getCache();
    const marketCompass = data?.macroMeta?.market_compass || {};
    const stockMeta = data?.stockMeta || {};
    const tickers = getActiveTickers(data?.ledgerData || []);
    const dataQuality = marketCompass?.data_quality || {};
    const alerts = makeAlerts(marketCompass, stockMeta, tickers);

    const topRisk = tickers
      .map((ticker) => ({
        ticker,
        risk: Number(stockMeta?.[ticker]?.risk_score),
        health: Number(stockMeta?.[ticker]?.quant_health_score),
        quality: stockMeta?.[ticker]?.data_quality || "N/A"
      }))
      .filter((item) => Number.isFinite(item.risk))
      .sort((a, b) => b.risk - a.risk)
      .slice(0, 4);

    const panel = ensurePanel(SUMMARY_PANEL_ID);

    panel.innerHTML = `
      <section class="ia-panel">
        <div class="ia-head">
          <div>
            <div class="ia-title">總覽｜市場狀態與優先檢查</div>
            <div class="ia-subtitle">只放在總覽頁：市場環境、資料品質、警報佇列與主要風險來源。</div>
          </div>
          <div class="ia-meta">updated=${esc(marketCompass?.date || "N/A")}<br>phase=summary-only</div>
        </div>

        <div class="ia-body">
          <div class="ia-grid">
            <div class="ia-kpi">
              <div class="ia-k">調整後分數</div>
              <div class="ia-v ${scoreClass(marketCompass?.adjusted_score)}">${num(marketCompass?.adjusted_score, 1)}/100</div>
              <div class="ia-note">來源：macro_meta.market_compass｜品質：${esc(dataQuality?.overall || "N/A")}</div>
            </div>

            <div class="ia-kpi">
              <div class="ia-k">原始分數</div>
              <div class="ia-v ${scoreClass(marketCompass?.raw_score)}">${num(marketCompass?.raw_score, 1)}/100</div>
              <div class="ia-note">算法：Market Compass raw modules</div>
            </div>

            <div class="ia-kpi">
              <div class="ia-k">市場環境</div>
              <div class="ia-v" style="font-size:13px">${esc(marketCompass?.regime || marketCompass?.label || "N/A")}</div>
              <div class="ia-note">不輸出操作結論，只描述資料狀態。</div>
            </div>

            <div class="ia-kpi">
              <div class="ia-k">資料品質</div>
              <div class="ia-v ${qualityClass(dataQuality?.overall || marketCompass?.fred_status)}">${esc(dataQuality?.overall || "N/A")}</div>
              <div class="ia-note">FRED=${esc(marketCompass?.fred_status || dataQuality?.fred_status || "N/A")}｜Credit=${esc(dataQuality?.credit_quality || "N/A")}</div>
            </div>
          </div>

          <div class="ia-grid-3">
            <div class="ia-panel" style="margin:0">
              <div class="ia-head">
                <div>
                  <div class="ia-title">警報佇列</div>
                  <div class="ia-subtitle">依資料品質、扣分原因、單檔風險整理。</div>
                </div>
              </div>
              <div class="ia-body">
                <div class="ia-alert-list">
                  ${alerts.map((alert) => `
                    <div class="ia-alert">
                      <div class="ia-alert-sev ${
                        alert.severity === "BAD" ? "ia-bad" :
                        alert.severity === "WARN" ? "ia-warn" :
                        "ia-ok"
                      }">${esc(alert.severity)}</div>
                      <div>
                        <div class="ia-alert-title">${esc(alert.title)}</div>
                        <div class="ia-alert-detail">${esc(alert.detail)}</div>
                      </div>
                      <span class="ia-chip">${esc(alert.tag)}</span>
                    </div>
                  `).join("")}
                </div>
              </div>
            </div>

            <div class="ia-panel" style="margin:0">
              <div class="ia-head">
                <div>
                  <div class="ia-title">主要風險來源</div>
                  <div class="ia-subtitle">以單檔 risk_score 排序，非完整風險貢獻模型。</div>
                </div>
              </div>
              <div class="ia-body">
                ${
                  topRisk.length
                    ? topRisk.map((item) => `
                      <div class="ia-alert">
                        <div class="ia-alert-sev ${scoreClass(item.risk, true)}">${num(item.risk, 1)}</div>
                        <div>
                          <div class="ia-alert-title">${esc(item.ticker)}</div>
                          <div class="ia-alert-detail">健康度=${num(item.health, 2)}｜品質=${esc(item.quality)}</div>
                        </div>
                        <span class="ia-chip">Risk</span>
                      </div>
                    `).join("")
                    : `<div class="ia-note">尚無可排序的 risk_score。</div>`
                }
              </div>
            </div>

            <div class="ia-panel" style="margin:0">
              <div class="ia-head">
                <div>
                  <div class="ia-title">資料口徑</div>
                  <div class="ia-subtitle">核心資料來源與可信度。</div>
                </div>
              </div>
              <div class="ia-body">
                <div class="ia-metadata-grid" style="grid-template-columns:1fr">
                  <div class="ia-source-card">
                    <div class="ia-source-label">Market Compass</div>
                    <div class="ia-source-value">${esc(dataQuality?.overall || "N/A")}</div>
                  </div>
                  <div class="ia-source-card">
                    <div class="ia-source-label">Stock Meta</div>
                    <div class="ia-source-value">${tickers.length} 檔</div>
                  </div>
                  <div class="ia-source-card">
                    <div class="ia-source-label">Ledger</div>
                    <div class="ia-source-value">${(data?.ledgerData || []).length} 筆</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    `;
  }

  function renderMetadataPanel() {
    const panel = ensurePanel(META_PANEL_ID, SUMMARY_PANEL_ID);

    panel.innerHTML = `
      <section class="ia-panel">
        <div class="ia-head">
          <div>
            <div class="ia-title">KPI 來源與品質字典</div>
            <div class="ia-subtitle">只放在總覽頁；用來說明核心指標來源與可信度。</div>
          </div>
          <div class="ia-meta">scope=frontend display</div>
        </div>

        <div class="ia-body">
          <div class="ia-metadata-grid">
            <div class="ia-source-card">
              <div class="ia-source-label">NAV / TWR / MWR</div>
              <div class="ia-source-value">Supabase ledger / frontend</div>
              <div class="ia-note">品質取決於交易紀錄完整性。</div>
            </div>

            <div class="ia-source-card">
              <div class="ia-source-label">Alpha / Beta</div>
              <div class="ia-source-value">frontend / stock_meta</div>
              <div class="ia-note">需標明 CAPM 假設或持倉加權。</div>
            </div>

            <div class="ia-source-card">
              <div class="ia-source-label">MDD / VaR / CVaR</div>
              <div class="ia-source-value">NAV history</div>
              <div class="ia-note">需看樣本數與頻率。</div>
            </div>

            <div class="ia-source-card">
              <div class="ia-source-label">Market Compass</div>
              <div class="ia-source-value">macro_meta.market_compass</div>
              <div class="ia-note">FRED / Yahoo / credit quality。</div>
            </div>

            <div class="ia-source-card">
              <div class="ia-source-label">月線位置</div>
              <div class="ia-source-value">stock_meta pivot</div>
              <div class="ia-note">位置判讀，不是買賣建議。</div>
            </div>
          </div>
        </div>
      </section>
    `;
  }

  function render() {
    removeAllIaPanels();

    if (!isSummaryActive()) {
      return;
    }

    renderSummaryPanel();
    renderMetadataPanel();
  }

  function bindNavButtons() {
    document.querySelectorAll("nav button").forEach((button) => {
      button.addEventListener("click", () => {
        currentTabLabel = (button.textContent || "").trim();

        removeAllIaPanels();

        window.setTimeout(render, 80);
        window.setTimeout(render, 260);
      });
    });
  }

  function boot() {
    const activeButton = [...document.querySelectorAll("nav button")].find((button) => {
      const cls = String(button.className || "");
      return cls.includes("bg-white") || cls.includes("text-slate-900");
    });

    currentTabLabel = (activeButton?.textContent || "總覽").trim();

    bindNavButtons();

    let tries = 0;
    const timer = window.setInterval(() => {
      tries += 1;
      render();

      if (tries >= 8) {
        window.clearInterval(timer);
      }
    }, 900);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
