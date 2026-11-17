#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/js/src/app.bundle.source.js"
INDEX = ROOT / "index.html"

src = SRC.read_text(encoding="utf-8")
index = INDEX.read_text(encoding="utf-8")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)

src = replace_once(
    src,
    "let chartSML, chartCML, chartAlloc, chartHist, chartRolling, chartMC, chartFire, chartCorr;",
    "let chartSML, chartCML, chartAlloc, chartHist, chartDetrend, chartRolling, chartMC, chartFire, chartCorr;",
    "chart variable"
)

src = replace_once(
    src,
    """        chartAlloc,
        chartHist,
        chartSML,""",
    """        chartAlloc,
        chartHist,
        chartDetrend,
        chartSML,""",
    "chart resize registry"
)

helper_anchor = """        function navTrendFormatRatio(ratio, suffix = '') {
"""
helper_code = r'''        function navTrendDetrendPoints() {
            const points = navTrendTwrIndexPoints();
            if (!points.length) return [];

            const out = [];
            points.forEach((point) => {
                const trend = navTrendMovingAverage(points, point.ts, 12);
                if (!Number.isFinite(trend) || trend <= 0 || !Number.isFinite(point.value)) return;
                const deviation = point.value / trend - 1;
                if (!Number.isFinite(deviation)) return;
                out.push({
                    ...point,
                    trend,
                    deviation
                });
            });
            return out;
        }

        function navTrendDeviationWindowStats(points, endTs, months = 12) {
            if (!Array.isArray(points) || !points.length || !Number.isFinite(endTs)) return null;
            const startTs = navTrendShiftMonths(endTs, -months);
            const windowPoints = points.filter((point) =>
                Number.isFinite(point?.ts) &&
                Number.isFinite(point?.deviation) &&
                point.ts >= startTs &&
                point.ts <= endTs
            );
            if (windowPoints.length < 8) return null;

            const values = windowPoints.map((point) => point.deviation);
            const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
            const variance = values.length > 1
                ? values.reduce((sum, value) => sum + Math.pow(value - mean, 2), 0) / (values.length - 1)
                : 0;
            const std = Math.sqrt(Math.max(0, variance));
            const latest = windowPoints[windowPoints.length - 1];
            const z = std > 1e-12 ? (latest.deviation - mean) / std : 0;

            return {
                count: windowPoints.length,
                mean,
                std,
                z
            };
        }

'''
src = replace_once(src, helper_anchor, helper_code + helper_anchor, "detrend helper insertion")

summary_anchor = """        // ===== Compatibility layer for terminal IA template =====
"""
summary_code = r'''        const twrDetrendSummary = computed(() => {
            const points = navTrendDetrendPoints();
            const latest = points.length ? points[points.length - 1] : null;

            if (!latest) {
                return {
                    available: false,
                    twrIndex: 'N/A',
                    trendIndex: 'N/A',
                    deviation: 'N/A',
                    deviationZ: 'N/A',
                    sampleCount: 0,
                    statusLabel: '至少需要約 12 個月歷史',
                    statusClass: 'border-slate-500/30 bg-slate-500/10 text-slate-300'
                };
            }

            const deviationStats = navTrendDeviationWindowStats(points, latest.ts, 12);
            const z = deviationStats?.z;
            const absZ = Number.isFinite(z) ? Math.abs(z) : null;
            let statusLabel = '接近長期趨勢';
            let statusClass = 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';

            if (absZ === null) {
                statusLabel = 'Z-score 樣本不足';
                statusClass = 'border-amber-500/30 bg-amber-500/10 text-amber-300';
            } else if (absZ >= 2) {
                statusLabel = z > 0 ? '顯著高於長期趨勢' : '顯著低於長期趨勢';
                statusClass = 'border-red-500/30 bg-red-500/10 text-red-300';
            } else if (absZ >= 1) {
                statusLabel = z > 0 ? '中度高於長期趨勢' : '中度低於長期趨勢';
                statusClass = 'border-amber-500/30 bg-amber-500/10 text-amber-300';
            }

            return {
                available: true,
                twrIndex: latest.value.toFixed(2),
                trendIndex: latest.trend.toFixed(2),
                deviation: navTrendFormatRatio(latest.deviation),
                deviationZ: Number.isFinite(z)
                    ? `${z > 0 ? '+' : ''}${z.toFixed(2)}`
                    : 'N/A',
                sampleCount: deviationStats?.count || points.length,
                statusLabel,
                statusClass,
                basis: 'Flow-adjusted TWR index ÷ 12M time-weighted MA − 1'
            };
        });

'''
src = replace_once(src, summary_anchor, summary_code + summary_anchor, "detrend summary insertion")

