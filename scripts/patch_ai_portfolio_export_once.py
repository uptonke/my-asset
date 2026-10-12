from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/js/src/app.bundle.source.js"
INDEX = ROOT / "index.html"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


source = SOURCE.read_text(encoding="utf-8")

insert_marker = "        function portfolioReportEscape(value) {"
if "function exportAiPortfolioJson()" in source:
    raise RuntimeError("AI portfolio export already exists")

ai_export = r'''        function portfolioAiFinite(value) {
            const n = Number(value);
            return Number.isFinite(n) ? n : null;
        }

        function portfolioAiClean(value) {
            if (value === null || value === undefined) return null;
            if (typeof value === 'number') return Number.isFinite(value) ? value : null;
            if (typeof value === 'string' || typeof value === 'boolean') return value;
            if (Array.isArray(value)) return value.map(portfolioAiClean);
            if (typeof value === 'object') {
                return Object.fromEntries(
                    Object.entries(value).map(([key, item]) => [key, portfolioAiClean(item)])
                );
            }
            return String(value);
        }

        function exportAiPortfolioJson() {
            const rows = portfolioExportRows();
            const nav = portfolioAiFinite(totalPortfolioNav.value) || 0;
            const cash = portfolioAiFinite(cashBalance.value) || 0;
            const syntheticRisk = stockMeta.value?.['__SYNTHETIC_PORTFOLIO_RISK__'] || {};
            const actionSummary = holdingsActionSummary?.value || {};
            const rebalanceSummary = rebalanceTradePlanSummary?.value || {};
            const governance = allocationGovernance?.value || {};

            const holdings = rows.map((row) => {
                const meta = stockMeta.value?.[row.ticker] || {};
                return {
                    ticker: row.ticker,
                    category: row.category,
                    shares: portfolioAiFinite(row.shares),
                    market: {
                        current_price_twd: portfolioAiFinite(row.currentPriceTwd),
                        average_cost_twd: portfolioAiFinite(row.avgCostTwd),
                        total_cost_twd: portfolioAiFinite(row.totalCostTwd),
                        market_value_twd: portfolioAiFinite(row.marketValueTwd),
                        unrealized_pl_twd: portfolioAiFinite(row.unrealizedPLTwd),
                        return_pct: portfolioAiFinite(row.returnRate),
                        annualized_return_pct: portfolioAiFinite(row.annualizedReturnRate),
                    },
                    allocation: {
                        weight_pct: portfolioAiFinite(row.weightPct),
                        target_weight_pct: portfolioAiFinite(row.targetWeightPct),
                        drift_pct: portfolioAiFinite(row.driftPct),
                    },
                    quant_factors: {
                        beta: portfolioAiFinite(meta.beta ?? row.beta),
                        beta_benchmark: meta.beta_benchmark ?? null,
                        correlation: portfolioAiFinite(meta.corr ?? meta.correlation),
                        trend_score: portfolioAiFinite(meta.trend_score ?? row.trendScore),
                        momentum_score: portfolioAiFinite(meta.momentum_score ?? row.momentumScore),
                        technical_score: portfolioAiFinite(meta.technical_score),
                        valuation_score: portfolioAiFinite(meta.valuation_score),
                        valuation_pressure: portfolioAiFinite(meta.valuation_pressure),
                        health_score: portfolioAiFinite(meta.quant_health_score ?? row.healthScore),
                    },
                    risk_metrics: {
                        risk_score: portfolioAiFinite(meta.risk_score ?? row.riskScore),
                        max_drawdown_1y: portfolioAiFinite(meta.max_drawdown_1y),
                        liquidity_score: portfolioAiFinite(meta.liquidity_score),
                        volatility_20d: portfolioAiFinite(meta.volatility_20d ?? meta.vol_20d),
                        annualized_volatility: portfolioAiFinite(meta.annualized_volatility ?? meta.volatility_annualized),
                    },
                    technical_context: {
                        monthly_support: portfolioAiClean(meta.monthly_support ?? meta.pivot_support),
                        monthly_resistance: portfolioAiClean(meta.monthly_resistance ?? meta.pivot_resistance),
                        monthly_position: meta.pivot_position_plain ?? meta.pivot_status ?? null,
                        signal: meta.pivot_signal ?? null,
                        signal_reason: meta.pivot_signal_reason ?? null,
                    },
                    data_quality: {
                        quality: meta.quality ?? meta.data_quality ?? null,
                        source: meta.source ?? null,
                        last_market_date: meta.last_market_date ?? null,
                        updated_at: meta.updated_at ?? meta.last_updated ?? null,
                    },
                };
            });

            const payload = {
                schema: 'portfolio_ai_export_v1',
                purpose: 'Structured portfolio snapshot for AI analysis. This is not a transaction backup.',
                exported_at: new Date().toISOString(),
                base_currency: 'TWD',
                field_semantics: {
                    percentage_fields: 'Values ending in _pct are percentage points, e.g. 12.5 means 12.5%.',
                    score_range: 'Quant scores are generally 0-10.',
                    risk_score: 'Higher means riskier; it is not a positive quality score.',
                    health_score: 'Higher means healthier/stronger composite condition.',
                    trend_momentum_technical_valuation: 'Higher generally means stronger/more favorable according to the model.',
                    null_values: 'null means unavailable or not reliably computable; do not infer a numeric zero.',
                    target_weight: 'Target weight is a model target, not an automatic trade instruction.',
                },
                portfolio: {
                    nav_twd: nav,
                    cash_twd: cash,
                    cash_weight_pct: nav > 0 ? (cash / nav) * 100 : null,
                    holdings_market_value_twd: portfolioAiFinite(totalStockValueTwd.value),
                    holdings_cost_twd: portfolioAiFinite(totalStockCostTwd.value),
                    unrealized_pl_twd: portfolioAiFinite(totalStockUnrealizedPL.value),
                    holdings_return_pct: portfolioAiFinite(totalStockReturnRate.value),
                    usd_twd: portfolioAiFinite(exchangeRate.value),
                    holding_count: holdings.length,
                },
                risk_summary: {
                    governance_mode: governance.mode ?? null,
                    governance_headline: governance.headline ?? governance.badgeText ?? null,
                    high_risk_holding_count: portfolioAiFinite(actionSummary.highRisk),
                    overweight_holding_count: portfolioAiFinite(actionSummary.overweight),
                    drift_holding_count: portfolioAiFinite(actionSummary.drift),
                    rebalance: {
                        triggered: rebalanceSummary.triggered ?? null,
                        trim_pct: portfolioAiFinite(rebalanceSummary.trimPct),
                        add_pct: portfolioAiFinite(rebalanceSummary.addPct),
                        target_cash_pct: portfolioAiFinite(rebalanceSummary.targetCashPct),
                        planned_cash_after_pct: portfolioAiFinite(rebalanceSummary.plannedCashAfterPct),
                        self_financing_within_tolerance: rebalanceSummary.selfFinancingWithinTolerance ?? null,
                        add_disabled: rebalanceSummary.addDisabled ?? null,
                    },
                    synthetic_portfolio_risk: {
                        status: syntheticRisk.status ?? null,
                        confidence: syntheticRisk.confidence ?? syntheticRisk.confidence_level ?? null,
                        metrics: portfolioAiClean(syntheticRisk.metrics ?? null),
                        coverage: portfolioAiClean(syntheticRisk.coverage ?? null),
                    },
                },
                holdings,
            };

            portfolioExportDownload(
                `portfolio-ai-${portfolioExportDateStamp()}.json`,
                JSON.stringify(portfolioAiClean(payload), null, 2),
                'application/json;charset=utf-8'
            );
        }

'''
source = replace_once(source, insert_marker, ai_export + insert_marker, "insert AI export function")

