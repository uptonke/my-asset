from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/js/src/app.bundle.source.js'
INDEX = ROOT / 'index.html'

src = SOURCE.read_text(encoding='utf-8')
html = INDEX.read_text(encoding='utf-8')

# 1) Make overlay labels explicit about raw NAV vs flow-adjusted TWR drawdown.
old_overlay = """        const navOverlayOptions = [
            { value: 'nav', label: 'NAV' },
            { value: 'drawdown', label: '回撤' },
            { value: 'both', label: 'NAV + 回撤' }
        ];"""
new_overlay = """        const navOverlayOptions = [
            { value: 'nav', label: 'Raw NAV' },
            { value: 'drawdown', label: 'TWR 回撤' },
            { value: 'both', label: 'NAV + TWR 回撤' }
        ];"""
if old_overlay not in src:
    raise SystemExit('navOverlayOptions block not found')
src = src.replace(old_overlay, new_overlay, 1)

old_ma = """        const navMaConfig = computed(() => ({
            monthLabel: '短期趨勢：3M MA',
            yearLabel: '長期趨勢：12M MA',
            frequencyNote: '以現有 NAV history 計算；資料不足時顯示為 N/A'
        }));"""
new_ma = """        const navMaConfig = computed(() => ({
            monthLabel: '績效短期：3M MA',
            yearLabel: '績效長期：12M MA',
            frequencyNote: '趨勢卡與回撤採 Flow-adjusted TWR；主圖 Raw NAV / Cost 保留資產規模變化'
        }));"""
if old_ma not in src:
    raise SystemExit('navMaConfig block not found')
src = src.replace(old_ma, new_ma, 1)

# 2) Replace raw-NAV trend helpers with a flow-adjusted TWR index.
nav_start = src.find('        function navTrendParseDate')
nav_end = src.find('        function getTypeColor', nav_start)
if nav_start < 0 or nav_end < 0:
    raise SystemExit('NAV trend helper block boundaries not found')

