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

        return { 
            currentTab, showHistoryModal, isUpdating,
            transactions, groupedHoldings, categoryTotals, riskTotals, portfolioStats, 
            totalStockValueTwd, totalStockCostTwd, totalStockUnrealizedPL, totalStockReturnRate, 
            reversedTransactions, txForm, historyForm, riskParams, stats, exchangeRate, 
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
            expandedCardTicker, toggleCard, isHistoryExpanded, cloudRebalanceMeta, sysCorr,
            syncHoldingsHeaderScroll,
            croInsight, isCroThinking, liquidityBufferRatio, bufferPresets, applyLiquidityBuffer, nudgeLiquidityBuffer, generateQuantInsight, chaosMeta,
            xrayStats, rebalanceMonitor, tailStatsLite, cashBalance, totalPortfolioNav, cashBalance, totalPortfolioNav, isCashNegative, isCashTooHigh, isCashAlert            
        };
    }
}).mount('#app');