hist_init_anchor = """            const histCtx = document.getElementById('historyChart'); if(histCtx && !chartHist) chartHist = new Chart(histCtx, { type: 'line', data: { labels: [], datasets: [{data:[]},{data:[]}] }, options: { responsive: true, maintainAspectRatio: false } });
"""
hist_init_code = hist_init_anchor + r'''            const detrendCtx = document.getElementById('twrDetrendChart');
            if (detrendCtx && !chartDetrend) {
                chartDetrend = new Chart(detrendCtx, {
                    type: 'line',
                    data: { labels: [], datasets: [] },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        plugins: {
                            legend: { labels: { color: '#cbd5e1' } },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => {
                                        const value = Number(ctx.raw);
                                        if (!Number.isFinite(value)) return `${ctx.dataset.label}: N/A`;
                                        return `${ctx.dataset.label}: ${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: { display: false },
                                ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 8 }
                            },
                            y: {
                                title: { display: true, text: 'TWR 偏離 12M 趨勢 (%)' },
                                ticks: { callback: (value) => `${Number(value).toFixed(0)}%` }
                            }
                        }
                    }
                });
            }
'''
src = replace_once(src, hist_init_anchor, hist_init_code, "detrend chart init")

update_anchor = """            chartHist.update();
        }

        if (chartFire) {
"""
update_code = r'''            chartHist.update();
        }

        if (chartDetrend) {
            const detrendPoints = navTrendDetrendPoints();
            const labels = detrendPoints.map((point) => new Date(point.ts).toISOString().slice(0, 10));
            const deviations = detrendPoints.map((point) => Number((point.deviation * 100).toFixed(4)));
            const zeroLine = detrendPoints.map(() => 0);

            chartDetrend.data.labels = labels;
            chartDetrend.data.datasets = [
                {
                    label: 'TWR 去趨勢偏離',
                    data: deviations,
                    borderColor: '#22d3ee',
                    backgroundColor: 'rgba(34,211,238,0.10)',
                    fill: true,
                    tension: 0.2,
                    pointRadius: 2,
                    pointHoverRadius: 4,
                    borderWidth: 2
                },
                {
                    label: '12M 趨勢基準',
                    data: zeroLine,
                    borderColor: '#64748b',
                    borderDash: [6, 6],
                    fill: false,
                    tension: 0,
                    pointRadius: 0,
                    borderWidth: 1.5
                }
            ];
            chartDetrend.update();
        }

        if (chartFire) {
'''
src = replace_once(src, update_anchor, update_code, "detrend chart update")

watch_anchor = """        watch([exchangeRate, sheetUrl, riskParams, quantStartDate, dataFrequency, fireTargets, correlationMatrix], () => updateCharts(), { deep: true });
"""
watch_code = watch_anchor + """        watch([displayHistory, transactions], () => updateCharts(), { deep: true });
"""
src = replace_once(src, watch_anchor, watch_code, "history watcher")

