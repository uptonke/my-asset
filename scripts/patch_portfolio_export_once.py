from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/js/src/app.bundle.source.js"
INDEX = ROOT / "index.html"
CSS = ROOT / "assets/css/10-components.css"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


source = SOURCE.read_text(encoding="utf-8")
old_export = '''        function exportAll() { const data = { ledger: transactions.value, history: realHistoryData.value, stockMeta: stockMeta.value }; const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([JSON.stringify(data)], {type: "application/json"})); link.download = "backup.json"; link.click(); }'''
new_export = r'''        function portfolioExportDateStamp() {
            return new Date().toISOString().slice(0, 10);
        }

        function portfolioExportDownload(filename, content, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        }

        function portfolioExportRows() {
            const nav = Number(totalPortfolioNav.value || 0);
            const rows = [];
            Object.entries(groupedHoldings.value || {}).forEach(([category, group]) => {
                (group?.items || []).forEach((item) => {
                    const meta = stockMeta.value?.[item.ticker] || {};
                    const marketValue = Number(item.marketValueTwd || 0);
                    const weightPct = nav > 0
                        ? (marketValue / nav) * 100
                        : Number(item.totalWeight || 0) * 100;
                    const targetPct = Number(item.blendedWeight ?? item.rebalanceTargetWeight ?? item.targetWeight ?? 0);
                    rows.push({
                        ticker: String(item.ticker || ''),
                        category: String(category || item.category || ''),
                        shares: Number(item.shares || 0),
                        avgCostTwd: Number(item.avgCostTwd || 0),
                        currentPriceTwd: Number(item.currentPriceTwd || 0),
                        totalCostTwd: Number(item.totalCostTwd || 0),
                        marketValueTwd: marketValue,
                        unrealizedPLTwd: Number(item.unrealizedPLTwd || 0),
                        returnRate: Number(item.returnRate || 0),
                        annualizedReturnRate: Number(item.annualizedReturnRate || 0),
                        weightPct,
                        targetWeightPct: targetPct,
                        driftPct: targetPct - weightPct,
                        beta: Number.isFinite(Number(item.beta ?? meta.beta)) ? Number(item.beta ?? meta.beta) : null,
                        trendScore: Number.isFinite(Number(meta.trend_score)) ? Number(meta.trend_score) : null,
                        momentumScore: Number.isFinite(Number(meta.momentum_score)) ? Number(meta.momentum_score) : null,
                        riskScore: Number.isFinite(Number(meta.risk_score)) ? Number(meta.risk_score) : null,
                        healthScore: Number.isFinite(Number(meta.quant_health_score)) ? Number(meta.quant_health_score) : null,
                    });
                });
            });
            return rows.sort((a, b) => b.marketValueTwd - a.marketValueTwd);
        }

        function exportAll() {
            const data = {
                exportedAt: new Date().toISOString(),
                ledger: transactions.value,
                history: realHistoryData.value,
                stockMeta: stockMeta.value,
            };
            portfolioExportDownload(
                `portfolio-backup-${portfolioExportDateStamp()}.json`,
                JSON.stringify(data, null, 2),
                'application/json;charset=utf-8'
            );
        }

        function portfolioCsvCell(value) {
            const text = value === null || value === undefined ? '' : String(value);
            return `"${text.replace(/"/g, '""')}"`;
        }

        function exportHoldingsCsv() {
            const rows = portfolioExportRows();
            const headers = [
                '代號', '類別', '股數', '平均成本_TWD', '現價_TWD', '總成本_TWD', '市值_TWD',
                '未實現損益_TWD', '報酬率_%', '年化報酬_%', '投組權重_%', '目標權重_%', '偏離_%',
                'Beta', '趨勢', '動能', '風險', '健康度'
            ];
            const body = rows.map((row) => [
                row.ticker, row.category, row.shares, row.avgCostTwd, row.currentPriceTwd, row.totalCostTwd,
                row.marketValueTwd, row.unrealizedPLTwd, row.returnRate, row.annualizedReturnRate, row.weightPct,
                row.targetWeightPct, row.driftPct, row.beta, row.trendScore, row.momentumScore, row.riskScore, row.healthScore
            ].map(portfolioCsvCell).join(','));
            portfolioExportDownload(
                `portfolio-holdings-${portfolioExportDateStamp()}.csv`,
                '\uFEFF' + [headers.map(portfolioCsvCell).join(','), ...body].join('\r\n'),
                'text/csv;charset=utf-8'
            );
        }

        function portfolioReportEscape(value) {
            return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
            }[ch]));
        }

        function exportPortfolioPdf() {
            const reportWindow = window.open('', '_blank');
            if (!reportWindow) {
                alert('瀏覽器阻擋了報告視窗，請允許此網站開啟彈出視窗後再試一次。');
                return;
            }
            reportWindow.opener = null;

            const rows = portfolioExportRows();
            const fmt = (value, digits = 0) => Number.isFinite(Number(value))
                ? Number(value).toLocaleString('zh-TW', { minimumFractionDigits: digits, maximumFractionDigits: digits })
                : 'N/A';
            const score = (value) => Number.isFinite(Number(value)) ? Number(value).toFixed(2) : '—';
            const signClass = (value) => Number(value) > 0 ? 'pos' : (Number(value) < 0 ? 'neg' : '');
            const generatedAt = new Date().toLocaleString('zh-TW', { hour12: false });
            const reportRows = rows.map((row) => `
                <tr>
                    <td class="ticker">${portfolioReportEscape(row.ticker)}</td>
                    <td>${portfolioReportEscape(row.category)}</td>
                    <td class="num">${fmt(row.shares, 4)}</td>
                    <td class="num">${fmt(row.marketValueTwd)}</td>
                    <td class="num">${fmt(row.weightPct, 2)}%</td>
                    <td class="num ${signClass(row.returnRate)}">${fmt(row.returnRate, 2)}%</td>
                    <td class="num">${fmt(row.targetWeightPct, 2)}%</td>
                    <td class="num ${signClass(row.driftPct)}">${fmt(row.driftPct, 2)}%</td>
                    <td class="num">${score(row.beta)}</td>
                    <td class="num">${score(row.trendScore)}</td>
                    <td class="num">${score(row.momentumScore)}</td>
                    <td class="num">${score(row.riskScore)}</td>
                    <td class="num">${score(row.healthScore)}</td>
                </tr>`).join('');

            const nav = Number(totalPortfolioNav.value || 0);
            const cash = Number(cashBalance.value || 0);
            const stockValue = Number(totalStockValueTwd.value || 0);
            const unrealized = Number(totalStockUnrealizedPL.value || 0);
            const stockReturn = Number(totalStockReturnRate.value || 0);
            const cashPct = nav > 0 ? (cash / nav) * 100 : 0;
            const html = `<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>Portfolio Report ${portfolioExportDateStamp()}</title>
<style>
@page{size:A4 landscape;margin:10mm}*{box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans TC",sans-serif;color:#172033;margin:0;font-size:10px}h1{font-size:22px;margin:0 0 3px}.sub{color:#667085;margin-bottom:14px}.hint{padding:9px 12px;border:1px solid #d0d5dd;border-radius:8px;background:#f8fafc;margin-bottom:12px}.summary{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:14px}.card{border:1px solid #d8dee9;border-radius:8px;padding:9px}.k{font-size:8px;color:#667085;text-transform:uppercase}.v{font-size:14px;font-weight:750;margin-top:4px}.pos{color:#067647}.neg{color:#b42318}table{width:100%;border-collapse:collapse;table-layout:auto}th{font-size:8px;color:#475467;text-align:right;padding:6px 5px;border-bottom:2px solid #98a2b3;white-space:nowrap}td{padding:6px 5px;border-bottom:1px solid #e4e7ec;text-align:right;white-space:nowrap}th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}.ticker{font-weight:750}.num{font-variant-numeric:tabular-nums}.foot{margin-top:10px;color:#667085;font-size:8px;line-height:1.5}@media print{.hint{display:none}}
</style></head><body>
<h1>Portfolio Snapshot</h1><div class="sub">匯出時間：${portfolioReportEscape(generatedAt)} ｜ 持倉：${rows.length} ｜ USD/TWD：${fmt(exchangeRate.value, 2)}</div>
<div class="hint">列印視窗開啟後，選擇「另存為 PDF」即可下載 PDF 報告。</div>
<div class="summary">
<div class="card"><div class="k">NAV</div><div class="v">NT$ ${fmt(nav)}</div></div>
<div class="card"><div class="k">股票市值</div><div class="v">NT$ ${fmt(stockValue)}</div></div>
<div class="card"><div class="k">現金</div><div class="v">NT$ ${fmt(cash)}</div><div>${fmt(cashPct,2)}%</div></div>
<div class="card"><div class="k">股票成本</div><div class="v">NT$ ${fmt(totalStockCostTwd.value)}</div></div>
<div class="card"><div class="k">未實現損益</div><div class="v ${signClass(unrealized)}">NT$ ${fmt(unrealized)}</div></div>
<div class="card"><div class="k">股票報酬</div><div class="v ${signClass(stockReturn)}">${fmt(stockReturn,2)}%</div></div>
</div>
<table><thead><tr><th>代號</th><th>類別</th><th>股數</th><th>市值 TWD</th><th>權重</th><th>報酬</th><th>目標</th><th>偏離</th><th>Beta</th><th>趨勢</th><th>動能</th><th>風險</th><th>健康度</th></tr></thead><tbody>${reportRows || '<tr><td colspan="13">目前沒有可匯出的持倉。</td></tr>'}</tbody></table>
<div class="foot">權重以當下 NAV（含現金）計算；量化分數取自目前 stock_meta 快照。此報告僅為投資組合資料快照，不構成交易指令或投資建議。</div>
</body></html>`;
            reportWindow.document.open();
            reportWindow.document.write(html);
            reportWindow.document.close();
            setTimeout(() => {
                try {
                    reportWindow.focus();
                    reportWindow.print();
                } catch (err) {
                    console.error('Portfolio report print failed', err);
                }
            }, 350);
        }'''
