        function getTypeColor(type) { return (type==='Buy' || type==='Expense') ? 'text-red-400' : 'text-green-400'; }
        function getCategoryColorCode(cat) { return '#3b82f6'; }
        function formatNumber(n) { return new Intl.NumberFormat('zh-TW', {maximumFractionDigits:0}).format(n||0); }
        function formatPercent(n) { return ((n||0)*100).toFixed(1) + '%'; }
        function updateStickyHeaderOffsets() {
            const headerEl = document.querySelector('header');
            const root = document.documentElement;

            if (!headerEl || !root) return;

            const headerHeight = Math.ceil(headerEl.getBoundingClientRect().height);
            root.style.setProperty('--app-header-height', `${headerHeight}px`);
        }
        function syncHoldingsHeaderScroll(event) {
    const headerScroll = document.getElementById('holdingsHeaderScroll');
    if (!headerScroll || !event?.target) return;
    headerScroll.scrollLeft = event.target.scrollLeft;
}

        let chartSML, chartCML, chartAlloc, chartHist, chartRolling, chartMC, chartFire, chartCorr;
        let chartUpdateFrame = null;
        let chartResizeTimer1 = null;
        let chartResizeTimer2 = null;
        function getAllCharts() {
    return [
        chartAlloc,
        chartHist,
        chartSML,
        chartCML,
        chartRolling,
        chartMC,
        chartFire,
        chartCorr
    ].filter(Boolean);
}

function resizeAllCharts() {
    requestAnimationFrame(() => {
        getAllCharts().forEach(chart => {
            try {
                chart.resize();
                chart.update('none');
            } catch (err) {
                console.warn('chart resize failed:', err);
            }
        });
    });
}

        function drawCorrelationMatrix() {
    const canvas = document.getElementById('corrChart');
    if (!canvas || !correlationMatrix.value) return;

    const matrixObj = correlationMatrix.value;
    const tickers = Object.keys(matrixObj);
    if (tickers.length === 0) return;

    const dataPoints = [];
    for (let i = 0; i < tickers.length; i++) {
        for (let j = 0; j < tickers.length; j++) {
            dataPoints.push({
                x: j,
                y: i,
                v: matrixObj[tickers[i]][tickers[j]]
            });
        }
    }

    if (!chartCorr) {
        chartCorr = new Chart(canvas, {
            type: 'matrix',
            data: {
                datasets: [{
                    label: 'Correlation',
                    data: dataPoints,
                    backgroundColor: (context) => {
                        const val = context.raw.v;
                        if (val === 1) return 'rgba(16, 185, 129, 0.9)';
                        if (val > 0) return `rgba(16, 185, 129, ${val * 0.8})`;
                        if (val < 0) return `rgba(239, 68, 68, ${Math.abs(val) * 0.8})`;
                        return 'rgba(30, 41, 59, 1)';
                    },
                    borderColor: '#1e293b',
                    borderWidth: 1,
                    width: (c) => c.chart.chartArea ? (c.chart.chartArea.width / tickers.length - 2) : 20,
                    height: (c) => c.chart.chartArea ? (c.chart.chartArea.height / tickers.length - 2) : 20,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: () => null,
                            label: (context) =>
                                `${tickers[context.raw.y]} & ${tickers[context.raw.x]}: ${context.raw.v.toFixed(2)}`
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        labels: tickers,
                        ticks: { color: '#94a3b8', font: { size: 10 } },
                        grid: { display: false }
                    },
                    y: {
                        type: 'category',
                        labels: tickers,
                        ticks: { color: '#94a3b8', font: { size: 10 } },
                        grid: { display: false },
                        reverse: true
                    }
                }
            }
        });
        return;
    }

    chartCorr.data.datasets[0].data = dataPoints;
    chartCorr.options.scales.x.labels = tickers;
    chartCorr.options.scales.y.labels = tickers;
    chartCorr.options.plugins.tooltip.callbacks.label = (context) =>
        `${tickers[context.raw.y]} & ${tickers[context.raw.x]}: ${context.raw.v.toFixed(2)}`;

    chartCorr.update('none');
}

        function initCharts() {
            Chart.defaults.color = '#94a3b8'; Chart.defaults.borderColor = '#334155';
            const allocCtx = document.getElementById('allocationChart'); if(allocCtx && !chartAlloc) chartAlloc = new Chart(allocCtx, { type: 'doughnut', data: { labels: [], datasets: [{data:[]}] }, options: { responsive: true, maintainAspectRatio: false } });
            const histCtx = document.getElementById('historyChart'); if(histCtx && !chartHist) chartHist = new Chart(histCtx, { type: 'line', data: { labels: [], datasets: [{data:[]},{data:[]}] }, options: { responsive: true, maintainAspectRatio: false } });
            const smlCtx = document.getElementById('smlChart');
if (smlCtx && !chartSML) {
    chartSML = new Chart(smlCtx, {
        type: 'scatter',
        data: { datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Beta (β)' },
                    min: 0,
                    max: 2
                },
                y: {
                    title: { display: true, text: 'Annualized Return (%)' },
                    min: -20,
                    max: 60
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const rawY = ctx.raw?.rawY ?? ctx.raw?.y ?? 0;
                            const capped = ctx.raw?.y ?? 0;
                            const suffix = rawY !== capped ? ` (顯示封頂: ${capped.toFixed(2)}%)` : '';
                            return `${ctx.raw.name}: (${ctx.raw.x.toFixed(2)}, 原始 ${rawY.toFixed(2)}%)${suffix}`;
                        }
                    }
                }
            }
        }
    });
}
            const cmlCtx = document.getElementById('cmlChart');
