from pathlib import Path

REBALANCE_BLOCK = r'''        function buildSelfFinancingRebalancePlan(inputRows, basePct, addDisabled, desiredAssetSumPct) {
            const eps = 1e-7;
            const base = Math.max(0, Number(basePct || 0));
            const rows = (inputRows || []).map(row => {
                const currentWeightPct = Number(row.currentWeightPct || 0);
                const targetWeightPct = Math.max(0, Number(row.targetWeightPct || 0));
                const lowerBoundPct = Math.max(0, targetWeightPct - base);
                const upperBoundPct = targetWeightPct + base;
                const boundaryBreachHigh = currentWeightPct > upperBoundPct + eps;
                const boundaryBreachLow = currentWeightPct < lowerBoundPct - eps;
                return {
                    ...row,
                    currentWeightPct,
                    targetWeightPct,
                    lowerBoundPct,
                    upperBoundPct,
                    boundaryBreachHigh,
                    boundaryBreachLow,
                    boundaryBreach: boundaryBreachHigh || boundaryBreachLow,
                    postTradeWeightPct: currentWeightPct,
                    plannedTradeReason: 'NO_TRADE_ZONE'
                };
            });

            const targetSum = rows.reduce((sum, row) => sum + Number(row.targetWeightPct || 0), 0);
            const desiredAssetSum = Number.isFinite(Number(desiredAssetSumPct))
                ? Number(desiredAssetSumPct)
                : targetSum;
            const triggered = rows.some(row => row.boundaryBreach);

            if (!triggered) {
                return {
                    rows,
                    triggered: false,
                    desiredAssetSumPct: desiredAssetSum,
                    unresolvedAssetSumGapPct: desiredAssetSum - rows.reduce((sum, row) => sum + row.currentWeightPct, 0)
                };
            }

            // 1) Minimal trades: project breached holdings back to the no-trade band.
            rows.forEach(row => {
                if (row.boundaryBreachHigh) {
                    row.postTradeWeightPct = row.upperBoundPct;
                    row.plannedTradeReason = 'BAND_TRIM';
                } else if (row.boundaryBreachLow && !addDisabled) {
                    row.postTradeWeightPct = row.lowerBoundPct;
                    row.plannedTradeReason = 'BAND_ADD';
                } else if (row.boundaryBreachLow && addDisabled) {
                    row.plannedTradeReason = 'BLOCKED_ADD';
                }
            });

            // 2) Capital conservation: use released cash on the largest remaining target gaps first.
            // This minimizes extra ticket count and never crosses the model target.
            let balance = desiredAssetSum - rows.reduce((sum, row) => sum + row.postTradeWeightPct, 0);
            if (balance > eps && !addDisabled) {
                const receivers = rows
                    .filter(row => row.postTradeWeightPct < row.targetWeightPct - eps)
                    .sort((a, b) => (b.targetWeightPct - b.postTradeWeightPct) - (a.targetWeightPct - a.postTradeWeightPct));
                for (const row of receivers) {
                    if (balance <= eps) break;
                    const room = Math.max(0, row.targetWeightPct - row.postTradeWeightPct);
                    const add = Math.min(room, balance);
                    if (add <= eps) continue;
                    row.postTradeWeightPct += add;
                    balance -= add;
                    row.plannedTradeReason = row.plannedTradeReason === 'BAND_ADD'
                        ? 'BAND_ADD_PLUS_REALLOCATION'
                        : 'REALLOCATION_ADD';
                }
            }

            if (balance < -eps) {
                const funders = rows
                    .filter(row => row.postTradeWeightPct > row.targetWeightPct + eps)
                    .sort((a, b) => (b.postTradeWeightPct - b.targetWeightPct) - (a.postTradeWeightPct - a.targetWeightPct));
                for (const row of funders) {
                    if (balance >= -eps) break;
                    const room = Math.max(0, row.postTradeWeightPct - row.targetWeightPct);
                    const trim = Math.min(room, -balance);
                    if (trim <= eps) continue;
                    row.postTradeWeightPct -= trim;
                    balance += trim;
                    row.plannedTradeReason = row.plannedTradeReason === 'BAND_TRIM'
                        ? 'BAND_TRIM_PLUS_REALLOCATION'
                        : 'REALLOCATION_TRIM';
                }
            }

            return {
                rows,
                triggered: true,
                desiredAssetSumPct: desiredAssetSum,
                unresolvedAssetSumGapPct: balance
            };
        }

        const rebalanceCockpitRows = computed(() => {
            const base = Math.max(0, Number(tradeBufferBasePct.value || 3));
            const addDisabled = !!tradeBufferProfile.value.addDisabled;
            const nav = Number(totalPortfolioNav?.value || totalStockValueTwd?.value || 0);
            const rawRows = flattenHoldingRows(false).map(stock => {
                const currentWeightPct = Number(stock.totalWeight || 0) * 100;
                const targetWeightPct = Number(stock.blendedWeight ?? stock.targetWeight ?? 0);
                return {
                    ticker: stock.ticker || '-',
                    categoryName: stock.categoryName || stock.category || '-',
                    currentWeightPct,
                    targetWeightPct,
                    driftPct: targetWeightPct - currentWeightPct
                };
            });

            const metaAssetSum = Number(cloudRebalanceMeta.value?.target_asset_weight_sum_pct);
            const fallbackTargetSum = rawRows.reduce((sum, row) => sum + Number(row.targetWeightPct || 0), 0);
            const desiredAssetSum = Number.isFinite(metaAssetSum) ? metaAssetSum : fallbackTargetSum;
            const plan = buildSelfFinancingRebalancePlan(rawRows, base, addDisabled, desiredAssetSum);
            const actionEps = 0.0005;

            const rows = plan.rows.map(row => {
                const plannedTradePct = Number(row.postTradeWeightPct || 0) - Number(row.currentWeightPct || 0);
                const pendingRequiredPct = row.boundaryBreachLow && addDisabled
                    ? Math.max(0, Number(row.lowerBoundPct || 0) - Number(row.currentWeightPct || 0))
                    : 0;
                let bucket = 'hold';
                let action = '暫不動';
                let actionClass = 'text-slate-300 bg-slate-500/10 border-slate-500/20';

                if (plannedTradePct < -actionEps) {
                    bucket = 'trim';
                    action = row.plannedTradeReason === 'REALLOCATION_TRIM' ? '再分配減碼' : '減碼';
                    actionClass = 'text-red-300 bg-red-500/10 border-red-500/20';
                } else if (plannedTradePct > actionEps) {
                    bucket = 'add';
                    action = row.plannedTradeReason === 'REALLOCATION_ADD' ? '再分配加碼' : '加碼';
                    actionClass = 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20';
                } else if (pendingRequiredPct > actionEps) {
                    bucket = 'pending';
                    action = '候補加碼';
                    actionClass = 'text-amber-300 bg-amber-500/10 border-amber-500/20';
                }

                const actionPct = bucket === 'pending' ? pendingRequiredPct : Math.abs(plannedTradePct);
                const actionValue = nav * actionPct / 100;
                let governanceNote = '在 no-trade zone 內';
                if (bucket === 'pending') governanceNote = '低於緩衝下界，但目前 governance / buffer policy 暫停加碼';
                else if (row.plannedTradeReason === 'REALLOCATION_ADD') governanceNote = '接收減碼資金；仍不超過完整目標';
                else if (row.plannedTradeReason === 'REALLOCATION_TRIM') governanceNote = '提供加碼資金；仍不低於完整目標';
                else if (bucket !== 'hold') governanceNote = '先回到緩衝區，再以完整目標做資金守恆分配';

                return {
                    ...row,
                    driftText: `${row.driftPct >= 0 ? '+' : ''}${row.driftPct.toFixed(1)}%`,
                    plannedTradePct,
                    plannedTradeTwd: nav * plannedTradePct / 100,
                    actionValueText: bucket === 'hold' ? '—' : `NT$ ${formatNumber(actionValue)}`,
                    action,
                    actionClass,
                    decisionOwner: bucket === 'pending' ? 'CRO' : 'MC',
                    governanceNote,
                    bucket,
                    trimThresholdPct: base,
                    addThresholdPct: addDisabled ? Infinity : base,
                    tradePlanTriggered: plan.triggered,
                    unresolvedAssetSumGapPct: plan.unresolvedAssetSumGapPct
                };
            });

            const rank = { trim: 0, add: 1, pending: 2, hold: 3 };
            return rows.sort((a, b) =>
                (rank[a.bucket] ?? 9) - (rank[b.bucket] ?? 9)
                || Math.abs(Number(b.plannedTradePct || 0)) - Math.abs(Number(a.plannedTradePct || 0))
                || Math.abs(b.driftPct) - Math.abs(a.driftPct)
            );
        });

        const rebalanceTradePlanSummary = computed(() => {
            const rows = rebalanceCockpitRows.value || [];
            const nav = Number(totalPortfolioNav?.value || totalStockValueTwd?.value || 0);
            const trimPct = rows.reduce((sum, row) => sum + Math.max(0, -Number(row.plannedTradePct || 0)), 0);
            const addPct = rows.reduce((sum, row) => sum + Math.max(0, Number(row.plannedTradePct || 0)), 0);
            const currentAssetSumPct = rows.reduce((sum, row) => sum + Number(row.currentWeightPct || 0), 0);
            const postTradeAssetSumPct = rows.reduce((sum, row) => sum + Number(row.postTradeWeightPct || row.currentWeightPct || 0), 0);
            const inferredCurrentCashPct = 100 - currentAssetSumPct;
            const plannedCashAfterPct = 100 - postTradeAssetSumPct;
            const targetCashRaw = Number(cloudRebalanceMeta.value?.cash_target_weight_pct);
            const targetCashPct = Number.isFinite(targetCashRaw) ? targetCashRaw : Math.max(0, 100 - postTradeAssetSumPct);
            const residualCashVsTargetPct = plannedCashAfterPct - targetCashPct;
            return {
                triggered: rows.some(row => row.tradePlanTriggered),
                method: 'buffer_boundary_projection_then_largest_gap_self_financing',
                trimPct,
                addPct,
                trimTwd: nav * trimPct / 100,
                addTwd: nav * addPct / 100,
                inferredCurrentCashPct,
                plannedCashAfterPct,
                targetCashPct,
                residualCashVsTargetPct,
                selfFinancingWithinTolerance: Math.abs(residualCashVsTargetPct) <= 0.05,
                addDisabled: !!tradeBufferProfile.value.addDisabled
            };
        });

'''