source = replace_once(source, old_export, new_export, "replace exportAll")
source = replace_once(
    source,
    "            exportAll, importData, getTypeColor, getCategoryColorCode, formatNumber, formatPercent, ",
    "            exportAll, exportHoldingsCsv, exportPortfolioPdf, importData, getTypeColor, getCategoryColorCode, formatNumber, formatPercent, ",
    "expose export methods",
)
SOURCE.write_text(source, encoding="utf-8")

index = INDEX.read_text(encoding="utf-8")
old_button = '''    <button @click="exportAll" class="tool-btn tool-btn-green">
        <i class="fas fa-download"></i>
        <span>匯出</span>
    </button>'''
new_button = '''    <details class="portfolio-export-menu">
        <summary class="tool-btn tool-btn-green" title="匯出投資組合">
            <i class="fas fa-download"></i>
            <span>匯出</span>
            <i class="fas fa-chevron-down portfolio-export-chevron"></i>
        </summary>
        <div class="portfolio-export-popover">
            <button type="button" @click="exportPortfolioPdf(); $event.currentTarget.closest('details').removeAttribute('open')" class="portfolio-export-item">
                <i class="fas fa-file-pdf"></i>
                <span><strong>投組報告 PDF</strong><small>NAV、持倉、權重與量化因子</small></span>
            </button>
            <button type="button" @click="exportHoldingsCsv(); $event.currentTarget.closest('details').removeAttribute('open')" class="portfolio-export-item">
                <i class="fas fa-file-csv"></i>
                <span><strong>持倉 CSV</strong><small>Excel / Numbers / 分析工具</small></span>
            </button>
            <button type="button" @click="exportAll(); $event.currentTarget.closest('details').removeAttribute('open')" class="portfolio-export-item">
                <i class="fas fa-file-code"></i>
                <span><strong>JSON 備份</strong><small>Ledger、歷史與 stock_meta</small></span>
            </button>
        </div>
    </details>'''
