(() => {
  "use strict";

  const Q_PANEL_ID = "quant-meta-inline-panel-v9";
  const MI_SUMMARY_ID = "market-intelligence-summary-panel-v2";
  const MI_ANALYSIS_ID = "market-intelligence-analysis-panel-v2";
  const STYLE_ID = "quant-market-intelligence-style-v9";
  const SUPABASE_URL = "https://yrccanqxzrcoknzabifz.supabase.co";
  const SUPABASE_KEY = "sb_publishable_lDfwRDxgMhzRwVk0-Qu3vg_9HTmTFZy";
  const TABLE = "portfolio_db";
  const ROW_ID = 1;

  let cache = { stockMeta: null, ledgerData: null, macroMeta: null, lastFetch: 0, error: null };

  const $ = (sel) => document.querySelector(sel);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[m]));
  const n = (v, d = 1) => Number.isFinite(Number(v)) ? Number(v).toFixed(d) : "N/A";
  const pct = (v) => Number.isFinite(Number(v)) ? `${Number(v) >= 0 ? "+" : ""}${Number(v).toFixed(2)}%` : "N/A";
  const arr = (v) => Array.isArray(v) ? v : [];
  const statusClass = (v) => {
    const s = String(v || "").toUpperCase();
    if (["OK", "ON", "FULL", "NORMAL"].includes(s)) return "ok";
    if (["OFF", "FAILED", "INVALID", "PROXY_ONLY"].includes(s)) return "bad";
    return "mid";
  };
  const scoreClass = (v, inverse = false) => {
    const x = Number(v);
    if (!Number.isFinite(x)) return "";
    if (inverse) return x >= 7 ? "bad" : x >= 4 ? "mid" : "ok";
    return x >= 7 ? "ok" : x >= 4 ? "mid" : "bad";
  };

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    const s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = `
      #${Q_PANEL_ID},#${MI_SUMMARY_ID},#${MI_ANALYSIS_ID}{margin:0 0 16px;border:1px solid rgba(255,255,255,.12);border-radius:18px;background:rgba(15,23,42,.80);backdrop-filter:blur(18px);box-shadow:0 18px 45px rgba(0,0,0,.22);overflow:hidden;color:#e2e8f0}
      .qmi-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:16px 18px;border-bottom:1px solid rgba(255,255,255,.10);background:linear-gradient(135deg,rgba(250,204,21,.08),rgba(56,189,248,.05))}
      .qmi-title{color:#fff;font-weight:900;font-size:15px;letter-spacing:.02em}.qmi-sub{color:#94a3b8;font-size:11px;line-height:1.6;margin-top:5px}.qmi-meta{color:#94a3b8;font:10px ui-monospace,SFMono-Regular,Menlo,monospace;text-align:right;white-space:nowrap}
      .qmi-body{padding:16px 18px;display:grid;gap:12px}.qmi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.qmi-grid6{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}
      .qmi-card{border:1px solid rgba(255,255,255,.10);border-radius:14px;padding:12px;background:rgba(0,0,0,.18)}.qmi-k{color:#94a3b8;font-size:9px;text-transform:uppercase;letter-spacing:.12em;font-weight:900}.qmi-v{margin-top:5px;color:#fff;font-weight:900;font:18px ui-monospace,SFMono-Regular,Menlo,monospace}.qmi-note{margin-top:6px;color:#94a3b8;font-size:10px;line-height:1.5}
      .qmi-pill{display:inline-flex;align-items:center;gap:6px;border:1px solid rgba(255,255,255,.12);border-radius:999px;padding:5px 9px;font-size:12px;font-weight:900}.ok{color:#4ade80}.mid{color:#facc15}.bad{color:#fb7185}.qmi-section{border:1px solid rgba(255,255,255,.10);border-radius:14px;padding:12px;background:rgba(255,255,255,.035);font-size:12px;line-height:1.65}.qmi-section.warn{border-color:rgba(251,113,133,.20);background:rgba(239,68,68,.06);color:#fecdd3}.qmi-label{color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:.12em;font-weight:900;margin-bottom:6px}
      #${Q_PANEL_ID} .qwrap{overflow-x:auto}#${Q_PANEL_ID} table{width:max-content;min-width:100%;border-collapse:collapse;font-size:12px}#${Q_PANEL_ID} th,#${Q_PANEL_ID} td{padding:10px;border-bottom:1px solid rgba(255,255,255,.07);text-align:right;white-space:nowrap}#${Q_PANEL_ID} th{color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:.08em;background:rgba(15,23,42,.96)}#${Q_PANEL_ID} th:first-child,#${Q_PANEL_ID} td:first-child{text-align:left;position:sticky;left:0;background:rgba(15,23,42,.98);z-index:2}.badge{display:inline-flex;min-width:42px;justify-content:center;border-radius:999px;border:1px solid rgba(255,255,255,.10);padding:3px 7px;background:rgba(255,255,255,.04);font-weight:800}.ticker{font-weight:900;color:#fff}
      details.qmi-details>summary{cursor:pointer;color:#93c5fd;font-weight:900;margin-bottom:8px}
      @media(max-width:1000px){.qmi-grid,.qmi-grid6{grid-template-columns:repeat(2,minmax(0,1fr))}.qmi-head{flex-direction:column}.qmi-meta{text-align:left}}
    `;
    document.head.appendChild(s);
  }

  async function fetchData(force = false) {
    const now = Date.now();
    if (!force && cache.stockMeta && now - cache.lastFetch < 60000) return cache;
    if (!window.supabase?.createClient) {
      cache.error = "Supabase JS 尚未載入";
      return cache;
    }
    try {
      const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
      const { data, error } = await client.from(TABLE).select("stock_meta,ledger_data,macro_meta").eq("id", ROW_ID).single();
      if (error) throw error;
      cache = { stockMeta: data?.stock_meta || {}, ledgerData: data?.ledger_data || [], macroMeta: data?.macro_meta || {}, lastFetch: now, error: null };
    } catch (e) {
      cache.error = e?.message || String(e);
    }
    window.__quantMetaDisplayCache = cache;
    return cache;
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

  function zone(meta, side) {
    const lo = Number(meta?.[`pivot_${side}_zone_low`]);
    const hi = Number(meta?.[`pivot_${side}_zone_high`]);
    const dist = meta?.[`pivot_${side}_distance_pct`];
    if (!Number.isFinite(lo) || !Number.isFinite(hi)) return "N/A";
    const z = Math.abs(lo - hi) < Math.max(Math.abs(lo), 1) * 0.0005 ? ((lo + hi) / 2).toFixed(2) : `${lo.toFixed(2)}–${hi.toFixed(2)}`;
    return `${z}<br><span style="color:#94a3b8;font-size:10px">${esc(pct(dist))}</span>`;
  }

  function ensureQuantPanel() {
    let p = document.getElementById(Q_PANEL_ID);
    if (p) return p;
    const anchor = $(".holdings-terminal-view");
    if (!anchor) return null;
    p = document.createElement("div");
    p.id = Q_PANEL_ID;
    anchor.insertBefore(p, anchor.firstChild);
    return p;
  }

  function ensureAnalysisPanel() {
    let p = document.getElementById(MI_ANALYSIS_ID);
    if (p) return p;
    const anchor = $(".analytics-command-toolbar") || $(".analytics-panel") || $("#analysis");
    if (!anchor?.parentNode) return null;
    p = document.createElement("div");
    p.id = MI_ANALYSIS_ID;
    anchor.parentNode.insertBefore(p, anchor);
    return p;
  }

  function ensureSummaryPanel() {
    let p = document.getElementById(MI_SUMMARY_ID);
    if (p) return p;
    const anchors = [".overview-dashboard", ".dashboard-overview", ".portfolio-overview", ".main-dashboard", "#overview", ".analytics-command-toolbar"];
    const anchor = anchors.map((s) => $(s)).find(Boolean);
    if (!anchor?.parentNode) return null;
    p = document.createElement("div");
    p.id = MI_SUMMARY_ID;
    anchor.parentNode.insertBefore(p, anchor);
    return p;
  }

  function renderQuant(data) {
    const p = ensureQuantPanel();
    if (!p) return;
    if (data.error) {
      p.innerHTML = `<div class="qmi-head"><div><div class="qmi-title">量化因子總覽讀取失敗</div><div class="qmi-sub">${esc(data.error)}</div></div></div>`;
      return;
    }
    const meta = data.stockMeta || {};
    const tickers = activeTickers(data.ledgerData);
    const list = tickers.length ? tickers : Object.keys(meta).sort();
    const latest = list.map((t) => meta?.[t]?.updated_at).filter(Boolean).sort().slice(-1)[0] || "N/A";
    const rows = list.map((t) => {
      const x = meta[t] || {};
      return `<tr><td><span class="ticker">${esc(t)}</span></td><td>${n(x.beta,2)}</td><td><span class="badge ${scoreClass(x.trend_score)}">${n(x.trend_score,2)}</span></td><td><span class="badge ${scoreClass(x.momentum_score)}">${n(x.momentum_score,2)}</span></td><td><span class="badge ${scoreClass(x.risk_score,true)}">${n(x.risk_score,2)}</span></td><td>${n(x.technical_score,2)}</td><td>${n(x.valuation_score,2)}</td><td>${n(x.chip_score,2)}</td><td><span class="badge ${scoreClass(x.quant_health_score)}">${n(x.quant_health_score,2)}</span></td><td>${zone(x,"support")}</td><td>${zone(x,"resistance")}</td><td>${esc(x.pivot_status || "N/A")}</td><td>${esc(x.data_quality || "N/A")}</td><td>${esc(x.source || "N/A")}</td><td>${esc(x.updated_at || "N/A")}</td></tr>`;
    }).join("");
    p.innerHTML = `<div class="qmi-head"><div><div class="qmi-title">量化因子總覽</div><div class="qmi-sub">庫存頁只放單檔資料：Beta、趨勢、動能、風險、健康度與月線支撐/壓力。</div></div><div class="qmi-meta">持倉數=${list.length}<br>最新=${esc(latest)}</div></div><div class="qwrap"><table><thead><tr><th>代號</th><th>Beta</th><th>趨勢</th><th>動能</th><th>風險</th><th>技術</th><th>估值</th><th>籌碼</th><th>健康度</th><th>月支撐</th><th>月壓力</th><th>樞軸狀態</th><th>品質</th><th>來源</th><th>更新</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  function chip(k, v) {
    return `<div class="qmi-card"><div class="qmi-k">${esc(k)}</div><div class="qmi-v ${statusClass(v)}">${esc(v ?? "N/A")}</div></div>`;
  }

  function list(items) {
    return arr(items).length ? arr(items).map((x) => `<div>• ${esc(x?.reason || x)}</div>`).join("") : "<div>• N/A</div>";
  }

  function moduleCard(key, mod) {
    const names = { trend: "Trend 趨勢", breadth: "Breadth 廣度", credit: "Credit 信用", volatility: "Volatility 波動", liquidity: "Liquidity 流動性", cross_asset: "Cross-Asset 跨資產" };
    const score = Number(mod?.score);
    return `<div class="qmi-card"><div class="qmi-k">${names[key] || key}</div><div class="qmi-v ${scoreClass(score)}">${Number.isFinite(score) ? score.toFixed(1) : "N/A"}</div><div class="qmi-note"><b>${esc(mod?.label || "")}</b><br>${esc(mod?.note || "")}</div></div>`;
  }

  function officialChips(official) {
    const twse = official?.twse?.errors?.length ?? 0;
    const treas = official?.us_treasury?.errors?.length ?? 0;
    const wb = official?.world_bank?.errors?.length ?? 0;
    const opt = official?.optional_global_sources?.missing_config?.length ?? 0;
    return [chip("TWSE errors", String(twse)), chip("Treasury errors", String(treas)), chip("World Bank errors", String(wb)), chip("Optional missing", String(opt))].join("");
  }

  function aiBlock(ai, compact = false) {
    if (!ai) return "";
    const engine = ai.analysis_engine || ai.engine || "rule_based";
    if (compact) {
      return `<div class="qmi-section"><div class="qmi-label">AI 數據深度分析摘要</div><div>${esc(ai.market_structure || ai.summary || "N/A")}</div><div class="qmi-note">engine=${esc(engine)}${ai.fallback_used ? "｜fallback" : ""}</div></div>`;
    }
    return `<div class="qmi-section"><div class="qmi-label">${esc(ai.title || "AI 數據深度分析")}</div><div class="qmi-note">${esc(ai.subtitle || "只整理數據、背離與資料品質，不輸出操作結論。")}｜engine=${esc(engine)}${ai.fallback_used ? "｜fallback" : ""}</div><div style="margin-top:8px"><b>市場結構：</b>${esc(ai.market_structure || "N/A")}</div><div style="margin-top:8px"><b>分數拆解：</b>${list(ai.score_decomposition)}</div><div style="margin-top:8px"><b>主要背離：</b>${list(ai.divergences)}</div><div style="margin-top:8px"><b>資料品質：</b>${list(ai.data_quality)}</div><div style="margin-top:8px"><b>投組暴露：</b>${list(ai.portfolio_exposure_notes)}</div><div style="margin-top:8px"><b>人工檢查：</b>${list(ai.manual_checks)}</div></div>`;
  }

  function compassData(data) {
    const c = data?.macroMeta?.market_compass || null;
    const o = data?.macroMeta?.official_weekly || null;
    return { c, o };
  }

  function renderSummary(data) {
    const p = ensureSummaryPanel();
    if (!p) return;
    const { c, o } = compassData(data);
    if (data.error) { p.innerHTML = `<div class="qmi-head"><div><div class="qmi-title">Market Intelligence 讀取失敗</div><div class="qmi-sub">${esc(data.error)}</div></div></div>`; return; }
    if (!c) { p.innerHTML = `<div class="qmi-head"><div><div class="qmi-title">Market Intelligence｜市場環境總覽</div><div class="qmi-sub">尚未偵測到 macro_meta.market_compass。</div></div></div>`; return; }
    const dq = c.data_quality || {};
    const topPen = arr(c.penalties).slice(0, 3);
    p.innerHTML = `<div class="qmi-head"><div><div class="qmi-title">Market Intelligence｜市場環境總覽</div><div class="qmi-sub">總覽頁簡版：看市場狀態、資料品質與主要扣分，不展開完整模型。</div></div><div class="qmi-meta">更新=${esc(c.date || "N/A")}<br>Regime=${esc(c.regime || c.label || "N/A")}</div></div><div class="qmi-body"><div class="qmi-grid">${chip("Adjusted Score", `${n(c.adjusted_score ?? c.score,1)}/100`)}${chip("Raw Score", `${n(c.raw_score ?? c.score,1)}/100`)}${chip("Penalty", `-${n(c.penalty_points ?? 0,1)}`)}${chip("Data Quality", dq.overall || "N/A")}${chip("FRED", c.fred_status || dq.fred_status || "N/A")}${chip("Credit", dq.credit_quality || "N/A")}${chip("Yahoo", dq.yahoo_status || "N/A")}${chip("TWSE", o?.twse?.errors?.length ? "ERROR" : "OK")}</div><div class="qmi-section warn"><div class="qmi-label">Top Penalty Reasons</div>${list(topPen)}</div>${aiBlock(c.ai_data_deep_analysis,true)}</div>`;
  }

  function renderAnalysis(data) {
    const p = ensureAnalysisPanel();
    if (!p) return;
    const { c, o } = compassData(data);
    if (!c) { p.innerHTML = `<div class="qmi-head"><div><div class="qmi-title">Market Intelligence｜市場環境完整版</div><div class="qmi-sub">尚未偵測到 macro_meta.market_compass。</div></div></div>`; return; }
    const dq = c.data_quality || {};
    const mods = c.modules || {};
    const order = ["trend","breadth","credit","volatility","liquidity","cross_asset"];
    p.innerHTML = `<div class="qmi-head"><div><div class="qmi-title">Market Intelligence｜市場環境完整版</div><div class="qmi-sub">分析頁完整版：Market Compass + Official Data Health + AI 數據深度分析。</div></div><div class="qmi-meta">更新=${esc(c.date || "N/A")}<br>FRED=${esc(c.fred_status || dq.fred_status || "N/A")}</div></div><div class="qmi-body"><div class="qmi-grid">${chip("Adjusted Score", `${n(c.adjusted_score ?? c.score,1)}/100`)}${chip("Raw Score", `${n(c.raw_score ?? c.score,1)}/100`)}${chip("Regime", c.regime || c.label || "N/A")}${chip("Credit", dq.credit_quality || "N/A")}</div><div class="qmi-section"><div class="qmi-label">Primary Reasons</div>${list(c.reasons)}</div><div class="qmi-section warn"><div class="qmi-label">Penalty Reasons</div>${list(c.penalties)}</div><div class="qmi-grid6">${order.map((k)=>moduleCard(k,mods[k]||{})).join("")}</div><div class="qmi-section"><div class="qmi-label">Official Data Health</div><div class="qmi-grid">${officialChips(o)}</div></div>${aiBlock(c.ai_data_deep_analysis,false)}</div>`;
  }

  async function render(force = false) {
    injectStyle();
    const data = await fetchData(force);
    renderSummary(data);
    renderQuant(data);
    renderAnalysis(data);
  }

  function boot() {
    let tries = 0;
    const timer = setInterval(() => {
      tries += 1;
      render(false);
      if (tries >= 20) clearInterval(timer);
    }, 800);
    document.addEventListener("click", () => setTimeout(() => render(false), 250), true);
    document.addEventListener("change", () => setTimeout(() => render(true), 300), true);
    setInterval(() => render(true), 120000);
  }

  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", boot) : boot();
})();