POST_TRADE_BLOCK = r'''        const rebalancePostTradeEstimate = computed(() => {
            const rows = rebalanceCockpitRows.value || [];
            const weights = rows.map(row => Number(row.currentWeightPct || 0)).filter(Number.isFinite);
            const concentrationBefore = weights.length ? Math.max(...weights) : null;
            const afterWeights = rows
                .map(row => Number(row.postTradeWeightPct ?? row.currentWeightPct ?? 0))
                .filter(Number.isFinite);
            const concentrationAfter = afterWeights.length ? Math.max(...afterWeights) : null;
            const base = Math.max(0, Number(tradeBufferBasePct.value || 3));
            const breached = rows.filter(row => Math.max(0, Math.abs(Number(row.driftPct || 0)) - base) > 1e-7);
            const gapBefore = row => Math.max(0, Math.abs(Number(row.targetWeightPct || 0) - Number(row.currentWeightPct || 0)) - base);
            const gapAfter = row => Math.max(0, Math.abs(Number(row.targetWeightPct || 0) - Number(row.postTradeWeightPct ?? row.currentWeightPct ?? 0)) - base);
            const avgGapBefore = breached.length
                ? breached.reduce((sum, row) => sum + gapBefore(row), 0) / breached.length
                : 0;
            const avgGapAfter = breached.length
                ? breached.reduce((sum, row) => sum + gapAfter(row), 0) / breached.length
                : 0;

            return {
                concentrationBefore,
                concentrationAfter,
                bufferGapBefore: avgGapBefore,
                bufferGapAfter: avgGapAfter
            };
        });

'''


