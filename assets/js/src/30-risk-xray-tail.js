             // 【CRO 防禦機制：資料異常監控】
             nextTick(() => {
                 let warningMsgs = [];
             
                 // 2. 暴增/暴跌的報酬率檢測
                 if (h.length >= 2) {
                     const latestReturn = h[h.length - 1].dailyReturn;
                     if (latestReturn > 0.15) { 
                         warningMsgs.push(`🚨 偵測到單期異常暴漲 (+${(latestReturn*100).toFixed(1)}%)！請檢查快照是否遺漏了交易紀錄。`);
                     } else if (latestReturn < -0.15) { 
                         warningMsgs.push(`🚨 偵測到單期異常暴跌 (${(latestReturn*100).toFixed(1)}%)！請檢查快照是否遺漏了交易紀錄。`);
                     }
                 }
             
                 // 觸發警報
                 if (warningMsgs.length > 0) {
                     console.warn("CRO System Warning:", warningMsgs);
                     alert("🤖 CRO 風控系統警告：\n\n" + warningMsgs.join('\n\n')); 
                 }
             });

        }, { deep: true, immediate: true });

        // ==========================================
        // 📊 進階量化指標：X-Ray / Rebalance / Tail Risk (Deep Object Schema)
        // ==========================================
        const xrayStats = ref({
            mrcTable: [],
            pca: { pc1Explained: '0.0', pc3CumExplained: '0.0' },
            fx: { netFxExposurePct: '0.0', usdNavImpact1pct: '0.0' }
        });

       const rebalanceMonitor = ref({
    trimCount: 0,
    alertCount: 0,
    volDrag30d: '0.00',
    volDrag90d: '0.00',
    bufferFloorPct: '0.0',
    currentBufferPct: '0.0',
    bufferGapPct: '0.0',
    bufferBlockingRiskBuys: false,
    hardBufferTickers: ['SHY', 'BOXX'],
    alerts: []
});

       const tailStatsLite = ref({
    conditionalCorr: '-',
    crisisCorr: '-',
    downsideBeta: '-',
    stressedCvar: '-',
    jointDownsideHitRate: '-',
    coDrawdownFrequency: '-',
    tailDependenceLite: '-',
    rollingCvar26w: '-',
    rollingCvar52w: '-',
    crisisWindowLabel: '-',
    tailSampleCount: '-',
    crisisSampleCount: '-',
    coDrawdownThreshold: '-',
    tailThresholdQuantile: '-',

    // Jump-Diffusion
    jdVar95: '-',
    jdEs95: '-',
    jdCrashProb: '-',
    jdTailLoss: '-',
    jdHorizonWeeks: '-',
    jdEffectiveLambda: '-',
    jdEffectiveJumpMean: '-',
    jdEffectiveJumpStd: '-',

    // EVT
    evtVar95: '-',
    evtEs95: '-',
    evtShapeXi: '-',
    evtScaleBeta: '-',
    evtThreshold: '-',
    evtExceedanceCount: '-',
    evtAlphaConf: '-'
});
function fmtNum(val, digits = 2) {
    if (val === null || val === undefined || val === '') return '-';
    const n = Number(val);
    return Number.isFinite(n) ? n.toFixed(digits) : '-';
}

function fmtPctMaybe(val, digits = 2) {
    if (val === null || val === undefined || val === '') return '-';
    const n = Number(val);
    return Number.isFinite(n) ? n.toFixed(digits) : '-';
}