new_nav_block = r'''        function navTrendParseDate(value) {
            const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
            if (match) return Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
            const fallback = Date.parse(value);
            return Number.isFinite(fallback) ? fallback : NaN;
        }

        function navTrendExternalFlow(prevTs, currTs) {
            let flow = 0;
            (transactions.value || []).forEach((tx) => {
                if (tx?.type !== 'Deposit' && tx?.type !== 'Withdraw') return;
                const txTs = navTrendParseDate(tx?.date);
                const amount = Number(tx?.totalCashFlow || 0);
                if (!Number.isFinite(txTs) || !Number.isFinite(amount)) return;
                if (txTs > prevTs && txTs <= currTs) flow += amount;
            });
            return flow;
        }

        function navTrendTwrIndexPoints() {
            const byTimestamp = new Map();
            (displayHistory.value || []).forEach((row) => {
                const ts = navTrendParseDate(row?.date);
                const nav = Number(row?.assets);
                if (!Number.isFinite(ts) || !Number.isFinite(nav) || nav <= 0) return;
                byTimestamp.set(ts, { ts, nav });
            });
            const raw = [...byTimestamp.values()].sort((a, b) => a.ts - b.ts);
            if (!raw.length) return [];

            let twrIndex = 100;
            const out = [{ ts: raw[0].ts, value: twrIndex, rawNav: raw[0].nav, periodReturn: null }];
            for (let i = 1; i < raw.length; i += 1) {
                const prev = raw[i - 1];
                const curr = raw[i];
                const externalFlow = navTrendExternalFlow(prev.ts, curr.ts);
                const periodReturn = prev.nav > 0
                    ? ((curr.nav - externalFlow) / prev.nav) - 1
                    : NaN;

                // A <= -100% subperiod or invalid NAV/flow relation makes a chained TWR index unreliable.
                if (!Number.isFinite(periodReturn) || periodReturn <= -1) return [];
                twrIndex *= (1 + periodReturn);
                if (!Number.isFinite(twrIndex) || twrIndex <= 0) return [];
                out.push({
                    ts: curr.ts,
                    value: twrIndex,
                    rawNav: curr.nav,
                    periodReturn,
                    externalFlow,
                });
            }
            return out;
        }

        function navTrendShiftMonths(timestamp, monthDelta) {
            if (!Number.isFinite(timestamp)) return NaN;
            const d = new Date(timestamp);
            const originalDay = d.getUTCDate();
            d.setUTCDate(1);
            d.setUTCMonth(d.getUTCMonth() + monthDelta);
            const daysInTargetMonth = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0)).getUTCDate();
            d.setUTCDate(Math.min(originalDay, daysInTargetMonth));
            return d.getTime();
        }

        function navTrendMovingAverage(points, endTs, months) {
            if (!Array.isArray(points) || !points.length || !Number.isFinite(endTs) || months <= 0) return null;
            const startTs = navTrendShiftMonths(endTs, -months);
            if (!Number.isFinite(startTs) || endTs <= startTs) return null;

            let carriedPoint = null;
            for (const point of points) {
                if (point.ts <= startTs) carriedPoint = point;
                else break;
            }
            if (!carriedPoint || !Number.isFinite(carriedPoint.value)) return null;

            let cursor = startTs;
            let carriedValue = carriedPoint.value;
            let weightedValueMs = 0;
            let observationsInWindow = 0;

            for (const point of points) {
                if (point.ts <= startTs) continue;
                if (point.ts > endTs) break;
                if (!Number.isFinite(point.value)) return null;
                if (point.ts > cursor) {
                    weightedValueMs += carriedValue * (point.ts - cursor);
                    cursor = point.ts;
                }
                carriedValue = point.value;
                observationsInWindow += 1;
            }

            // Avoid presenting an MA from one stale observation only.
            if (observationsInWindow < 2) return null;
            if (cursor < endTs) weightedValueMs += carriedValue * (endTs - cursor);

            const durationMs = endTs - startTs;
            return durationMs > 0 ? weightedValueMs / durationMs : null;
        }

        function navTrendFormatRatio(ratio, suffix = '') {
            if (!Number.isFinite(ratio)) return 'N/A';
            const pct = ratio * 100;
            const sign = pct > 0 ? '+' : '';
            return `${sign}${pct.toFixed(1)}%${suffix}`;
        }

        const navTrendSummary = computed(() => {
            const modeMap = {
                nav: 'Raw NAV',
                drawdown: 'TWR Drawdown',
                both: 'Raw NAV + TWR Drawdown'
            };
            const points = navTrendTwrIndexPoints();
            const latest = points.length ? points[points.length - 1] : null;

            if (!latest) {
                return {
                    navVsMonth: 'N/A',
                    navVsYear: 'N/A',
                    monthSlope: 'N/A',
                    yearSlope: 'N/A',
                    currentDrawdown: 'N/A',
                    overlayModeLabel: modeMap[navOverlayMode.value] || 'Raw NAV',
                    basis: 'Flow-adjusted TWR index'
                };
            }

            const ma3m = navTrendMovingAverage(points, latest.ts, 3);
            const ma12m = navTrendMovingAverage(points, latest.ts, 12);
            const priorMonthEnd = navTrendShiftMonths(latest.ts, -1);
            const priorMa3m = navTrendMovingAverage(points, priorMonthEnd, 3);
            const priorMa12m = navTrendMovingAverage(points, priorMonthEnd, 12);
            const peakIndex = Math.max(...points.filter((point) => point.ts <= latest.ts).map((point) => point.value));

            return {
                navVsMonth: ma3m && ma3m > 0 ? navTrendFormatRatio(latest.value / ma3m - 1) : 'N/A',
                navVsYear: ma12m && ma12m > 0 ? navTrendFormatRatio(latest.value / ma12m - 1) : 'N/A',
                monthSlope: ma3m && priorMa3m && priorMa3m > 0
                    ? navTrendFormatRatio(ma3m / priorMa3m - 1, ' / 月')
                    : 'N/A',
                yearSlope: ma12m && priorMa12m && priorMa12m > 0
                    ? navTrendFormatRatio(ma12m / priorMa12m - 1, ' / 月')
                    : 'N/A',
                currentDrawdown: Number.isFinite(peakIndex) && peakIndex > 0
                    ? navTrendFormatRatio(latest.value / peakIndex - 1)
                    : 'N/A',
                overlayModeLabel: modeMap[navOverlayMode.value] || 'Raw NAV',
                basis: 'Flow-adjusted TWR index'
            };
        });

'''
src = src[:nav_start] + new_nav_block + src[nav_end:]

# 3) Make the chart modes real: raw NAV/Cost, TWR drawdown, or both.
hist_start = src.find('        if (chartHist) {')
hist_end = src.find('\n        if (chartFire) {', hist_start)
if hist_start < 0 or hist_end < 0:
    raise SystemExit('history chart update block not found')

