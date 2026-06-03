(() => {
  "use strict";

  const SUMMARY_PANEL_ID = "terminal-ia-summary-panel";
  const META_PANEL_ID = "terminal-ia-kpi-metadata-panel";
  const HOLDINGS_PANEL_ID = "terminal-ia-holdings-market-list";

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
      if (n >= 7) return "ia-bad";
      if (n >= 4) return "ia-warn";
      return "ia-ok";
    }

    if (n >= 7) return "ia-ok";
    if (n >= 4) return "ia-warn";
    return "ia-bad";
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

  function removeAllById(id, exceptNode = null) {
    document.querySelectorAll(`[id="${id}"]`).forEach((el) => {
      if (el !== exceptNode) el.remove();
    });
  }

  function removeIaPanels() {
    removeAllById(HOLDINGS_PANEL_ID);
  }

  function activeTickers(ledger) {
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

  function getVisibleSections() {
    return [...document.querySelectorAll("main section")].filter((section) => {
      const style = window.getComputedStyle(section);
      return style.display !== "none" && section.offsetParent !== null;
    });
  }

  function findSummarySection() {
    const visibleSections = getVisibleSections();

    return visibleSections.find((section) => {
      const text = section.textContent || "";
      return (
        text.includes("總資產淨值") ||
        text.includes("閒置現金") ||
        text.includes("股票市值") ||
        text.includes("NAV")
      );
    }) || null;
  }

  function isSummaryTabActive() {
    const activeNavButton = [...document.querySelectorAll("nav button")].find((button) => {
      const className = String(button.className || "");
      return className.includes("bg-white") || className.includes("text-slate-900");
    });

    if (activeNavButton) {
      return (activeNavButton.textContent || "").includes("總覽");
    }

    return Boolean(findSummarySection());
  }

  function ensurePanelInsideSummary(id, summarySection, position = "top") {
    if (!summarySection) return null;

    const existing = document.getElementById(id);

    if (existing && summarySection.contains(existing)) {
      return existing;
    }

    removeAllById(id);

    const panel = document.createElement("div");
    panel.id = id;

    if (position === "after-summary-panel") {
      const summaryPanel = document.getElementById(SUMMARY_PANEL_ID);
      if (summaryPanel && summarySection.contains(summaryPanel)) {
        summaryPanel.insertAdjacentElement("afterend", panel);
      } else {
        summarySection.insertBefore(panel, summarySection.firstChild);
      }
    } else {
      summarySection.insertBefore(panel, summarySection.firstChild);
    }

    return panel;
  }

  function makeAlerts(marketCompass, stockMeta, tickers) {
    const alerts = [];
    const dq = marketCompass?.data_quality || {};

    const add = (sev, title, detail, tag) => {
      alerts.push({ sev, title, detail, tag });
    };

    (marketCompass?.penalties || []).slice(0, 3).forEach((p) => {
      add("WARN", "市場環境扣分", p?.reason || String(p), "Market");
    });

    if (dq.overall && dq.overall !== "OK") {
      add("WARN", "資料品質不是完全 OK", `overall=${dq.overall}`, "Data");
    }

    if (
      marketCompass?.fred_status &&
      !["ON", "OK"].includes(String(marketCompass.fred_status).toUpperCase())
    ) {
      add("WARN", "FRED 資料源非 ON", `FRED=${marketCompass.fred_status}`, "Data");
    }

    tickers
      .map((ticker) => [ticker, stockMeta?.[ticker]])
      .filter(([, x]) => Number(x?.quant_health_score) < 4)
      .slice(0, 3)
      .forEach(([ticker, x]) => {
        add(
          "BAD",
          `${ticker} 量化健康度偏弱`,
          `健康度=${num(x?.quant_health_score, 2)}；風險=${num(x?.risk_score, 2)}`,
          "Holding"
        );
      });

    tickers
      .map((ticker) => [ticker, stockMeta?.[ticker]])
      .filter(([, x]) => {
        if (!x?.updated_at) return false;
        const ts = Date.parse(x.updated_at);
        return Number.isFinite(ts) && Date.now() - ts > 1000 * 60 * 60 * 24 * 10;
      })
      .slice(0, 3)
      .forEach(([ticker, x]) => {
        add("WARN", `${ticker} 更新時間偏舊`, `updated=${x?.updated_at || "N/A"}`, "Data");
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

  function renderSummaryPanel(summarySection) {
    const data = cache();
    const marketCompass = data?.macroMeta?.market_compass || {};
    const stockMeta = data?.stockMeta || {};
    const tickers = activeTickers(data?.ledgerData || []);
    const dq = marketCompass?.data_quality || {};
    const alerts = makeAlerts(marketCompass, stockMeta, tickers);

    const topRisk = tickers
      .map((ticker) => ({
        ticker,
        risk: Number(stockMeta?.[ticker]?.risk_score),
        health: Number(stockMeta?.[ticker]?.quant_health_score),
        quality: stockMeta?.[ticker]?.data_quality || "N/A"
      }))
      .filter((x) => Number.isFinite(x.risk))
      .sort((a, b) => b.risk - a.risk)
      .slice(0, 4);

    const panel = ensurePanelInsideSummary(SUMMARY_PANEL_ID, summarySection, "top");
    if (!panel) return;

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
              <div class="ia-note">來源：macro_meta.market_compass｜品質：${esc(dq?.overall || "N/A")}</div>
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
              <div class="ia-v ${qualityClass(dq?.overall || marketCompass?.fred_status)}">${esc(dq?.overall || "N/A")}</div>
              <div class="ia-note">FRED=${esc(marketCompass?.fred_status || dq?.fred_status || "N/A")}｜Credit=${esc(dq?.credit_quality || "N/A")}</div>
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
                  ${alerts.map((a) => `
                    <div class="ia-alert">
                      <div class="ia-alert-sev ${
                        a.sev === "BAD" ? "ia-bad" : a.sev === "WARN" ? "ia-warn" : "ia-ok"
                      }">${esc(a.sev)}</div>
                      <div>
                        <div class="ia-alert-title">${esc(a.title)}</div>
                        <div class="ia-alert-detail">${esc(a.detail)}</div>
                      </div>
                      <span class="ia-chip">${esc(a.tag)}</span>
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
                    ? topRisk.map((x) => `
                      <div class="ia-alert">
                        <div class="ia-alert-sev ${scoreClass(x.risk, true)}">${num(x.risk, 1)}</div>
                        <div>
                          <div class="ia-alert-title">${esc(x.ticker)}</div>
                          <div class="ia-alert-detail">健康度=${num(x.health, 2)}｜品質=${esc(x.quality)}</div>
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
                    <div class="ia-source-value">${esc(dq?.overall || "N/A")}</div>
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

  function renderMetadataPanel(summarySection) {
    const panel = ensurePanelInsideSummary(META_PANEL_ID, summarySection, "after-summary-panel");
    if (!panel) return;

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
    removeIaPanels();

    if (!isSummaryTabActive()) {
      removeAllById(SUMMARY_PANEL_ID);
      removeAllById(META_PANEL_ID);
      return;
    }

    const summarySection = findSummarySection();

    if (!summarySection) {
      removeAllById(SUMMARY_PANEL_ID);
      removeAllById(META_PANEL_ID);
      return;
    }

    renderSummaryPanel(summarySection);
    renderMetadataPanel(summarySection);
  }

  function boot() {
    let tries = 0;

    const timer = setInterval(() => {
      tries += 1;
      render();

      if (tries >= 12) {
        clearInterval(timer);
      }
    }, 800);

    document.querySelectorAll("nav button").forEach((button) => {
      button.addEventListener("click", () => {
        window.setTimeout(render, 180);
        window.setTimeout(render, 500);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
