from pathlib import Path

SOURCE = Path('assets/js/src/app.bundle.source.js')
text = SOURCE.read_text(encoding='utf-8')

old = """        const navTrendSummary = computed(() => {
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
"""

new = """        function navTrendParseDate(value) {
            const match = String(value || '').match(/^(\\d{4})-(\\d{2})-(\\d{2})/);
            if (!match) return NaN;
            return Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
        }

        function navTrendHistoryPoints() {
            const byTimestamp = new Map();
            (displayHistory.value || []).forEach((row) => {
                const ts = navTrendParseDate(row?.date);
                const nav = Number(row?.assets);
                if (!Number.isFinite(ts) || !Number.isFinite(nav) || nav <= 0) return;
                byTimestamp.set(ts, { ts, nav });
            });
            return [...byTimestamp.values()].sort((a, b) => a.ts - b.ts);
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
            if (!carriedPoint) return null;

            let cursor = startTs;
            let carriedNav = carriedPoint.nav;
            let weightedNavMs = 0;
            let observationsInWindow = 0;

            for (const point of points) {
                if (point.ts <= startTs) continue;
                if (point.ts > endTs) break;
                if (point.ts > cursor) {
                    weightedNavMs += carriedNav * (point.ts - cursor);
                    cursor = point.ts;
                }
                carriedNav = point.nav;
                observationsInWindow += 1;
            }

            // Avoid presenting a moving average from one stale observation only.
            if (observationsInWindow < 2) return null;
            if (cursor < endTs) weightedNavMs += carriedNav * (endTs - cursor);

            const durationMs = endTs - startTs;
            return durationMs > 0 ? weightedNavMs / durationMs : null;
        }

        function navTrendFormatRatio(ratio, suffix = '') {
            if (!Number.isFinite(ratio)) return 'N/A';
            const pct = ratio * 100;
            const sign = pct > 0 ? '+' : '';
            return `${sign}${pct.toFixed(1)}%${suffix}`;
        }

        const navTrendSummary = computed(() => {
            const modeMap = {
                nav: 'NAV',
                drawdown: 'Drawdown',
                both: 'NAV + Drawdown'
            };
            const points = navTrendHistoryPoints();
            const latest = points.length ? points[points.length - 1] : null;

            if (!latest) {
                return {
                    navVsMonth: 'N/A',
                    navVsYear: 'N/A',
                    monthSlope: 'N/A',
                    yearSlope: 'N/A',
                    currentDrawdown: 'N/A',
                    overlayModeLabel: modeMap[navOverlayMode.value] || 'NAV'
                };
            }

            const ma3m = navTrendMovingAverage(points, latest.ts, 3);
            const ma12m = navTrendMovingAverage(points, latest.ts, 12);
            const priorMonthEnd = navTrendShiftMonths(latest.ts, -1);
            const priorMa3m = navTrendMovingAverage(points, priorMonthEnd, 3);
            const priorMa12m = navTrendMovingAverage(points, priorMonthEnd, 12);
            const peakNav = Math.max(...points.filter((point) => point.ts <= latest.ts).map((point) => point.nav));

            return {
                navVsMonth: ma3m && ma3m > 0 ? navTrendFormatRatio(latest.nav / ma3m - 1) : 'N/A',
                navVsYear: ma12m && ma12m > 0 ? navTrendFormatRatio(latest.nav / ma12m - 1) : 'N/A',
                monthSlope: ma3m && priorMa3m && priorMa3m > 0
                    ? navTrendFormatRatio(ma3m / priorMa3m - 1, ' / 月')
                    : 'N/A',
                yearSlope: ma12m && priorMa12m && priorMa12m > 0
                    ? navTrendFormatRatio(ma12m / priorMa12m - 1, ' / 月')
                    : 'N/A',
                currentDrawdown: Number.isFinite(peakNav) && peakNav > 0
                    ? navTrendFormatRatio(latest.nav / peakNav - 1)
                    : 'N/A',
                overlayModeLabel: modeMap[navOverlayMode.value] || 'NAV'
            };
        });
"""

count = text.count(old)
if count != 1:
    raise SystemExit(f'Expected exactly one navTrendSummary placeholder block, found {count}')

text = text.replace(old, new, 1)
SOURCE.write_text(text, encoding='utf-8')
print('Patched NAV trend summary calculations')