old_return = "            exportAll, exportHoldingsCsv, exportPortfolioPdf, importData, getTypeColor, getCategoryColorCode, formatNumber, formatCurrency, formatPercent,"
new_return = "            exportAll, exportHoldingsCsv, exportPortfolioPdf, exportAiPortfolioJson, importData, getTypeColor, getCategoryColorCode, formatNumber, formatCurrency, formatPercent,"
source = replace_once(source, old_return, new_return, "expose AI export method")
SOURCE.write_text(source, encoding="utf-8")

index = INDEX.read_text(encoding="utf-8")
menu_marker = '''        <div class="portfolio-export-popover">\n            <button type="button" @click="exportPortfolioPdf(); $event.currentTarget.closest('details').removeAttribute('open')" class="portfolio-export-item">'''
ai_button = '''        <div class="portfolio-export-popover">\n            <button type="button" @click="exportAiPortfolioJson(); $event.currentTarget.closest('details').removeAttribute('open')" class="portfolio-export-item">\n                <i class="fas fa-brain"></i>\n                <span><strong>AI 分析 JSON</strong><small>NAV、配置、量化因子與風險摘要</small></span>\n            </button>\n            <button type="button" @click="exportPortfolioPdf(); $event.currentTarget.closest('details').removeAttribute('open')" class="portfolio-export-item">'''
index = replace_once(index, menu_marker, ai_button, "insert AI export menu item")
index, count = re.subn(r'assets/js/app\.bundle\.js\?v=[^"\']+', 'assets/js/app.bundle.js?v=portfolio-ai-export-v1', index, count=1)
if count != 1:
    raise RuntimeError(f"cache bust: expected one app bundle URL, found {count}")
INDEX.write_text(index, encoding="utf-8")
print("AI portfolio export patch applied")
