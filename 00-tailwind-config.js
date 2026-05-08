/* ===== 共用面板元件 ===== */
.panel-card {
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 1rem;
    overflow: hidden;
    position: relative;
}

.chart-card {
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 1rem;
    overflow: hidden;
    position: relative;
    min-height: 320px;
}

@media (min-width: 768px) {
    .chart-card {
        min-height: 420px;
    }
}

.panel-title {
    color: #ffffff;
    font-weight: 700;
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

@media (min-width: 768px) {
    .panel-title {
        font-size: 1.125rem;
    }
}

.panel-subtitle {
    color: #6b7280;
    font-size: 0.75rem;
    margin-top: 0.25rem;
}

.tool-btn {
    padding: 0.625rem 0.75rem;
    border-radius: 0.75rem;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.2s ease-in-out;
    border: 1px solid transparent;
}

.tool-btn:hover {
    transform: translateY(-1px);
}

.tool-btn-blue {
    color: #60a5fa;
    background: rgba(59, 130, 246, 0.10);
    border-color: rgba(59, 130, 246, 0.12);
}
.tool-btn-blue:hover {
    color: white;
    background: rgba(59, 130, 246, 0.20);
}

.tool-btn-yellow {
    color: #facc15;
    background: rgba(234, 179, 8, 0.10);
    border-color: rgba(234, 179, 8, 0.12);
}
.tool-btn-yellow:hover {
    color: white;
    background: rgba(234, 179, 8, 0.20);
}

.tool-btn-green {
    color: #4ade80;
    background: rgba(34, 197, 94, 0.10);
    border-color: rgba(34, 197, 94, 0.12);
}
.tool-btn-green:hover {
    color: white;
    background: rgba(34, 197, 94, 0.20);
}

.tool-btn-red {
    color: #f87171;
    background: rgba(239, 68, 68, 0.10);
    border-color: rgba(239, 68, 68, 0.12);
}
.tool-btn-red:hover {
    color: white;
    background: rgba(239, 68, 68, 0.20);
}

.panel-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.625rem;
    border-radius: 0.5rem;
    font-size: 11px;
    font-weight: 700;
    border: 1px solid rgba(99, 102, 241, 0.20);
    background: rgba(99, 102, 241, 0.10);
    color: #a5b4fc;
}
/* ===== Badge 元件 ===== */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.625rem;
    border-radius: 0.5rem;
    font-size: 11px;
    font-weight: 700;
    border: 1px solid transparent;
}

.badge-indigo {
    color: #a5b4fc;
    background: rgba(99, 102, 241, 0.10);
    border-color: rgba(99, 102, 241, 0.20);
}

.badge-blue {
    color: #93c5fd;
    background: rgba(59, 130, 246, 0.10);
    border-color: rgba(59, 130, 246, 0.20);
}

.badge-purple {
    color: #c4b5fd;
    background: rgba(147, 51, 234, 0.10);
    border-color: rgba(147, 51, 234, 0.20);
}

.badge-red {
    color: #fecaca;
    background: rgba(127, 29, 29, 0.40);
    border-color: rgba(153, 27, 27, 0.60);
}
:root {
    --app-header-height: 0px;
}

.holdings-fake-header-anchor {
    position: relative;
    height: 64px;
    z-index: 40;
}

.holdings-fake-header {
    position: sticky;
    top: var(--app-header-height);
    z-index: 40;
    background: rgba(17, 24, 39, 0.98);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.holdings-fake-header table,
.holdings-body-table {
    width: max-content;
    min-width: 100%;
}

#holdingsHeaderScroll {
    overflow: hidden;
}

#holdingsBodyScroll {
    overflow-x: auto;
    overflow-y: visible;
}

.holdings-sticky-th,
.holdings-sticky-thead {
    position: static !important;
    top: auto !important;
    z-index: auto !important;
    background: rgba(17, 24, 39, 0.98) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.06);
}

.group-header td {
    background-color: rgba(30, 41, 59, 0.98);
    color: #60a5fa;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
}