index = replace_once(index, old_button, new_button, "replace header export button")
index, count = re.subn(r'assets/js/app\.bundle\.js\?v=[^"\']+', 'assets/js/app.bundle.js?v=portfolio-export-v1', index, count=1)
if count != 1:
    raise RuntimeError(f"cache bust: expected one app bundle URL, found {count}")
INDEX.write_text(index, encoding="utf-8")

css = CSS.read_text(encoding="utf-8")
marker = "/* ===== Portfolio export menu v1 ===== */"
if marker in css:
    raise RuntimeError("portfolio export CSS already exists")
css += r'''

/* ===== Portfolio export menu v1 ===== */
.portfolio-export-menu {
    position: relative;
}

.portfolio-export-menu > summary {
    list-style: none;
    cursor: pointer;
    user-select: none;
}

.portfolio-export-menu > summary::-webkit-details-marker {
    display: none;
}

.portfolio-export-chevron {
    font-size: 0.6rem;
    opacity: 0.65;
    transition: transform 0.18s ease;
}

.portfolio-export-menu[open] .portfolio-export-chevron {
    transform: rotate(180deg);
}

.portfolio-export-popover {
    position: absolute;
    right: 0;
    top: calc(100% + 0.5rem);
    z-index: 120;
    width: 260px;
    padding: 0.4rem;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.12);
    background: rgba(8, 15, 30, 0.98);
    box-shadow: 0 18px 48px rgba(0,0,0,0.42);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
}

.portfolio-export-item {
    width: 100%;
    display: grid;
    grid-template-columns: 28px 1fr;
    align-items: center;
    gap: 0.65rem;
    border: 0;
    border-radius: 11px;
    padding: 0.72rem 0.75rem;
    color: #e5e7eb;
    background: transparent;
    text-align: left;
    cursor: pointer;
    transition: background 0.15s ease, color 0.15s ease;
}

.portfolio-export-item:hover,
.portfolio-export-item:focus-visible {
    background: rgba(255,255,255,0.08);
    color: #fff;
    outline: none;
}

.portfolio-export-item > i {
    color: #86efac;
    text-align: center;
    font-size: 0.95rem;
}

.portfolio-export-item span {
    min-width: 0;
}

.portfolio-export-item strong,
.portfolio-export-item small {
    display: block;
}

.portfolio-export-item strong {
    font-size: 0.75rem;
    line-height: 1.35;
}

.portfolio-export-item small {
    margin-top: 0.12rem;
    color: rgba(203,213,225,0.62);
    font-size: 0.62rem;
    line-height: 1.35;
}

@media (max-width: 640px) {
    .portfolio-export-popover {
        right: -3.25rem;
        width: min(260px, calc(100vw - 1.5rem));
    }
}
'''
CSS.write_text(css, encoding="utf-8")

print("portfolio export patch applied")