new_hist_block = r'''        if (chartHist) {
            const history = displayHistory.value || [];
            const sorted = [...history]
                .filter((row) => Number.isFinite(navTrendParseDate(row?.date)) && Number.isFinite(Number(row?.assets)))
                .sort((a, b) => navTrendParseDate(a.date) - navTrendParseDate(b.date));
            chartHist.data.labels = sorted.map((h) => h.date);

            const navDataset = {
                label: 'Raw NAV',
                data: sorted.map((h) => Number(h.assets)),
                borderColor: '#3b82f6',
                fill: true,
                backgroundColor: 'rgba(59,130,246,0.1)',
                tension: 0.1,
                yAxisID: 'y'
            };
            const costDataset = {
                label: 'Cost',
                data: sorted.map((h) => Number(h.cost)),
                borderColor: '#10b981',
                borderDash: [5, 5],
                tension: 0.1,
                yAxisID: 'y'
            };

            const twrPoints = navTrendTwrIndexPoints();
            const drawdownByTs = new Map();
            let peakIndex = -Infinity;
            twrPoints.forEach((point) => {
                peakIndex = Math.max(peakIndex, point.value);
                const ddPct = Number.isFinite(peakIndex) && peakIndex > 0
                    ? (point.value / peakIndex - 1) * 100
                    : null;
                drawdownByTs.set(point.ts, ddPct);
            });
            const drawdownDataset = {
                label: 'TWR Drawdown',
                data: sorted.map((h) => drawdownByTs.get(navTrendParseDate(h.date)) ?? null),
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245,158,11,0.08)',
                borderDash: [4, 4],
                fill: false,
                tension: 0.1,
                yAxisID: 'y1',
                pointRadius: 2,
                pointHoverRadius: 4
            };

            if (navOverlayMode.value === 'drawdown') {
                chartHist.data.datasets = [drawdownDataset];
            } else if (navOverlayMode.value === 'both') {
                chartHist.data.datasets = [navDataset, costDataset, drawdownDataset];
            } else {
                chartHist.data.datasets = [navDataset, costDataset];
            }

            chartHist.options.scales = {
                y: {
                    type: 'linear',
                    display: navOverlayMode.value !== 'drawdown',
                    position: 'left',
                    beginAtZero: false,
                    ticks: { callback: (value) => Number(value).toLocaleString('zh-TW') }
                },
                y1: {
                    type: 'linear',
                    display: navOverlayMode.value !== 'nav',
                    position: 'right',
                    max: 0,
                    grid: { drawOnChartArea: false },
                    ticks: { callback: (value) => `${Number(value).toFixed(0)}%` },
                    title: { display: navOverlayMode.value !== 'nav', text: 'TWR Drawdown' }
                }
            };
            chartHist.update();
        }
'''
src = src[:hist_start] + new_hist_block + src[hist_end:]

# 4) Clarify the UI: chart = raw asset size; trend cards/drawdown = flow-adjusted TWR.
replacements = {
    '淨值成長趨勢 (NAV)': '資產規模 / 績效趨勢',
    '觀察資產淨值隨時間的變化，並加入短期 / 長期趨勢線與 Cost 對照。': '主圖用 Raw NAV / Cost 看資產規模；趨勢卡與回撤用 Flow-adjusted TWR index 看投資績效。',
    '回撤疊圖（Drawdown Overlay）＝把回撤曲線疊加到 NAV 圖上，拿來一起看最大跌幅、目前仍在水下多少，以及修復進度。': 'TWR 回撤＝Flow-adjusted TWR index 相對自身歷史高點的跌幅；Deposit / Withdraw 不會直接被誤判為投資虧損。',
    '<div class="terminal-mini-label">NAV vs 短期</div>': '<div class="terminal-mini-label">TWR vs 3M MA</div>',
    '<div class="terminal-mini-label">NAV vs 長期</div>': '<div class="terminal-mini-label">TWR vs 12M MA</div>',
    '<div class="terminal-mini-label">短期斜率</div>': '<div class="terminal-mini-label">3M MA 斜率</div>',
    '<div class="terminal-mini-label">長期斜率</div>': '<div class="terminal-mini-label">12M MA 斜率</div>',
    '<div class="terminal-mini-label">目前距前高跌幅</div>': '<div class="terminal-mini-label">TWR 目前回撤</div>',
    'assets/js/app.bundle.js?v=fractional-sell-v1': 'assets/js/app.bundle.js?v=twr-trend-v1',
}
for old, new in replacements.items():
    if old not in html:
        raise SystemExit(f'index.html target not found: {old}')
    html = html.replace(old, new, 1)

# Add an explicit basis chip next to the MA chips.
needle = """        <span class=\"terminal-chip\">{{ navMaConfig?.yearLabel || '長期趨勢：N/A' }}</span>"""
insert = needle + "\n        <span class=\"terminal-chip border-cyan-500/30 bg-cyan-500/10 text-cyan-200\">Flow-adjusted TWR</span>"
if needle not in html:
    raise SystemExit('yearLabel chip not found')
html = html.replace(needle, insert, 1)

SOURCE.write_text(src, encoding='utf-8')
INDEX.write_text(html, encoding='utf-8')
print('Patched NAV trend cards and overlay to use flow-adjusted TWR index.')