return_anchor = """expandedCardTicker, toggleCard, isHistoryExpanded, cloudRebalanceMeta, sysCorr, navOverlayMode, navOverlayOptions, setNavOverlayMode, navMaConfig, riskRegimeStrip, navTrendSummary,"""
return_new = """expandedCardTicker, toggleCard, isHistoryExpanded, cloudRebalanceMeta, sysCorr, navOverlayMode, navOverlayOptions, setNavOverlayMode, navMaConfig, riskRegimeStrip, navTrendSummary, twrDetrendSummary,"""
src = replace_once(src, return_anchor, return_new, "return exposure")

index_anchor = """                    </div>
                </div>
            </section>

            <!-- ===== Holdings Tab / 庫存 ===== -->
"""
detrend_card = r'''                    </div>

                    <div class="glass chart-card p-5 md:p-6">
                        <div class="flex flex-col gap-5">
                            <div class="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-4">
                                <div>
                                    <h4 class="panel-title">
                                        <i class="fas fa-wave-square text-cyan-400"></i>
                                        TWR 去趨勢診斷（12M）
                                    </h4>
                                    <p class="panel-subtitle">用 Flow-adjusted TWR index 相對 12M time-weighted MA 的偏離觀察績效是否暫時脫離長期軌道；0% 代表貼近長期趨勢。</p>
                                </div>
                                <span class="terminal-chip shrink-0" :class="twrDetrendSummary?.statusClass || 'border-slate-500/30 bg-slate-500/10 text-slate-300'">
                                    {{ twrDetrendSummary?.statusLabel || '等待資料' }}
                                </span>
                            </div>

                            <div class="grid grid-cols-2 lg:grid-cols-4 gap-2">
                                <div class="terminal-mini-stat soft">
                                    <div class="terminal-mini-label">目前 TWR Index</div>
                                    <div class="terminal-mini-value">{{ twrDetrendSummary?.twrIndex || 'N/A' }}</div>
                                </div>
                                <div class="terminal-mini-stat soft">
                                    <div class="terminal-mini-label">12M Trend</div>
                                    <div class="terminal-mini-value">{{ twrDetrendSummary?.trendIndex || 'N/A' }}</div>
                                </div>
                                <div class="terminal-mini-stat soft">
                                    <div class="terminal-mini-label">偏離長期趨勢</div>
                                    <div class="terminal-mini-value">{{ twrDetrendSummary?.deviation || 'N/A' }}</div>
                                </div>
                                <div class="terminal-mini-stat soft">
                                    <div class="terminal-mini-label">偏離 Z-score</div>
                                    <div class="terminal-mini-value">{{ twrDetrendSummary?.deviationZ || 'N/A' }}</div>
                                </div>
                            </div>

                            <div class="text-[11px] text-gray-500 leading-relaxed">
                                Z-score 以最近 12 個月可用的去趨勢偏離樣本估計；至少需要 8 個有效偏離樣本。這是診斷工具，不是買賣訊號。
                                <span v-if="twrDetrendSummary?.sampleCount">目前 Z 樣本：{{ twrDetrendSummary.sampleCount }}。</span>
                            </div>

                            <div class="relative min-h-[280px] md:min-h-[340px] rounded-2xl border border-white/5 bg-black/10 p-2 md:p-3">
                                <canvas id="twrDetrendChart"></canvas>
                                <div v-if="!twrDetrendSummary?.available" class="absolute inset-0 flex items-center justify-center text-gray-500 text-xs bg-gray-900/40 rounded-2xl">
                                    <p>需要約 12 個月以上的 Flow-adjusted TWR 歷史才能建立去趨勢序列</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ===== Holdings Tab / 庫存 ===== -->
'''
index = replace_once(index, index_anchor, detrend_card, "detrend card insertion")

index = index.replace(
    'assets/js/app.bundle.js?v=ai-signal-audit-v1',
    'assets/js/app.bundle.js?v=twr-detrend-v1'
)

SRC.write_text(src.rstrip() + "\n", encoding="utf-8")
INDEX.write_text(index.rstrip() + "\n", encoding="utf-8")
print("Applied TWR detrend diagnostic patch")