if (cmlCtx && !chartCML) {
    chartCML = new Chart(cmlCtx, {
        type: 'scatter',
        data: { datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
    title: { display: true, text: 'StdDev (σ%)' },
    min: 0,
    max: 40
},
                y: {
                    title: { display: true, text: 'Annualized Return (%)' },
                    min: -20,
                    max: 60
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
    const rawX = ctx.raw?.rawX ?? ctx.raw?.x ?? 0;
    const rawY = ctx.raw?.rawY ?? ctx.raw?.y ?? 0;
    const cappedX = ctx.raw?.x ?? 0;
    const cappedY = ctx.raw?.y ?? 0;

    const xSuffix = rawX !== cappedX ? ` (波動顯示封頂: ${cappedX.toFixed(2)}%)` : '';
    const ySuffix = rawY !== cappedY ? ` (報酬顯示封頂: ${cappedY.toFixed(2)}%)` : '';

    return `${ctx.raw.name}: 原始 (${rawX.toFixed(2)}%, ${rawY.toFixed(2)}%)${xSuffix}${ySuffix}`;
}
                    }
                }
            }
        }
    });
}            const rollingCtx = document.getElementById('rollingChart');
            if(rollingCtx && !chartRolling) { chartRolling = new Chart(rollingCtx, { type: 'line', data: { labels: [], datasets: [] }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { type: 'linear', display: true, position: 'left', title: {display: true, text: 'Sharpe Ratio'} }, y1: { type: 'linear', display: true, position: 'right', grid: {drawOnChartArea: false}, title: {display: true, text: 'Volatility (%)'} } } } }); }
            const fireCtx = document.getElementById('fireChart');
            if(fireCtx && !chartFire) { chartFire = new Chart(fireCtx, { type: 'line', data: { labels: [], datasets: [] }, options: { responsive: true, maintainAspectRatio: false, scales: { x: { title: {display:true, text:'年份'} }, y: { title: {display:true, text:'總淨值 (TWD)'}, beginAtZero: true } }, plugins: { tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: NT$ ${new Intl.NumberFormat('zh-TW').format(ctx.raw)}` } }, legend: { labels: { color: '#e2e8f0' } } } } }); }
        }

        function updateCharts() {
            function capPlotReturn(val) {
    const n = parseFloat(val);
    if (isNaN(n)) return 0;
    return Math.max(-20, Math.min(n, 60));
    }
    function capPlotStdDev(val) {
    const n = parseFloat(val);
    if (isNaN(n)) return 0;
    return Math.max(0, Math.min(n, 40));
}
    if (chartUpdateFrame) cancelAnimationFrame(chartUpdateFrame);
    if (chartResizeTimer1) clearTimeout(chartResizeTimer1);
    if (chartResizeTimer2) clearTimeout(chartResizeTimer2);

    chartUpdateFrame = requestAnimationFrame(() => {
        initCharts();

        if (chartAlloc) {
            const cats = categoryTotals.value;
            chartAlloc.data.labels = Object.keys(cats);
            chartAlloc.data.datasets[0].data = Object.values(cats);
            chartAlloc.data.datasets[0].backgroundColor = ['#f59e0b','#3b82f6','#10b981','#a855f7'];
            chartAlloc.update();
        }

        if (chartHist) {
            const history = displayHistory.value;
            const sorted = [...history].sort((a,b)=>new Date(a.date)-new Date(b.date));
            chartHist.data.labels = sorted.map(h=>h.date);
            chartHist.data.datasets[0] = {
                label: 'NAV',
                data: sorted.map(h=>h.assets),
                borderColor: '#3b82f6',
                fill: true,
                backgroundColor: 'rgba(59,130,246,0.1)',
                tension: 0.1
            };
            chartHist.data.datasets[1] = {
                label: 'Cost',
                data: sorted.map(h=>h.cost),
                borderColor: '#10b981',
                borderDash:[5,5],
                tension: 0.1
            };
            if (chartHist.data.datasets.length > 2) chartHist.data.datasets.splice(2);
            chartHist.update();
        }

        if (chartFire) {
            const targets = fireTargets.value;
            const maxYear = targets.length > 0 ? Math.max(...targets.map(t => t.year)) : 2052;
            const startYear = 2028;
            const labels = [];
            for (let y = startYear; y <= maxYear; y++) labels.push(y);

            const targetData = labels.map(y => {
                if (y === startYear) return 0;
                const t = targets.find(target => target.year === y);
                return t ? t.amount : null;
            });

            const history = displayHistory.value;
            let lastKnownAsset = 0;
            const currentYear = new Date().getFullYear();
            const actualData = labels.map(y => {
                if (y === startYear && history.filter(h => h.date.startsWith(startYear.toString())).length > 0) {
                    const yearHistory = history.filter(h => h.date.startsWith(startYear.toString()));
                    lastKnownAsset = yearHistory[yearHistory.length - 1].assets;
                    return lastKnownAsset;
                }
                if (y <= currentYear) {
                    const yearHistory = history.filter(h => h.date.startsWith(y.toString()));
                    if (yearHistory.length > 0) {
                        lastKnownAsset = yearHistory[yearHistory.length - 1].assets;
                        return lastKnownAsset;
                    }
                    return null;
                }
                return null;
            });

            chartFire.data.labels = labels;
chartFire.data.datasets = [
    {
        label: 'FIRE 目標線',
        data: targetData,
        borderColor: '#f87171',
        backgroundColor: 'rgba(248,113,113,0.12)',
        borderDash: [6, 6],
        tension: 0.2,
        spanGaps: true,
        borderWidth: 3,
        pointRadius: 3,
        pointHoverRadius: 4,
        fill: false
    },
    {
        label: '實際淨值',
        data: actualData,
        borderColor: '#fbbf24',
        backgroundColor: 'rgba(251,191,36,0.15)',
        tension: 0.25,
        spanGaps: true,
        borderWidth: 3,
        pointRadius: 3,
        pointHoverRadius: 4,
        fill: false
    }
];
chartFire.update();
        }

        if (chartSML) {
    const points = [];
    for (const cat in groupedHoldings.value) {
        groupedHoldings.value[cat].items.forEach(item => {
            const rawY = parseFloat(item.annualizedReturnRate) || 0;
            points.push({
                x: parseFloat(item.beta) || 0,
                y: capPlotReturn(rawY),
                rawY,
                name: item.ticker
            });
        });
    }

    const rf = parseFloat(riskParams.value.rf) || 0;
    const rm = parseFloat(riskParams.value.rm) || 0;

    const portfolioSmlPoint = {
    x: parseFloat(portfolioStats.value.beta) || 0,
    y: capPlotReturn(parseFloat(stats.value.annRet) || 0),
    rawY: parseFloat(stats.value.annRet) || 0,
    name: 'Portfolio'
};

chartSML.data.datasets = [
    {
        label: 'Assets',
        data: points,
        backgroundColor: '#60a5fa',
        pointRadius: 4,
        pointHoverRadius: 5
    },
    {
        label: 'Portfolio',
        data: [portfolioSmlPoint],
        backgroundColor: '#f43f5e',
        borderColor: '#ffffff',
        borderWidth: 2,
        pointRadius: 8,
        pointHoverRadius: 10,
        pointStyle: 'circle'
    },
    {
        type: 'line',
        label: 'SML',
        data: [
            { x: 0, y: rf },
            { x: 2, y: rf + 2 * (rm - rf) }
        ],
        borderColor: '#fbbf24',
        pointRadius: 0,
        tension: 0
    }
];

    chartSML.update();
}

        if (chartCML) {
    const points = [];
    for (const cat in groupedHoldings.value) {
        groupedHoldings.value[cat].items.forEach(item => {
            const rawY = parseFloat(item.annualizedReturnRate) || 0;
            points.push({
    x: capPlotStdDev(parseFloat(item.stdDev) || 0),
    rawX: parseFloat(item.stdDev) || 0,
    y: capPlotReturn(rawY),
    rawY,
    name: item.ticker
});
        });
    }

    const rf = parseFloat(riskParams.value.rf) || 0;
    const rm = parseFloat(riskParams.value.rm) || 0;
    const sm = parseFloat(riskParams.value.sm) || 15;

    const portfolioCmlPoint = {
    x: capPlotStdDev(parseFloat(stats.value.annVol) || 0),
    rawX: parseFloat(stats.value.annVol) || 0,
    y: capPlotReturn(parseFloat(stats.value.annRet) || 0),
    rawY: parseFloat(stats.value.annRet) || 0,
    name: 'Portfolio'
};

chartCML.data.datasets = [
    {
        label: 'Assets',
        data: points,
        backgroundColor: '#a78bfa',
        pointRadius: 4,
        pointHoverRadius: 5
    },
    {
        label: 'Portfolio',
        data: [portfolioCmlPoint],
        backgroundColor: '#f43f5e',
        borderColor: '#ffffff',
        borderWidth: 2,
        pointRadius: 8,
        pointHoverRadius: 10,
        pointStyle: 'circle'
    },
    {
        type: 'line',
        label: 'CML',
        data: [
            { x: 0, y: rf },
            { x: Math.min(sm * 2, 40), y: rf + 2 * (rm - rf) }
        ],
        borderColor: '#34d399',
        pointRadius: 0,
        tension: 0
    }
];

    chartCML.update();
}

        if (chartRolling) {
            const h = [...enrichedHistory.value].reverse();
            const rollingLabels = [];
            const sharpeSeries = [];
            const volSeries = [];

            for (let i = 12; i < h.length; i++) {
                const windowData = h.slice(i - 12, i + 1).map(item => item.dailyReturn).filter(v => v !== null);
                if (windowData.length < 2) continue;

                const avg = windowData.reduce((a, b) => a + b, 0) / windowData.length;
                const std = Math.sqrt(windowData.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / (windowData.length - 1));
                const annVol = std * Math.sqrt(52);
                const annRet = Math.pow(windowData.reduce((a, r) => a * (1 + r), 1), 52 / windowData.length) - 1;
                const rf = (parseFloat(riskParams.value.rf) || 0) / 100;
                const sharpe = annVol > 0 ? (annRet - rf) / annVol : 0;

                rollingLabels.push(h[i].date);
                sharpeSeries.push(parseFloat(sharpe.toFixed(2)));
                volSeries.push(parseFloat((annVol * 100).toFixed(2)));
            }

            chartRolling.data.labels = rollingLabels;
            chartRolling.data.datasets = [
                {
                    label: 'Rolling Sharpe',
                    data: sharpeSeries,
                    borderColor: '#60a5fa',
                    backgroundColor: 'rgba(96,165,250,0.12)',
                    yAxisID: 'y',
                    tension: 0.2
                },
                {
                    label: 'Rolling Volatility',
                    data: volSeries,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245,158,11,0.12)',
                    yAxisID: 'y1',
                    tension: 0.2
                }
            ];
            chartRolling.update();
        }

        drawCorrelationMatrix();

        chartResizeTimer1 = setTimeout(() => {
            resizeAllCharts();
        }, 0);

        chartResizeTimer2 = setTimeout(() => {
            resizeAllCharts();
        }, 120);
    });
}

        onMounted(() => {
            updateStickyHeaderOffsets();

    window.addEventListener('resize', updateStickyHeaderOffsets);
    loadDataFromCloud();

    window.addEventListener('resize', () => {
        resizeAllCharts();
    });
});
        watch(currentTab, async () => {
            await nextTick();
            updateStickyHeaderOffsets();
            updateCharts();

            setTimeout(() => {
                updateStickyHeaderOffsets();
                resizeAllCharts();
            }, 60);

            setTimeout(() => {
                updateStickyHeaderOffsets();
                resizeAllCharts();
            }, 180);
        });

        watch([exchangeRate, sheetUrl, riskParams, quantStartDate, dataFrequency, fireTargets, correlationMatrix], () => updateCharts(), { deep: true });
        watch(liquidityBufferRatio, async (newVal, oldVal) => {
    const clamped = clampLiquidityBuffer(newVal);
    if (clamped !== newVal) {
        liquidityBufferRatio.value = clamped;
        return;
    }

    updateCharts();

    if (oldVal !== undefined && newVal !== oldVal) {
        await saveData();
        if (showMCModal.value) {
            nextTick(() => runMonteCarlo());
        }
    }
});


        const allocationGovernance = computed(() => {
            const sr = syntheticRiskMeta?.value || null;
            const confidence = sr?.confidence || 'N/A';
            const status = sr?.status || 'PENDING';
            const sampleCount = Number(sr?.metrics?.sample_count || 0);
            const alertCount = Number(rebalanceMonitor?.value?.alertCount || 0);
            const bufferBlocked = !!rebalanceMonitor?.value?.bufferBlockingRiskBuys;

            const hardFlags = [];
            const softFlags = [];

            if (status === 'FAILED' || status === 'INVALID' || confidence === 'INVALID') {
                hardFlags.push({
                    code: 'SYNTHETIC_RISK_INVALID',
                    label: '合成風險資料不可用',
                    detail: sr?.confidence_reason || 'synthetic risk 尚未產生或資料不足。'
                });
            }

            if (bufferBlocked) {
                hardFlags.push({
                    code: 'BUFFER_BLOCK',
                    label: '流動性緩衝不足',
                    detail: '再平衡監控顯示暫停新增風險資產。'
                });
            }

            if (alertCount >= 3) {
                softFlags.push({
                    code: 'REBALANCE_ALERTS',
                    label: '再平衡警示偏多',
                    detail: `目前有 ${alertCount} 個再平衡警示。`
                });
            }

            if (confidence === 'LOW' || (sampleCount > 0 && sampleCount < 750)) {
                softFlags.push({
                    code: 'SHORT_SAMPLE',
                    label: '樣本偏短',
                    detail: `synthetic risk 樣本日數 ${sampleCount || 'N/A'}；可看方向，不宜當成硬交易規則。`
                });
            }

            if (confidence === 'MEDIUM') {
                softFlags.push({
                    code: 'MEDIUM_CONFIDENCE',
                    label: '模型信心中等',
                    detail: '樣本與涵蓋度可作主要風控參考，但仍需人工判讀。'
                });
            }

            let mode = 'MC_PRIMARY';
            if (hardFlags.length) mode = 'CRO_VETO';
            else if (softFlags.length) mode = 'CRO_CAUTION_MC_ALLOWED';

            const base = {
                mode,
                hardFlags,
                softFlags,
                primaryReasons: (hardFlags.length ? hardFlags : softFlags).slice(0, 3),
                deterministicNote: '這一層是 deterministic governance，不靠 prompt 自由發揮。'
            };

            if (mode === 'CRO_VETO') {
                return {
                    ...base,
                    icon: 'fa-triangle-exclamation',
                    badgeText: 'CRO 否決 / 風控紅燈',
                    badgeClass: 'border-red-500/30 bg-red-500/10 text-red-300',
                    panelClass: 'border-red-500/25 bg-red-500/5',
                    headline: '風險資料或緩衝條件不足，先不要放大風險。',
                    summary: 'synthetic risk 或再平衡監控出現 hard flag；先處理資料完整性、buffer 與集中度。',
                    croRole: 'CRO = 否決層（整體投組風險裁決）',
                    mcRole: 'MC = 配置器，但目前不可主導加風險'
                };
            }

            if (mode === 'CRO_CAUTION_MC_ALLOWED') {
                return {
                    ...base,
                    icon: 'fa-flask',
                    badgeText: '樣本偏短 / 警戒',
                    badgeClass: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
                    panelClass: 'border-amber-500/25 bg-amber-500/5',
                    headline: '可看風險方向，但不能把模型結果當成硬指令。',
                    summary: '目前沒有 hard veto；但 synthetic risk 樣本偏短或警示偏多，配置調整應保守。',
                    croRole: 'CRO = 提醒整體投組風險，不搶單一資產權重',
                    mcRole: 'MC = 風險資產配置器，可作主配置但需降自信'
                };
            }

            return {
                ...base,
                icon: 'fa-circle-check',
                badgeText: 'MC 主導',
                badgeClass: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
                panelClass: 'border-emerald-500/25 bg-emerald-500/5',
                headline: '無硬風險阻礙，由 MC 主導配置。',
                summary: 'CRO 未見 hard veto；whole-portfolio 可以放行，risky sleeve 交由 MC 最佳化。',
                croRole: 'CRO = 監督層，不主動搶配置權',
                mcRole: 'MC = 風險資產配置器，主導權重建議'
            };
        });


        const navOverlayMode = ref('nav');
        const navOverlayOptions = [
            { value: 'nav', label: 'NAV' },
            { value: 'drawdown', label: '回撤' },
            { value: 'both', label: 'NAV + 回撤' }
        ];
        const setNavOverlayMode = (mode) => {
            const allowed = new Set(navOverlayOptions.map(opt => opt.value));
            navOverlayMode.value = allowed.has(mode) ? mode : 'nav';
            try {
                setTimeout(() => updateCharts && updateCharts(), 0);
            } catch (err) {
                console.warn('setNavOverlayMode chart refresh skipped:', err);
            }
        };
        const navMaConfig = computed(() => ({
            monthLabel: '短期趨勢：3M MA',
            yearLabel: '長期趨勢：12M MA',
            frequencyNote: '以現有 NAV history 計算；資料不足時顯示為 N/A'
        }));
        const riskRegimeStrip = computed(() => {
            const sr = syntheticRiskMeta?.value || null;
            const confidence = sr?.confidence || 'N/A';
            const mdd = Number(sr?.metrics?.max_drawdown_pct || 0);
            const es95 = Number(sr?.metrics?.es95_pct || 0);
            if (sr?.status === 'FAILED' || sr?.status === 'INVALID') {
                return {
                    class: 'border-red-500/30 bg-red-500/10 text-red-200',
                    label: '風控資料不足',
                    note: 'synthetic risk 尚未可用'
                };
            }
            if (mdd <= -20 || es95 >= 6) {
                return {
                    class: 'border-orange-500/30 bg-orange-500/10 text-orange-200',
                    label: '風險偏高',
                    note: '尾部風險或回撤偏高'
                };
            }
            if (confidence === 'LOW') {
                return {
                    class: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
                    label: '樣本偏短',
                    note: '模型方向可參考，信心偏低'
                };
            }
            return {
                class: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200',
                label: '風險穩定',
                note: '目前未見 hard veto'
            };
        });
        const navTrendSummary = computed(() => {
            const modeMap = {
                nav: 'NAV',
                drawdown: 'Drawdown',
                both: 'NAV + Drawdown'
            };
            return {
                navVsMonth: 'N/A',
                navVsYear: 'N/A',
                monthSlope: 'N/A',
                yearSlope: 'N/A',
                currentDrawdown: syntheticRiskMeta?.value?.metrics?.max_drawdown_pct != null
                    ? `${syntheticRiskMeta.value.metrics.max_drawdown_pct}%`
                    : 'N/A',
                overlayModeLabel: modeMap[navOverlayMode.value] || 'NAV'
            };
        });



        // ===== Compatibility layer for terminal IA template =====
        // This block provides safe defaults for template-only variables so Vue render
        // does not crash while cloud data is still loading.
        const filteredHoldingsGroups = computed(() => filteredGroupedHoldings?.value || {});

        const holdingsVisibleStats = computed(() => {
            const groups = filteredHoldingsGroups.value || {};
            let visible = 0;
            Object.values(groups).forEach(group => {
                if (Array.isArray(group?.items)) visible += group.items.length;
                else if (Array.isArray(group)) visible += group.length;
            });

            let total = 0;
            Object.values(groupedHoldings?.value || {}).forEach(group => {
                if (Array.isArray(group?.items)) total += group.items.length;
                else if (Array.isArray(group)) total += group.length;
            });

            return { visible, total };
        });

        const tradeBufferBasePct = ref(3.0);
        const tradeBufferPresets = [1, 2, 3, 5, 7.5];

        const holdingsActionFilter = ref('all');
        const holdingsViewOptions = [
            { value: 'all', label: '全部' },
            { value: 'trim', label: '先減碼' },
            { value: 'add', label: '可加碼' },
            { value: 'locked', label: '鎖定' },
            { value: 'watch', label: '觀察' },
            { value: 'high_risk', label: '高風險' },
            { value: 'overweight', label: '過重' },
            { value: 'drift', label: 'Drift' }
        ];

        const goToTab = (tab) => {
            if (!tab) return;
            currentTab.value = tab;
            try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (err) {}
        };

        const flattenHoldingRows = (useFiltered = false) => {
            const groups = useFiltered ? (filteredHoldingsGroups.value || {}) : (groupedHoldings?.value || {});
            const rows = [];
            Object.entries(groups || {}).forEach(([catName, group]) => {
                const items = Array.isArray(group?.items) ? group.items : (Array.isArray(group) ? group : []);
                items.forEach(stock => {
                    if (stock) rows.push({ ...stock, categoryName: stock.categoryName || catName });
                });
            });
            return rows;
        };

        const historyIntegrityRisk = computed(() => {
            const reasons = [];
            const hist = displayHistory?.value || [];
            if (hist.length < 2) reasons.push('NAV history 少於 2 筆，績效與趨勢判讀信心低。');
            const invalid = hist.filter(row => !row || !row.date || !Number.isFinite(Number(row.assets)));
            if (invalid.length) reasons.push(`NAV history 有 ${invalid.length} 筆日期或資產值異常。`);
            return { reasons };
        });

        const historyIntegrityBadge = computed(() => {
            const reasons = historyIntegrityRisk.value?.reasons || [];
            if (reasons.length) {
                return {
                    label: '需檢查',
                    detail: reasons[0],
                    badgeClass: 'border-amber-500/40 bg-amber-500/10 text-amber-300'
                };
            }
            return {
                label: '樣本正常',
                detail: '歷史樣本暫時沒有明顯污染跡象。',
                badgeClass: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
            };
        });

        const tradeBufferProfile = computed(() => {
            const ag = allocationGovernance?.value || {};
            const addDisabled = ag.mode === 'CRO_VETO';
            return {
                mode: addDisabled ? 'CRO LOCK' : 'NORMAL',
                addDisabled,
                modeNote: addDisabled
                    ? 'CRO 目前否決加風險：只允許減碼、降低集中度或提高現金緩衝。'
                    : '沒有 hard veto：超出緩衝區才進入再平衡流程。'
            };
        });

        const applyTradeBuffer = (value) => {
            const n = Number(value);
            if (!Number.isFinite(n)) return;
            tradeBufferBasePct.value = Math.min(10, Math.max(0.5, n));
        };

        const nudgeTradeBuffer = (delta) => {
            applyTradeBuffer(Number(tradeBufferBasePct.value || 0) + Number(delta || 0));
        };

        const rebalanceCockpitRows = computed(() => {
            const rows = flattenHoldingRows(false).map(stock => {
                const currentWeightPct = Number(stock.totalWeight || 0) * 100;
                const targetWeightPct = Number(stock.blendedWeight ?? stock.targetWeight ?? 0);
                const driftPct = targetWeightPct - currentWeightPct;
                const base = Number(tradeBufferBasePct.value || 3);
                const addDisabled = !!tradeBufferProfile.value.addDisabled;

                let bucket = 'hold';
                let action = '暫不動';
                let actionClass = 'text-slate-300 bg-slate-500/10 border-slate-500/20';
                if (driftPct <= -base) {
                    bucket = 'trim';
                    action = '減碼';
                    actionClass = 'text-red-300 bg-red-500/10 border-red-500/20';
                } else if (driftPct >= base && addDisabled) {
                    bucket = 'pending';
                    action = '候補加碼';
                    actionClass = 'text-amber-300 bg-amber-500/10 border-amber-500/20';
                } else if (driftPct >= base) {
                    bucket = 'add';
                    action = '加碼';
                    actionClass = 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20';
                }

                const nav = Number(totalPortfolioNav?.value || totalStockValueTwd?.value || 0);
                const actionValue = nav * Math.abs(driftPct) / 100;

                return {
                    ticker: stock.ticker || '-',
                    categoryName: stock.categoryName || stock.category || '-',
                    currentWeightPct,
                    targetWeightPct,
                    driftPct,
                    driftText: `${driftPct >= 0 ? '+' : ''}${driftPct.toFixed(1)}%`,
                    actionValueText: `NT$ ${formatNumber(actionValue)}`,
                    action,
                    actionClass,
                    decisionOwner: bucket === 'pending' ? 'CRO' : 'MC',
                    governanceNote: bucket === 'hold' ? '在 no-trade zone 內' : tradeBufferProfile.value.modeNote,
                    bucket,
                    trimThresholdPct: base,
                    addThresholdPct: addDisabled ? Infinity : base
                };
            });

            return rows.sort((a, b) => Math.abs(b.driftPct) - Math.abs(a.driftPct));
        });

        const rebalanceCockpitBuckets = computed(() => {
            const buckets = { trim: [], add: [], pending: [], hold: [] };
            (rebalanceCockpitRows.value || []).forEach(row => {
                const key = buckets[row.bucket] ? row.bucket : 'hold';
                buckets[key].push(row);
            });
            return buckets;
        });

        const tradeBufferSummary = computed(() => {
            const buckets = rebalanceCockpitBuckets.value || { trim: [], add: [], pending: [], hold: [] };
            const base = Number(tradeBufferBasePct.value || 3);
            return {
                basePct: base,
                trimThresholdPct: base,
                addThresholdPct: tradeBufferProfile.value.addDisabled ? 0 : base,
                trimCount: (buckets.trim || []).length,
                addCount: (buckets.add || []).length,
                pendingAddCount: (buckets.pending || []).length,
                holdCount: (buckets.hold || []).length
            };
        });

        const holdingsActionSummary = computed(() => {
            const rows = flattenHoldingRows(false);
            const out = { total: rows.length, trim: 0, add: 0, locked: 0, watch: 0, highRisk: 0, overweight: 0, drift: 0 };
            rows.forEach(stock => {
                const currentPct = Number(stock.totalWeight || 0) * 100;
                const targetPct = Number(stock.blendedWeight ?? stock.targetWeight ?? 0);
                const gap = targetPct - currentPct;
                if (gap <= -tradeBufferBasePct.value) out.trim++;
                if (gap >= tradeBufferBasePct.value) out.add++;
                if (Math.abs(gap) >= tradeBufferBasePct.value) out.drift++;
                if (stock.isOverweight || currentPct >= 20) out.overweight++;
                const riskScore = Number(stock.riskScore ?? stock.risk_score ?? stock.riskLevelScore ?? 0);
                if (String(stock.riskLevel || '').toLowerCase() === 'high' || riskScore >= 7) out.highRisk++;
                if (stock.governanceStatus && String(stock.governanceStatus).includes('鎖')) out.locked++;
                if (Math.abs(gap) < tradeBufferBasePct.value && Math.abs(gap) >= Math.max(1, tradeBufferBasePct.value * 0.5)) out.watch++;
            });
            return out;
        });

        const rebalancePostTradeEstimate = computed(() => {
            const rows = rebalanceCockpitRows.value || [];
            const weights = rows.map(row => Number(row.currentWeightPct || 0)).filter(Number.isFinite);
            const concentrationBefore = weights.length ? Math.max(...weights) : null;
            const afterWeights = rows.map(row => {
                const current = Number(row.currentWeightPct || 0);
                const target = Number(row.targetWeightPct || current);
                if (row.bucket === 'trim' || row.bucket === 'add') return target;
                return current;
            }).filter(Number.isFinite);
            const concentrationAfter = afterWeights.length ? Math.max(...afterWeights) : null;
            const active = rows.filter(row => row.bucket !== 'hold');
            const avgGapBefore = active.length
                ? active.reduce((sum, row) => sum + Math.abs(Number(row.driftPct || 0)), 0) / active.length
                : 0;

            return {
                concentrationBefore,
                concentrationAfter,
                bufferGapBefore: avgGapBefore,
                bufferGapAfter: Math.max(0, avgGapBefore - Number(tradeBufferBasePct.value || 3))
            };
        });

        const alertCenterItems = computed(() => {
            const items = [];
            const ag = allocationGovernance?.value || null;
            if (ag) {
                items.push({
                    id: 'allocation-governance',
                    tone: ag.mode === 'CRO_VETO' ? 'risk' : 'info',
                    badgeClass: ag.badgeClass || 'border-slate-500/40 bg-slate-500/10 text-slate-300',
                    panelClass: ag.panelClass || 'border-white/10 bg-black/20',
                    icon: ag.icon || 'fa-shield-halved',
                    sourceLabel: 'CRO',
                    suggestedAction: 'Review',
                    title: ag.headline || ag.badgeText || '風控治理',
                    detail: ag.summary || '等待風控資料載入。',
                    ctaLabel: '看量化',
                    tab: 'analytics'
                });
            }
            const hRisk = historyIntegrityRisk.value?.reasons || [];
            if (hRisk.length) {
                items.push({
                    id: 'history-integrity',
                    tone: 'warn',
                    badgeClass: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
                    panelClass: 'border-amber-500/20 bg-amber-500/5',
                    icon: 'fa-database',
                    sourceLabel: 'Data',
                    suggestedAction: 'Check',
                    title: '歷史資料需檢查',
                    detail: hRisk[0],
                    ctaLabel: '看總覽',
                    tab: 'summary'
                });
            }
            return items;
        });

        const alertCenterSections = computed(() => {
            const items = alertCenterItems.value || [];
            return [{
                key: 'priority',
                label: items.length ? '優先處理' : '目前無急迫警報',
                items
            }];
        });

        const txPreview = computed(() => {
            const type = String(txForm?.value?.type || '');
            const flow = Number(txForm?.value?.totalCashFlow || 0);
            let finalFlow = flow;
            if (type === 'Buy' || type === 'Expense') finalFlow = -Math.abs(flow);
            if (type === 'Sell' || type === 'Deposit') finalFlow = Math.abs(flow);
            if (type === 'Withdraw') finalFlow = -Math.abs(flow);

            const projectedCashAfter = Number(cashBalance?.value || 0) + finalFlow;
            const errors = [];
            const blockers = [];
            const warnings = [];
            if ((type === 'Buy' || type === 'Withdraw' || type === 'Expense') && projectedCashAfter < -1) {
                blockers.push('送出後現金會變成負數。');
            }
            if (!type) warnings.push('尚未選擇交易類型。');

            return { finalFlow, projectedCashAfter, errors, blockers, warnings };
        });

        return { 
            filteredHoldingsGroups, holdingsVisibleStats, holdingsActionFilter, holdingsViewOptions, holdingsActionSummary, goToTab, historyIntegrityRisk, historyIntegrityBadge, alertCenterItems, alertCenterSections, tradeBufferBasePct, tradeBufferPresets, tradeBufferProfile, applyTradeBuffer, nudgeTradeBuffer, rebalanceCockpitRows, rebalanceCockpitBuckets, tradeBufferSummary, rebalancePostTradeEstimate, txPreview,
            currentTab, showHistoryModal, isUpdating,
            transactions, groupedHoldings, filteredGroupedHoldings, categoryTotals, riskTotals, portfolioStats, 
            totalStockValueTwd, totalStockCostTwd, totalStockUnrealizedPL, totalStockReturnRate, 
            reversedTransactions, txForm, historyForm, riskParams, stats, exchangeRate, 
            holdingsSearch, holdingsView, holdingsSort, filteredHoldingsCount, holdingsAlertCount, holdingsVisibleStats,
            txFlowMode, txTypeOptions, ledgerDraftPreview,
            sheetUrl, addTransaction, addHistoryRecord,
            removeTransaction, removeHistoryByDate, manualUpdate, updateMeta, fetchPrices, 
            exportAll, importData, getTypeColor, getCategoryColorCode, formatNumber, formatPercent, 
            lastUpdate, displayHistory, enrichedHistory, quantStartDate, dataFrequency, 
            snapshotToHistory, snapshotDate, isDbSyncing, 
            isAppReady, showMCModal, mcOptimal, openMonteCarlo, aiInsights, isAiExpanded, quantDays,
            fireTargets, activeFireStageIndex, activeFireTarget, isLoggedIn, loginEmail, loginPassword, loginError, 
            isAuthenticating, handleLogin, handleLogout, checkAuth, fireProgress, 
            updateCharts, addFireTarget, macroRegime, enableBlackSwan, mcRisk, blViews, mcAvailableAssets, addBlView, enableInflation,
            generateAutoViews, runMonteCarlo, stressTestResults,
            expandedCardTicker, toggleCard, isHistoryExpanded, cloudRebalanceMeta, sysCorr, navOverlayMode, navOverlayOptions, setNavOverlayMode, navMaConfig, riskRegimeStrip, navTrendSummary,
            syncHoldingsHeaderScroll,
            croInsight, isCroThinking, liquidityBufferRatio, bufferPresets, applyLiquidityBuffer, nudgeLiquidityBuffer, generateQuantInsight, chaosMeta,
            xrayStats, rebalanceMonitor, tailStatsLite, syntheticRiskMeta, allocationGovernance, decisionCenter, cashBalance, totalPortfolioNav, cashBalance, totalPortfolioNav, isCashNegative, isCashTooHigh, isCashAlert            
        };
    }
}).mount('#app');
