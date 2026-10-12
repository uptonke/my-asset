from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"Expected block not found in {path}: {old[:160]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Canonical frontend source only; runtime bundle is rebuilt afterwards.
p = ROOT / "assets" / "js" / "src" / "app.bundle.source.js"

replace_once(
    p,
    "        function formatNumber(n) { return new Intl.NumberFormat('zh-TW', {maximumFractionDigits:0}).format(n||0); }\n",
    "        function formatNumber(n) { return new Intl.NumberFormat('zh-TW', {maximumFractionDigits:0}).format(n||0); }\n"
    "        function formatQuantity(n) {\n"
    "            const value = Number(n);\n"
    "            if (!Number.isFinite(value)) return '0';\n"
    "            return new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 8 }).format(value);\n"
    "        }\n",
)

replace_once(
    p,
    "            else if (qty > holding.shares) output.warnings.push(`賣出股數超過現有持倉 (${formatNumber(holding.shares)})。`);\n",
    "            else if (qty - Number(holding.shares || 0) > 1e-8) output.warnings.push(`賣出股數超過現有持倉 (${formatQuantity(holding.shares)})。`);\n",
)

replace_once(
    p,
    "            if (finalShares > holding.shares) {\n                alert(`賣出股數超過現有持倉 (${formatNumber(holding.shares)})`);\n",
    "            if (finalShares - Number(holding.shares || 0) > 1e-8) {\n                alert(`賣出股數超過現有持倉 (${formatQuantity(holding.shares)})`);\n",
)

replace_once(
    p,
    "                    else if (qty > Number(holding.shares || 0)) blockers.push(`賣出數量超過現有持倉 (${formatNumber(holding.shares)})。`);\n",
    "                    else if (qty - Number(holding.shares || 0) > 1e-8) blockers.push(`賣出數量超過現有持倉 (${formatQuantity(holding.shares)})。`);\n",
)

replace_once(
    p,
    "            exportAll, exportHoldingsCsv, exportPortfolioPdf, exportAiPortfolioJson, importData, getTypeColor, getCategoryColorCode, formatNumber, formatCurrency, formatPercent,\n",
    "            exportAll, exportHoldingsCsv, exportPortfolioPdf, exportAiPortfolioJson, importData, getTypeColor, getCategoryColorCode, formatNumber, formatQuantity, formatCurrency, formatPercent,\n",
)

# Template: fractional quantities must be visible and enterable, especially on iOS.
p = ROOT / "index.html"
text = p.read_text(encoding="utf-8")
old_input = '<input v-model.number="txForm.shares" type="number" placeholder="股數" class="w-full input-dark p-2 rounded text-xs">'
new_input = '<input v-model.number="txForm.shares" type="number" step="any" inputmode="decimal" min="0" placeholder="數量（可輸入小數）" class="w-full input-dark p-2 rounded text-xs">'
if new_input not in text:
    if old_input not in text:
        raise SystemExit("Transaction quantity input not found")
    text = text.replace(old_input, new_input, 1)

old_qty = '{{ formatNumber(stock.shares) }}'
new_qty = '{{ formatQuantity(stock.shares) }}'
if new_qty not in text:
    qty_count = text.count(old_qty)
    if qty_count < 2:
        raise SystemExit(f"Expected at least 2 holdings quantity displays, found {qty_count}")
    text = text.replace(old_qty, new_qty)

# Cache-bust the rebuilt runtime bundle.
text, n = re.subn(r'assets/js/app\.bundle\.js\?v=[^"\']+', 'assets/js/app.bundle.js?v=fractional-sell-v1', text, count=1)
if n != 1 and 'assets/js/app.bundle.js?v=fractional-sell-v1' not in text:
    raise SystemExit("app.bundle.js cache-bust reference not found")
p.write_text(text, encoding="utf-8")

print("Fractional holding display/sell patch applied.")
