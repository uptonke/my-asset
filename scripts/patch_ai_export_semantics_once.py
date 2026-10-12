#!/usr/bin/env python3
from pathlib import Path

PATH = Path('assets/js/src/app.bundle.source.js')
text = PATH.read_text(encoding='utf-8')

old_helper = """        function portfolioAiFinite(value) {\n            const n = Number(value);\n            return Number.isFinite(n) ? n : null;\n        }\n"""
new_helper = """        function portfolioAiFinite(value) {\n            if (value === null || value === undefined || value === '') return null;\n            const n = Number(value);\n            return Number.isFinite(n) ? n : null;\n        }\n\n        function portfolioAiHasQuantSource(meta) {\n            if (!meta || typeof meta !== 'object') return false;\n            return [meta.source, meta.data_quality, meta.last_market_date].some((value) =>\n                value !== null && value !== undefined && String(value).trim() !== ''\n            );\n        }\n\n        function portfolioAiPivotZone(meta, side) {\n            const low = portfolioAiFinite(meta?.[`pivot_${side}_zone_low`]);\n            const high = portfolioAiFinite(meta?.[`pivot_${side}_zone_high`]);\n            if (low === null || high === null) return null;\n            return {\n                low,\n                high,\n                mid: portfolioAiFinite(meta?.[`pivot_${side}_zone_mid`]),\n                distance_pct: portfolioAiFinite(meta?.[`pivot_${side}_distance_pct`])\n            };\n        }\n"""
if text.count(old_helper) != 1:
    raise SystemExit(f'Expected exactly one portfolioAiFinite helper, found {text.count(old_helper)}')
text = text.replace(old_helper, new_helper, 1)

start_marker = '        function exportAiPortfolioJson() {'
end_marker = '        function portfolioReportEscape(value) {'
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('Could not isolate exportAiPortfolioJson region')
region = text[start:end]

replacements = {
    "                        trend_score: portfolioAiFinite(meta.trend_score ?? row.trendScore),":
        "                        trend_score: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.trend_score ?? row.trendScore) : null,",
    "                        momentum_score: portfolioAiFinite(meta.momentum_score ?? row.momentumScore),":
        "                        momentum_score: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.momentum_score ?? row.momentumScore) : null,",
    "                        technical_score: portfolioAiFinite(meta.technical_score),":
        "                        technical_score: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.technical_score) : null,",
    "                        valuation_score: portfolioAiFinite(meta.valuation_score),":
        "                        valuation_score: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.valuation_score) : null,",
    "                        valuation_pressure: portfolioAiFinite(meta.valuation_pressure),":
        "                        valuation_pressure: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.valuation_pressure) : null,",
    "                        health_score: portfolioAiFinite(meta.quant_health_score ?? row.healthScore),":
        "                        health_score: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.quant_health_score ?? row.healthScore) : null,",
    "                        risk_score: portfolioAiFinite(meta.risk_score ?? row.riskScore),":
        "                        risk_score: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.risk_score ?? row.riskScore) : null,",
    "                        max_drawdown_1y: portfolioAiFinite(meta.max_drawdown_1y),":
        "                        max_drawdown_1y: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.max_drawdown_1y) : null,",
    "                        volatility_20d: portfolioAiFinite(meta.volatility_20d ?? meta.vol_20d),":
        "                        volatility_20d: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.volatility_20d ?? meta.vol_20d) : null,",
    "                        annualized_volatility: portfolioAiFinite(meta.annualized_volatility ?? meta.volatility_annualized),":
        "                        annualized_volatility: portfolioAiHasQuantSource(meta) ? portfolioAiFinite(meta.annualized_volatility ?? meta.volatility_annualized) : null,",
    "                        monthly_support: portfolioAiClean(meta.monthly_support ?? meta.pivot_support),":
        "                        monthly_support: portfolioAiPivotZone(meta, 'support'),",
    "                        monthly_resistance: portfolioAiClean(meta.monthly_resistance ?? meta.pivot_resistance),":
        "                        monthly_resistance: portfolioAiPivotZone(meta, 'resistance'),",
}

for old, new in replacements.items():
    count = region.count(old)
    if count != 1:
        raise SystemExit(f'Expected one export line for {old.strip()!r}, found {count}')
    region = region.replace(old, new, 1)

text = text[:start] + region + text[end:]

# Guard against accidental duplicate application or stale mapping.
if text.count('function portfolioAiHasQuantSource(meta)') != 1:
    raise SystemExit('portfolioAiHasQuantSource helper count mismatch')
if text.count('function portfolioAiPivotZone(meta, side)') != 1:
    raise SystemExit('portfolioAiPivotZone helper count mismatch')
if 'monthly_support: portfolioAiClean(meta.monthly_support ?? meta.pivot_support)' in region:
    raise SystemExit('Old monthly_support mapping still present')
if 'monthly_resistance: portfolioAiClean(meta.monthly_resistance ?? meta.pivot_resistance)' in region:
    raise SystemExit('Old monthly_resistance mapping still present')

PATH.write_text(text, encoding='utf-8')
print('AI export semantics patch applied.')
