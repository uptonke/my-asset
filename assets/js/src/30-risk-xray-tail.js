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
            pca: { pc1Explained: '-', pc3CumExplained: '-' },
            fx: { netFxExposurePct: '-', usdNavImpact1pct: '-' },
            lookthrough: normalizeLookthrough(null)
        });

       const rebalanceMonitor = ref({
    trimCount: 0,
    addCount: 0,
    blockedAddCount: 0,
    driftCount: 0,
    concentrationCount: 0,
    alertCount: 0,
    volDrag30d: '0.00',
    volDrag90d: '0.00',
    bufferFloorPct: '0.0',
    currentBufferPct: '0.0',
    bufferGapPct: '0.0',
    bufferBlockingRiskBuys: false,
    hardBufferTickers: ['SHY', 'BOXX'],
    universePolicy: '',
    ruleThresholdPp: 1,
    economicDustTickers: [],
    sheetOnlyTickersExcluded: [],
    backendSignalCount: 0,
    alerts: []
});

       const syntheticRiskMeta = computed(() => {
    const meta = stockMeta.value?.__synthetic_portfolio_risk__;
    return meta && typeof meta === 'object' ? meta : null;
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
    downsideSampleCount: '-',
    coDrawdownThreshold: '-',
    tailThresholdQuantile: '-',

    // Block-bootstrap inference for conditional tail statistics
    tailInferenceStatus: 'not_computed',
    tailInferenceMethod: '-',
    tailBootstrapReplicates: '-',
    tailBootstrapBlockWeeks: '-',
    tailCiLevel: '-',
    conditionalCorrCiLow: '-',
    conditionalCorrCiHigh: '-',
    crisisCorrCiLow: '-',
    crisisCorrCiHigh: '-',
    downsideBetaCiLow: '-',
    downsideBetaCiHigh: '-',

    // Horizon-aligned empirical comparison
    historicalVar95_1w: '-',
    historicalEs95_1w: '-',
    historicalSampleCount1w: '-',
    historicalHorizonVar95: '-',
    historicalHorizonEs95: '-',
    historicalHorizonWeeks: '-',
    historicalHorizonSampleCount: '-',
    historicalHorizonMethod: '-',

    // Jump stress scenario
    jdVar95: '-',
    jdEs95: '-',
    jdCrashProb: '-',
    jdTailLoss: '-',
    jdHorizonWeeks: '-',
    jdEffectiveLambda: '-',
    jdEffectiveJumpMean: '-',
    jdEffectiveJumpStd: '-',
    jdCrashThresholdPct: '-',
    jdModelType: '-',
    jdParameterSource: '-',
    jdJumpAggregation: '-',
    jdDriftCompensated: '-',
    jdExpectedJumpDragWeeklyPct: '-',
    jdSimulationCount: '-',

    // EVT robustness (one-day current-weight diagnostic)
    evtVar95: '-',
    evtEs95: '-',
    evtShapeXi: '-',
    evtScaleBeta: '-',
    evtThreshold: '-',
    evtExceedanceCount: '-',
    evtAlphaConf: '-',
    evtReturnFrequency: '-',
    evtHorizonDays: '-',
    evtComparableToJd: '-',
    evtComparisonNote: '-',
    evtRobustStatus: 'not_computed',
    evtDailySampleCount: '-',
    evtXiCiLow: '-',
    evtXiCiHigh: '-',
    evtVarCiLow: '-',
    evtVarCiHigh: '-',
    evtEsCiLow: '-',
    evtEsCiHigh: '-',
    evtBootstrapReplicates: '-',
    evtBootstrapValidReps: '-',
    evtBootstrapBlockDays: '-',
    evtThresholdValidCount: '-',
    evtXiMin: '-',
    evtXiMax: '-',
    evtXiSignStability: 'insufficient',
    evtEvidenceFlag: 'insufficient_sample',
    evtFiniteEndpointLossPct: '-'
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

function normalizeAlphaRegressionResult(row) {
    const raw = row && typeof row === 'object' ? row : {};
    const finite = (value) => {
        if (value === null || value === undefined || value === '') return null;
        const n = Number(value);
        return Number.isFinite(n) ? n : null;
    };
    return {
        status: raw.status || 'unavailable',
        available: raw.status === 'available',
        benchmark: raw.benchmark || '',
        alphaAnnualPct: finite(raw.alpha_annualized_pct),
        alphaPeriodPct: finite(raw.alpha_period_pct),
        alphaSeAnnualPct: finite(raw.alpha_hac_se_annualized_pct),
        tStat: finite(raw.alpha_t_stat_hac),
        pValue: finite(raw.alpha_p_value_hac),
        ciLow: finite(raw.alpha_ci95_low_annualized_pct),
        ciHigh: finite(raw.alpha_ci95_high_annualized_pct),
        beta: finite(raw.beta),
        betaSe: finite(raw.beta_hac_se),
        rSquared: finite(raw.r_squared),
        n: finite(raw.n),
        sampleStart: raw.sample_start || '',
        sampleEnd: raw.sample_end || '',
        medianPeriodDays: finite(raw.median_period_days),
        hacLags: finite(raw.hac_lags),
        evidence: raw.evidence_5pct || ''
    };
}

const alphaRegressionStats = computed(() => {
    const raw = chaosMeta.value?.alpha_regression || {};
    const benchmarks = raw.benchmarks && typeof raw.benchmarks === 'object' ? raw.benchmarks : {};
    return {
        status: raw.status || 'unavailable',
        method: raw.method || '',
        portfolioReturnSource: raw.portfolio_return_source || '',
        benchmarkPolicy: raw.benchmark_policy || '',
        riskFreeSource: raw.risk_free_source || '',
        riskFreeMethod: raw.risk_free_method || '',
        generatedAt: raw.generated_at || '',
        portfolioPeriodCount: Number(raw.portfolio_period_count || 0),
        benchmarkAlphaSpreadPp: Number.isFinite(Number(raw.benchmark_alpha_spread_pp)) ? Number(raw.benchmark_alpha_spread_pp) : null,
        spy: normalizeAlphaRegressionResult(benchmarks.SPY),
        twii: normalizeAlphaRegressionResult(benchmarks['^TWII']),
        limitations: Array.isArray(raw.limitations) ? raw.limitations : [],
        refreshStatus: raw.refresh_status || '',
        refreshError: raw.refresh_error || ''
    };
});

function finiteOrNull(val) {
    if (val === null || val === undefined || val === '') return null;
    const n = Number(val);
    return Number.isFinite(n) ? n : null;
}

function lookthroughStatusLabel(status) {
    const labels = {
        available_official: '官方資料可用',
        available_mixed_sources: '可用・混合來源',
        available_stale_or_unknown_freshness: '可用・資料待更新',
        partial_missing_funds: '部分可用',
        missing_holdings_snapshot: '等待持股快照',
        no_supported_equity_etf_in_portfolio: '目前無支援 ETF',
        backend_xray_unavailable: '後端 X-Ray 未提供',
        unknown: '等待資料'
    };
    return labels[status] || status || '等待資料';
}

function lookthroughSourceLabel(sourceQuality) {
    const source = String(sourceQuality || 'UNKNOWN');
    if (source === 'OFFICIAL_DAILY') return '官方每日';
    if (source === 'OFFICIAL_MONTHLY') return '官方月度';
    if (source === 'OFFICIAL_WEEKLY') return '官方每週';
    if (source.startsWith('OFFICIAL')) return '官方來源';
    if (source === 'THIRD_PARTY_FALLBACK') return '第三方備援';
    return source;
}

function lookthroughModeLabel(mode) {
    const labels = {
        DERIVATIVE_STRATEGY: '衍生品策略・不做股票穿透',
        BOND_LOOKTHROUGH: '債券曝險・獨立處理',
        COMMODITY_PHYSICAL: '實體商品曝險',
        DIRECT_CRYPTO: '直接加密資產'
    };
    return labels[mode] || mode || '其他曝險';
}

function lookthroughTimestampLabel(value) {
    if (!value) return '';
    const dt = new Date(value);
    if (Number.isNaN(dt.getTime())) return String(value);
    return dt.toLocaleString('zh-TW', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function normalizeLookthrough(meta) {
    const raw = meta && typeof meta === 'object' ? meta : {};
    const status = raw.status || 'unknown';
    const available = status.startsWith('available_') || status === 'partial_missing_funds';
    const warning = ['available_mixed_sources', 'available_stale_or_unknown_freshness', 'partial_missing_funds'].includes(status);
    const coverageObject = raw.fund_coverage && typeof raw.fund_coverage === 'object' ? raw.fund_coverage : {};

    const topUnderlying = Array.isArray(raw.top_underlying)
        ? raw.top_underlying.map((row, idx) => ({
            rank: idx + 1,
            ticker: row?.ticker || '',
            name: row?.name || '',
            portfolioWeightPct: finiteOrNull(row?.portfolio_weight_pct),
            sourceFunds: Array.isArray(row?.source_funds) ? row.source_funds : []
        }))
        : [];

    const pairwiseOverlap = Array.isArray(raw.pairwise_overlap)
        ? raw.pairwise_overlap.map(row => ({
            fundA: row?.fund_a || '',
            fundB: row?.fund_b || '',
            overlapPct: finiteOrNull(row?.overlap_pct)
        }))
        : [];

    const fundCoverage = Object.entries(coverageObject).map(([fund, row]) => ({
        fund,
        portfolioWeightPct: finiteOrNull(row?.portfolio_weight_pct),
        asOf: row?.as_of || '',
        staleDays: finiteOrNull(row?.stale_days_recomputed),
        sourceQuality: row?.source_quality || 'UNKNOWN',
        sourceLabel: lookthroughSourceLabel(row?.source_quality),
        isOfficialSource: String(row?.source_quality || '').startsWith('OFFICIAL'),
        refreshStatus: row?.refresh_status || 'UNKNOWN',
        equityCoveragePct: finiteOrNull(row?.equity_coverage_pct),
        holdingsCount: finiteOrNull(row?.holdings_count)
    })).sort((a, b) => (b.portfolioWeightPct || 0) - (a.portfolioWeightPct || 0));

    const specialExposures = Array.isArray(raw.special_exposures)
        ? raw.special_exposures.map(row => ({
            ticker: row?.ticker || '',
            portfolioWeightPct: finiteOrNull(row?.portfolio_weight_pct),
            lookthroughMode: row?.lookthrough_mode || '',
            modeLabel: lookthroughModeLabel(row?.lookthrough_mode)
        }))
        : [];

    const loadedFunds = Array.isArray(raw.loaded_funds) ? raw.loaded_funds : [];
    const missingFunds = Array.isArray(raw.missing_funds) ? raw.missing_funds : [];
    const nonofficialFunds = Array.isArray(raw.nonofficial_funds) ? raw.nonofficial_funds : [];
    const staleFunds = Array.isArray(raw.stale_funds) ? raw.stale_funds : [];
    const mappedPct = finiteOrNull(raw.mapped_equity_portfolio_pct);
    const topRow = topUnderlying[0] || null;
    const maxPair = pairwiseOverlap[0] || null;
    let displayNote = raw.note || '';
    if (available) {
        const parts = [];
        if (loadedFunds.length) parts.push(`已載入 ${loadedFunds.join(' / ')}`);
        if (mappedPct !== null) parts.push(`已映射底層股票占整體投資組合 ${mappedPct.toFixed(1)}%`);
        if (topRow?.portfolioWeightPct !== null && topRow) {
            parts.push(`最大底層部位 ${topRow.ticker || topRow.name || 'N/A'} ${topRow.portfolioWeightPct.toFixed(2)}%`);
        }
        if (maxPair?.overlapPct !== null && maxPair) {
            parts.push(`最高兩兩重疊 ${maxPair.fundA}/${maxPair.fundB} ${maxPair.overlapPct.toFixed(1)}%`);
        }
        if (missingFunds.length) parts.push(`缺少 ${missingFunds.join(' / ')}`);
        if (nonofficialFunds.length) parts.push(`非官方來源 ${nonofficialFunds.join(' / ')}`);
        if (staleFunds.length) parts.push(`資料待更新 ${staleFunds.join(' / ')}`);
        displayNote = parts.length ? `${parts.join('；')}。` : displayNote;
    }

    return {
        status,
        statusLabel: lookthroughStatusLabel(status),
        available,
        warning,
        note: raw.note || '',
        displayNote,
        method: raw.method || '',
        overlapMethod: raw.overlap_method || '',
        identityLimit: raw.identity_limit || '',
        generatedAt: raw.generated_at || '',
        generatedAtLabel: lookthroughTimestampLabel(raw.generated_at),
        heldSupportedEtfSleevePct: finiteOrNull(raw.held_supported_etf_sleeve_pct),
        loadedEtfSleevePct: finiteOrNull(raw.loaded_etf_sleeve_pct),
        mappedEquityPortfolioPct: finiteOrNull(raw.mapped_equity_portfolio_pct),
        loadedSleeveEquityCoveragePct: finiteOrNull(raw.loaded_sleeve_equity_coverage_pct),
        heldSupportedSleeveCoveragePct: finiteOrNull(raw.held_supported_sleeve_coverage_pct),
        top5UnderlyingPortfolioPct: finiteOrNull(raw.top5_underlying_portfolio_pct),
        top10UnderlyingPortfolioPct: finiteOrNull(raw.top10_underlying_portfolio_pct),
        mappedEquityHhi: finiteOrNull(raw.mapped_equity_hhi),
        heldSupportedFunds: Array.isArray(raw.held_supported_funds) ? raw.held_supported_funds : [],
        loadedFunds,
        missingFunds,
        nonofficialFunds,
        staleFunds,
        topUnderlying,
        pairwiseOverlap,
        fundCoverage,
        specialExposures
    };
}

watch([groupedHoldings, portfolioStats, stats, sysCorr, chaosMeta, cloudRebalanceMeta, liquidityBufferRatio], () => {
    let trims = 0;
    let adds = 0;
    let drifts = 0;
    let concentrations = 0;
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

            const currentWeightPct = item.totalWeight * 100;
            const targetWeightRaw = Number(item.blendedWeight);
            // A tiny residual should not reopen an economically closed position via stale target metadata.
            const isEconomicDustForFallback = currentWeightPct > 0 && currentWeightPct < 0.02;
            const hasTargetWeight =
                !isEconomicDustForFallback &&
                Number.isFinite(targetWeightRaw) &&
                ((Number(item.targetWeight) || 0) > 0 || (Number(item.mcWeight) || 0) > 0);
            const signedDrift = hasTargetWeight ? currentWeightPct - targetWeightRaw : null;
            const drift = signedDrift === null ? null : Math.abs(signedDrift);

            if (signedDrift !== null && signedDrift > 5) trims++;
            if (signedDrift !== null && signedDrift < -5) adds++;
            if (drift !== null && drift > 5) drifts++;
            if (currentWeightPct > 20) concentrations++;

            const isHighDrift = drift !== null && drift > 10;
            const isHighConcentration = currentWeightPct > 30;
            if (isHighDrift || isHighConcentration) {
                alertCount++;
                let candidateAction = 'REVIEW';
                if (isHighConcentration || (signedDrift !== null && signedDrift > 10)) candidateAction = 'TRIM';
                else if (signedDrift !== null && signedDrift < -10) candidateAction = 'ADD / REVIEW TARGET';

                const targetText = hasTargetWeight ? `${targetWeightRaw.toFixed(1)}%` : 'N/A';
                const driftText = signedDrift === null
                    ? 'N/A'
                    : `${signedDrift >= 0 ? '+' : ''}${signedDrift.toFixed(1)}pp`;
                alertList.push(
                    `[${item.ticker}] 目前 ${currentWeightPct.toFixed(1)}% / 目標 ${targetText} / drift ${driftText} / 候選動作 ${candidateAction}。`
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
    const evtRobust = backendTail?.evt_robustness || chaosMeta.value?.evt_robustness || chaosMeta.value?.evt_tail?.evt_robustness || {};

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
            },
            lookthrough: normalizeLookthrough(backendXray?.lookthrough_overlap)
        };
    } else {
        xrayStats.value = {
            mrcTable: mrcTemp,
            pca: {
                pc1Explained: '-',
                pc3CumExplained: '-'
            },
            fx: {
                netFxExposurePct: (fxExposure * 100).toFixed(1),
                usdNavImpact1pct: '-'
            },
            lookthrough: normalizeLookthrough(
                backendXray?.lookthrough_overlap || {
                    status: 'backend_xray_unavailable',
                    note: 'PCA、TWD FX impact 與 ETF look-through 未由後端提供；不得使用代理值冒充實測值。'
                }
            )
        };
    }

    const backendRebalance = cloudRebalanceMeta.value || {};
    const backendSignals = Array.isArray(backendRebalance.signals) ? backendRebalance.signals : [];
    const backendBlockedSignals = Array.isArray(backendRebalance.blocked_signals) ? backendRebalance.blocked_signals : [];
    const authoritativeRebalance =
        backendRebalance.universe_policy === 'material_ledger_holdings_plus_hard_buffer_only';

    const normalizeSignalDirection = (signal) => {
        const explicit = String(signal?.direction || '').toUpperCase();
        if (explicit === 'ADD' || explicit === 'TRIM') return explicit;
        const legacy = String(signal?.action || '').toUpperCase();
        if (legacy.includes('BUY')) return 'ADD';
        if (legacy.includes('SELL')) return 'TRIM';
        return 'REVIEW';
    };

    if (authoritativeRebalance) {
        trims = backendSignals.filter(s => normalizeSignalDirection(s) === 'TRIM').length;
        adds = backendSignals.filter(s => normalizeSignalDirection(s) === 'ADD').length;
        drifts = [...backendSignals, ...backendBlockedSignals]
            .filter(s => String(s?.signal_type || 'TARGET_DRIFT') === 'TARGET_DRIFT').length;
        alertCount = backendSignals.length + backendBlockedSignals.length;

        // Backend rule engine is authoritative for actionable direction. Discard local
        // target fallbacks so stale metadata cannot manufacture an ADD/TRIM.
        alertList.splice(0, alertList.length);
        [...backendSignals, ...backendBlockedSignals].forEach(signal => {
            const direction = normalizeSignalDirection(signal);
            const current = Number(signal?.current_weight_pct);
            const target = Number(signal?.target_weight_pct);
            const drift = Number(signal?.signed_drift_pp);
            const status = String(signal?.execution_status || 'ACTIONABLE');
            const pieces = [
                `[${signal?.ticker || 'N/A'}]`,
                Number.isFinite(current) ? `目前 ${current.toFixed(1)}%` : '',
                Number.isFinite(target) ? `目標 ${target.toFixed(1)}%` : '',
                Number.isFinite(drift) ? `drift ${drift >= 0 ? '+' : ''}${drift.toFixed(1)}pp` : '',
                `候選動作 ${direction}`,
                status === 'BLOCKED_BY_BUFFER' ? '狀態 BLOCKED_BY_BUFFER' : ''
            ].filter(Boolean);
            alertList.push(`${pieces.join(' / ')}。`);
        });
    }

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
            `硬緩衝不足：目前 ${resolvedCurrentBufferPct}% / 目標 ${resolvedBufferFloorPct}% ，風險資產 ADD 已暫停，請優先補足 ${resolvedHardBufferTickers.join(' + ')}。`
        );
    }

    rebalanceMonitor.value = {
        trimCount: trims,
        addCount: adds,
        blockedAddCount: backendBlockedSignals.filter(s => normalizeSignalDirection(s) === 'ADD').length,
        driftCount: drifts,
        concentrationCount: concentrations,
        alertCount: alertCount + (resolvedBufferBlocking ? 1 : 0),
        // 0.5*sigma^2*time is a geometric-return volatility-drag approximation,
        // not evidence of leverage.
        volDrag30d: ((0.5 * Math.pow(portVol, 2) * (30 / 365)) * 100).toFixed(2),
        volDrag90d: ((0.5 * Math.pow(portVol, 2) * (90 / 365)) * 100).toFixed(2),
        bufferFloorPct: resolvedBufferFloorPct,
        currentBufferPct: resolvedCurrentBufferPct,
        bufferGapPct: resolvedBufferGapPct,
        bufferBlockingRiskBuys: resolvedBufferBlocking,
        hardBufferTickers: resolvedHardBufferTickers,
        universePolicy: backendRebalance.universe_policy || '',
        ruleThresholdPp: Number(backendRebalance.rule_threshold_pp || 1),
        economicDustTickers: Array.isArray(backendRebalance.economic_dust_tickers_excluded)
            ? backendRebalance.economic_dust_tickers_excluded : [],
        sheetOnlyTickersExcluded: Array.isArray(backendRebalance.sheet_only_tickers_excluded)
            ? backendRebalance.sheet_only_tickers_excluded : [],
        backendSignalCount: backendSignals.length,
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
        downsideSampleCount: backendTail.tail_inference?.downside_sample_count ?? '-',
        coDrawdownThreshold: fmtNum(backendTail.co_drawdown_threshold, 1),
        tailThresholdQuantile: fmtNum((backendTail.tail_threshold_quantile ?? 0) * 100, 0),

        tailInferenceStatus: backendTail.tail_inference?.status || 'not_computed',
        tailInferenceMethod: backendTail.tail_inference?.method || '-',
        tailBootstrapReplicates: backendTail.tail_inference?.bootstrap_replicates_requested ?? '-',
        tailBootstrapBlockWeeks: backendTail.tail_inference?.block_length_weeks ?? '-',
        tailCiLevel: fmtNum((backendTail.tail_inference?.ci_level ?? 0) * 100, 0),
        conditionalCorrCiLow: fmtNum(backendTail.tail_inference?.conditional_corr_ci95_low, 2),
        conditionalCorrCiHigh: fmtNum(backendTail.tail_inference?.conditional_corr_ci95_high, 2),
        crisisCorrCiLow: fmtNum(backendTail.tail_inference?.crisis_corr_ci95_low, 2),
        crisisCorrCiHigh: fmtNum(backendTail.tail_inference?.crisis_corr_ci95_high, 2),
        downsideBetaCiLow: fmtNum(backendTail.tail_inference?.downside_beta_ci95_low, 2),
        downsideBetaCiHigh: fmtNum(backendTail.tail_inference?.downside_beta_ci95_high, 2),

        historicalVar95_1w: fmtPctMaybe(backendTail.historical_var95_1w, 2),
        historicalEs95_1w: fmtPctMaybe(backendTail.historical_es95_1w, 2),
        historicalSampleCount1w: backendTail.historical_sample_count_1w ?? '-',
        historicalHorizonVar95: fmtPctMaybe(backendTail.historical_var95_horizon, 2),
        historicalHorizonEs95: fmtPctMaybe(backendTail.historical_es95_horizon, 2),
        historicalHorizonWeeks: backendTail.historical_horizon_weeks ?? '-',
        historicalHorizonSampleCount: backendTail.historical_horizon_sample_count ?? '-',
        historicalHorizonMethod: backendTail.historical_horizon_method || '-',

        // Jump stress scenario
        jdVar95: fmtPctMaybe(backendTail.jd_var95, 2),
        jdEs95: fmtPctMaybe(backendTail.jd_es95, 2),
        jdCrashProb: fmtPctMaybe(backendTail.jd_crash_prob, 2),
        jdTailLoss: fmtPctMaybe(backendTail.jd_tail_loss, 2),
        jdHorizonWeeks: backendTail.jd_horizon_weeks ?? '-',
        jdEffectiveLambda: fmtNum(backendTail.jd_effective_lambda, 2),
        jdEffectiveJumpMean: fmtNum(backendTail.jd_effective_jump_mean, 4),
        jdEffectiveJumpStd: fmtNum(backendTail.jd_effective_jump_std, 4),
        jdCrashThresholdPct: fmtPctMaybe(backendTail.jd_crash_threshold_pct, 1),
        jdModelType: backendTail.jd_model_type || '-',
        jdParameterSource: backendTail.jd_parameter_source || '-',
        jdJumpAggregation: backendTail.jd_jump_aggregation || '-',
        jdDriftCompensated: backendTail.jd_drift_compensated ?? '-',
        jdExpectedJumpDragWeeklyPct: fmtPctMaybe(backendTail.jd_expected_jump_drag_weekly_pct, 4),
        jdSimulationCount: backendTail.jd_simulation_count ?? '-',

        // EVT robustness (one-day current-weight diagnostic)
        evtVar95: fmtPctMaybe(evtRobust.var95_pct ?? backendTail.evt_var95, 2),
        evtEs95: fmtPctMaybe(evtRobust.es95_pct ?? backendTail.evt_es95, 2),
        evtShapeXi: fmtNum(evtRobust.shape_xi ?? backendTail.evt_shape_xi, 4),
        evtScaleBeta: fmtNum(evtRobust.scale_beta ?? backendTail.evt_scale_beta, 6),
        evtThreshold: fmtPctMaybe(
            evtRobust.threshold_loss_pct !== null && evtRobust.threshold_loss_pct !== undefined
                ? -Math.abs(Number(evtRobust.threshold_loss_pct))
                : backendTail.evt_threshold,
            2
        ),
        evtExceedanceCount: evtRobust.exceedance_count ?? backendTail.evt_exceedance_count ?? '-',
        evtAlphaConf: fmtNum((evtRobust.alpha_conf ?? backendTail.evt_alpha_conf ?? 0) * 100, 0),
        evtReturnFrequency: evtRobust.return_frequency || backendTail.evt_return_frequency || 'daily',
        evtHorizonDays: evtRobust.horizon_days ?? backendTail.evt_horizon_days ?? 1,
        evtComparableToJd: backendTail.evt_comparable_to_jd ?? false,
        evtComparisonNote: backendTail.evt_comparison_note || 'one_day_evt_not_directly_comparable_to_13_week_jump_stress',
        evtRobustStatus: evtRobust.status || 'not_computed',
        evtDailySampleCount: evtRobust.sample_count ?? '-',
        evtXiCiLow: fmtNum(evtRobust.shape_xi_ci95_low, 4),
        evtXiCiHigh: fmtNum(evtRobust.shape_xi_ci95_high, 4),
        evtVarCiLow: fmtPctMaybe(evtRobust.var95_ci95_low_pct, 2),
        evtVarCiHigh: fmtPctMaybe(evtRobust.var95_ci95_high_pct, 2),
        evtEsCiLow: fmtPctMaybe(evtRobust.es95_ci95_low_pct, 2),
        evtEsCiHigh: fmtPctMaybe(evtRobust.es95_ci95_high_pct, 2),
        evtBootstrapReplicates: evtRobust.bootstrap_replicates_requested ?? '-',
        evtBootstrapValidReps: evtRobust.bootstrap_valid_reps ?? '-',
        evtBootstrapBlockDays: evtRobust.bootstrap_block_days ?? '-',
        evtThresholdValidCount: evtRobust.threshold_valid_count ?? '-',
        evtXiMin: fmtNum(evtRobust.shape_xi_min, 4),
        evtXiMax: fmtNum(evtRobust.shape_xi_max, 4),
        evtXiSignStability: evtRobust.shape_xi_sign_stability || 'insufficient',
        evtEvidenceFlag: evtRobust.evidence_flag || 'insufficient_sample',
        evtFiniteEndpointLossPct: fmtPctMaybe(evtRobust.finite_upper_endpoint_loss_pct, 2)
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
        downsideSampleCount: '-',
        coDrawdownThreshold: '-10.0',
        tailThresholdQuantile: '5',

        tailInferenceStatus: 'not_computed',
        tailInferenceMethod: '-',
        tailBootstrapReplicates: '-',
        tailBootstrapBlockWeeks: '-',
        tailCiLevel: '-',
        conditionalCorrCiLow: '-',
        conditionalCorrCiHigh: '-',
        crisisCorrCiLow: '-',
        crisisCorrCiHigh: '-',
        downsideBetaCiLow: '-',
        downsideBetaCiHigh: '-',

        historicalVar95_1w: '-',
        historicalEs95_1w: '-',
        historicalSampleCount1w: '-',
        historicalHorizonVar95: '-',
        historicalHorizonEs95: '-',
        historicalHorizonWeeks: '-',
        historicalHorizonSampleCount: '-',
        historicalHorizonMethod: '-',

        // Jump stress fallback
        jdVar95: '-',
        jdEs95: '-',
        jdCrashProb: '-',
        jdTailLoss: '-',
        jdHorizonWeeks: '-',
        jdEffectiveLambda: '-',
        jdEffectiveJumpMean: '-',
        jdEffectiveJumpStd: '-',
        jdCrashThresholdPct: '-',
        jdModelType: '-',
        jdParameterSource: '-',
        jdJumpAggregation: '-',
        jdDriftCompensated: '-',
        jdExpectedJumpDragWeeklyPct: '-',
        jdSimulationCount: '-',

        // EVT fallback
        evtVar95: '-',
        evtEs95: '-',
        evtShapeXi: '-',
        evtScaleBeta: '-',
        evtThreshold: '-',
        evtExceedanceCount: '-',
        evtAlphaConf: '-',
        evtReturnFrequency: '-',
        evtHorizonDays: '-',
        evtComparableToJd: '-',
        evtComparisonNote: '-',
        evtRobustStatus: 'not_computed',
        evtDailySampleCount: '-',
        evtXiCiLow: '-',
        evtXiCiHigh: '-',
        evtVarCiLow: '-',
        evtVarCiHigh: '-',
        evtEsCiLow: '-',
        evtEsCiHigh: '-',
        evtBootstrapReplicates: '-',
        evtBootstrapValidReps: '-',
        evtBootstrapBlockDays: '-',
        evtThresholdValidCount: '-',
        evtXiMin: '-',
        evtXiMax: '-',
        evtXiSignStability: 'insufficient',
        evtEvidenceFlag: 'insufficient_sample',
        evtFiniteEndpointLossPct: '-'
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

        const decisionCenter = computed(() => {
            const holdings = [];
            for (const cat in groupedHoldings.value) {
                groupedHoldings.value[cat].items.forEach(item => holdings.push(item));
            }

            const topDriftList = [...holdings]
                .sort((a, b) => Math.abs(b.weightGap || 0) - Math.abs(a.weightGap || 0))
                .slice(0, 3)
                .map(item => ({
                    ticker: item.ticker,
                    drift: Math.abs(item.weightGap || 0).toFixed(1),
                    currentWeight: ((item.totalWeight || 0) * 100).toFixed(1),
                    targetWeight: Number(item.blendedWeight || 0).toFixed(1)
                }));

            const queue = [];
            if (isCashNegative.value) {
                queue.push({
                    level: 'high',
                    icon: 'fa-wallet',
                    title: '現金為負',
                    detail: `Cash ${formatNumber(cashBalance.value)}，優先檢查是否「先出金後賣出」。`
                });
            }
            if (rebalanceMonitor.value.bufferBlockingRiskBuys) {
                queue.push({
                    level: 'high',
                    icon: 'fa-shield-halved',
                    title: '防線不足',
                    detail: `目前 ${rebalanceMonitor.value.currentBufferPct}% / 目標 ${rebalanceMonitor.value.bufferFloorPct}% ，先補硬緩衝。`
                });
            }
            if ((rebalanceMonitor.value.alertCount || 0) > 0 && topDriftList[0]) {
                queue.push({
                    level: 'medium',
                    icon: 'fa-crosshairs',
                    title: '再平衡偏移擴大',
                    detail: `${topDriftList[0].ticker} drift ${topDriftList[0].drift}% ，目前 ${topDriftList[0].currentWeight}% / 目標 ${topDriftList[0].targetWeight}%。`
                });
            }
            if ((Number(tailStatsLite.value.jdCrashProb) || 0) >= 8 || tailStatsLite.value.evtEvidenceFlag === 'positive_xi_robust_across_tested_thresholds') {
                const evtCi = tailStatsLite.value.evtXiCiLow !== '-' && tailStatsLite.value.evtXiCiHigh !== '-'
                    ? `（95% CI ${tailStatsLite.value.evtXiCiLow} ~ ${tailStatsLite.value.evtXiCiHigh}）`
                    : '';
                queue.push({
                    level: 'medium',
                    icon: 'fa-burst',
                    title: '尾部風險偏高',
                    detail: `Crash Prob ${tailStatsLite.value.jdCrashProb}% / EVT ξ ${tailStatsLite.value.evtShapeXi}${evtCi}，僅在 EVT 正 ξ 同時通過門檻敏感度與 CI 時視為較穩健的肥尾證據。`
                });
            }
            if (!queue.length) {
                queue.push({
                    level: 'low',
                    icon: 'fa-circle-check',
                    title: '目前無重大異常',
                    detail: '今天主要工作是維持快照紀律與價格更新。'
                });
            }

            const topFocus = queue[0];
            return {
                headline: topFocus.title,
                detail: topFocus.detail,
                tone: topFocus.level,
                queue: queue.slice(0, 4),
                topDriftList,
                alertCount: rebalanceMonitor.value.alertCount || 0,
                trimCount: rebalanceMonitor.value.trimCount || 0,
                bufferGap: Number(rebalanceMonitor.value.bufferGapPct || 0).toFixed(1)
            };
        });

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
        