def patch_rows(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    if 'function buildSelfFinancingRebalancePlan(' not in text:
        start = text.index('        const rebalanceCockpitRows = computed(() => {')
        end = text.index('        const rebalanceCockpitBuckets = computed(() => {', start)
        text = text[:start] + REBALANCE_BLOCK + text[end:]
    start = text.index('        const rebalancePostTradeEstimate = computed(() => {')
    end = text.index('        const alertCenterItems = computed(() => {', start)
    text = text[:start] + POST_TRADE_BLOCK + text[end:]
    path.write_text(text, encoding='utf-8')


def patch_cro(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    if 'trade_plan_method: rebalanceTradePlanSummary.value.method' not in text:
        needle = '        backend_actionable_signal_count: rebalanceMonitor.value.backendSignalCount || 0,\n'
        insert = needle + (
            '        trade_plan_method: rebalanceTradePlanSummary.value.method,\n'
            '        trade_plan_triggered: rebalanceTradePlanSummary.value.triggered,\n'
            '        planned_trim_total_pp: rebalanceTradePlanSummary.value.trimPct,\n'
            '        planned_add_total_pp: rebalanceTradePlanSummary.value.addPct,\n'
            '        planned_trim_total_twd: rebalanceTradePlanSummary.value.trimTwd,\n'
            '        planned_add_total_twd: rebalanceTradePlanSummary.value.addTwd,\n'
            '        inferred_current_cash_pct: rebalanceTradePlanSummary.value.inferredCurrentCashPct,\n'
            '        planned_cash_after_pct: rebalanceTradePlanSummary.value.plannedCashAfterPct,\n'
            '        target_cash_pct: rebalanceTradePlanSummary.value.targetCashPct,\n'
            '        planned_cash_residual_vs_target_pct: rebalanceTradePlanSummary.value.residualCashVsTargetPct,\n'
            '        self_financing_within_005pp: rebalanceTradePlanSummary.value.selfFinancingWithinTolerance,\n'
        )
        if needle not in text:
            raise RuntimeError(f'missing CRO payload insertion point in {path}')
        text = text.replace(needle, insert, 1)

    if 'planned_trade_pct: Number(row.plannedTradePct || 0)' not in text:
        needle = '                visible_buffer_pp: Number(tradeBufferBasePct.value || 3)\n'
        replacement = (
            '                visible_buffer_pp: Number(tradeBufferBasePct.value || 3),\n'
            '                post_trade_weight_pct: Number(row.postTradeWeightPct ?? row.currentWeightPct ?? 0),\n'
            '                planned_trade_pct: Number(row.plannedTradePct || 0),\n'
            '                planned_trade_twd: Number(row.plannedTradeTwd || 0),\n'
            "                trade_reason: row.plannedTradeReason || 'N/A',\n"
            '                boundary_breach: Boolean(row.boundaryBreach)\n'
        )
        if needle not in text:
            raise RuntimeError(f'missing CRO row insertion point in {path}')
        text = text.replace(needle, replacement, 1)

    prompt = '4. 【再平衡監控】Distinguish Trim, Add, general drift and concentration candidates. State the exact direction of major alerts.'
    extra = prompt + ' When trade_plan_method is available, treat planned_trade_pct / planned_trade_twd and post_trade_weight_pct as the executable buffer-aware plan; do not report the full target drift as the trade size. If self_financing_within_005pp is true and target_cash_pct is near zero, explain that trim proceeds are reallocated to ADD legs rather than intentionally retained as cash.'
    if extra not in text:
        if prompt not in text:
            raise RuntimeError(f'missing CRO prompt insertion point in {path}')
        text = text.replace(prompt, extra, 1)

    path.write_text(text, encoding='utf-8')


for p in [Path('assets/js/src/60-ui-and-charts.js'), Path('assets/js/src/app.bundle.source.js')]:
    patch_rows(p)
for p in [Path('assets/js/src/00-bootstrap-and-cro.js'), Path('assets/js/src/app.bundle.source.js')]:
    patch_cro(p)

print('patched rebalance self-financing plan')