watch([groupedHoldings, portfolioStats, stats, sysCorr, chaosMeta, cloudRebalanceMeta, liquidityBufferRatio], () => {
    let trims = 0;
    let alertCount = 0;
    let fxExposure = 0;
    const mrcTemp = [];
    const alertList = [];

    const portVol = parseFloat(stats.value.annVol) / 100 || 0.15;
    const marketVol = parseFloat(riskParams.value.sm) / 100 || 0.15;
    const portBeta = parseFloat(portfolioStats.value.beta) || 1.0;

    for (const cat in groupedHoldings.value) {
        groupedHoldings.value[cat].items.forEach(item => {
            if (item.isUSD) fxExposure += item.totalWeight;

            const drift = Math.abs((item.totalWeight * 100) - item.blendedWeight);
            if (item.totalWeight > 0.20 || drift > 5) trims++;

            if (drift > 10 || item.totalWeight > 0.30) {
                alertCount++;
                alertList.push(
                    `[${item.ticker}] 權重 ${(item.totalWeight * 100).toFixed(1)}% 嚴重偏離綜合目標，或單一佔比過高 (>30%)。`
                );
            }

            const assetBeta = parseFloat(item.beta) || 1.0;
            const covProxy = assetBeta * portBeta * Math.pow(marketVol, 2);
            const mrc = portVol > 0 ? (item.totalWeight * covProxy) / portVol : 0;
            const rcPercent = portVol > 0 ? (mrc / portVol) * 100 : 0;

            mrcTemp.push({
                ticker: item.ticker,
                weightPct: (item.totalWeight * 100).toFixed(1),
                riskPct: rcPercent.toFixed(1),
                mrc: (mrc * 100).toFixed(2),
                rc: rcPercent.toFixed(1)
            });
        });
    }

    mrcTemp.sort((a, b) => parseFloat(b.riskPct) - parseFloat(a.riskPct));

    const backendXray = chaosMeta.value?.xray_meta || {};
    const backendTail = chaosMeta.value?.tail_meta || {};

    if (backendXray?.mrc_table?.length) {
        xrayStats.value = {
            mrcTable: backendXray.mrc_table.map(row => ({
                ticker: row.ticker,
                weightPct: fmtNum(row.weight_pct, 1),
                riskPct: fmtNum(row.risk_pct, 1),
                mrc: fmtNum(row.mrc, 2),
                rc: fmtNum(row.rc, 2)
            })),
            pca: {
                pc1Explained: fmtNum(backendXray?.pca?.pc1_explained, 1),
                pc3CumExplained: fmtNum(backendXray?.pca?.pc3_cum_explained, 1)
            },
            fx: {
                netFxExposurePct: fmtNum(backendXray?.fx?.net_fx_exposure_pct, 1),
                usdNavImpact1pct: fmtNum(backendXray?.fx?.usd_nav_impact_1pct_twd, 0)
            }
        };
    } else {
        const pc1Proxy = (sysCorr.value * 100) || 65.0;
        xrayStats.value = {
            mrcTable: mrcTemp,
            pca: {
                pc1Explained: pc1Proxy.toFixed(1),
                pc3CumExplained: Math.min((pc1Proxy + 15), 98).toFixed(1)
            },
            fx: {
                netFxExposurePct: (fxExposure * 100).toFixed(1),
                usdNavImpact1pct: (fxExposure * 1).toFixed(2)
            }
        };
    }

    const backendRebalance = cloudRebalanceMeta.value || {};

const fallbackBufferFloorPct = (parseFloat(liquidityBufferRatio.value) || 0).toFixed(1);

let fallbackCurrentBufferPct = '0.0';
if (typeof getSleeveStats === 'function') {
    fallbackCurrentBufferPct = ((getSleeveStats().hardBufferWeight || 0) * 100).toFixed(1);
}

const resolvedBufferFloorPct =
    backendRebalance.buffer_floor_pct !== undefined && backendRebalance.buffer_floor_pct !== null
        ? fmtNum(backendRebalance.buffer_floor_pct, 1)
        : fallbackBufferFloorPct;

const backendCurrent = Number(backendRebalance.current_buffer_pct);
const fallbackCurrent = Number(fallbackCurrentBufferPct);

const resolvedCurrentBufferPct =
    Number.isFinite(backendCurrent) && Math.abs(backendCurrent - fallbackCurrent) < 2
        ? backendCurrent.toFixed(1)
        : fallbackCurrent.toFixed(1);

const resolvedBufferGapPct =
    Math.max(0, parseFloat(resolvedBufferFloorPct) - parseFloat(resolvedCurrentBufferPct)).toFixed(1);

const resolvedBufferBlocking = parseFloat(resolvedBufferGapPct) > 0.05;

const resolvedHardBufferTickers =
    Array.isArray(backendRebalance.hard_buffer_tickers) && backendRebalance.hard_buffer_tickers.length
        ? backendRebalance.hard_buffer_tickers
        : ['SHY', 'BOXX'];

if (resolvedBufferBlocking) {
    alertList.unshift(
        `硬緩衝不足：目前 ${resolvedCurrentBufferPct}% / 目標 ${resolvedBufferFloorPct}% ，風險資產買入已暫停，請優先補足 ${resolvedHardBufferTickers.join(' + ')}。`
    );
}

rebalanceMonitor.value = {
    trimCount: trims,
    alertCount: alertCount,
    volDrag30d: ((0.5 * Math.pow(portVol, 2) * (30 / 365)) * 100).toFixed(2),
    volDrag90d: ((0.5 * Math.pow(portVol, 2) * (90 / 365)) * 100).toFixed(2),
    bufferFloorPct: resolvedBufferFloorPct,
    currentBufferPct: resolvedCurrentBufferPct,
    bufferGapPct: resolvedBufferGapPct,
    bufferBlockingRiskBuys: resolvedBufferBlocking,
    hardBufferTickers: resolvedHardBufferTickers,
    alerts: alertList
};

    const baseCvar = parseFloat(stats.value.cvar95) || 0;
const currentSysCorr = sysCorr.value || 0.6;

if (backendTail && (
    backendTail.conditional_correlation !== null ||
    backendTail.crisis_window_correlation !== null ||
    backendTail.downside_beta !== null ||
    backendTail.stressed_cvar !== null ||
    backendTail.jd_var95 !== null ||
    backendTail.evt_var95 !== null
)) {
    tailStatsLite.value = {
        conditionalCorr: fmtNum(backendTail.conditional_correlation, 2),
        crisisCorr: fmtNum(backendTail.crisis_window_correlation, 2),
        downsideBeta: fmtNum(backendTail.downside_beta, 2),
        stressedCvar: fmtPctMaybe(backendTail.stressed_cvar, 2),
        jointDownsideHitRate: fmtPctMaybe(backendTail.joint_downside_hit_rate, 2),
        coDrawdownFrequency: fmtPctMaybe(backendTail.co_drawdown_frequency, 2),
        tailDependenceLite: fmtPctMaybe(backendTail.tail_dependence_lite, 2),
        rollingCvar26w: fmtPctMaybe(backendTail.rolling_cvar_26w, 2),
        rollingCvar52w: fmtPctMaybe(backendTail.rolling_cvar_52w, 2),
        crisisWindowLabel: backendTail.crisis_window_label || '-',
        tailSampleCount: backendTail.tail_sample_count ?? '-',
        crisisSampleCount: backendTail.crisis_sample_count ?? '-',
        coDrawdownThreshold: fmtNum(backendTail.co_drawdown_threshold, 1),
        tailThresholdQuantile: fmtNum((backendTail.tail_threshold_quantile ?? 0) * 100, 0),

        // Jump-Diffusion
        jdVar95: fmtPctMaybe(backendTail.jd_var95, 2),
        jdEs95: fmtPctMaybe(backendTail.jd_es95, 2),
        jdCrashProb: fmtPctMaybe(backendTail.jd_crash_prob, 2),
        jdTailLoss: fmtPctMaybe(backendTail.jd_tail_loss, 2),
        jdHorizonWeeks: backendTail.jd_horizon_weeks ?? '-',
        jdEffectiveLambda: fmtNum(backendTail.jd_effective_lambda, 2),
        jdEffectiveJumpMean: fmtNum(backendTail.jd_effective_jump_mean, 4),
        jdEffectiveJumpStd: fmtNum(backendTail.jd_effective_jump_std, 4),

        // EVT
        evtVar95: fmtPctMaybe(backendTail.evt_var95, 2),
        evtEs95: fmtPctMaybe(backendTail.evt_es95, 2),
        evtShapeXi: fmtNum(backendTail.evt_shape_xi, 4),
        evtScaleBeta: fmtNum(backendTail.evt_scale_beta, 6),
        evtThreshold: fmtPctMaybe(backendTail.evt_threshold, 2),
        evtExceedanceCount: backendTail.evt_exceedance_count ?? '-',
        evtAlphaConf: fmtNum((backendTail.evt_alpha_conf ?? 0) * 100, 0)
    };
} else {
    tailStatsLite.value = {
        conditionalCorr: Math.min((currentSysCorr * 1.15), 0.99).toFixed(2),
        crisisCorr: Math.min((currentSysCorr * 1.30), 0.99).toFixed(2),
        downsideBeta: (portBeta * 1.2).toFixed(2),
        stressedCvar: (baseCvar * 1.5).toFixed(2),
        jointDownsideHitRate: '-',
        coDrawdownFrequency: '-',
        tailDependenceLite: '-',
        rollingCvar26w: (baseCvar * 0.9).toFixed(2),
        rollingCvar52w: (baseCvar * 1.05).toFixed(2),
        crisisWindowLabel: 'Benchmark < q20 或 VIX 飆升',
        tailSampleCount: '-',
        crisisSampleCount: '-',
        coDrawdownThreshold: '-10.0',
        tailThresholdQuantile: '5',

        // Jump-Diffusion fallback
        jdVar95: '-',
        jdEs95: '-',
        jdCrashProb: '-',
        jdTailLoss: '-',
        jdHorizonWeeks: '-',
        jdEffectiveLambda: '-',
        jdEffectiveJumpMean: '-',
        jdEffectiveJumpStd: '-',

        // EVT fallback
        evtVar95: '-',
        evtEs95: '-',
        evtShapeXi: '-',
        evtScaleBeta: '-',
        evtThreshold: '-',
        evtExceedanceCount: '-',
        evtAlphaConf: '-'
    };
}
}, { deep: true, immediate: true });

        const aiInsights = computed(() => {
            const val = totalStockValueTwd.value;
            if (val === 0) return { summary: '尚無庫存資料，請先新增交易紀錄。', details: [] };

            let finalSummary = ""; const finalDetails = [];
            if (cloudAiAnalysis.value && cloudAiAnalysis.value.summary) {
                finalSummary = `🤖 【宏觀診斷】` + cloudAiAnalysis.value.summary;
                cloudAiAnalysis.value.details.forEach(d => finalDetails.push(d));
            }

            if (cloudRebalanceMeta.value && cloudRebalanceMeta.value.ai_execution_plan) {
                const plan = cloudRebalanceMeta.value.ai_execution_plan;
                finalSummary += `\n⚖️ 【交易策略】` + plan.execution_summary;
                plan.priority_trades.forEach(trade => {
                    const meta = stockMeta.value[trade.ticker] || {};
                    const targetW = meta.target_weight ? (meta.target_weight * 100).toFixed(1) + '%' : 'N/A';
                    finalDetails.push({ icon: '⚡', color: 'text-purple-400', title: `建議交易: ${trade.ticker} (目標權重: ${targetW})`, desc: trade.reason });
                });
            }

            let overweights = [];
            for (const cat in groupedHoldings.value) {
                groupedHoldings.value[cat].items.forEach(item => { if (item.totalWeight > 0.20) overweights.push(item.ticker); });
            }
            if (overweights.length > 0) {
                finalDetails.push({ icon: '🎯', color: 'text-orange-400', title: '集中度警報', desc: `[ ${overweights.join(', ')} ] 佔總資產權重過高 (>20%)。請盡速執行 Rebalance。` });
            }

            if (!cloudAiAnalysis.value) {
                 finalSummary = "等待雲端排程生成 AI 報告中...";
                 finalDetails.push({ icon: '📊', color: 'text-gray-400', title: '系統提示', desc: '目前的 AI 診斷與最佳權重正在背景運算中，請稍候。' });
            }

            return { summary: finalSummary, details: finalDetails };
        });

        function addFireTarget() {
            const last = fireTargets.value[fireTargets.value.length - 1];
            fireTargets.value.push({ age: last ? last.age + 5 : 30, year: last ? last.year + 5 : new Date().getFullYear() + 5, amount: last ? last.amount * 1.5 : 5000000 });
            saveData();
        }

        const activeFireStageIndex = computed(() => {
            if (fireTargets.value.length === 0) return -1;
            const val = totalStockValueTwd.value;
            const index = fireTargets.value.findIndex(t => val < t.amount);
            return index === -1 ? fireTargets.value.length - 1 : index;
        });

        const activeFireTarget = computed(() => {
            if (fireTargets.value.length === 0) return { age: '?', year: '?', amount: 0 };
            return fireTargets.value[activeFireStageIndex.value] || { age: '?', year: '?', amount: 0 };
        });

        const fireProgress = computed(() => {
            if (!activeFireTarget.value || activeFireTarget.value.amount <= 0) return 0;
            return (totalStockValueTwd.value / activeFireTarget.value.amount) * 100;
        });

        async function manualUpdate(stock) { if(stock.manualPrice) { priceMap.value[stock.ticker] = stock.manualPrice; saveData(); } }
        
