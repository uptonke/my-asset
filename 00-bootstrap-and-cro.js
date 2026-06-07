/* Executive + institutional polish v5 */
:root {
  --exec-line: rgba(255,255,255,0.075);
  --exec-line-soft: rgba(255,255,255,0.04);
  --exec-bg-soft: rgba(255,255,255,0.025);
  --exec-amber: rgba(255,176,0,0.86);
  --exec-cyan: rgba(111,211,255,0.86);
  --exec-red: rgba(248,113,113,0.88);
}

.summary-exec-grid {
  align-items: start !important;
}

.executive-command-card,
.executive-alert-card,
.institutional-governance-shell,
.institutional-cockpit-shell,
.cro-intelligence-shell,
.analytics-hierarchy-strip,
.holdings-terminal-shell {
  position: relative;
  overflow: hidden;
}

.executive-command-card::after,
.executive-alert-card::after,
.institutional-governance-shell::after,
.institutional-cockpit-shell::after,
.cro-intelligence-shell::after,
.analytics-hierarchy-strip::after,
.holdings-terminal-shell::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255,255,255,0.022), transparent 14%, transparent 86%, rgba(255,255,255,0.015));
}

.executive-command-card > *,
.executive-alert-card > *,
.institutional-governance-shell > *,
.institutional-cockpit-shell > *,
.cro-intelligence-shell > *,
.analytics-hierarchy-strip > *,
.holdings-terminal-shell > * {
  position: relative;
  z-index: 1;
}

.executive-command-card {
  border-color: rgba(255,176,0,0.22) !important;
  background:
    linear-gradient(180deg, rgba(21,28,39,0.90), rgba(10,14,22,0.92)) !important;
}

.executive-command-card .border-b {
  border-bottom-color: rgba(255,176,0,0.12) !important;
}

.executive-command-card .rounded-2xl.border.border-white\/10.bg-black\/20 {
  background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.02)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

.executive-kpi-rail > div {
  min-height: 88px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.025);
}

.executive-command-body {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.015), transparent 48%),
    linear-gradient(90deg, transparent 0, transparent calc(100% - 1px), rgba(255,255,255,0.018) calc(100% - 1px));
  background-size: 100% 100%, 24px 24px;
}

.executive-alert-card {
  border-color: rgba(111,211,255,0.18) !important;
  background: linear-gradient(180deg, rgba(12,25,40,0.88), rgba(11,16,25,0.92)) !important;
}

.executive-alert-card .p-4.md\:p-5.space-y-3 > div {
  backdrop-filter: blur(8px);
}

.ios-story-card {
  min-height: 168px;
}

.holdings-terminal-shell {
  border: 1px solid rgba(255,255,255,0.08) !important;
  background:
    linear-gradient(180deg, rgba(15,22,33,0.94), rgba(9,12,18,0.98)) !important;
}

.holdings-terminal-toolbar {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.018)) !important;
}

.holdings-terminal-toolbar h3::after {
  content: "TERMINAL";
  display: inline-flex;
  margin-left: 0.6rem;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  font-size: 10px;
  letter-spacing: 0.16em;
  color: rgba(255,176,0,0.92);
  border: 1px solid rgba(255,176,0,0.16);
  background: rgba(255,176,0,0.06);
  vertical-align: middle;
}

.bloomberg-table {
  border-collapse: separate;
  border-spacing: 0;
}

.bloomberg-table th {
  position: relative;
  font-size: 10.5px !important;
  letter-spacing: 0.10em !important;
  color: rgba(255,196,90,0.92) !important;
  text-transform: uppercase;
  border-right: 1px solid rgba(255,255,255,0.045);
}

.bloomberg-table td {
  font-size: 12px;
  padding-top: 0.52rem !important;
  padding-bottom: 0.52rem !important;
  border-right: 1px solid rgba(255,255,255,0.03);
}

.bloomberg-table td:last-child,
.bloomberg-table th:last-child {
  border-right: none;
}

.bloomberg-table-body tbody tr:hover {
  background: linear-gradient(90deg, rgba(111,211,255,0.07), rgba(255,255,255,0.015)) !important;
}

.group-header td {
  position: sticky;
  top: 0;
  z-index: 2;
}

.analytics-command-toolbar {
  background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015)) !important;
  border-color: rgba(255,255,255,0.08) !important;
}

.analytics-hierarchy-strip {
  background: linear-gradient(180deg, rgba(16,22,32,0.88), rgba(11,16,25,0.92)) !important;
}

.institutional-stack-grid {
  background:
    linear-gradient(90deg, transparent 0, transparent calc(100% - 1px), rgba(255,255,255,0.022) calc(100% - 1px));
  background-size: 24px 24px;
}

.stack-card {
  border-radius: 1.05rem;
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.022));
  padding: 1rem;
  min-height: 132px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

.stack-card-governance { border-left: 3px solid rgba(248,113,113,0.82); }
.stack-card-execution { border-left: 3px solid rgba(255,176,0,0.82); }
.stack-card-insight { border-left: 3px solid rgba(111,211,255,0.82); }

.stack-kicker {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: rgba(235,235,245,0.46);
  margin-bottom: 0.5rem;
  font-weight: 800;
}

.stack-title {
  color: #fff;
  font-weight: 800;
  font-size: 0.98rem;
}

.stack-copy {
  color: rgba(255,196,90,0.96);
  font-weight: 700;
  margin-top: 0.55rem;
  font-size: 0.88rem;
}

.stack-note {
  color: rgba(235,235,245,0.6);
  margin-top: 0.45rem;
  line-height: 1.5;
  font-size: 12px;
}

.institutional-governance-shell {
  border-left: 3px solid rgba(248,113,113,0.78) !important;
}

.institutional-governance-shell .rounded-2xl.border.border-white\/10.bg-black\/20,
.institutional-cockpit-shell .rounded-2xl.border.border-white\/10.bg-black\/20,
.cro-intelligence-shell .rounded-2xl.border.border-white\/10.bg-black\/20 {
  background: linear-gradient(180deg, rgba(255,255,255,0.038), rgba(255,255,255,0.018)) !important;
}

.institutional-cockpit-shell {
  border-left: 3px solid rgba(255,176,0,0.82) !important;
}

.cockpit-table thead {
  background: rgba(8,12,19,0.96) !important;
}

.cockpit-table td,
.cockpit-table th {
  border-right: 1px solid rgba(255,255,255,0.04);
}

.cockpit-table td:last-child,
.cockpit-table th:last-child { border-right: none; }

.cro-intelligence-shell {
  border-left: 3px solid rgba(111,211,255,0.82) !important;
  background: linear-gradient(180deg, rgba(10,22,38,0.92), rgba(10,14,22,0.94)) !important;
}

.cro-diagnosis-shell ul li {
  border-left: 2px solid rgba(111,211,255,0.35);
}

@media (min-width: 1280px) {
  .summary-exec-grid {
    grid-template-columns: minmax(0, 1.9fr) minmax(360px, 0.95fr);
  }
}

@media (max-width: 1023px) {
  .ios-story-card { min-height: auto; }
  .stack-card { min-height: auto; }
}
