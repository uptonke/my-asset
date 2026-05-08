/* iOS + Bloomberg hybrid polish v4 */
:root {
  --bbg-amber: #ffb000;
  --bbg-amber-soft: rgba(255,176,0,0.14);
  --bbg-cyan: #6fd3ff;
  --bbg-surface: rgba(13, 18, 28, 0.78);
  --bbg-surface-2: rgba(17, 24, 39, 0.88);
  --bbg-border: rgba(255,255,255,0.07);
  --bbg-grid: rgba(255,255,255,0.035);
  --bbg-shadow: 0 20px 48px rgba(0,0,0,0.30);
}

html, body {
  background:
    radial-gradient(circle at 8% 6%, rgba(74, 144, 226, 0.10), transparent 18%),
    radial-gradient(circle at 88% 10%, rgba(255,176,0,0.08), transparent 16%),
    linear-gradient(180deg, #070c14 0%, #0b1220 48%, #0a0f18 100%) !important;
}

body::before {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.045), transparent 14%, transparent 84%, rgba(255,255,255,0.02)),
    linear-gradient(90deg, transparent 0, transparent calc(100% - 1px), rgba(255,255,255,0.012) calc(100% - 1px));
  background-size: 100% 100%, 22px 22px;
  opacity: 0.95;
}

.glass,
.panel-card,
.chart-card,
.glass-sim {
  background: linear-gradient(180deg, rgba(20,27,39,0.82), rgba(11,16,25,0.84)) !important;
  border-color: var(--bbg-border) !important;
  box-shadow: var(--bbg-shadow), inset 0 1px 0 rgba(255,255,255,0.06) !important;
}

.glass::before {
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.018) 24%, transparent 54%) !important;
}

header.glass {
  background: linear-gradient(180deg, rgba(15,22,34,0.88), rgba(11,17,27,0.84)) !important;
  border-bottom-color: rgba(255,255,255,0.06) !important;
}

.tool-btn,
.badge,
.panel-badge {
  letter-spacing: 0.02em;
}

.tool-btn {
  background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.025)) !important;
  border-color: rgba(255,255,255,0.08) !important;
}

.tool-btn-blue { color: #9cd8ff !important; border-color: rgba(111,211,255,0.20) !important; }
.tool-btn-yellow { color: #ffd37a !important; border-color: rgba(255,176,0,0.22) !important; }
.tool-btn-green { color: #89f0b5 !important; }
.tool-btn-red { color: #ffb0a8 !important; }

nav.rounded-2xl {
  background: rgba(8, 13, 21, 0.62) !important;
  border-color: rgba(255,255,255,0.07) !important;
}

nav button[class*="bg-white text-slate-900"] {
  background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(235,240,248,0.90)) !important;
  color: #111827 !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.8) !important;
}

.text-yellow-400, .text-yellow-500 {
  color: var(--bbg-amber) !important;
}

.border-yellow-500\/20,
.border-yellow-500\/30,
.border-yellow-500\/50 {
  border-color: rgba(255,176,0,0.24) !important;
}

.bg-yellow-500\/5,
.bg-yellow-500\/10 {
  background-color: rgba(255,176,0,0.08) !important;
}

.bg-cyan-500\/5,
.bg-cyan-500\/10 { background-color: rgba(111,211,255,0.08) !important; }
.border-cyan-500\/20,
.border-cyan-500\/30 { border-color: rgba(111,211,255,0.22) !important; }

.ios-story-label,
.text-\[11px\].uppercase,
.text-xs.text-gray-400.font-bold.uppercase.tracking-wider,
.excel-table th {
  color: rgba(255, 196, 90, 0.92) !important;
  letter-spacing: 0.08em !important;
  font-weight: 800 !important;
}

.ios-story-card,
.ios-reason-chip,
.rebalance-cockpit-row,
.quant-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.022)) !important;
  border-color: rgba(255,255,255,0.075) !important;
}

.ios-step {
  border-bottom-color: rgba(255,255,255,0.05) !important;
}

.ios-step-index {
  background: rgba(255,176,0,0.16) !important;
  border-color: rgba(255,176,0,0.24) !important;
  color: #ffd37a !important;
}

.font-mono {
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.04em;
}

.excel-table th,
.holdings-sticky-th,
.holdings-sticky-thead {
  background: rgba(10, 14, 22, 0.96) !important;
  box-shadow: inset 0 -1px 0 rgba(255,176,0,0.16) !important;
}

.excel-table td {
  border-bottom-color: rgba(255,255,255,0.045) !important;
}

.group-header td {
  background: linear-gradient(90deg, rgba(20, 28, 42, 0.98), rgba(16, 22, 33, 0.98)) !important;
  color: #7fd7ff !important;
  border-top: 1px solid rgba(111,211,255,0.12);
  border-bottom: 1px solid rgba(111,211,255,0.10);
}

input, select, textarea {
  background-color: rgba(255,255,255,0.03) !important;
  border-color: rgba(255,255,255,0.10) !important;
}

input:focus, select:focus, textarea:focus {
  box-shadow: 0 0 0 4px rgba(111,211,255,0.12) !important;
  border-color: rgba(111,211,255,0.40) !important;
}

.text-gray-500 { color: rgba(235,235,245,0.42) !important; }
.text-gray-400 { color: rgba(235,235,245,0.62) !important; }
.text-gray-300 { color: rgba(245,247,251,0.80) !important; }

.rounded-2xl.border.border-white\/10.bg-black\/20,
.rounded-2xl.border.border-white\/10.bg-black\/15 {
  background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)) !important;
  border-color: rgba(255,255,255,0.08) !important;
}

/* make analytics areas feel denser */
@media (min-width: 1024px) {
  .excel-table td { padding-top: 0.68rem; padding-bottom: 0.68rem; }
  .excel-table th { padding-top: 0.72rem; padding-bottom: 0.72rem; }
}
