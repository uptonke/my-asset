const { createApp, ref, computed, onMounted, watch, nextTick } = Vue;

createApp({
    setup() {
        const blViews = ref([]); 
        const cloudRebalanceMeta = ref(null); 
        
        const mcAvailableAssets = computed(() => {
            const list = [];
            for (const cat in groupedHoldings.value) {
                groupedHoldings.value[cat].items.forEach(item => {
                    if(item.beta > 0 && item.stdDev > 0) list.push(item);
                });
            }
            return list;
        });

        function addBlView() {
            if(mcAvailableAssets.value.length > 0) {
                blViews.value.push({
                    type: 'absolute',
                    asset1: mcAvailableAssets.value[0].ticker,
                    asset2: mcAvailableAssets.value.length > 1 ? mcAvailableAssets.value[1].ticker : mcAvailableAssets.value[0].ticker,
                    value: 8.0
                });
            } else {
                alert('庫存中沒有合格的標的 (需設定 Beta 與 StdDev)');
            }
        }

        // ==========================================
        // 🤖 專屬 AI 量化風險總監 (CRO)
        // ==========================================
        const croInsight = ref(null);
        const isCroThinking = ref(false);

        async function generateQuantInsight() {
            const apiKey = localStorage.getItem('GEMINI_API_KEY') || prompt('首次使用請輸入您的 Gemini API Key (將安全儲存於瀏覽器):');
            if (!apiKey) return;
            localStorage.setItem('GEMINI_API_KEY', apiKey);

            isCroThinking.value = true;
            croInsight.value = null;

            const payload = {
    return_metrics: {
        time_weighted_return_twr: stats.value.annRet + '%',
        money_weighted_return_mwr: stats.value.mwr === '-' ? 'N/A' : stats.value.mwr + '%',
        log_return: stats.value.annLogRet + '%',
        alpha_jensen: stats.value.alpha + '%'
    },
    risk_efficiency: {
    portfolio_beta: riskParams.value.beta,
    portfolio_volatility: stats.value.annVol + '%',
    historical_sharpe: stats.value.sharpe,
    historical_psr: stats.value.psr === '-' ? 'N/A' : stats.value.psr + '%',
    mc_sharpe_raw: mcOptimal.value?.sharpeRaw ?? 'N/A',
    mc_psr: mcOptimal.value?.psr ? mcOptimal.value.psr + '%' : 'N/A',
    mc_dsr: mcOptimal.value?.dsr ? mcOptimal.value.dsr + '%' : 'N/A',
    mc_dsr_trials: mcOptimal.value?.dsrTrials ?? 'N/A',
    mc_dsr_sample_n: mcOptimal.value?.dsrSampleN ?? 'N/A',
    sortino_ratio: stats.value.sortino,
    treynor_ratio: stats.value.treynor
},
kelly_sizing: {
        full_kelly: mcOptimal.value?.fullKelly ? mcOptimal.value.fullKelly + '%' : 'N/A',
        half_kelly: mcOptimal.value?.halfKelly ? mcOptimal.value.halfKelly + '%' : 'N/A',
        recommended_buffer: mcOptimal.value?.recommendedBuffer ? mcOptimal.value.recommendedBuffer + '%' : 'N/A'
    },
    asymmetry_and_win_rate: {
        omega_ratio: stats.value.omega,
        profit_factor_pf: stats.value.profitFactor,
        skewness: stats.value.skew,
        kurtosis: stats.value.kurt
    },
    catastrophic_risk: {
        max_drawdown_mdd: stats.value.mdd + '%',
        ulcer_index_ui: stats.value.ulcer,
        time_under_water_tuw_days: stats.value.tuw,
        calmar_ratio: stats.value.calmar,
        value_at_risk_var_95: stats.value.var95 + '%',
        cvar_95: stats.value.cvar95 + '%'
    },
    systemic_correlation: sysCorr.value.toFixed(2),

    regime_rebalance_monitor: {
    trim_candidates: rebalanceMonitor.value.trimCount,
    high_priority_alerts: rebalanceMonitor.value.alertCount,
    leverage_vol_drag_30d: rebalanceMonitor.value.volDrag30d + '%',
    leverage_vol_drag_90d: rebalanceMonitor.value.volDrag90d + '%',

    buffer_floor_pct: rebalanceMonitor.value.bufferFloorPct + '%',
    current_buffer_pct: rebalanceMonitor.value.currentBufferPct + '%',
    buffer_gap_pct: rebalanceMonitor.value.bufferGapPct + '%',
    buffer_blocking_risk_buys: rebalanceMonitor.value.bufferBlockingRiskBuys ? '是' : '否',
    hard_buffer_tickers: (rebalanceMonitor.value.hardBufferTickers || []).join(' + '),

    rebalance_alerts: rebalanceMonitor.value.alerts.slice(0, 5)
},

    portfolio_xray: {
        pc1_explained: xrayStats.value.pca.pc1Explained + '%',
        pc1_to_pc3_cumulative: xrayStats.value.pca.pc3CumExplained + '%',
        usd_exposure_pct: xrayStats.value.fx.netFxExposurePct + '%',
        fx_1pct_nav_impact_twd: xrayStats.value.fx.usdNavImpact1pct,
        top_risk_contributors: xrayStats.value.mrcTable.slice(0, 5)
    },

    tail_crash_radar: {
    conditional_correlation: tailStatsLite.value.conditionalCorr,
    crisis_correlation: tailStatsLite.value.crisisCorr,
    downside_beta: tailStatsLite.value.downsideBeta,
    stressed_cvar: tailStatsLite.value.stressedCvar + '%',
    joint_downside_hit_rate: tailStatsLite.value.jointDownsideHitRate + '%',
    co_drawdown_frequency: tailStatsLite.value.coDrawdownFrequency + '%',
    tail_dependence_lite: tailStatsLite.value.tailDependenceLite,
    rolling_cvar_26w: tailStatsLite.value.rollingCvar26w + '%',
    rolling_cvar_52w: tailStatsLite.value.rollingCvar52w + '%',
    crisis_window_label: tailStatsLite.value.crisisWindowLabel,
    tail_sample_count: tailStatsLite.value.tailSampleCount,
    crisis_sample_count: tailStatsLite.value.crisisSampleCount,
    co_drawdown_threshold: tailStatsLite.value.coDrawdownThreshold + '%',
    tail_threshold_quantile: 'P' + tailStatsLite.value.tailThresholdQuantile
},

jump_diffusion: {
    jd_var95: tailStatsLite.value.jdVar95 === '-' ? 'N/A' : tailStatsLite.value.jdVar95 + '%',
    jd_es95: tailStatsLite.value.jdEs95 === '-' ? 'N/A' : tailStatsLite.value.jdEs95 + '%',
    jd_crash_prob: tailStatsLite.value.jdCrashProb === '-' ? 'N/A' : tailStatsLite.value.jdCrashProb + '%',
    jd_tail_loss: tailStatsLite.value.jdTailLoss === '-' ? 'N/A' : tailStatsLite.value.jdTailLoss + '%',
    jd_horizon_weeks: tailStatsLite.value.jdHorizonWeeks,
    jd_effective_lambda: tailStatsLite.value.jdEffectiveLambda,
    jd_effective_jump_mean: tailStatsLite.value.jdEffectiveJumpMean,
    jd_effective_jump_std: tailStatsLite.value.jdEffectiveJumpStd
},

evt_tail: {
    evt_var95: tailStatsLite.value.evtVar95 === '-' ? 'N/A' : tailStatsLite.value.evtVar95 + '%',
    evt_es95: tailStatsLite.value.evtEs95 === '-' ? 'N/A' : tailStatsLite.value.evtEs95 + '%',
    evt_shape_xi: tailStatsLite.value.evtShapeXi,
    evt_scale_beta: tailStatsLite.value.evtScaleBeta,
    evt_threshold: tailStatsLite.value.evtThreshold === '-' ? 'N/A' : tailStatsLite.value.evtThreshold + '%',
    evt_exceedance_count: tailStatsLite.value.evtExceedanceCount,
    evt_alpha_conf: tailStatsLite.value.evtAlphaConf === '-' ? 'N/A' : 'P' + tailStatsLite.value.evtAlphaConf
}
};

            const promptText = `
[SYSTEM_DIRECTIVE]
Task: Act as a coldly rational, highly analytical Quant Chief Risk Officer (CRO) for a family office.
Tone: Brutally honest, strictly data-driven, and logically flawless. Zero tolerance for financial contradictions.
Constraint: Output strictly in Traditional Chinese. Max 8 bullet points. No pleasantries.

[LOGICAL_GUARDRAILS]
- DO NOT confuse "Diversification/Rotation" with "Hedging".
- TRUE HEDGING means moving to cash, bonds, or negative-beta assets.
- DO NOT suggest buying high-beta, risk-on assets as a hedge.
- If Portfolio X-Ray, Rebalance Monitor, and Tail / Crash Radar are present, you MUST use them explicitly.
- If jump_diffusion is present, you MUST explicitly judge discontinuous crash risk using jd_var95, jd_es95, jd_crash_prob, and jd_tail_loss. Do not ignore it just because historical CVaR exists.
- If evt_tail is present, you MUST explicitly judge whether historical tail risk is being understated using evt_var95, evt_es95, evt_shape_xi, evt_threshold, and evt_exceedance_count.
- Treat tail metrics with low sample counts cautiously. If tail_sample_count, crisis_sample_count, or evt_exceedance_count is small, explicitly mention that the signal direction matters more than the exact magnitude.
- If regime_rebalance_monitor shows buffer_blocking_risk_buys = YES, you MUST treat Buffer Floor as a hard constraint, not a soft suggestion.
- When buffer_gap_pct > 0, DO NOT recommend buying high-beta or risk-on assets first. The portfolio must replenish hard buffer assets before any discretionary risk-on add.
- If risk_efficiency contains historical_psr, mc_psr, or mc_dsr, you MUST explicitly discuss whether the portfolio's apparent Sharpe is statistically credible.
- Do not treat a high raw Sharpe as strong evidence if DSR is materially lower.
- If PSR or DSR is N/A, say so explicitly rather than inferring significance.
- [KELLY INTEGRATION RULE]: If kelly_sizing.recommended_buffer is near 0%, it means the macro environment strongly favors risk-on. If the portfolio concurrently shows severe structural risks (e.g., False Diversification, high Downside Beta), your final tactical instruction MUST BE "強勢輪動 (Aggressive Rotation)". You must explicitly command the user to Trim toxic/overweight assets to release cash, and IMMEDIATELY REINVEST that cash into the optimal risky assets to maintain full exposure. DO NOT suggest holding cash if Kelly says 0%.

[ANALYSIS_RULES]
You MUST analyze the portfolio holistically using all modules below:

1. 【資金效率與選股】Compare TWR vs MWR and Jensen's Alpha. Judge whether timing and selection are adding value or destroying value.
2. 【風險報酬定價】Use historical_sharpe, historical_psr, mc_sharpe_raw, mc_psr, mc_dsr, Sortino, Treynor, Beta, and Volatility.
State whether the portfolio is being paid enough for the risk it is taking.
If PSR or DSR is present, explicitly judge whether the observed Sharpe is statistically credible or likely inflated by selection / optimization.
Treat DSR as more important than raw Sharpe when Monte Carlo optimization has tested many candidate portfolios.
3. 【Portfolio X-Ray】Use PC1 explained, PC1-3 cumulative explained, USD exposure, FX impact, and top risk contributors. Judge whether the portfolio is truly diversified or only appears diversified.
4. 【市場狀態 / 再平衡監控】Use trim candidates, high-priority alerts, leverage volatility drag, buffer_floor_pct, current_buffer_pct, buffer_gap_pct, buffer_blocking_risk_buys, hard_buffer_tickers, and rebalance alerts. Judge whether risk is drifting because the user failed to rebalance, and whether the portfolio is currently constrained by a Buffer Floor shortfall.
5. 【Tail / Crash Radar】Use conditional correlation, crisis correlation, downside beta, stressed CVaR, joint downside hit rate, co-drawdown frequency, tail dependence lite, and rolling CVaR. Judge how fragile the portfolio becomes in bad states.
6. 【Jump-Diffusion / EVT】If jump_diffusion or evt_tail is present, you MUST explicitly compare historical tail metrics vs jump-adjusted tail metrics vs EVT-implied tail metrics. State whether historical CVaR is understating discontinuous crash risk or fat-tail risk. Use jd_var95, jd_es95, jd_crash_prob, jd_tail_loss, evt_var95, evt_es95, evt_shape_xi, evt_threshold, and evt_exceedance_count.
7. 【肥尾與痛苦結構】Use Kurtosis, Skewness, MDD, UI, TUW, and Calmar. Judge whether the portfolio is psychologically and statistically survivable.
8. 【真正的風險來源排序】Name the top 3 real risks now. Prioritize concentration, rebalance drift, tail fragility, leverage drag, false diversification, and jump/EVT tail underestimation where applicable.
9. 【CRO 最終指令】Give ONE definitive tactical instruction using Buy / Hold / Trim / Cut / Hedge / Raise Cash. The instruction must be logically consistent with the data.
If buffer_blocking_risk_buys = YES, the final tactical instruction must prioritize Raise Cash / Hold / Trim / add hard buffer assets, and must not recommend risk-on accumulation first.


[OUTPUT_FORMAT]
- **[維度名稱]**: [一針見血的解讀與具體調整建議]

[INPUT_DATA]
${JSON.stringify(payload, null, 2)}
`;

            const model_pipeline = ["gemini-3.1-pro-preview", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"];
            let success = false;
            let resultText = "";

            for (const model_name of model_pipeline) {
                try {
                    console.log(`🤖 CRO 嘗試使用模型: ${model_name}...`);
                    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model_name}:generateContent?key=${apiKey}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            contents: [{ parts: [{ text: promptText }] }],
                            generationConfig: { temperature: 0.2 } 
                        })
                    });

                    const data = await response.json();
                    if (data.error) throw new Error(data.error.message);
                    if (data.candidates && data.candidates[0] && data.candidates[0].content) {
                        resultText = data.candidates[0].content.parts[0].text;
                        success = true;
                        
                        const parsedInsight = resultText.split('\n')
                            .filter(line => line.trim().length > 0)
                            .map(line => line.replace(/^[\*\-]\s*/, '').replace(/\*\*/g, ''));
                        
                        croInsight.value = parsedInsight;
                        await supabase.from('portfolio_db').update({ 
                            cro_insight: parsedInsight,
                            cro_last_update: new Date().toISOString()
                        }).eq('id', 1);

                        break; 
                    } else {
                        throw new Error("回傳格式異常");
                    }
                } catch (e) {
                    console.warn(`⚠️ 模型 ${model_name} 失敗: ${e.message}`);
                    if (e.message.includes('API key not valid')) {
                        localStorage.removeItem('GEMINI_API_KEY');
                        alert('API Key 無效，請重新整理網頁後再次輸入。');
                        isCroThinking.value = false;
                        return;
                    }
                }
            }

            if (!success) alert('所有 AI 模型皆無回應或發生錯誤，請稍後再試。');
            isCroThinking.value = false;
        }
        
        function generateAutoViews() {
            const assets = [...mcAvailableAssets.value];
            if (assets.length < 2) {
                alert("需要至少 2 檔合格標的才能進行 AI 動能預測。");
                return;
            }

            blViews.value = [];
            assets.sort((a, b) => parseFloat(b.returnRate) - parseFloat(a.returnRate));
            const strongest = assets[0];
            const weakest = assets[assets.length - 1];

            const expectedOutperformance = ((strongest.stdDev + weakest.stdDev) / 2) * 0.5;
            
            blViews.value.push({
                type: 'relative',
                asset1: strongest.ticker,
                asset2: weakest.ticker,
                value: parseFloat(expectedOutperformance.toFixed(1))
            });

            if (assets.length >= 3) {
                const secondStrongest = assets[1];
                const rf = riskParams.value.rf;
                const rm = riskParams.value.rm;
                const expectedReturn = rf + secondStrongest.beta * (rm - rf) + 3.0;
                
                blViews.value.push({
                    type: 'absolute',
                    asset1: secondStrongest.ticker,
                    asset2: strongest.ticker, 
                    value: parseFloat(expectedReturn.toFixed(1))
                });
            }
        }

        const currentTab = ref('summary');
        const analyticsViewMode = ref('risk');
        const isAiExpanded = ref(false); 
        const isHistoryExpanded = ref(false);
        
        const supabaseUrl = 'https://yrccanqxzrcoknzabifz.supabase.co';
        const supabaseKey = 'sb_publishable_lDfwRDxgMhzRwVk0-Qu3vg_9HTmTFZy';
        const supabase = window.supabase.createClient(supabaseUrl, supabaseKey);

        const isAppReady = ref(false); 
        const showMCModal = ref(false); 
        const mcOptimal = ref(null); 

        const expandedCardTicker = ref(null);
        function toggleCard(ticker) {
            if (expandedCardTicker.value === ticker) {
                expandedCardTicker.value = null;
            } else {
                expandedCardTicker.value = ticker; 
            }
        }

        const isLoggedIn = ref(false);
        const loginEmail = ref('');
        const loginPassword = ref('');
        const loginError = ref('');
        const isAuthenticating = ref(false);

        const checkAuth = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (session) isLoggedIn.value = true;
            else isAppReady.value = true; 
        };

        const handleLogin = async () => {
            isAuthenticating.value = true;
            loginError.value = '';
            const { data, error } = await supabase.auth.signInWithPassword({ email: loginEmail.value, password: loginPassword.value });
            if (error) loginError.value = 'Access Denied: ' + error.message;
            else { isLoggedIn.value = true; isAppReady.value = true; }
            isAuthenticating.value = false;
        };

        const handleLogout = async () => {
            await supabase.auth.signOut();
            window.location.reload();
        };

        onMounted(() => { checkAuth(); });
        
        const isDbSyncing = ref(false); 
        const showHistoryModal = ref(false);
        const isUpdating = ref(false);
        const lastUpdate = ref(null);
        
        const exchangeRate = ref(32.5);
        const sheetUrl = ref('');
        const liquidityBufferRatio = ref(0);
        const chaosMeta = ref(null);
        
        const cloudAiAnalysis = ref(null);
        const correlationMatrix = ref(null);
        const sysCorr = ref(0);

        const fireTargets = ref([
            { age: 28, year: 2032, amount: 5000000 },
            { age: 33, year: 2037, amount: 10000000 },
            { age: 38, year: 2042, amount: 20000000 },
            { age: 43, year: 2047, amount: 35000000 },
            { age: 48, year: 2052, amount: 50000000 }
        ]);

        const riskParams = ref({ rf: 1.5, beta: 1.0, rm: 10.0, sm: 15.0 });
        const quantStartDate = ref(''); 
        const dataFrequency = ref('Weekly');
        const snapshotDate = ref(new Date().toISOString().split('T')[0]); 

        const transactions = ref([]);
        const realHistoryData = ref([]);
        const priceMap = ref({});
        const stockMeta = ref({});

        const stats = ref({ 
            annRet:'0.00', annLogRet:'0.00', mwr:'0.00', annVol:'0.00', sharpe:'0.00', psr: '-', sortino:'0.00', treynor:'0.00', 
            alpha:'0.00', var95:'0.00', cvar95:'0.00', mdd:'0.00', calmar:'0.00', skew:'0.00', kurt:'0.00', 
            tuw: '0', ulcer: '0.00', omega: '0.00', profitFactor: '0.00', 
            ff_alpha: '-', ff_mkt_beta: '-', ff_smb: '-', ff_hml: '-', 
            ff_rmw: '-', ff_cma: '-', ff_wml: '-', ff_r_squared: '-', 
            ff_tw_mkt: '-', ff_crypto: '-'
        });

        async function loadDataFromCloud() {
            isDbSyncing.value = true;
            try {
                const { data, error } = await supabase.from('portfolio_db').select('*').eq('id', 1).single();
                if (error && error.code !== 'PGRST116') throw error;

                if (data) {
                    transactions.value = data.ledger_data || [];
                    realHistoryData.value = data.history_data || [];
                    stockMeta.value = data.stock_meta || {};

                    if (data.macro_meta) {
                        const macroData = data.macro_meta;

    const backendStage = macroData.ai_analysis?.calculated_stage || '';

    if (backendStage === 'expansion') {
        macroRegime.value = 'Bull';       // 狂牛
    } else if (backendStage === 'recession_risk') {
        macroRegime.value = 'Crisis';     // 衰退危機
    } else if (backendStage === 'stagflation' || backendStage === 'tight_liquidity') {
        macroRegime.value = 'Bear';       // 停滯性通膨或流動性緊縮 -> 熊市防守
    } else if (backendStage === 'neutral' || backendStage === 'mixed') {
        macroRegime.value = 'Normal';     // 中性或多空分歧 -> 正常基準
    } else {
        if (macroData.hy_spread > 5.0 && macroData.yield_curve < 0.5) macroRegime.value = 'Crisis';
        else if (macroData.hy_spread > 4.0 || macroData.btc_1m_mom < -15) macroRegime.value = 'Bear';
        else if (macroData.yield_curve > 0 && macroData.hy_spread < 3.5 && macroData.btc_1m_mom > 5) macroRegime.value = 'Bull';
        else macroRegime.value = 'Normal';
    }

                        if (macroData.market_rf) riskParams.value.rf = macroData.market_rf;
                        if (macroData.market_rm) riskParams.value.rm = macroData.market_rm;
                        if (macroData.market_sm) riskParams.value.sm = macroData.market_sm;
                        if (macroData.ai_analysis) cloudAiAnalysis.value = macroData.ai_analysis;
                        if (macroData.corr_matrix) correlationMatrix.value = macroData.corr_matrix;
                        if (macroData.sys_corr) sysCorr.value = macroData.sys_corr;

                        if (macroData.fama_french) {
                            stats.value.ff_alpha = macroData.fama_french.alpha;
                            stats.value.ff_mkt_beta = macroData.fama_french.mkt_beta;
                            stats.value.ff_smb = macroData.fama_french.smb;
                            stats.value.ff_hml = macroData.fama_french.hml;
                            stats.value.ff_rmw = macroData.fama_french.rmw;
                            stats.value.ff_cma = macroData.fama_french.cma;
                            stats.value.ff_wml = macroData.fama_french.wml;
                            stats.value.ff_r_squared = macroData.fama_french.r_squared;
                            stats.value.ff_tw_mkt = macroData.fama_french.tw_mkt;
                            stats.value.ff_crypto = macroData.fama_french.crypto;
                        }
                    }

                    if (data.rebalance_meta) cloudRebalanceMeta.value = data.rebalance_meta;
                    if (data.cro_insight) croInsight.value = data.cro_insight;
                    if (data.chaos_meta) chaosMeta.value = data.chaos_meta;

                    if (data.settings) {
                        if (data.settings.exchangeRate) exchangeRate.value = parseFloat(data.settings.exchangeRate);
                        if (data.settings.sheetUrl) sheetUrl.value = data.settings.sheetUrl;
                        if (data.settings.fireTargets) fireTargets.value = data.settings.fireTargets;
                        if (data.settings.priceMap) priceMap.value = data.settings.priceMap;
                        if (data.settings.liquidityBufferRatio !== undefined && data.settings.liquidityBufferRatio !== null) {
                            liquidityBufferRatio.value = parseFloat(data.settings.liquidityBufferRatio) || 0;
                        }
                    }
                }

                await localforage.setItem('ledgerData', JSON.stringify(transactions.value));
                await localforage.setItem('historyData', JSON.stringify(realHistoryData.value));
                await localforage.setItem('stockMeta', JSON.stringify(stockMeta.value));
                await localforage.setItem('chaosMeta', JSON.stringify(chaosMeta.value));
                await localforage.setItem('settings', JSON.stringify({
                    exchangeRate: exchangeRate.value,
                    sheetUrl: sheetUrl.value,
                    fireTargets: fireTargets.value,
                    priceMap: priceMap.value,
                    liquidityBufferRatio: liquidityBufferRatio.value
                }));

            } catch (err) {
                transactions.value = JSON.parse(await localforage.getItem('ledgerData') || '[]');
                realHistoryData.value = JSON.parse(await localforage.getItem('historyData') || '[]');
                stockMeta.value = JSON.parse(await localforage.getItem('stockMeta') || '{}');
                chaosMeta.value = JSON.parse(await localforage.getItem('chaosMeta') || 'null');

                const localSettings = JSON.parse(await localforage.getItem('settings') || '{}');
                if (localSettings.exchangeRate) exchangeRate.value = localSettings.exchangeRate;
                if (localSettings.sheetUrl) sheetUrl.value = localSettings.sheetUrl;
                if (localSettings.fireTargets) fireTargets.value = localSettings.fireTargets;
                if (localSettings.priceMap) priceMap.value = localSettings.priceMap;
                if (localSettings.liquidityBufferRatio !== undefined && localSettings.liquidityBufferRatio !== null) {
                    liquidityBufferRatio.value = parseFloat(localSettings.liquidityBufferRatio) || 0;
                }
            } finally {
                isDbSyncing.value = false;
                isAppReady.value = true;
                nextTick(() => updateCharts());
            }
        }

        const txForm = ref({
    date: new Date().toISOString().split('T')[0],
    type: 'Buy',
    category: '美股',
    ticker: '',
    price: null,
    shares: null,
    amount: null
});
        const holdingsSearch = ref('');
        const holdingsView = ref('all');
        const holdingsSort = ref('value_desc');
        const txFlowMode = ref('internal');
        const txTypeOptions = computed(() => txFlowMode.value === 'external'
            ? [
                { value: 'Deposit', label: '入金', hint: '外部資金匯入投資帳戶' },
                { value: 'Withdraw', label: '出金', hint: '資金領回銀行 / 生活帳戶' }
            ]
            : [
                { value: 'Buy', label: '買入', hint: '用帳上資金買資產' },
                { value: 'Sell', label: '賣出', hint: '賣掉部位，現金留在投資帳戶' }
            ]
        );

        watch(txFlowMode, (mode) => {
            const nextType = mode === 'external' ? 'Deposit' : 'Buy';
            if (!txTypeOptions.value.some(opt => opt.value === txForm.value.type)) {
                txForm.value.type = nextType;
            }
            if (mode === 'external') {
                txForm.value.ticker = '';
                txForm.value.price = null;
                txForm.value.shares = null;
                if (!txForm.value.amount) txForm.value.amount = null;
            } else {
                txForm.value.amount = null;
            }
        }, { immediate: true });

        watch(() => txForm.value.type, (type) => {
            txFlowMode.value = (type === 'Deposit' || type === 'Withdraw') ? 'external' : 'internal';
        }, { immediate: true });
        
        const historyForm = ref({
            date: new Date().toISOString().split('T')[0],
            assets: null,
            cost: null
        });

        const displayHistory = computed(() => realHistoryData.value);

        watch(displayHistory, (newVal) => {
            if (newVal.length > 0 && !quantStartDate.value) {
                const sorted = [...newVal].sort((a,b) => new Date(a.date) - new Date(b.date));
                quantStartDate.value = sorted[0].date;
            }
        }, { immediate: true });

        function updateMeta(stock) {
            if (stock.ticker) {
                stockMeta.value[stock.ticker] = {
                    ...(stockMeta.value[stock.ticker] || {}),
                    risk: stock.riskLevel,
                    beta: stock.beta,
                    std: stock.stdDev
                };
                saveData();
            }
        }

        async function fetchPrices() {
            if (!sheetUrl.value) { alert('請輸入 Google Sheet 網址'); return; }
            let sheetId = null; let gid = '0';
            const matchId = sheetUrl.value.match(/\/d\/([a-zA-Z0-9-_]+)/);
            const matchGid = sheetUrl.value.match(/[#&?]gid=([0-9]+)/);
            if (matchId && matchId[1]) sheetId = matchId[1]; else { alert('網址錯誤'); return; }
            if (matchGid && matchGid[1]) gid = matchGid[1];
            isUpdating.value = true;
            const gvizUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:csv&gid=${gid}`;
            
            const processCSV = async (csvText) => {
                Papa.parse(csvText, {
                    header: false,
                    complete: async (results) => {
                        let count = 0;
                        results.data.forEach(row => {
                            if (row.length >= 2) {
                                const t = row[0]?.toString().toUpperCase().trim();
                                const p = parseFloat(row[1]);
                                if (t && !isNaN(p)) { 
                                   priceMap.value[t] = p; 
                                   if(t.includes(':')) { const parts = t.split(':'); if(parts.length > 1) priceMap.value[parts[1].trim()] = p; }
                                   count++; 
                                }
                            }
                        });
                        saveData();
                        lastUpdate.value = new Date().toLocaleTimeString();
                        isUpdating.value = false;
                        nextTick(() => updateCharts());
                        alert(`成功更新 ${count} 筆。`);
                    }
                });
            };
            try {
                const res = await fetch(gvizUrl); if(!res.ok) throw new Error('D-Fail'); await processCSV(await res.text());
            } catch (e1) {
                try {
                    const proxyUrl = `https://api.allorigins.win/raw?url=${encodeURIComponent(gvizUrl)}&timestamp=${Date.now()}`;
                    const resP = await fetch(proxyUrl); if(!resP.ok) throw new Error('P-Fail'); await processCSV(await resP.text());
                } catch (e2) { isUpdating.value = false; alert('更新失敗'); }
            }
        }

        const holdingsFlat = computed(() => {
            const map = {};
            transactions.value.forEach(tx => {
                // 🟢 此處設計會自動略過 Deposit 與 Withdraw，確保總成本計算不受影響
                if(!tx.ticker) return; 
                const t = tx.ticker.toUpperCase();
                if(!map[t]) map[t] = { ticker: t, category: tx.category || '台股', shares: 0, totalCostTwd: 0 };
                if(tx.type === 'Buy') { map[t].shares += tx.shares; map[t].totalCostTwd += Math.abs(tx.totalCashFlow); }
                else if(tx.type === 'Sell') { 
                    const avgCost = map[t].shares ? map[t].totalCostTwd / map[t].shares : 0; 
                    map[t].shares -= tx.shares; map[t].totalCostTwd -= avgCost * tx.shares; 
                }
            });
            return Object.values(map).filter(h => h.shares > 0.0001);
        });

        const groupedHoldings = computed(() => {
            const groups = {};
            let grandTotal = 0; 
            const holdingDaysMap = {};
            const today = new Date();
            
            transactions.value.forEach(tx => {
                if(!tx.ticker || tx.type !== 'Buy') return;
                const t = tx.ticker.toUpperCase();
                const txDate = new Date(tx.date);
                const 日Held = Math.max(1, (today - txDate) / (1000 * 60 * 60 * 24)); 
                const investedAmount = Math.abs(tx.totalCashFlow);

                if (!holdingDaysMap[t]) holdingDaysMap[t] = { totalInvested: 0, weightedDaysSum: 0 };
                holdingDaysMap[t].totalInvested += investedAmount;
                holdingDaysMap[t].weightedDaysSum += (investedAmount * 日Held);
            });

            holdingsFlat.value.forEach(h => {
                const rawPrice = priceMap.value[h.ticker];
                let isUSD = (h.category === '美股' || h.category === '加密貨幣');
                let effectiveNativePrice = h.manualPrice || rawPrice || (h.totalCostTwd / h.shares / (isUSD ? exchangeRate.value : 1));
                const currentPriceTwd = effectiveNativePrice * (isUSD ? exchangeRate.value : 1);
                let mvTwd = h.shares * currentPriceTwd;

                grandTotal += mvTwd; 
                if (!groups[h.category]) groups[h.category] = { totalValue: 0, totalCost: 0, items: [] };
                
                const meta = stockMeta.value[h.ticker] || {};
                const cumulativeReturn = h.totalCostTwd ? (mvTwd - h.totalCostTwd) / h.totalCostTwd : 0;
                
                let annualizedReturn = cumulativeReturn; 
                let avgDaysHeld = 0;
                
                if (holdingDaysMap[h.ticker] && holdingDaysMap[h.ticker].totalInvested > 0) {
                    avgDaysHeld = holdingDaysMap[h.ticker].weightedDaysSum / holdingDaysMap[h.ticker].totalInvested;
                    if (avgDaysHeld > 7) {
                        const yearsHeld = avgDaysHeld / 365;
                        annualizedReturn = Math.pow(1 + cumulativeReturn, 1 / yearsHeld) - 1;
                    }
                }
                
                if (annualizedReturn > 5) annualizedReturn = 5;
                if (annualizedReturn < -1) annualizedReturn = -1;

                const rsi = meta.rsi || 50;
                const macdH = meta.macd_h || 0;

                let rsiSignal = '⚖️ 中性'; let rsiColor = 'text-gray-400 border-gray-600';
                if (rsi >= 70) { rsiSignal = '🔥 超買 (>70)'; rsiColor = 'text-red-400 border-red-900/50 bg-red-900/20'; }
                else if (rsi <= 30) { rsiSignal = '🧊 超賣 (<30)'; rsiColor = 'text-green-400 border-green-900/50 bg-green-900/20'; }

                let macdSignal = '無訊號'; let macdColor = 'text-gray-400 border-gray-600';
                if (macdH > 0) { macdSignal = '🟢 黃金交叉'; macdColor = 'text-green-400 border-green-900/50 bg-green-900/20'; }
                else if (macdH < 0) { macdSignal = '🔴 死亡交叉'; macdColor = 'text-red-400 border-red-900/50 bg-red-900/20'; }

                const cloudTargetWeight = meta.target_weight ? (meta.target_weight * 100) : 0;
                let mcWeight = 0;
                if (mcOptimal.value && mcOptimal.value.weights) {
                    const match = mcOptimal.value.weights.find(w => w.ticker === h.ticker);
                    if (match) mcWeight = parseFloat(match.opt);
                }
                let finalBlendedWeight = cloudTargetWeight;
                if (mcOptimal.value) finalBlendedWeight = (cloudTargetWeight * 0.5) + (mcWeight * 0.5);

                const rawLiquidityScore = meta.liquidity_score ?? meta.liquidityScore ?? '-';
                const rawContagionScore = meta.contagion_score ?? meta.contagionScore ?? '-';

                const liquidityScore =
                    typeof rawLiquidityScore === 'number'
                        ? rawLiquidityScore.toFixed(2)
                        : rawLiquidityScore;

                const contagionScore =
                    typeof rawContagionScore === 'number'
                        ? rawContagionScore.toFixed(2)
                        : rawContagionScore;

                const betaRaw = meta.beta;
                const stdRaw = meta.std;
                const betaValue = (
                    betaRaw !== null &&
                    betaRaw !== undefined &&
                    betaRaw !== '' &&
                    Number.isFinite(Number(betaRaw))
                ) ? Number(betaRaw) : 1.0;
                const stdValue = (
                    stdRaw !== null &&
                    stdRaw !== undefined &&
                    stdRaw !== '' &&
                    Number.isFinite(Number(stdRaw))
                ) ? Number(stdRaw) : 20.0;

                groups[h.category].items.push({
                    ...h,
                    isUSD,
                    riskLevel: meta.risk || 'High',
                    // Preserve valid zero values, but do not turn null/blank into zero.
                    beta: betaValue,
                    stdDev: stdValue,
                    betaBenchmark: meta.beta_benchmark || meta.benchmark || '',
                    betaMethod: meta.beta_method || '',
                    liquidityScore,
                    contagionScore,
                    techSignals: {
                        rsiVal: rsi.toFixed(1),
                        rsiText: rsiSignal,
                        rsiColor: rsiColor,
                        macdVal: macdH.toFixed(3),
                        macdText: macdSignal,
                        macdColor: macdColor
                    },
                    fetchedPrice: effectiveNativePrice,
                    avgCostTwd: h.totalCostTwd / h.shares,
                    currentPriceTwd: currentPriceTwd,
                    marketValueTwd: mvTwd,
                    unrealizedPLTwd: mvTwd - h.totalCostTwd,
                    returnRate: cumulativeReturn * 100,
                    annualizedReturnRate: annualizedReturn * 100,
                    targetWeight: cloudTargetWeight,
                    mcWeight: mcWeight,
                    blendedWeight: finalBlendedWeight
                });

                groups[h.category].totalValue += mvTwd;
                groups[h.category].totalCost += h.totalCostTwd;
            });

            for (const cat in groups) {
                let groupTotalInvested = 0;
                let groupWeightedDaysSum = 0;

                groups[cat].items.forEach(item => {
                    item.totalWeight = grandTotal > 0 ? (item.marketValueTwd / grandTotal) : 0;
                    item.isOverweight = item.totalWeight > 0.20; 
                    item.weightGap = item.blendedWeight - (item.totalWeight * 100); 

                    if (holdingDaysMap[item.ticker]) {
                        groupTotalInvested += holdingDaysMap[item.ticker].totalInvested;
                        groupWeightedDaysSum += holdingDaysMap[item.ticker].weightedDaysSum;
                    }
                });
                
                groups[cat].items.sort((a,b) => b.marketValueTwd - a.marketValueTwd);
                groups[cat].unrealizedPL = groups[cat].totalValue - groups[cat].totalCost;
                
                const groupCumulativeReturn = groups[cat].totalCost > 0 ? (groups[cat].unrealizedPL / groups[cat].totalCost) : 0;
                groups[cat].returnRate = groupCumulativeReturn * 100;

                let groupAnnualizedReturn = groupCumulativeReturn; 
                if (groupTotalInvested > 0) {
                    const groupAvgDaysHeld = groupWeightedDaysSum / groupTotalInvested;
                    if (groupAvgDaysHeld > 7) {
                        const groupYearsHeld = groupAvgDaysHeld / 365;
                        groupAnnualizedReturn = Math.pow(1 + groupCumulativeReturn, 1 / groupYearsHeld) - 1;
                    }
                }
                
                if (groupAnnualizedReturn > 5) groupAnnualizedReturn = 5;
                if (groupAnnualizedReturn < -1) groupAnnualizedReturn = -1;

                groups[cat].annualizedReturnRate = groupAnnualizedReturn * 100;
            }
            return groups;
        });

        const categoryTotals = computed(() => { const totals = {}; for(const cat in groupedHoldings.value) totals[cat] = groupedHoldings.value[cat].totalValue; return totals; });
        const riskTotals = computed(() => { let high = 0; let low = 0; for(const cat in groupedHoldings.value) { groupedHoldings.value[cat].items.forEach(item => { if(item.riskLevel === 'Low') low += item.marketValueTwd; else high += item.marketValueTwd; }); } return { High: high, Low: low }; });
        const filteredGroupedHoldings = computed(() => {
            const keyword = (holdingsSearch.value || '').trim().toUpperCase();
            const view = holdingsView.value || 'all';
            const sortKey = holdingsSort.value || 'value_desc';
            const out = {};

            const scoreIsHigh = (val) => {
                const n = Number(val);
                return Number.isFinite(n) && n >= 7;
            };

            const sorter = (a, b) => {
                switch (sortKey) {
                    case 'drift_desc':
                        return Math.abs(b.weightGap || 0) - Math.abs(a.weightGap || 0);
                    case 'pl_desc':
                        return (b.unrealizedPLTwd || 0) - (a.unrealizedPLTwd || 0);
                    case 'return_desc':
                        return (b.returnRate || 0) - (a.returnRate || 0);
                    case 'weight_desc':
                        return (b.totalWeight || 0) - (a.totalWeight || 0);
                    default:
                        return (b.marketValueTwd || 0) - (a.marketValueTwd || 0);
                }
            };

            Object.entries(groupedHoldings.value).forEach(([catName, group]) => {
                let items = [...group.items].filter((stock) => {
                    const matchesKeyword = !keyword || stock.ticker.includes(keyword) || catName.toUpperCase().includes(keyword);
                    if (!matchesKeyword) return false;

                    const drift = Math.abs(stock.weightGap || 0);
                    const isAlert = stock.isOverweight || drift >= 5 || scoreIsHigh(stock.liquidityScore) || scoreIsHigh(stock.contagionScore);

                    if (view === 'alert') return isAlert;
                    if (view === 'overweight') return stock.isOverweight;
                    if (view === 'lowrisk') return stock.riskLevel === 'Low';
                    return true;
                });

                if (!items.length) return;
                items.sort(sorter);

                const totalValue = items.reduce((sum, stock) => sum + (stock.marketValueTwd || 0), 0);
                const totalCost = items.reduce((sum, stock) => sum + (stock.totalCostTwd || 0), 0);
                const unrealizedPL = totalValue - totalCost;
                const returnRate = totalCost > 0 ? (unrealizedPL / totalCost) * 100 : 0;
                const annualizedWeight = items.reduce((sum, stock) => sum + (Number(stock.totalCostTwd) || 0), 0);
                const annualizedReturnRate = annualizedWeight > 0
                    ? items.reduce((sum, stock) => sum + ((Number(stock.totalCostTwd) || 0) * (Number(stock.annualizedReturnRate) || 0)), 0) / annualizedWeight
                    : 0;

                out[catName] = {
                    ...group,
                    items,
                    totalValue,
                    totalCost,
                    unrealizedPL,
                    returnRate,
                    annualizedReturnRate
                };
            });

            return out;
        });
        const filteredHoldingsCount = computed(() => Object.values(filteredGroupedHoldings.value).reduce((sum, group) => sum + group.items.length, 0));
        const holdingsAlertCount = computed(() => {
            let count = 0;
            Object.values(groupedHoldings.value).forEach(group => {
                group.items.forEach(stock => {
                    const drift = Math.abs(stock.weightGap || 0);
                    const scoreIsHigh = (val) => {
                        const n = Number(val);
                        return Number.isFinite(n) && n >= 7;
                    };
                    if (stock.isOverweight || drift >= 5 || scoreIsHigh(stock.liquidityScore) || scoreIsHigh(stock.contagionScore)) count++;
                });
            });
            return count;
        });
        const totalStockValueTwd = computed(() => Object.values(categoryTotals.value).reduce((a,b)=>a+b,0));
        const portfolioStats = ref({ beta: 0, std: 0 });

        // 堅固日期函數（可留可不留；若你後面別處會用到就一起補）
function d2num(dStr) {
    if (!dStr) return 0;
    return parseInt(String(dStr).trim().split('T')[0].replace(/-/g, ''), 10);
}

// 只認外部出入金（可留可不留；主要給績效/現金流口徑用）
function getTxFlow(tx) {
    const tType = String(tx.type || '').toLowerCase();

    if (
        !tType.includes('deposit') &&
        !tType.includes('withdraw') &&
        !tType.includes('入金') &&
        !tType.includes('出金')
    ) {
        return 0;
    }

    let amt = 0;
    if (tx.amount) {
        amt = Math.abs(Number(String(tx.amount).replace(/,/g, '')) || 0);
    } else if (tx.totalCashFlow !== undefined && tx.totalCashFlow !== null) {
        amt = Math.abs(Number(String(tx.totalCashFlow).replace(/,/g, '')) || 0);
    }

    return (tType.includes('withdraw') || tType.includes('出')) ? -amt : amt;
}

// 真實現金池：Deposit +, Withdraw -, Buy -, Sell +, Expense -
const CASH_EPS = 0.01;

const cashBalance = computed(() => {
    const raw = transactions.value.reduce((sum, tx) => {
        let flow = Number(tx.totalCashFlow) || 0;
        if (String(tx.type).toLowerCase() === 'expense') flow = -Math.abs(flow);
        return sum + flow;
    }, 0);

    // 避免浮點殘差造成 NT$ -0 / 假性負現金
    return Math.abs(raw) < CASH_EPS ? 0 : raw;
});

const totalPortfolioNav = computed(() => {
    const safeCash = Math.max(0, cashBalance.value);
    return totalStockValueTwd.value + safeCash;
});

const isCashNegative = computed(() => cashBalance.value < -CASH_EPS);
const isCashTooHigh = computed(() => totalPortfolioNav.value > 0 && cashBalance.value > totalPortfolioNav.value * 0.5);
const isCashAlert = computed(() => isCashNegative.value || isCashTooHigh.value);
        watch([groupedHoldings, totalStockValueTwd], () => {
            let totalBeta = 0; let totalStd = 0; const totalVal = totalStockValueTwd.value;
            if(totalVal > 0) {
                for(const cat in groupedHoldings.value) {
                   groupedHoldings.value[cat].items.forEach(item => {
                        const weight = item.marketValueTwd / totalVal;
                        totalBeta += weight * item.beta; totalStd += weight * item.stdDev;
                    });
                }
            }
            portfolioStats.value = { beta: totalBeta.toFixed(2), std: totalStd.toFixed(2) };
            if(Math.abs(riskParams.value.beta - totalBeta) >= 0.01) riskParams.value.beta = parseFloat(totalBeta.toFixed(2));
        }, { deep: true, immediate: true });

        const totalStockCostTwd = computed(() => holdingsFlat.value.reduce((sum, h) => sum + h.totalCostTwd, 0));
        const totalStockUnrealizedPL = computed(() => totalStockValueTwd.value - totalStockCostTwd.value);
        const totalStockReturnRate = computed(() => totalStockCostTwd.value ? ((totalStockUnrealizedPL.value/totalStockCostTwd.value)*100).toFixed(2) : 0);
        
        // 🟢 修正 3：讓 Ledger (交易流水帳) 正確依據日期排序，避免順序錯亂
        const reversedTransactions = computed(() => {
            return [...transactions.value].sort((a, b) => new Date(b.date) - new Date(a.date));
        });

        const filteredHistory = computed(() => {
            const data = displayHistory.value;
            if(!quantStartDate.value) return data;
            return data.filter(h => new Date(h.date) >= new Date(quantStartDate.value));
        });

        // 🟢 修正 4: 終極 TWR 計算 (完全從 Ledger 讀取現金流，不需手動輸入)
        const enrichedHistory = computed(() => {
            const sorted = [...filteredHistory.value].sort((a, b) => new Date(a.date) - new Date(b.date));

            return sorted.map((item, index) => {
                let dailyReturn = null;
                let periodExternalFlow = 0;

                if (index > 0) {
                    const prev = sorted[index - 1];
                    const prevDate = new Date(prev.date);
                    const currDate = new Date(item.date);

                    // 自動掃描 Ledger，找出這段期間內的真實外部出入金
                    transactions.value.forEach(tx => {
                        if (tx.type === 'Deposit' || tx.type === 'Withdraw') {
                            const txDate = new Date(tx.date);
                            // 若這筆出入金發生在前一次快照(不含)與本次快照(含)之間
                            if (txDate > prevDate && txDate <= currDate) {
                                periodExternalFlow += Number(tx.totalCashFlow || 0);
                            }
                        }
                    });

                    // 真正純淨的 TWR：期末 NAV 扣除此期間的外部淨流入後，去除以期初 NAV
                    dailyReturn = prev.assets > 0
                        ? ((item.assets - periodExternalFlow) / prev.assets) - 1
                        : 0;
                }

                return {
                    ...item,
                    dailyReturn,
                    withdrawal: -periodExternalFlow, // 為了相容你的 UI 欄位
                    computedFlow: periodExternalFlow
                };
            }).reverse();
        });

        const stressTestResults = computed(() => {
            const currentBeta = parseFloat(portfolioStats.value.beta) || 1.0;
            const historicalScenarios = [
                { name: '2008 金融海嘯 (Lehman)', desc: '次貸風暴，系統性流動性枯竭', benchDrop: -50.9 },
                { name: '2000 達康泡沫 (Dot-com)', desc: '網路科技股本夢比估值破滅', benchDrop: -49.1 },
                { name: '2020 新冠鎔斷 (COVID-19)', desc: '疫情爆發恐慌，全球經濟瞬間停擺', benchDrop: -33.9 },
                { name: '2022 暴力升息 (Rate Hikes)', desc: '通膨失控，聯準會急升息狂殺估值', benchDrop: -25.4 }
            ];

            return historicalScenarios.map(scenario => {
                let expectedDrop = scenario.benchDrop * currentBeta;
                if (expectedDrop < -100) expectedDrop = -100;

                return {
                    ...scenario,
                    portDrop: expectedDrop.toFixed(1),
                    valueLost: (totalStockValueTwd.value * Math.abs(expectedDrop) / 100)
                };
            });
        });

        function xnpv(rate, cashflows) {
            if (rate <= -0.999999) return Infinity;
            const d0 = new Date(cashflows[0].date);
            return cashflows.reduce((sum, cf) => {
                const dt = (new Date(cf.date) - d0) / (1000 * 60 * 60 * 24);
                return sum + cf.amount / Math.pow(1 + rate, dt / 365.25);
            }, 0);
        }

        function dxnpv(rate, cashflows) {
            if (rate <= -0.999999) return Infinity;
            const d0 = new Date(cashflows[0].date);
            return cashflows.reduce((sum, cf) => {
                const dt = (new Date(cf.date) - d0) / (1000 * 60 * 60 * 24);
                const yr = dt / 365.25;
                return sum - (yr * cf.amount) / Math.pow(1 + rate, yr + 1);
            }, 0);
        }

        function xirr(cashflows, guess = 0.1) {
            let rate = guess;

            for (let i = 0; i < 100; i++) {
                const f = xnpv(rate, cashflows);
                const df = dxnpv(rate, cashflows);

                if (!Number.isFinite(f) || !Number.isFinite(df) || Math.abs(df) < 1e-12) break;

                const next = rate - f / df;
                if (Math.abs(next - rate) < 1e-10) return next;
                rate = next;
            }

            let low = -0.9999;
            let high = 10.0;
            let fLow = xnpv(low, cashflows);
            let fHigh = xnpv(high, cashflows);

            if (!Number.isFinite(fLow) || !Number.isFinite(fHigh) || fLow * fHigh > 0) return null;

            for (let i = 0; i < 200; i++) {
                const mid = (low + high) / 2;
                const fMid = xnpv(mid, cashflows);

                if (Math.abs(fMid) < 1e-10) return mid;
                if (fLow * fMid < 0) {
                    high = mid;
                    fHigh = fMid;
                } else {
                    low = mid;
                    fLow = fMid;
                }
            }

            return (low + high) / 2;
        }

        watch([enrichedHistory, riskParams, dataFrequency], () => {
             const h = [...enrichedHistory.value].reverse(); 
             
             if (h.length < 3) return;

             const returns = h.slice(1).map(item => item.dailyReturn);

let cumIndex = 1.0; let peakIndex = 1.0; let maxDrawdown = 0;
let peakDate = new Date(h[0].date); let maxTuwDays = 0; let sqDrawdownSum = 0;

returns.forEach((r, idx) => {
    cumIndex = cumIndex * (1 + r);
    const currentDate = new Date(h[idx + 1].date); 
    if (cumIndex > peakIndex) { peakIndex = cumIndex; peakDate = currentDate; } 
    else {
        const tuw = (currentDate - peakDate) / (1000 * 60 * 60 * 24);
        if (tuw > maxTuwDays) maxTuwDays = tuw;
    }
    const dd = peakIndex > 0 ? (peakIndex - cumIndex) / peakIndex : 0;
    if (dd > maxDrawdown) maxDrawdown = dd; 
    sqDrawdownSum += Math.pow(dd * 100, 2);
});

const totalDays = (new Date(h[h.length - 1].date) - new Date(h[0].date)) / (1000 * 60 * 60 * 24);
const years = totalDays > 0 ? totalDays / 365.25 : 0;
const periodsPerYear = years > 0 ? (returns.length / years) : 52.0;

const cumTwr = returns.reduce((acc, r) => acc * (1 + r), 1) - 1;
const annRet = years > 0 ? (Math.pow(1 + cumTwr, 1 / years) - 1) : 0;
const annLogRet = years > 0 ? (Math.log(1 + cumTwr) / years) : 0;
const factor = Math.sqrt(periodsPerYear);

// 🟢 修正 5: 真 MWR / XIRR (直接讀取 Ledger，無損精準還原)
let mwr = null;
const cashflows = [];

if (h.length >= 2) {
    const startDate = new Date(h[0].date);
    const endDate = new Date(h[h.length - 1].date);

    // 1. 用樣本起點 NAV 當作初始投入 (對投資人而言是流出，故轉為負)
    cashflows.push({
        date: h[0].date,
        amount: -(Number(h[0].assets) || 0)
    });

    // 2. 中間只吃「真實 Ledger 外部出入金」
    transactions.value.forEach(tx => {
        if (tx.type === 'Deposit' || tx.type === 'Withdraw') {
            const txDate = new Date(tx.date);
            if (txDate > startDate && txDate <= endDate) {
                // 入金(+) 對投資人是流出(-); 出金(-) 對投資人是流入(+)
                cashflows.push({
                    date: tx.date,
                    amount: -Number(tx.totalCashFlow || 0)
                });
            }
        }
    });

    // 3. 期末 NAV 視為最終結算收回
    cashflows.push({
        date: endDate,
        amount: Number(h[h.length - 1].assets || 0)
    });

    // 將同一天的現金流合併，避免 XIRR 引擎報錯
    const consolidated = {};
    cashflows.forEach(cf => {
        consolidated[cf.date] = (consolidated[cf.date] || 0) + cf.amount;
    });
    
    const finalCf = Object.keys(consolidated).map(d => ({ date: d, amount: consolidated[d] }));

    mwr = xirr(finalCf, 0.10);
}

const avgR = returns.reduce((a, b) => a + b, 0) / returns.length;
const stdSample = Math.sqrt(
    returns.reduce((a, b) => a + Math.pow(b - avgR, 2), 0) / (returns.length - 1)
);
const annVol = stdSample * factor || 0;
const rf = riskParams.value.rf / 100;
const rm = riskParams.value.rm / 100;
const beta = riskParams.value.beta || 1;

const sharpe = annVol > 0 ? (annRet - rf) / annVol : 0;
const treynor = beta !== 0 ? (annRet - rf) / beta : 0;

const downsideReturns = returns.filter(r => r < 0);
const downsideDev = Math.sqrt(
    downsideReturns.length > 0
        ? downsideReturns.reduce((a, b) => a + Math.pow(b, 2), 0) / returns.length
        : 0
) * factor;
const sortino = downsideDev > 0 ? (annRet - rf) / downsideDev : 0;

const calmar = Math.abs(maxDrawdown) > 0 ? annRet / Math.abs(maxDrawdown) : 0;

const ulcerIndex = Math.sqrt(sqDrawdownSum / returns.length) || 0;

const sumGainsAbs = returns.filter(r => r > 0).reduce((a, b) => a + b, 0);
const sumLossesAbs = Math.abs(returns.filter(r => r < 0).reduce((a, b) => a + b, 0));
const profitFactor = sumLossesAbs === 0 ? (sumGainsAbs > 0 ? 999 : 0) : (sumGainsAbs / sumLossesAbs);

const rf_period = rf / periodsPerYear;
const omegaGains = returns.reduce((a, r) => a + Math.max(r - rf_period, 0), 0);
const omegaLosses = returns.reduce((a, r) => a + Math.max(rf_period - r, 0), 0);
const omegaRatio = omegaLosses === 0 ? (omegaGains > 0 ? 999 : 0) : (omegaGains / omegaLosses);

const expectedRet = rf + beta * (rm - rf);
const alpha = annRet - expectedRet;

const sortedReturns = [...returns].sort((a, b) => a - b);
const idx95 = Math.floor(sortedReturns.length * 0.05);
const var95 = sortedReturns[idx95] || 0;

let cvar95 = 0;
if (idx95 > 0) {
    const worstReturns = sortedReturns.slice(0, idx95);
    cvar95 = worstReturns.reduce((a, b) => a + b, 0) / worstReturns.length;
} else {
    cvar95 = var95;
}

const n = returns.length;
const stdPop = Math.sqrt(returns.reduce((a, b) => a + Math.pow(b - avgR, 2), 0) / n) || 1;
let sumCubed = 0;
let sumQuart = 0;
returns.forEach(r => {
    sumCubed += Math.pow(r - avgR, 3);
    sumQuart += Math.pow(r - avgR, 4);
});

let skewVal = (sumCubed / n) / Math.pow(stdPop, 3);
let kurtVal = (sumQuart / n) / Math.pow(stdPop, 4) - 3;

if (isNaN(skewVal)) skewVal = 0;
if (isNaN(kurtVal)) kurtVal = 0;

const sampleN = returns.length;
const periodSharpe = sharpe / factor; 

const psr_hist = computePSR({
    sr: periodSharpe, 
    srBenchmark: 0,
    skew: skewVal,
    exKurt: kurtVal,
    nObs: sampleN
});

             stats.value = { 
                 annRet: (annRet*100).toFixed(2), 
                 annLogRet: (annLogRet*100).toFixed(2), 
                 mwr: mwr === null ? '-' : (mwr * 100).toFixed(2),            
                 annVol: (annVol*100).toFixed(2), 
                 sharpe: sharpe.toFixed(2), 
                 psr: psr_hist === null ? '-' : (psr_hist * 100).toFixed(2), 
                 sortino: sortino.toFixed(2), 
                 treynor: treynor.toFixed(4),            
                 alpha: (alpha * 100).toFixed(2),
                 var95: (var95 * 100).toFixed(2),
                 cvar95: (cvar95 * 100).toFixed(2), 
                 mdd: (maxDrawdown * 100).toFixed(2), 
                 calmar: calmar.toFixed(2), 
                 skew: skewVal.toFixed(2),
                 kurt: kurtVal.toFixed(2),
                 tuw: Math.round(maxTuwDays).toString(),
                 ulcer: ulcerIndex.toFixed(2),
                 omega: omegaRatio > 100 ? '∞' : Number(omegaRatio).toFixed(2),
                 profitFactor: profitFactor > 100 ? '∞' : Number(profitFactor).toFixed(2),
                 
                 ff_alpha: stats.value.ff_alpha || '-',
                 ff_mkt_beta: stats.value.ff_mkt_beta || '-',
                 ff_smb: stats.value.ff_smb || '-',
                 ff_hml: stats.value.ff_hml || '-',
                 ff_rmw: stats.value.ff_rmw || '-',
                 ff_cma: stats.value.ff_cma || '-',
                 ff_wml: stats.value.ff_wml || '-', 
                 ff_tw_mkt: stats.value.ff_tw_mkt || '-', 
                 ff_crypto: stats.value.ff_crypto || '-', 
                 ff_r_squared: stats.value.ff_r_squared || '-'
             };

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

       const syntheticRiskMeta = computed(() => {
    const meta = stockMeta.value?.__synthetic_portfolio_risk__;
    return meta && typeof meta === 'object' ? meta : null;
});

       const optimizerDependencyStatus = computed(() => {
    const meta = stockMeta.value?.__optimizer_dependency_status__;
    return meta && typeof meta === 'object' ? meta : null;
});

       const optimizerDependencyPackages = computed(() => {
    const packages = optimizerDependencyStatus.value?.packages || {};
    return Object.keys(packages).map((key) => ({ key, ...packages[key] }));
});

       const optimizerSandboxOutput = ref(null);
       const optimizerSandboxError = ref('');

       async function loadOptimizerSandboxOutput() {
    try {
        optimizerSandboxError.value = '';
        const response = await fetch(`data/optimizer/skfolio_sandbox_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            optimizerSandboxOutput.value = null;
            optimizerSandboxError.value = `尚未讀到 skfolio sandbox output (${response.status})`;
            return;
        }
        const data = await response.json();
        optimizerSandboxOutput.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        optimizerSandboxOutput.value = null;
        optimizerSandboxError.value = err?.message || String(err);
    }
}

       const optimizerSandboxPortfolios = computed(() => {
    const portfolios = optimizerSandboxOutput.value?.portfolios || {};
    return Object.keys(portfolios).map((key) => {
        const p = portfolios[key] || {};
        const m = p.metrics || {};
        return {
            key,
            label: key,
            status: p.status || 'N/A',
            annual_vol_pct: m.annual_vol_pct ?? null,
            var95_pct: m.var95_pct ?? null,
            es95_pct: m.es95_pct ?? null,
            max_drawdown_pct: m.max_drawdown_pct ?? null,
            sharpe: m.sharpe ?? null,
            turnover_vs_current_pct: p.turnover_vs_current_pct ?? null,
            weights: Array.isArray(p.weights) ? p.weights : [],
            method: p.method || {}
        };
    });
});

       const optimizerSandboxBestByES = computed(() => {
    return optimizerSandboxPortfolios.value
        .filter((p) => p.status === 'OK' && Number.isFinite(Number(p.es95_pct)))
        .slice()
        .sort((a, b) => Number(a.es95_pct) - Number(b.es95_pct))[0] || null;
});

       const optimizerSandboxSkfolioWeights = computed(() => {
    const p = optimizerSandboxOutput.value?.portfolios?.skfolio_min_variance;
    return Array.isArray(p?.weights) ? p.weights : [];
});

       const optimizerSandboxCvarWeights = computed(() => {
    const p = optimizerSandboxOutput.value?.portfolios?.skfolio_cvar_minimize;
    return Array.isArray(p?.weights) ? p.weights : [];
});

       const optimizerIntegratedComparison = computed(() => {
    const current = optimizerSandboxOutput.value?.portfolios?.current_weight?.metrics || {};
    const hrp = syntheticRiskMeta.value?.risk_budgeting || {};
    const componentEsRows = syntheticRiskMeta.value?.component_tail_risk?.var_es_95?.rows || [];
    const topTail = Array.isArray(componentEsRows) && componentEsRows.length ? componentEsRows[0] : null;

    return optimizerSandboxPortfolios.value.map((p) => {
        const volDelta = Number.isFinite(Number(p.annual_vol_pct)) && Number.isFinite(Number(current.annual_vol_pct))
            ? Number(p.annual_vol_pct) - Number(current.annual_vol_pct)
            : null;
        const esDelta = Number.isFinite(Number(p.es95_pct)) && Number.isFinite(Number(current.es95_pct))
            ? Number(p.es95_pct) - Number(current.es95_pct)
            : null;
        const mddDelta = Number.isFinite(Number(p.max_drawdown_pct)) && Number.isFinite(Number(current.max_drawdown_pct))
            ? Number(p.max_drawdown_pct) - Number(current.max_drawdown_pct)
            : null;
        return {
            ...p,
            vol_delta_vs_current_pct: volDelta === null ? null : Number(volDelta.toFixed(2)),
            es_delta_vs_current_pct: esDelta === null ? null : Number(esDelta.toFixed(3)),
            mdd_delta_vs_current_pct: mddDelta === null ? null : Number(mddDelta.toFixed(2)),
            hrp_lite_vol_pct: hrp.hrp_lite_portfolio_ewma_vol_pct ?? null,
            top_tail_ticker: topTail?.ticker ?? null,
            top_tail_es_share_pct: topTail?.component_es_share_pct ?? null
        };
    });
});

       const riskfolioSandboxOutput = ref(null);
       const riskfolioSandboxError = ref('');

       async function loadRiskfolioSandboxOutput() {
    try {
        riskfolioSandboxError.value = '';
        const response = await fetch(`data/optimizer/riskfolio_sandbox_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            riskfolioSandboxOutput.value = null;
            riskfolioSandboxError.value = `尚未讀到 Riskfolio sandbox output (${response.status})`;
            return;
        }
        const data = await response.json();
        riskfolioSandboxOutput.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        riskfolioSandboxOutput.value = null;
        riskfolioSandboxError.value = err?.message || String(err);
    }
}

       const riskfolioSandboxPortfolios = computed(() => {
    const portfolios = riskfolioSandboxOutput.value?.portfolios || {};
    return Object.keys(portfolios).map((key) => {
        const p = portfolios[key] || {};
        const m = p.metrics || {};
        return {
            key,
            label: key,
            source: key.startsWith('riskfolio_') ? 'Riskfolio-Lib' : 'Baseline',
            status: p.status || 'N/A',
            annual_vol_pct: m.annual_vol_pct ?? null,
            var95_pct: m.var95_pct ?? null,
            es95_pct: m.es95_pct ?? null,
            max_drawdown_pct: m.max_drawdown_pct ?? null,
            sharpe: m.sharpe ?? null,
            turnover_vs_current_pct: p.turnover_vs_current_pct ?? null,
            weights: Array.isArray(p.weights) ? p.weights : [],
            method: p.method || {}
        };
    });
});

       function normalizeOptimizerRow(p, source, currentMetrics) {
    const volDelta = Number.isFinite(Number(p.annual_vol_pct)) && Number.isFinite(Number(currentMetrics.annual_vol_pct))
        ? Number(p.annual_vol_pct) - Number(currentMetrics.annual_vol_pct)
        : null;
    const esDelta = Number.isFinite(Number(p.es95_pct)) && Number.isFinite(Number(currentMetrics.es95_pct))
        ? Number(p.es95_pct) - Number(currentMetrics.es95_pct)
        : null;
    const mddDelta = Number.isFinite(Number(p.max_drawdown_pct)) && Number.isFinite(Number(currentMetrics.max_drawdown_pct))
        ? Number(p.max_drawdown_pct) - Number(currentMetrics.max_drawdown_pct)
        : null;

    const turnoverNum = Number(p.turnover_vs_current_pct);
    let verdict = '觀察';
    if (p.status !== 'OK') {
        verdict = '失敗';
    } else if (Number.isFinite(turnoverNum) && turnoverNum >= 80) {
        verdict = '高換手';
    } else if (esDelta !== null && esDelta < 0 && volDelta !== null && volDelta < 0) {
        verdict = '風險降低';
    } else if (esDelta !== null && esDelta < 0) {
        verdict = '尾部改善';
    } else if (esDelta !== null && esDelta > 0) {
        verdict = '尾部變差';
    }

    return {
        ...p,
        source,
        vol_delta_vs_current_pct: volDelta === null ? null : Number(volDelta.toFixed(2)),
        es_delta_vs_current_pct: esDelta === null ? null : Number(esDelta.toFixed(3)),
        mdd_delta_vs_current_pct: mddDelta === null ? null : Number(mddDelta.toFixed(2)),
        verdict
    };
}

       const unifiedOptimizerComparison = computed(() => {
    const skfolioRows = optimizerSandboxPortfolios.value || [];
    const riskfolioRows = riskfolioSandboxPortfolios.value || [];
    const currentMetrics =
        optimizerSandboxOutput.value?.portfolios?.current_weight?.metrics ||
        riskfolioSandboxOutput.value?.portfolios?.current_weight?.metrics ||
        {};

    const keepSkfolio = new Set([
        'current_weight',
        'inverse_vol_baseline',
        'scipy_min_variance_fallback',
        'skfolio_min_variance',
        'skfolio_cvar_minimize'
    ]);
    const keepRiskfolio = new Set([
        'riskfolio_min_variance',
        'riskfolio_cvar_minimize',
        'riskfolio_risk_parity_mv',
        'riskfolio_hrp_mv'
    ]);

    const rows = [];

    skfolioRows.forEach((p) => {
        if (keepSkfolio.has(p.key)) {
            rows.push(normalizeOptimizerRow(p, p.key.startsWith('skfolio_') ? 'skfolio' : 'baseline', currentMetrics));
        }
    });

    riskfolioRows.forEach((p) => {
        if (keepRiskfolio.has(p.key)) {
            rows.push(normalizeOptimizerRow(p, 'Riskfolio-Lib', currentMetrics));
        }
    });

    const rb = syntheticRiskMeta.value?.risk_budgeting || {};
    if (rb && rb.status === 'OK') {
        rows.push({
            key: 'hrp_lite_v06',
            label: 'hrp_lite_v06',
            source: 'v0.6 internal',
            status: 'OK',
            annual_vol_pct: rb.hrp_lite_portfolio_ewma_vol_pct ?? null,
            var95_pct: null,
            es95_pct: null,
            max_drawdown_pct: null,
            sharpe: null,
            turnover_vs_current_pct: null,
            vol_delta_vs_current_pct: null,
            es_delta_vs_current_pct: null,
            mdd_delta_vs_current_pct: null,
            verdict: '內建基準',
            weights: Array.isArray(rb.rows) ? rb.rows : []
        });
    }

    return rows;
});

       const unifiedOptimizerBestByES = computed(() => {
    return unifiedOptimizerComparison.value
        .filter((p) => p.status === 'OK' && Number.isFinite(Number(p.es95_pct)))
        .slice()
        .sort((a, b) => Number(a.es95_pct) - Number(b.es95_pct))[0] || null;
});

       const riskfolioMinVarWeights = computed(() => {
    const p = riskfolioSandboxOutput.value?.portfolios?.riskfolio_min_variance;
    return Array.isArray(p?.weights) ? p.weights : [];
});

       const riskfolioCvarWeights = computed(() => {
    const p = riskfolioSandboxOutput.value?.portfolios?.riskfolio_cvar_minimize;
    return Array.isArray(p?.weights) ? p.weights : [];
});

       const selectedOptimizerBufferCandidateKey = ref('');

       function optimizerBufferWeightRows(candidate) {
    if (!candidate || candidate.status !== 'OK') return [];

    if (candidate.key === 'hrp_lite_v06') {
        return (candidate.weights || []).map((row) => {
            const current = Number(row.current_weight_pct ?? 0);
            const target = Number(row.hrp_lite_weight_pct ?? row.weight_pct ?? current);
            return {
                ticker: row.ticker,
                current_weight_pct: current,
                target_weight_pct: target
            };
        }).filter((row) => row.ticker);
    }

    return (candidate.weights || []).map((row) => {
        const current = Number(row.current_weight_pct ?? 0);
        const target = Number(row.weight_pct ?? current);
        return {
            ticker: row.ticker,
            current_weight_pct: current,
            target_weight_pct: target
        };
    }).filter((row) => row.ticker);
}

       function buildTradeBufferCandidate(candidate) {
    const base = Number(tradeBufferBasePct?.value || 3);
    const addDisabled = !!tradeBufferProfile?.value?.addDisabled;
    const nav = Number(totalPortfolioNav?.value || totalStockValueTwd?.value || 0);
    const rowsRaw = optimizerBufferWeightRows(candidate);

    let addCount = 0;
    let trimCount = 0;
    let holdCount = 0;
    let pendingCount = 0;
    let rawAbsGapSum = 0;
    let bufferedAbsGapSum = 0;

    const rows = rowsRaw.map((row) => {
        const current = Number(row.current_weight_pct || 0);
        const target = Number(row.target_weight_pct || 0);
        const drift = target - current;
        rawAbsGapSum += Math.abs(drift);

        let bucket = 'hold';
        let action = 'HOLD';
        let actionZh = '暫不動';
        let reason = `差距 ${drift.toFixed(2)}%，仍在 ±${base.toFixed(1)}% No-Trade Zone 內。`;
        let actionClass = 'text-slate-300 bg-slate-500/10 border-slate-500/20';
        let bufferedTarget = current;

        if (drift <= -base) {
            bucket = 'trim';
            action = 'TRIM';
            actionZh = '減碼';
            reason = `低於 Trim 門檻：${drift.toFixed(2)}% ≤ -${base.toFixed(1)}%。`;
            actionClass = 'text-red-300 bg-red-500/10 border-red-500/20';
            bufferedTarget = target;
            trimCount += 1;
        } else if (drift >= base && addDisabled) {
            bucket = 'pending';
            action = 'PENDING_ADD';
            actionZh = '候補加碼';
            reason = `超過 Add 門檻，但 CRO_VETO 啟動，只列候補不執行。`;
            actionClass = 'text-amber-300 bg-amber-500/10 border-amber-500/20';
            bufferedTarget = current;
            pendingCount += 1;
        } else if (drift >= base) {
            bucket = 'add';
            action = 'ADD';
            actionZh = '加碼';
            reason = `高於 Add 門檻：${drift.toFixed(2)}% ≥ +${base.toFixed(1)}%。`;
            actionClass = 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20';
            bufferedTarget = target;
            addCount += 1;
        } else {
            holdCount += 1;
        }

        const bufferedGap = bufferedTarget - current;
        bufferedAbsGapSum += Math.abs(bufferedGap);

        return {
            ticker: row.ticker,
            current_weight_pct: Number(current.toFixed(3)),
            target_weight_pct: Number(target.toFixed(3)),
            buffered_target_weight_pct: Number(bufferedTarget.toFixed(3)),
            drift_pct: Number(drift.toFixed(3)),
            action,
            action_zh: actionZh,
            bucket,
            reason,
            actionClass,
            action_value_twd: Math.round(nav * Math.abs(bufferedGap) / 100),
            raw_action_value_twd: Math.round(nav * Math.abs(drift) / 100),
            no_trade_zone_low_pct: Number((current - base).toFixed(3)),
            no_trade_zone_high_pct: Number((current + base).toFixed(3))
        };
    }).sort((a, b) => Math.abs(b.drift_pct) - Math.abs(a.drift_pct));

    const rawTurnover = Number((rawAbsGapSum / 2).toFixed(2));
    const bufferedTurnover = Number((bufferedAbsGapSum / 2).toFixed(2));
    const turnoverReduction = Number((rawTurnover - bufferedTurnover).toFixed(2));

    return {
        key: candidate.key,
        label: candidate.label || candidate.key,
        source: candidate.source || '-',
        status: candidate.status || 'N/A',
        verdict: candidate.verdict || '-',
        base_buffer_pct: base,
        trim_threshold_pct: base,
        add_threshold_pct: addDisabled ? null : base,
        add_disabled: addDisabled,
        raw_turnover_pct: Number(Number(candidate.turnover_vs_current_pct ?? rawTurnover).toFixed(2)),
        buffer_turnover_pct: bufferedTurnover,
        turnover_reduction_pct: turnoverReduction,
        add_count: addCount,
        trim_count: trimCount,
        hold_count: holdCount,
        pending_count: pendingCount,
        active_count: addCount + trimCount,
        rows
    };
}

       const optimizerBufferCandidateSummaries = computed(() => {
    const exclude = new Set(['current_weight']);
    return (unifiedOptimizerComparison.value || [])
        .filter((candidate) => candidate && candidate.status === 'OK' && !exclude.has(candidate.key))
        .filter((candidate) => Array.isArray(candidate.weights) && candidate.weights.length)
        .map(buildTradeBufferCandidate)
        .sort((a, b) => {
            const ar = Number(a.buffer_turnover_pct ?? 999);
            const br = Number(b.buffer_turnover_pct ?? 999);
            if (ar !== br) return ar - br;
            return String(a.label).localeCompare(String(b.label));
        });
});

       const selectedOptimizerBufferCandidate = computed(() => {
    const list = optimizerBufferCandidateSummaries.value || [];
    if (!list.length) return null;
    const selected = selectedOptimizerBufferCandidateKey.value
        ? list.find((x) => x.key === selectedOptimizerBufferCandidateKey.value)
        : null;
    if (selected) return selected;

    const bestEs = unifiedOptimizerBestByES.value?.key;
    if (bestEs) {
        const best = list.find((x) => x.key === bestEs);
        if (best) return best;
    }
    return list[0];
});

       const selectedOptimizerBufferRows = computed(() => {
    return selectedOptimizerBufferCandidate.value?.rows || [];
});

       const optimizerBufferActionSummary = computed(() => {
    const c = selectedOptimizerBufferCandidate.value;
    if (!c) {
        return { add: 0, trim: 0, hold: 0, pending: 0, active: 0 };
    }
    return {
        add: c.add_count || 0,
        trim: c.trim_count || 0,
        hold: c.hold_count || 0,
        pending: c.pending_count || 0,
        active: c.active_count || 0
    };
});

       function setOptimizerBufferCandidate(key) {
    selectedOptimizerBufferCandidateKey.value = key;
}


       function optimizerPolicyBucket(ticker) {
    const t = String(ticker || '').toUpperCase();
    if (!t) return 'other';
    if (t === 'BOXX' || t.includes('CASH')) return 'cash';
    if (t === 'GLDM' || t === 'GLD' || t.includes('GOLD')) return 'gold';
    if (t === 'BTC-USD' || t === 'ETH-USD' || t.includes('BTC') || t.includes('ETH') || t.includes('加密')) return 'crypto';
    if (/^[0-9]{4}[A-Z]?$/.test(t) || t === '2330' || t.includes('台灣')) return 'taiwan';
    if (['GRID', 'IFRA', 'PICK', 'SRVR', 'VNM'].includes(t)) return 'theme';
    if (['QQQ', 'VOO', 'VTI', 'AVUV', 'USMV'].includes(t)) return 'us_equity';
    if (['VEA'].includes(t)) return 'intl_equity';
    return 'other';
}

       const optimizerConstraintRules = computed(() => [
    { key: 'single_max', label: '單檔上限', limit: '≤ 20%', severity: 'VIOLATION' },
    { key: 'taiwan_max', label: '台股總上限', limit: '≤ 40%', severity: 'VIOLATION' },
    { key: 'crypto_max', label: '加密總上限', limit: '≤ 15%', severity: 'VIOLATION' },
    { key: 'gold_band', label: 'GLDM 黃金區間', limit: '3%–7%', severity: 'WARNING' },
    { key: 'cash_floor', label: 'BOXX / 類現金下限', limit: '≥ 3%', severity: 'WARNING' },
    { key: 'theme_single_max', label: '單一主題 ETF 上限', limit: '≤ 10%', severity: 'WARNING' },
    { key: 'high_vol_max', label: '高波動資產總上限', limit: '≤ 35%', severity: 'VIOLATION' }
]);

       function evaluateOptimizerConstraintPolicy(candidate) {
    if (!candidate || !Array.isArray(candidate.rows)) {
        return {
            key: candidate?.key || '',
            status: 'NO_DATA',
            issues: [],
            rows: [],
            totals: {},
            violation_count: 0,
            warning_count: 0,
            most_severe_issue: '尚無資料'
        };
    }

    const rows = candidate.rows.map((row) => {
        const buffered = Number(row.buffered_target_weight_pct ?? row.target_weight_pct ?? row.current_weight_pct ?? 0);
        const rawTarget = Number(row.target_weight_pct ?? buffered);
        const bucket = optimizerPolicyBucket(row.ticker);
        const rowIssues = [];
        if (buffered > 20) {
            rowIssues.push({
                rule: 'single_max',
                severity: 'VIOLATION',
                message: `單檔 ${row.ticker} buffer 後權重 ${buffered.toFixed(2)}% > 20%。`
            });
        }
        if (bucket === 'theme' && buffered > 10) {
            rowIssues.push({
                rule: 'theme_single_max',
                severity: 'WARNING',
                message: `主題 ETF ${row.ticker} buffer 後權重 ${buffered.toFixed(2)}% > 10%。`
            });
        }
        return {
            ...row,
            policy_bucket: bucket,
            policy_weight_pct: Number(buffered.toFixed(3)),
            raw_target_weight_pct: Number(rawTarget.toFixed(3)),
            policy_issues: rowIssues,
            policy_status: rowIssues.some((x) => x.severity === 'VIOLATION') ? 'VIOLATION' : rowIssues.length ? 'WARNING' : 'PASS'
        };
    });

    const sumBy = (predicate) => rows.reduce((sum, row) => sum + (predicate(row) ? Number(row.policy_weight_pct || 0) : 0), 0);
    const totals = {
        taiwan_pct: Number(sumBy((r) => r.policy_bucket === 'taiwan').toFixed(2)),
        crypto_pct: Number(sumBy((r) => r.policy_bucket === 'crypto').toFixed(2)),
        gold_pct: Number(sumBy((r) => r.policy_bucket === 'gold').toFixed(2)),
        cash_pct: Number(sumBy((r) => r.policy_bucket === 'cash').toFixed(2)),
        theme_pct: Number(sumBy((r) => r.policy_bucket === 'theme').toFixed(2)),
        high_vol_pct: Number(sumBy((r) => ['crypto', 'theme'].includes(r.policy_bucket)).toFixed(2)),
        max_single_pct: Number(Math.max(0, ...rows.map((r) => Number(r.policy_weight_pct || 0))).toFixed(2))
    };

    const issues = [];
    rows.forEach((row) => (row.policy_issues || []).forEach((issue) => issues.push({ ticker: row.ticker, ...issue })));

    if (totals.taiwan_pct > 40) {
        issues.push({ rule: 'taiwan_max', severity: 'VIOLATION', message: `台股總權重 ${totals.taiwan_pct}% > 40%。` });
    }
    if (totals.crypto_pct > 15) {
        issues.push({ rule: 'crypto_max', severity: 'VIOLATION', message: `加密總權重 ${totals.crypto_pct}% > 15%。` });
    }
    if (totals.high_vol_pct > 35) {
        issues.push({ rule: 'high_vol_max', severity: 'VIOLATION', message: `高波動資產總權重 ${totals.high_vol_pct}% > 35%。` });
    }
    if (totals.gold_pct > 0 && (totals.gold_pct < 3 || totals.gold_pct > 7)) {
        issues.push({ rule: 'gold_band', severity: 'WARNING', message: `GLDM / 黃金權重 ${totals.gold_pct}% 不在 3%–7% 區間。` });
    }
    if (totals.cash_pct < 3) {
        issues.push({ rule: 'cash_floor', severity: 'WARNING', message: `BOXX / 類現金權重 ${totals.cash_pct}% < 3%。` });
    }

    const violationCount = issues.filter((x) => x.severity === 'VIOLATION').length;
    const warningCount = issues.filter((x) => x.severity === 'WARNING').length;
    const status = violationCount ? 'VIOLATION' : warningCount ? 'WARNING' : 'PASS';

    return {
        key: candidate.key,
        label: candidate.label,
        source: candidate.source,
        status,
        rows,
        totals,
        issues,
        violation_count: violationCount,
        warning_count: warningCount,
        most_severe_issue: issues[0]?.message || '全部通過目前政策規則'
    };
}

       const optimizerConstraintPolicySummaries = computed(() => {
    return (optimizerBufferCandidateSummaries.value || []).map((candidate) => {
        const policy = evaluateOptimizerConstraintPolicy(candidate);
        return {
            key: candidate.key,
            label: candidate.label,
            source: candidate.source,
            buffer_turnover_pct: candidate.buffer_turnover_pct,
            active_count: candidate.active_count,
            policy_status: policy.status,
            violation_count: policy.violation_count,
            warning_count: policy.warning_count,
            most_severe_issue: policy.most_severe_issue,
            totals: policy.totals
        };
    });
});

       const selectedOptimizerConstraintPolicy = computed(() => {
    const candidate = selectedOptimizerBufferCandidate.value;
    return evaluateOptimizerConstraintPolicy(candidate);
});

       const selectedOptimizerConstraintRows = computed(() => {
    return selectedOptimizerConstraintPolicy.value?.rows || [];
});

       const selectedOptimizerConstraintIssues = computed(() => {
    return selectedOptimizerConstraintPolicy.value?.issues || [];
});



       const optimizerRobustnessOutput = ref(null);
       const optimizerRobustnessError = ref('');

       async function loadOptimizerRobustnessOutput() {
    try {
        optimizerRobustnessError.value = '';
        const response = await fetch(`data/optimizer/optimizer_robustness_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            optimizerRobustnessOutput.value = null;
            optimizerRobustnessError.value = `尚未讀到 optimizer robustness output (${response.status})`;
            return;
        }
        const data = await response.json();
        optimizerRobustnessOutput.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        optimizerRobustnessOutput.value = null;
        optimizerRobustnessError.value = err?.message || String(err);
    }
}

       const optimizerRobustnessWindows = computed(() => {
    return Array.isArray(optimizerRobustnessOutput.value?.windows) ? optimizerRobustnessOutput.value.windows : [];
});

       const optimizerRobustnessMethods = computed(() => {
    const stability = optimizerRobustnessOutput.value?.method_stability || {};
    return Object.keys(stability).map((key) => ({ key, ...stability[key] }))
        .sort((a, b) => {
            const order = { '穩定': 0, '可觀察': 1, '不穩定': 2, '樣本不足': 3 };
            const av = order[a.verdict] ?? 9;
            const bv = order[b.verdict] ?? 9;
            if (av !== bv) return av - bv;
            return Number(a.avg_pairwise_weight_turnover_pct ?? 999) - Number(b.avg_pairwise_weight_turnover_pct ?? 999);
        });
});

       const optimizerMostStableMethod = computed(() => {
    return optimizerRobustnessMethods.value.find((x) => x.status === 'OK') || null;
});

       const optimizerUnstableMethods = computed(() => {
    return optimizerRobustnessMethods.value.filter((x) => x.verdict === '不穩定');
});


       const optimizerStressOutput = ref(null);
       const optimizerStressError = ref('');

       async function loadOptimizerStressOutput() {
    try {
        optimizerStressError.value = '';
        const response = await fetch(`data/optimizer/optimizer_stress_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            optimizerStressOutput.value = null;
            optimizerStressError.value = `尚未讀到 optimizer stress output (${response.status})`;
            return;
        }
        const data = await response.json();
        optimizerStressOutput.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        optimizerStressOutput.value = null;
        optimizerStressError.value = err?.message || String(err);
    }
}

       const optimizerStressScenarios = computed(() => {
    return Array.isArray(optimizerStressOutput.value?.scenarios) ? optimizerStressOutput.value.scenarios : [];
});

       const optimizerStressRows = computed(() => {
    const rows = optimizerStressOutput.value?.comparison_rows;
    return Array.isArray(rows) ? rows : [];
});

       const optimizerStressWorstRows = computed(() => {
    return optimizerStressRows.value
        .slice()
        .sort((a, b) => Number(a.worst_scenario_return_pct ?? 0) - Number(b.worst_scenario_return_pct ?? 0));
});

       const optimizerStressBestWorst = computed(() => {
    return optimizerStressWorstRows.value.length ? optimizerStressWorstRows.value[optimizerStressWorstRows.value.length - 1] : null;
});

       const optimizerStressMostFragile = computed(() => {
    return optimizerStressWorstRows.value.length ? optimizerStressWorstRows.value[0] : null;
});

       const selectedStressScenarioKey = ref('');

       const selectedStressScenario = computed(() => {
    const scenarios = optimizerStressScenarios.value || [];
    if (!scenarios.length) return null;
    if (selectedStressScenarioKey.value) {
        const found = scenarios.find((x) => x.key === selectedStressScenarioKey.value);
        if (found) return found;
    }
    return scenarios[0];
});

       const selectedStressScenarioRows = computed(() => {
    const key = selectedStressScenario.value?.key;
    if (!key) return [];
    return optimizerStressRows.value
        .map((row) => {
            const scenario = row.scenario_returns?.[key] || {};
            return {
                label: row.label,
                source: row.source,
                status: row.status,
                scenario_return_pct: scenario.return_pct ?? null,
                top_contributors: scenario.top_contributors || []
            };
        })
        .sort((a, b) => Number(a.scenario_return_pct ?? 0) - Number(b.scenario_return_pct ?? 0));
});

       function setStressScenario(key) {
    selectedStressScenarioKey.value = key;
}


       const selectedOptimizerExplainKey = ref('');

       function getCandidateByKey(key) {
    const rows = unifiedOptimizerComparison.value || [];
    return rows.find((x) => x.key === key) || null;
}

       function getBufferSummaryByKey(key) {
    return (optimizerBufferCandidateSummaries.value || []).find((x) => x.key === key) || null;
}

       function getPolicySummaryByKey(key) {
    return (optimizerConstraintPolicySummaries.value || []).find((x) => x.key === key) || null;
}

       function getStressSummaryByKey(key) {
    return (optimizerStressRows.value || []).find((x) => x.key === key) || null;
}

       function getRobustnessSummaryByKey(key) {
    return (optimizerRobustnessMethods.value || []).find((x) => x.key === key) || null;
}

       function buildOptimizerExplainability(candidate) {
    if (!candidate) {
        return {
            status: 'NO_DATA',
            reasons: [],
            watchpoints: [],
            asset_reasons: []
        };
    }

    const key = candidate.key;
    const buffer = getBufferSummaryByKey(key) || {};
    const policy = getPolicySummaryByKey(key) || {};
    const stress = getStressSummaryByKey(key) || {};
    const robust = getRobustnessSummaryByKey(key) || {};
    const rows = (selectedOptimizerBufferCandidate?.value?.key === key ? selectedOptimizerBufferRows.value : (buffer.rows || [])) || [];

    const reasons = [];
    const watchpoints = [];

    const esDelta = Number(candidate.es_delta_vs_current_pct);
    const volDelta = Number(candidate.vol_delta_vs_current_pct);
    const mddDelta = Number(candidate.mdd_delta_vs_current_pct);
    const turnover = Number(candidate.turnover_vs_current_pct ?? buffer.raw_turnover_pct);
    const bufferTurnover = Number(buffer.buffer_turnover_pct);
    const worstStress = Number(stress.worst_scenario_return_pct);
    const avgStress = Number(stress.avg_scenario_return_pct);

    if (Number.isFinite(esDelta)) {
        if (esDelta < 0) reasons.push(`ES95 較目前權重下降 ${Math.abs(esDelta).toFixed(2)} 個百分點，尾部風險較低。`);
        if (esDelta > 0) watchpoints.push(`ES95 較目前權重上升 ${esDelta.toFixed(2)} 個百分點，尾部風險變差。`);
    }
    if (Number.isFinite(volDelta)) {
        if (volDelta < 0) reasons.push(`年化波動較目前權重下降 ${Math.abs(volDelta).toFixed(2)} 個百分點。`);
        if (volDelta > 0) watchpoints.push(`年化波動較目前權重上升 ${volDelta.toFixed(2)} 個百分點。`);
    }
    if (Number.isFinite(mddDelta)) {
        if (mddDelta > 0) reasons.push(`歷史最大回撤較目前權重改善 ${mddDelta.toFixed(2)} 個百分點。`);
        if (mddDelta < 0) watchpoints.push(`歷史最大回撤較目前權重惡化 ${Math.abs(mddDelta).toFixed(2)} 個百分點。`);
    }
    if (Number.isFinite(turnover)) {
        if (turnover >= 80) watchpoints.push(`原始換手率約 ${turnover.toFixed(1)}%，實務摩擦成本可能很高。`);
        else if (turnover >= 40) watchpoints.push(`原始換手率約 ${turnover.toFixed(1)}%，需要先過 Trade Buffer 與人工審核。`);
        else reasons.push(`原始換手率約 ${turnover.toFixed(1)}%，相對可觀察。`);
    }
    if (Number.isFinite(bufferTurnover)) {
        reasons.push(`套用目前 ±${tradeBufferBasePct.value}% No-Trade Zone 後，主動換手約 ${bufferTurnover.toFixed(1)}%。`);
    }
    if (policy.policy_status === 'PASS') {
        reasons.push('通過 v1.6.1 Constraint Policy，目前沒有政策違規。');
    } else if (policy.policy_status === 'WARNING') {
        watchpoints.push(`政策層級為 WARNING：${policy.most_severe_issue || '存在警示項目。'}`);
    } else if (policy.policy_status === 'VIOLATION') {
        watchpoints.push(`政策層級為 VIOLATION：${policy.most_severe_issue || '存在違規項目。'}`);
    }
    if (robust.verdict) {
        if (robust.verdict === '穩定') reasons.push(`v1.4 樣本穩健性判讀為「穩定」。`);
        if (robust.verdict === '可觀察') watchpoints.push(`v1.4 樣本穩健性判讀為「可觀察」，仍需注意回看期敏感度。`);
        if (robust.verdict === '不穩定') watchpoints.push(`v1.4 樣本穩健性判讀為「不穩定」，不適合作為主要候選。`);
    }
    if (Number.isFinite(worstStress)) {
        if (worstStress <= -35) watchpoints.push(`壓力測試最差情境約 ${worstStress.toFixed(1)}%，極端情境損失較深。`);
        else reasons.push(`壓力測試最差情境約 ${worstStress.toFixed(1)}%，相對可追蹤。`);
    }
    if (Number.isFinite(avgStress)) {
        reasons.push(`六個壓力情境平均約 ${avgStress.toFixed(1)}%。`);
    }

    const assetRows = (selectedOptimizerBufferCandidate?.value?.key === key ? selectedOptimizerBufferRows.value : [])
        .filter((row) => row && ['ADD', 'TRIM', 'PENDING_ADD'].includes(row.action))
        .slice()
        .sort((a, b) => Math.abs(Number(b.drift_pct || 0)) - Math.abs(Number(a.drift_pct || 0)))
        .slice(0, 12)
        .map((row) => {
            const policyRow = (selectedOptimizerConstraintRows.value || []).find((x) => x.ticker === row.ticker) || {};
            let why = '';
            if (row.action === 'TRIM') why = `模型目標低於目前 ${Math.abs(Number(row.drift_pct || 0)).toFixed(2)}%，超過 Trim buffer。`;
            else if (row.action === 'ADD') why = `模型目標高於目前 ${Math.abs(Number(row.drift_pct || 0)).toFixed(2)}%，超過 Add buffer。`;
            else why = `超過 Add buffer，但 CRO_VETO 或風險控管使其列為候補。`;
            if (policyRow.policy_status === 'VIOLATION') why += ' 但此標的或組合有政策違規，不能直接執行。';
            if (policyRow.policy_status === 'WARNING') why += ' 需注意政策警示。';
            return {
                ticker: row.ticker,
                action: row.action,
                action_zh: row.action_zh,
                drift_pct: row.drift_pct,
                current_weight_pct: row.current_weight_pct,
                target_weight_pct: row.target_weight_pct,
                buffered_target_weight_pct: row.buffered_target_weight_pct,
                policy_status: policyRow.policy_status || 'PASS',
                why
            };
        });

    let decision = 'WATCH';
    if (policy.policy_status === 'VIOLATION' || robust.verdict === '不穩定' || (Number.isFinite(worstStress) && worstStress <= -40)) {
        decision = 'REJECT_OR_REWORK';
    } else if ((Number.isFinite(esDelta) && esDelta < 0) && policy.policy_status !== 'VIOLATION' && robust.verdict !== '不穩定' && (!Number.isFinite(bufferTurnover) || bufferTurnover <= 35)) {
        decision = 'REVIEW_CANDIDATE';
    }

    if (!reasons.length) reasons.push('此候選沒有明確風險改善訊號，暫時只適合觀察。');
    if (!watchpoints.length) watchpoints.push('尚無重大警示，但仍需人工審核與成本估算。');

    return {
        key,
        label: candidate.label,
        source: candidate.source,
        status: 'OK',
        decision,
        reasons,
        watchpoints,
        asset_reasons: assetRows,
        metrics: {
            es_delta_vs_current_pct: candidate.es_delta_vs_current_pct,
            vol_delta_vs_current_pct: candidate.vol_delta_vs_current_pct,
            mdd_delta_vs_current_pct: candidate.mdd_delta_vs_current_pct,
            turnover_vs_current_pct: candidate.turnover_vs_current_pct,
            buffer_turnover_pct: buffer.buffer_turnover_pct ?? null,
            policy_status: policy.policy_status ?? 'N/A',
            robustness_verdict: robust.verdict ?? 'N/A',
            worst_stress_pct: stress.worst_scenario_return_pct ?? null,
            avg_stress_pct: stress.avg_scenario_return_pct ?? null
        }
    };
}

       const optimizerExplainabilityCandidates = computed(() => {
    return (unifiedOptimizerComparison.value || [])
        .filter((x) => x && x.status === 'OK')
        .filter((x) => !['current_weight'].includes(x.key))
        .filter((x) => x.key !== 'hrp_lite_v06' || Array.isArray(x.weights))
        .map((candidate) => buildOptimizerExplainability(candidate));
});

       const selectedOptimizerExplainability = computed(() => {
    const list = optimizerExplainabilityCandidates.value || [];
    if (!list.length) return null;
    if (selectedOptimizerExplainKey.value) {
        const found = list.find((x) => x.key === selectedOptimizerExplainKey.value);
        if (found) return found;
    }
    const review = list.find((x) => x.decision === 'REVIEW_CANDIDATE');
    return review || list[0];
});

       function setOptimizerExplainCandidate(key) {
    selectedOptimizerExplainKey.value = key;
    setOptimizerBufferCandidate(key);
}



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
            if ((Number(tailStatsLite.value.jdCrashProb) || 0) >= 8 || (Number(tailStatsLite.value.evtShapeXi) || 0) >= 0.25) {
                queue.push({
                    level: 'medium',
                    icon: 'fa-burst',
                    title: '尾部風險偏高',
                    detail: `Crash Prob ${tailStatsLite.value.jdCrashProb}% / EVT ξ ${tailStatsLite.value.evtShapeXi}，不要只看一般波動。`
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

        function removeTransaction(txToRemove) { 
            if(confirm('確認刪除此筆交易?')) { 
                const idx = transactions.value.indexOf(txToRemove);
                if (idx > -1) { transactions.value.splice(idx, 1); saveData(); updateCharts(); }
            } 
        }
        
        function removeHistoryByDate(date) { 
            if(confirm('確定刪除此快照?')) { realHistoryData.value = realHistoryData.value.filter(h=>h.date!==date); saveData(); updateCharts(); } 
        }

        
        let syncTimer = null;
async function saveData() {
    await localforage.setItem('ledgerData', JSON.stringify(transactions.value));
    await localforage.setItem('historyData', JSON.stringify(realHistoryData.value));
    await localforage.setItem('stockMeta', JSON.stringify(stockMeta.value));
    await localforage.setItem('chaosMeta', JSON.stringify(chaosMeta.value));
    await localforage.setItem('settings', JSON.stringify({
        exchangeRate: exchangeRate.value,
        sheetUrl: sheetUrl.value,
        fireTargets: fireTargets.value,
        priceMap: priceMap.value,
        liquidityBufferRatio: liquidityBufferRatio.value
    }));

    isDbSyncing.value = true;
    if (syncTimer) clearTimeout(syncTimer);

    syncTimer = setTimeout(async () => {
        try {
            const { error } = await supabase.from('portfolio_db').upsert({
                id: 1,
                ledger_data: transactions.value,
                history_data: realHistoryData.value,
                stock_meta: stockMeta.value,
                settings: {
                    exchangeRate: exchangeRate.value,
                    sheetUrl: sheetUrl.value,
                    fireTargets: fireTargets.value,
                    priceMap: priceMap.value,
                    liquidityBufferRatio: liquidityBufferRatio.value
                }
            }, { onConflict: 'id' });

            if (error) throw error;
        } catch (e) {
            console.error("❌ Supabase 同步失敗", e);
        } finally {
            isDbSyncing.value = false;
        }
    }, 1500);
}

        function exportAll() { const data = { ledger: transactions.value, history: realHistoryData.value, stockMeta: stockMeta.value }; const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([JSON.stringify(data)], {type: "application/json"})); link.download = "backup.json"; link.click(); }
        function importData(event) {
            const file = event.target.files[0]; if (!file) return; const reader = new FileReader();
            reader.onload = (e) => {
                const data = JSON.parse(e.target.result);
                transactions.value = data.ledger; realHistoryData.value = data.history; if(data.stockMeta) stockMeta.value = data.stockMeta;
                saveData(); updateCharts(); alert('匯入成功，已同步至雲端');
            }; reader.readAsText(file);
        }
        
        const ledgerDraftPreview = computed(() => {
    const { type, ticker, price, shares, amount } = txForm.value;
    const output = {
        impact: 0,
        projectedCash: cashBalance.value,
        warnings: [],
        estimatedAmount: 0
    };

    if (type === 'Buy' || type === 'Sell') {
        const qty = Number(shares) || 0;
        const inputPrice = price !== null && price !== '' ? Number(price) : null;
        const inputAmount = amount !== null && amount !== '' ? Number(amount) : null;
        const estimatedAmount = inputAmount && inputAmount > 0
            ? inputAmount
            : ((inputPrice && inputPrice > 0 && qty > 0) ? inputPrice * qty : 0);

        output.estimatedAmount = estimatedAmount;
        output.impact = (type === 'Buy' ? -1 : 1) * estimatedAmount;
        output.projectedCash = cashBalance.value + output.impact;

        if (!ticker) output.warnings.push('尚未填寫代號。');
        if (!qty || qty <= 0) output.warnings.push('股數尚未填妥。');
        if (!estimatedAmount || estimatedAmount <= 0) output.warnings.push('尚未形成有效成交金額。');

        const holding = holdingsFlat.value.find(h => h.ticker === String(ticker || '').toUpperCase());
        if (type === 'Sell') {
            if (!holding) output.warnings.push('目前沒有這檔持倉可賣。');
            else if (qty > holding.shares) output.warnings.push(`賣出股數超過現有持倉 (${formatNumber(holding.shares)})。`);
        }
    } else if (type === 'Deposit' || type === 'Withdraw') {
        const estimatedAmount = Number(amount) || 0;
        output.estimatedAmount = estimatedAmount;
        output.impact = (type === 'Deposit' ? 1 : -1) * estimatedAmount;
        output.projectedCash = cashBalance.value + output.impact;
        if (!estimatedAmount || estimatedAmount <= 0) output.warnings.push('金額尚未填妥。');
    }

    if ((type === 'Buy' || type === 'Withdraw') && output.estimatedAmount > 0 && output.projectedCash < -CASH_EPS) {
        output.warnings.push('這筆送出後現金會變成負數。');
    }

    return output;
});

        function addTransaction() {
    const { date, type, category, ticker, price, shares, amount } = txForm.value;
    if (!date) return;

    let finalPrice = null;
    let finalShares = null;
    let actualTotal = null;
    let finalFlow = 0;

    if (type === 'Buy' || type === 'Sell') {
        finalShares = Number(shares);

        if (!String(ticker || '').trim()) {
            alert('請填寫代號');
            return;
        }

        if (!finalShares || finalShares <= 0) {
            alert('請填寫有效股數');
            return;
        }

        const inputPrice = price !== null && price !== '' ? Number(price) : null;
        const inputAmount = amount !== null && amount !== '' ? Number(amount) : null;

        if ((!inputPrice || inputPrice <= 0) && (!inputAmount || inputAmount <= 0)) {
            alert('買賣至少要填「單價」或「總金額」其中一個');
            return;
        }

        if (inputPrice && inputPrice > 0) {
            finalPrice = inputPrice;
            actualTotal = inputAmount && inputAmount > 0 ? inputAmount : inputPrice * finalShares;
        } else {
            actualTotal = inputAmount;
            finalPrice = actualTotal / finalShares;
        }

        if (type === 'Sell') {
            const upperTicker = ticker.toUpperCase();
            const holding = holdingsFlat.value.find(h => h.ticker === upperTicker);
            if (!holding) {
                alert('目前沒有這檔持倉可賣出');
                return;
            }
            if (finalShares > holding.shares) {
                alert(`賣出股數超過現有持倉 (${formatNumber(holding.shares)})`);
                return;
            }
        }

        finalFlow = (type === 'Buy' ? -1 : 1) * actualTotal;
    } else if (type === 'Deposit' || type === 'Withdraw') {
        actualTotal = Number(amount);

        if (!actualTotal || actualTotal <= 0) {
            alert('請填寫有效金額');
            return;
        }

        finalFlow = (type === 'Deposit' ? 1 : -1) * actualTotal;
    } else {
        alert('未知交易類型');
        return;
    }

    const projectedCash = cashBalance.value + finalFlow;
    if ((type === 'Buy' || type === 'Withdraw') && projectedCash < -CASH_EPS) {
        const goOn = confirm(`這筆會讓現金變成負數 (NT$ ${formatNumber(projectedCash)})。
通常代表你可能少記了 Sell / Deposit。
仍要送出嗎？`);
        if (!goOn) return;
    }

    transactions.value.push({
        date,
        type,
        category,
        ticker: (type === 'Buy' || type === 'Sell') ? ticker?.toUpperCase() : '',
        price: finalPrice,
        shares: finalShares,
        amount: actualTotal,
        totalCashFlow: finalFlow
    });

    saveData();

    txForm.value.ticker = '';
    txForm.value.price = null;
    txForm.value.shares = null;
    txForm.value.amount = null;

    updateCharts();
}

        function snapshotToHistory() {
    const date = snapshotDate.value || new Date().toISOString().split('T')[0];
    const assets = Math.round(totalPortfolioNav.value);
    const cost = Math.round(totalStockCostTwd.value);

    const idx = realHistoryData.value.findIndex(h => h.date === date);
    if (idx >= 0) {
        if (confirm(`日期 (${date}) 已有紀錄，要覆蓋嗎？`)) {
            realHistoryData.value[idx] = { date, assets, cost };
        } else {
            return;
        }
    } else {
        realHistoryData.value.push({ date, assets, cost });
    }

    saveData();
    updateCharts();
    if (!quantStartDate.value) quantStartDate.value = date;
}

        const quantDays = computed(() => {
             const h = filteredHistory.value; if(h.length < 2) return 0;
             const sorted = [...h].sort((a,b) => new Date(a.date) - new Date(b.date));
             const start = new Date(sorted[0].date); const end = new Date(sorted[sorted.length-1].date);
             return Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        });

        function addHistoryRecord() { 
            const { date, assets, cost } = historyForm.value; 
            realHistoryData.value.push({ date, assets, cost }); 
            saveData(); updateCharts(); 
        }

        function openMonteCarlo() {
            showMCModal.value = true; mcOptimal.value = null; 
            if (cloudAiAnalysis.value) {
                const fullAiText = JSON.stringify(cloudAiAnalysis.value).toLowerCase();
                if (fullAiText.includes('通膨') || fullAiText.includes('inflation') || fullAiText.includes('升息') || fullAiText.includes('cpi')) enableInflation.value = true; else enableInflation.value = false;
                if (fullAiText.includes('尾部風險') || fullAiText.includes('衰退') || fullAiText.includes('黑天鵝') || fullAiText.includes('恐慌') || fullAiText.includes('利差擴大') || fullAiText.includes('衰退風險') || fullAiText.includes('滯脹期')) enableBlackSwan.value = true; else enableBlackSwan.value = false;
            }
            nextTick(() => { runMonteCarlo(); });
        }

        const mcRisk = ref('neutral'); const macroRegime = ref('Normal'); const enableBlackSwan = ref(false); const enableInflation = ref(false);
        const bufferPresets = [0, 5, 8, 10];

function clampLiquidityBuffer(val) {
    const n = Number(val);
    if (!Number.isFinite(n)) return 0;
    return Math.max(0, Math.min(80, Math.round(n)));
}

async function applyLiquidityBuffer(val) {
    const nextVal = clampLiquidityBuffer(val);
    if (nextVal === liquidityBufferRatio.value) {
        if (showMCModal.value) nextTick(() => runMonteCarlo());
        return;
    }

    liquidityBufferRatio.value = nextVal;
    await saveData();

    if (showMCModal.value) {
        nextTick(() => runMonteCarlo());
    }
}

async function nudgeLiquidityBuffer(delta) {
    await applyLiquidityBuffer((Number(liquidityBufferRatio.value) || 0) + delta);
}

        function calculateBlackLitterman(assets, rm, rf, sm, views = []) {
            const n = assets.length; const math = window.math; const varianceM = Math.pow(sm, 2);
            let covMatrix = [];
            for (let i = 0; i < n; i++) {
                covMatrix[i] = [];
                for (let j = 0; j < n; j++) { covMatrix[i][j] = (i === j) ? Math.pow(assets[i].stdDev / 100, 2) : assets[i].beta * assets[j].beta * varianceM; }
            }
            const lambda = (rm - rf) / varianceM; const wkt = assets.map(a => a.totalWeight); const Sigma = math.matrix(covMatrix);
            const Pi_excess = math.multiply(lambda, math.multiply(Sigma, wkt)).toArray();

            if (!views || views.length === 0) return Pi_excess.map(p => p + rf);

            const tau = 0.05; const tauSigma = math.multiply(tau, Sigma); const invTauSigma = math.inv(tauSigma);
            const K = views.length; let P = math.zeros([K, n]); let Q = [];

            views.forEach((v, k) => {
                const idx1 = assets.findIndex(a => a.ticker === v.asset1);
                if (idx1 < 0) return; 
                if (v.type === 'absolute') { P[k][idx1] = 1; Q.push((v.value / 100) - rf); } 
                else if (v.type === 'relative') {
                    const idx2 = assets.findIndex(a => a.ticker === v.asset2);
                    if (idx2 >= 0) { P[k][idx1] = 1; P[k][idx2] = -1; Q.push(v.value / 100); }
                }
            });

            const P_mat = math.matrix(P); const Q_vec = math.matrix(Q); let Omega = math.zeros([K, K]);
            const P_tauSigma_Pt = math.multiply(math.multiply(P_mat, tauSigma), math.transpose(P_mat)).toArray();
            for(let k=0; k<K; k++) { Omega[k][k] = P_tauSigma_Pt[k][k]; if(Omega[k][k] === 0) Omega[k][k] = 0.0001; }
            const invOmega = math.inv(math.matrix(Omega));
            const Pt_invOmega_P = math.multiply(math.multiply(math.transpose(P_mat), invOmega), P_mat);
            const term1 = math.inv(math.add(invTauSigma, Pt_invOmega_P));
            const partA = math.multiply(invTauSigma, Pi_excess);
            const partB = math.multiply(math.multiply(math.transpose(P_mat), invOmega), Q_vec);
            const term2 = math.add(partA, partB);
            const posterior_excess = math.multiply(term1, term2).toArray();

            return posterior_excess.map(p => p + rf);
        }

        const HARD_BUFFER_TICKERS = ['SHY', 'BOXX'];
const DEFENSIVE_TICKERS = ['USMV'];

function normTicker(t) {
    return String(t || '').trim().toUpperCase();
}

function isHardBufferAsset(item) {
    return HARD_BUFFER_TICKERS.includes(normTicker(item?.ticker));
}

function isDefensiveAsset(item) {
    return DEFENSIVE_TICKERS.includes(normTicker(item?.ticker));
}

function getAllHoldingItems() {
    const out = [];
    for (const cat in groupedHoldings.value) {
        groupedHoldings.value[cat].items.forEach(item => out.push(item));
    }
    return out;
}

function getSleeveStats() {
    const totalVal = totalStockValueTwd.value || 0;
    const allItems = getAllHoldingItems();

    const hardBufferValue = allItems
        .filter(isHardBufferAsset)
        .reduce((sum, item) => sum + (parseFloat(item.marketValueTwd) || 0), 0);

    const defensiveValue = allItems
        .filter(isDefensiveAsset)
        .reduce((sum, item) => sum + (parseFloat(item.marketValueTwd) || 0), 0);

    return {
        totalVal,
        hardBufferWeight: totalVal > 0 ? hardBufferValue / totalVal : 0,
        defensiveWeight: totalVal > 0 ? defensiveValue / totalVal : 0
    };
}

function getJumpParams(item) {
    const t = normTicker(item?.ticker);
    const cat = String(item?.category || '');

    const isCrypto =
        t.endsWith('-USD') ||
        cat.includes('加密');

    const isLeveraged =
        ['SSO', '00631L', '00675L'].includes(t);

    if (isHardBufferAsset(item)) {
        return { lambda: 0.4, mean: -0.03, std: 0.02, skewPenalty: 0.2, kurtBoost: 0.5 };
    }

    if (isDefensiveAsset(item)) {
        return { lambda: 0.7, mean: -0.05, std: 0.03, skewPenalty: 0.4, kurtBoost: 1.0 };
    }

    if (isCrypto || isLeveraged) {
        return { lambda: 2.0, mean: -0.18, std: 0.08, skewPenalty: 1.6, kurtBoost: 4.5 };
    }

    return { lambda: 1.2, mean: -0.10, std: 0.05, skewPenalty: 0.9, kurtBoost: 2.2 };
}

function getJumpParamsForAsset(asset) {
    const t = String(asset?.ticker || '').trim().toUpperCase();
    const category = String(asset?.category || '');

    const isCrypto = t.endsWith('-USD') || category.includes('加密') || t.includes('BTC') || t.includes('ETH');
    const isLeveraged = ['SSO', '00631L', '00675L'].includes(t);
    const isDefensive = ['USMV'].includes(t);
    const isHardBuffer = ['SHY', 'BOXX'].includes(t);

    if (isHardBuffer) {
        return { lambda: 0.4, mean: -0.03, std: 0.02 };
    }
    if (isDefensive) {
        return { lambda: 0.7, mean: -0.05, std: 0.03 };
    }
    if (isCrypto || isLeveraged) {
        return { lambda: 2.0, mean: -0.18, std: 0.08 };
    }
    return { lambda: 1.2, mean: -0.10, std: 0.05 };
}

function getEffectiveJumpParams(assets, weights) {
    let effLambda = 0;
    let effMean = 0;
    let effStd = 0;

    weights.forEach((w, i) => {
        const jp = getJumpParamsForAsset(assets[i]);
        effLambda += w * jp.lambda;
        effMean += w * jp.mean;
        effStd += w * jp.std;
    });

    return {
        lambda: effLambda,
        mean: effMean,
        std: effStd
    };
}

function simulateJumpDiffusionMoments({
    muWeekly,
    sigmaWeekly,
    jumpLambdaAnnual,
    jumpMean,
    jumpStd,
    horizonWeeks = 13,
    nSims = 400,
    seed = 42
}) {
    const rng = (() => {
        let s = seed;
        return () => {
            s = (s * 1664525 + 1013904223) % 4294967296;
            return s / 4294967296;
        };
    })();

    function randn() {
        let u = 0, v = 0;
        while (u === 0) u = rng();
        while (v === 0) v = rng();
        return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
    }

    function poisson(lambda) {
        const L = Math.exp(-lambda);
        let k = 0;
        let p = 1;
        do {
            k++;
            p *= rng();
        } while (p > L);
        return k - 1;
    }

    const lambdaWeekly = Math.max(0, jumpLambdaAnnual / 52);
    const simReturns = [];

    for (let s = 0; s < nSims; s++) {
        let wealth = 1.0;

        for (let w = 0; w < horizonWeeks; w++) {
            const z = randn();
            const jumpCount = poisson(lambdaWeekly);

            let jumpComponent = 0;
            if (jumpCount > 0) {
                jumpComponent =
                    jumpCount * jumpMean +
                    Math.sqrt(jumpCount) * jumpStd * randn();
            }

            let stepRet = muWeekly + sigmaWeekly * z + jumpComponent;
            stepRet = Math.max(-0.95, Math.min(3.0, stepRet));
            wealth *= (1 + stepRet);
        }

        simReturns.push(wealth - 1);
    }

    const n = simReturns.length;
    const mean = simReturns.reduce((a, b) => a + b, 0) / n;
    const variance = simReturns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / Math.max(1, n - 1);
    const std = Math.sqrt(variance);

    const m3 = simReturns.reduce((a, b) => a + Math.pow(b - mean, 3), 0) / n;
    const m4 = simReturns.reduce((a, b) => a + Math.pow(b - mean, 4), 0) / n;

    const skew = std > 0 ? m3 / Math.pow(std, 3) : 0;
    const kurtEx = std > 0 ? (m4 / Math.pow(std, 4)) - 3 : 0;

    const sorted = [...simReturns].sort((a, b) => a - b);
    const idx05 = Math.max(0, Math.floor(sorted.length * 0.05));
    const q05 = sorted[idx05] ?? mean;

    const tail = sorted.slice(0, idx05 + 1);
    const es05 = tail.length > 0
        ? tail.reduce((a, b) => a + b, 0) / tail.length
        : q05;

    return {
        mean,
        std,
        skew,
        kurtEx,
        q05,
        es05
    };
}
function normCdf(x) {
    const t = 1 / (1 + 0.2316419 * Math.abs(x));
    const d = 0.3989423 * Math.exp(-x * x / 2);
    let prob = d * t * (
        0.3193815 +
        t * (-0.3565638 +
        t * (1.781478 +
        t * (-1.821256 +
        t * 1.330274)))
    );
    prob = 1 - prob;
    return x >= 0 ? prob : 1 - prob;
}

function sharpeStdErrApprox(sr, skew, exKurt, nObs) {
    if (!Number.isFinite(sr) || !Number.isFinite(nObs) || nObs <= 1) return null;

    const kurt = (Number.isFinite(exKurt) ? exKurt : 0) + 3; // 轉成常規 kurtosis
    const denom = Math.max(
        1e-12,
        1 - (skew || 0) * sr + ((kurt - 1) / 4) * sr * sr
    );

    return Math.sqrt(denom / Math.max(1, nObs - 1));
}

function computePSR({ sr, srBenchmark = 0, skew = 0, exKurt = 0, nObs = 0 }) {
    const se = sharpeStdErrApprox(sr, skew, exKurt, nObs);
    if (!Number.isFinite(se) || se <= 0) return null;
    const z = (sr - srBenchmark) / se;
    return normCdf(z);
}

function computeDSR({ sr, skew = 0, exKurt = 0, nObs = 0, nTrials = 1 }) {
    const se = sharpeStdErrApprox(sr, skew, exKurt, nObs);
    if (!Number.isFinite(se) || se <= 0) return null;

    const effectiveTrials = Math.max(1, nTrials);
    const srStar = effectiveTrials > 1
        ? se * Math.sqrt(2 * Math.log(effectiveTrials))
        : 0;

    const z = (sr - srStar) / se;
    return normCdf(z);
}

        function runMonteCarlo() {
    const ctx = document.getElementById('mcChart');
    if (chartMC) chartMC.destroy();

    const allMcAssets = mcAvailableAssets.value || [];
    const riskyAssets = allMcAssets.filter(item => !isHardBufferAsset(item));

    if (riskyAssets.length < 2) {
        alert("⚠️ 需要至少 2 檔非 hard buffer 標的 (Beta 與 SD 需大於 0) 才能進行蒙地卡羅模擬。");
        showMCModal.value = false;
        return;
    }

    const { hardBufferWeight: currentHardBufferWeight, defensiveWeight: currentDefensiveWeight } = getSleeveStats();

    const targetHardBufferWeight = Math.max(0, Math.min((parseFloat(liquidityBufferRatio.value) || 0) / 100, 0.80));
    const riskyBudget = 1 - targetHardBufferWeight;

    if (riskyBudget <= 0.05) {
        alert("⚠️ 流動性緩衝比例過高，幾乎沒有剩餘風險資產可配置。");
        return;
    }

    const n_assets = riskyAssets.length;
    const n_portfolios = 5000;

    let minWeightAbs = 0.03;
    let maxWeightAbs = 0.20;

    if (minWeightAbs * n_assets > riskyBudget) minWeightAbs = 0.0;
    maxWeightAbs = Math.min(maxWeightAbs, riskyBudget);

    const baseRm = (parseFloat(riskParams.value.rm) || 10.0) / 100;
    const baseSm = (parseFloat(riskParams.value.sm) || 15.0) / 100;
    const baseRf = (parseFloat(riskParams.value.rf) || 1.5) / 100;

    const regimeParams = {
        Normal: { rm: baseRm, sm: baseSm, rf: baseRf, stressCorr: 0,   m_skew: -0.5, m_kurt_ex: 1.0 },
        Bull:   { rm: baseRm + 0.05, sm: baseSm * 0.8, rf: baseRf,     stressCorr: 0,   m_skew: 0.2,  m_kurt_ex: 0.5 },
        Bear:   { rm: baseRm - 0.10, sm: baseSm * 1.5, rf: baseRf*0.5, stressCorr: 0.5, m_skew: -1.0, m_kurt_ex: 2.0 },
        Crisis: { rm: baseRm - 0.20, sm: baseSm * 2.0, rf: 0.001,      stressCorr: 1.0, m_skew: -2.5, m_kurt_ex: 5.0 }
    };

    const { rm, sm, rf, stressCorr, m_skew, m_kurt_ex } =
        regimeParams[macroRegime.value] || regimeParams['Normal'];

    const bl_expected_returns = calculateBlackLitterman(riskyAssets, rm, rf, sm, blViews.value);

    const mcPoints = [];
    let bestScore = -999999;
    let maxScoreForColor = -999999;
    let minScoreForColor = 999999;
    let bestPort = null;

    let riskAversionA = 0;
    if (mcRisk.value === 'averse') riskAversionA = 10;
    else if (mcRisk.value === 'aggressive') riskAversionA = 1;

    for (let p = 0; p < n_portfolios; p++) {
        let weights = Array(n_assets).fill(minWeightAbs);
        let remaining = riskyBudget - (minWeightAbs * n_assets);

        if (remaining > 0) {
            const randValues = Array.from({ length: n_assets }, () => -Math.log(Math.random()));
            const sumRand = randValues.reduce((a, b) => a + b, 0) || 1;

            for (let i = 0; i < n_assets; i++) {
                weights[i] += (randValues[i] / sumRand) * remaining;
            }

            let needsRebalance = true;
            let iterations = 0;

            while (needsRebalance && iterations < 6) {
                needsRebalance = false;
                let excess = 0;
                const validReceivers = [];

                for (let i = 0; i < n_assets; i++) {
                    if (weights[i] > maxWeightAbs) {
                        excess += (weights[i] - maxWeightAbs);
                        weights[i] = maxWeightAbs;
                        needsRebalance = true;
                    } else if (weights[i] < maxWeightAbs - 0.0001) {
                        validReceivers.push(i);
                    }
                }

                if (excess > 0 && validReceivers.length > 0) {
                    const share = excess / validReceivers.length;
                    validReceivers.forEach(i => {
                        weights[i] += share;
                    });
                }

                iterations++;
            }
        }

        const weightSum = weights.reduce((a, b) => a + b, 0);
        if (weightSum <= 0) continue;
        weights = weights.map(w => (w / weightSum) * riskyBudget);

        let p_ret = targetHardBufferWeight * rf;
        let p_beta = 0;
        let weighted_vol_sum = 0;

        weights.forEach((w, i) => {
            const e_r = bl_expected_returns[i] || 0;
            const beta_i = parseFloat(riskyAssets[i].beta) || 1.0;
            const sig_i = (parseFloat(riskyAssets[i].stdDev) || 20.0) / 100;

            p_ret += w * e_r;
            p_beta += w * beta_i;
            weighted_vol_sum += w * sig_i;
        });

        let sys_var = Math.pow(p_beta, 2) * Math.pow(sm, 2);
        let idio_var = 0;

        weights.forEach((w, i) => {
            const sig_i = (parseFloat(riskyAssets[i].stdDev) || 20.0) / 100;
            const beta_i = parseFloat(riskyAssets[i].beta) || 1.0;
            let idio_i = Math.pow(sig_i, 2) - Math.pow(beta_i * sm, 2);
            if (idio_i < 0) idio_i = 0;
            idio_var += Math.pow(w, 2) * idio_i;
        });

        const standard_vol = Math.sqrt(sys_var + idio_var);
        let p_vol = standard_vol * (1 - stressCorr) + weighted_vol_sum * stressCorr;
        if (!Number.isFinite(p_vol) || p_vol <= 0) continue;

        let p_skew = (Math.pow(p_beta, 3) * Math.pow(sm, 3) * m_skew) / Math.pow(p_vol, 3);
        let p_kurt_ex = (Math.pow(p_beta, 4) * Math.pow(sm, 4) * m_kurt_ex) / Math.pow(p_vol, 4);

        let jumpTailLoss = 0;

            if (enableBlackSwan.value) {
                const jp = getEffectiveJumpParams(riskyAssets, weights);

                // 【解析解 (Analytical Moments) 替換原本的內部 MC 模擬】
                // 計算 Merton 模型下的跳躍補償期望值與變異數 (年化)
                const jumpExpectedReturn = jp.lambda * jp.mean;
                const jumpVariance = jp.lambda * (Math.pow(jp.mean, 2) + Math.pow(jp.std, 2));

                // 1. 直接疊加報酬率與波動率
                p_ret = p_ret + jumpExpectedReturn;
                p_vol = Math.sqrt(Math.pow(p_vol, 2) + jumpVariance);

                // 2. 估算高階動差 (直接使用解析解推導，完美反映肥尾與左傾)
                // 跳躍造成的偏度 = [lambda * E(J^3)] / p_vol^3
                const m3_jump = jp.lambda * (Math.pow(jp.mean, 3) + 3 * jp.mean * Math.pow(jp.std, 2));
                p_skew = p_skew + (m3_jump / Math.pow(p_vol, 3));

                // 跳躍造成的超額峰度 = [lambda * E(J^4)] / p_vol^4
                const m4_jump = jp.lambda * (Math.pow(jp.mean, 4) + 6 * Math.pow(jp.mean, 2) * Math.pow(jp.std, 2) + 3 * Math.pow(jp.std, 4));
                p_kurt_ex = p_kurt_ex + (m4_jump / Math.pow(p_vol, 4));

                // 3. 抓取尾部風險概估 (單純量化跳躍帶來的預期損失拖累)
                jumpTailLoss = Math.abs(jumpExpectedReturn);
            }

        let rf_effective = rf;
        if (enableInflation.value) {
            p_ret -= 0.025;
            p_vol = Math.sqrt(Math.pow(p_vol, 2) + Math.pow(0.015, 2));
            rf_effective = rf - 0.025;
        }

        const p_sharpe = (p_ret - rf_effective) / p_vol;
const p_asr = p_sharpe * (
    1 +
    (p_skew / 6) * p_sharpe -
    (p_kurt_ex / 24) * Math.pow(p_sharpe, 2)
);

let currentScore = 0;

if (mcRisk.value === 'neutral') {
    currentScore = p_asr;
} else if (mcRisk.value === 'averse') {
    currentScore = p_ret - (0.5 * riskAversionA * Math.pow(p_vol, 2));
} else {
    currentScore = p_ret - (0.15 * p_vol);
}

if (Number.isFinite(currentScore)) {
    mcPoints.push({
        x: p_vol * 100,
        y: p_ret * 100,
        score: currentScore
    });

    if (currentScore > maxScoreForColor) maxScoreForColor = currentScore;
    if (currentScore < minScoreForColor) minScoreForColor = currentScore;

    if (currentScore > bestScore) {
        bestScore = currentScore;
        bestPort = {
            ret: p_ret,
            vol: p_vol,
            sharpeRaw: p_sharpe,
            sharpeAdj: p_asr,
            skew: p_skew,
            kurt: p_kurt_ex,
            weights,
            jumpTailLoss,
            hardBufferTargetWeight: targetHardBufferWeight,
            hardBufferCurrentWeight: currentHardBufferWeight,
            defensiveCurrentWeight: currentDefensiveWeight
        };
    }
}
    }

    if (!bestPort) {
        alert("運算失敗，請檢查標的風險參數是否異常。");
        return;
    }

    const wList = [];
    const totalVal = totalStockValueTwd.value || 0;

    bestPort.weights.forEach((w, i) => {
        const optW = w * 100;
        const curW = totalVal > 0 ? (riskyAssets[i].marketValueTwd / totalVal) * 100 : 0;
        wList.push({
            ticker: riskyAssets[i].ticker,
            opt: optW.toFixed(2),
            cur: curW.toFixed(2),
            diff: (optW - curW).toFixed(2)
        });
    });

    wList.sort((a, b) => parseFloat(b.opt) - parseFloat(a.opt));

    const sampleN = Math.max(
    2,
    enrichedHistory.value.filter(x => x.dailyReturn !== null).length
);

const effectiveTrials = Math.max(1, mcPoints.length);

// 👇 同樣將 MC 算出的年化 Sharpe 退回週頻率
const mcPeriodSharpe = bestPort.sharpeRaw / Math.sqrt(52);

const psr = computePSR({
    sr: mcPeriodSharpe,
    srBenchmark: 0,
    skew: bestPort.skew,
    exKurt: bestPort.kurt,
    nObs: sampleN
});

const dsr = computeDSR({
    sr: mcPeriodSharpe,
    skew: bestPort.skew,
    exKurt: bestPort.kurt,
    nObs: sampleN,
    nTrials: effectiveTrials
});
const safeHardBufferGap = Math.max(
    0,
    (bestPort.hardBufferTargetWeight - bestPort.hardBufferCurrentWeight) * 100
);

const safeJumpTailLoss = Math.abs(bestPort.jumpTailLoss) < 1e-8
    ? 0
    : Math.abs(bestPort.jumpTailLoss);

    // ==========================================
    // 🎲 凱利公式 (Kelly Criterion) 曝險建議
    // ==========================================
    // 重新結算扣除通膨後的最終無風險利率
    let final_rf_effective = rf;
    if (enableInflation.value) {
        final_rf_effective = rf - 0.025;
    }
    
    const optRetExcess = bestPort.ret - final_rf_effective;
    const optVar = Math.pow(bestPort.vol, 2);

    let fullKelly = optVar > 0 ? (optRetExcess / optVar) : 0;
    let halfKelly = fullKelly / 2;

    if (bestPort.skew < -0.5 || safeJumpTailLoss > 0.05) {
        halfKelly = halfKelly * 0.8; 
    }

    let recommendedBuffer = (1 - halfKelly) * 100;
    recommendedBuffer = Math.max(0, Math.min(80, recommendedBuffer));

    if (fullKelly < 0) recommendedBuffer = 100; 

    mcOptimal.value = {
    ret: (bestPort.ret * 100).toFixed(2),
    vol: (bestPort.vol * 100).toFixed(2),

    // 顯示層：保留你原本的 ASR
    sharpe: bestPort.sharpeAdj.toFixed(3),

    // 新增：raw Sharpe / PSR / DSR
    sharpeRaw: bestPort.sharpeRaw.toFixed(3),
    psr: psr === null ? '-' : (psr * 100).toFixed(3),
    dsr: dsr === null ? '-' : (dsr * 100).toFixed(3),
    dsrTrials: effectiveTrials,
    dsrSampleN: sampleN,

    skew: bestPort.skew.toFixed(2),
    kurt: bestPort.kurt.toFixed(2),
    weights: wList,

    hardBufferTargetPct: (bestPort.hardBufferTargetWeight * 100).toFixed(2),
    hardBufferCurrentPct: (bestPort.hardBufferCurrentWeight * 100).toFixed(2),
    hardBufferGapPct: safeHardBufferGap.toFixed(2),
    defensiveSleevePct: (bestPort.defensiveCurrentWeight * 100).toFixed(2),
    bufferFloorRespected: bestPort.hardBufferCurrentWeight >= bestPort.hardBufferTargetWeight - 1e-6,

    jumpTailLossPct: (safeJumpTailLoss * 100).toFixed(2),
    
    // 新增 Kelly 輸出
    fullKelly: (fullKelly * 100).toFixed(1),
    halfKelly: (halfKelly * 100).toFixed(1),
    recommendedBuffer: recommendedBuffer.toFixed(1)
};

    chartMC = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Simulated Portfolios',
                    data: mcPoints,
                    backgroundColor: (context) => {
                        const val = context.raw?.score;
                        if (val === undefined || isNaN(val)) return '#3b82f6';
                        if (maxScoreForColor <= minScoreForColor) return 'rgba(59, 130, 246, 0.4)';
                        let ratio = (val - minScoreForColor) / (maxScoreForColor - minScoreForColor);
                        if (isNaN(ratio) || ratio < 0 || ratio > 1) ratio = 0.5;
                        return `rgba(${Math.round(255 * ratio)}, ${Math.round(150 * ratio)}, 200, 0.4)`;
                    },
                    pointRadius: 2
                },
                {
                    label: 'Optimal Portfolio',
                    data: [{ x: bestPort.vol * 100, y: bestPort.ret * 100 }],
                    backgroundColor: '#fbbf24',
                    pointRadius: 8,
                    borderColor: '#fff',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Vol: ${ctx.raw.x.toFixed(2)}%, Ret: ${ctx.raw.y.toFixed(2)}%`
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Volatility (σ%)' } },
                y: { title: { display: true, text: 'Expected Return (%)' } }
            }
        }
    });
}

        function getTypeColor(type) { return (type==='Buy' || type==='Expense') ? 'text-red-400' : 'text-green-400'; }
        function getCategoryColorCode(cat) { return '#3b82f6'; }
        function formatNumber(n) { return new Intl.NumberFormat('zh-TW', {maximumFractionDigits:0}).format(n||0); }
        function formatCurrency(n, currency='TWD') {
            const value = Number(n || 0);
            if (!Number.isFinite(value)) return '—';
            const ccy = String(currency || 'TWD').toUpperCase();
            if (ccy === 'TWD' || ccy === 'NTD' || ccy === 'NT$') {
                return 'NT$ ' + new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 0 }).format(value);
            }
            if (ccy === 'USD' || ccy === '$') {
                return 'US$ ' + new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
            }
            return `${ccy} ` + new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 2 }).format(value);
        }
        function formatPercent(n) { return ((n||0)*100).toFixed(1) + '%'; }
        const ZH_TEXT_MAP = Object.freeze({
            'OK': '正常',
            'FAIL': '失敗',
            'WARN': '警示',
            'N/A': '不適用',
            'true': '是',
            'false': '否',
            'baseline': '基準',
            'candidate': '候選',
            'watch': '觀察',
            'watch_only': '僅觀察',
            'reject': '拒絕',
            'rejected': '已拒絕',
            'pending_review': '待人工確認',
            'approved_for_manual_execution': '已核准手動執行',
            'constraint_pass_review_required': '約束通過，仍需審核',
            'manual_approval_required': '需要人工確認',
            'requires_manual_approval': '需要人工確認',
            'not_trade_order': '非交易指令',
                'price_return_features_available': '價格報酬特徵可用',
                'fallback_metadata_only': '僅有備援中繼資料',
                'positive_research_prior': '正向研究先驗',
                'negative_research_prior': '負向研究先驗',
                'neutral_research_prior': '中性研究先驗',
                'insufficient_data': '資料不足',
                'further_research': '進一步研究',
                'observe_only': '僅供觀察',
                'observe_only_insufficient_data': '僅觀察｜資料不足',
                'observe_only_risk_penalty': '僅觀察｜風險懲罰',
                'negative_prior_observe': '負向先驗｜觀察',
            'execution_permission_false': '未開放自動執行',
            'model_candidate_generated': '模型候選已產生',
            'watch_only_with_governance_warnings': '僅觀察｜治理警示',
            'current_weight': '目前投組權重',
            'current': '目前投組',
            'inverse_vol_baseline': '逆波動基準',
            'scipy_min_variance_fallback': 'SciPy 最小變異數備援',
            'skfolio_min_variance': 'skfolio 最小變異數',
            'skfolio_cvar_minimize': 'skfolio 最小化 CVaR',
            'riskfolio_min_variance': 'Riskfolio 最小變異數',
            'riskfolio_cvar_minimize': 'Riskfolio 最小化 CVaR',
            'riskfolio_risk_parity_mv': 'Riskfolio 風險平價',
            'riskfolio_hrp_mv': 'Riskfolio HRP',
            'risk_off_liquidity_pressure': '避險／流動性壓力',
            'risk_on': '風險偏好',
            'neutral': '中性',
            'overweight': '加碼',
            'underweight': '減碼',
            'equal_weight': '等權重',
            'relative_overweight_prior': '相對加碼先驗',
            'relative_underweight_prior': '相對減碼先驗',
            'high': '高',
            'medium': '中',
            'low': '低',
            'critical': '嚴重',
            'warning': '警示',
            'info': '資訊',
            'soft_pass': '軟性通過',
            'hard_fail': '硬性失敗',
            'pass': '通過',
            'constraint_pass': '約束通過',
            'constraint_violation': '違反約束',
            'high_turnover_review': '高換手率待審',
            'turnover_too_high': '換手率過高',
                'research_validation_pass': '研究驗證通過',
                'watch_only_validation': '僅觀察驗證',
                'research_validation_failed': '研究驗證失敗',
                'blocked_by_validation_gate': '驗證閘門阻擋',
                'manual_research_proposal': '人工研究提案',
                'watch_only_proposal': '僅觀察提案',
                'blocked_by_alpha_validation_gate': 'Alpha 驗證閘門阻擋',
                'blocked_constraint': '約束阻擋',
                'watch_high_turnover': '高換手率觀察',
                'blocked_by_ranking': '排序層阻擋',
                'pre_execution_draft_available_for_manual_review': '預執行草案可供人工檢視',
                'no_manual_research_proposal': '無人工研究提案',
                'draftable_for_manual_entry_review': '可形成手動輸入前檢查草案',
                'g1_feature_coverage': '特徵覆蓋',
                'g2_alpha_research_exists': 'Alpha 研究資料存在',
                'g3_rebalance_ranking_exists': '調倉排序資料存在',
                'g4_walk_forward_sample': '滾動樣本外深度',
                'g5_model_governance': '模型治理',
                'g6_safety_flags': '安全旗標',
                'g7_candidate_availability': '研究候選可用性',
            'formal_rebalance_review_draft_available': '正式再平衡草案可供人工審閱',
            'blocked_missing_alpha_validation': '阻擋｜缺 Alpha 驗證',
            'blocked_no_manual_research_proposal': '阻擋｜無人工研究提案',
            'blocked_no_pre_execution_draft': '阻擋｜無預執行草案',
            'blocked_no_formal_draft': '阻擋｜無正式草案',
            'blocked_formal_draft': '正式草案阻擋',
            'formal_review_draft': '正式審閱草案',
            'alpha_validation_gate_not_passed': 'Alpha 驗證閘門未通過',
            'governance_not_full_pass': '模型治理未完全通過',
            'no_rebalance_candidate_cleared_research_threshold': '沒有調倉候選通過研究門檻',
            'no_manual_research_proposal': '沒有人工研究提案',
            'no_pre_execution_draft': '沒有預執行草案',
            'pre_execution_draft_not_draftable': '預執行草案不可形成正式草案',
            'manual_proposal_not_promoted': '人工提案未升級',
            'turnover_above_formal_draft_threshold': '換手率高於正式草案門檻',
            'ranking_score_below_formal_draft_threshold': '排序分數低於正式草案門檻',
            'manual_trade_ticket_review_draft_available': '人工交易票據草案可供審閱',
            'blocked_by_formal_rebalance_draft_gate': '正式再平衡草案閘門阻擋',
            'blocked_missing_explicit_trade_lines_or_target_weights': '阻擋｜缺明確交易列或目標權重',
            'blocked_no_formal_rebalance_draft': '阻擋｜無正式再平衡草案',
            'formal_rebalance_draft_gate_not_available': '正式再平衡草案閘門不可用',
            'no_formal_rebalance_draft_rows': '沒有正式再平衡草案列',
            'missing_explicit_trade_lines_or_target_weights': '缺明確交易列或目標權重',
            'manual_ticket_draft_requires_human_entry': '人工票據草案｜需手動輸入',
            'risk_reduction_detected': '偵測到風險降低',
            'missing_data': '資料不足',
            'insufficient_data': '資料不足',
            'sample_too_short': '樣本過短',
            'proxy_only': '僅代理估計',
            'PROXY_ONLY': '僅代理估計',
            'true_walk_forward_from_price_returns': '價格報酬真實滾動樣本外',
            'proxy_from_robustness_windows_not_true_walk_forward': '由穩健性視窗代理，不是真實樣本外',
            'absolute_expected_return_forecast_enabled': '已啟用絕對預期報酬預測',
            'absolute_expected_return_forecast_disabled': '未啟用絕對預期報酬預測',
            'alpha_model_enabled': '已啟用 alpha 模型',
            'alpha_model_disabled': '未啟用 alpha 模型',
            'maximum_sharpe_optimization_enabled': '已啟用最大夏普最佳化',
            'maximum_sharpe_optimization_disabled': '未啟用最大夏普最佳化',
            'rules_based_view_engine': '規則化觀點引擎',
            'no_manual_views': '不接受任意手動觀點',
            'safe_mode': '安全模式',
            'BUY': '買入',
            'SELL': '賣出',
            'Buy': '買入',
            'Sell': '賣出',
            'Deposit': '入金',
            'Withdraw': '出金',
            'Expense': '支出',

            'regime_watch_review_required': '市場狀態觀察｜需人工審核',
            'regime_watch_high_turnover': '市場狀態觀察｜高換手率',
            'watch_only_validation': '僅觀察驗證',
            'review_required': '需要審核',
            'REVIEW_CANDIDATE': '候選待審',
            'REJECT_OR_REWORK': '拒絕或重做',
            'BLOCKED': '已阻擋',
            'blocked': '已阻擋',
            'strict': '嚴格模式',
            'deterministic_stress_proxy': '確定性壓力代理',
            'rule_based': '規則式',
            'rules_based': '規則式',
            'enabled': '啟用',
            'disabled': '停用',
            'cash': '現金',
            'CASH': '現金',
            'crypto': '加密資產',
            'CRYPTO': '加密資產',
            'us_tech': '美國科技',
            'US_TECH': '美國科技',
            'taiwan_tech': '台股科技',
            'TAIWAN_TECH': '台股科技',
            'TAIWAN TECH': '台股科技',
            'gold': '黃金',
            'global_equity': '全球股票',
            'us_equity': '美股',
            'emerging_market': '新興市場',
            'theme_etf': '主題 ETF',
            'commodity_equity': '商品股票',
            'other': '其他',
            'neutral_or_no_edge_prior': '中性／無明確優勢先驗',
            'three_year_window_unavailable': '3 年樣本視窗不可用',
            'sample_quality_limited': '樣本品質受限',
            'Risk-off regime raises liquidity buffer.': '避險環境提高流動性緩衝需求。',
            'Crypto tail risk is penalized under liquidity pressure.': '加密資產尾部風險在流動性壓力下受懲罰。',
            'High-duration tech is stress-sensitive.': '高存續期科技資產對壓力環境敏感。',
            'Small hedge allocation; not treated as guaranteed hedge.': '小幅避險配置；不視為保證避險。',
            'Sample quality limited: three_year_window_unavailable': '樣本品質受限：3 年樣本視窗不可用',
            '樣本品質限制：three_year_window_unavailable': '樣本品質限制：3 年樣本視窗不可用',
            'rebalance_candidate_ranking_engine': '調倉研究候選排序引擎',
            'exclude_constraint_violation': '排除｜違反約束',
            'exclude_high_turnover': '排除｜高換手率',
            'exclude_low_research_value': '排除｜研究價值不足',
            'observe_sample_quality': '僅觀察｜樣本品質受限',
            'blocked_governance': '治理阻擋',
            'turnover_low': '低換手率',
            'turnover_moderate': '中等換手率',
            'turnover_high_review': '高換手率警示',
            'turnover_unknown_or_zero': '換手率未知或為零',
            'alpha_alignment_positive': 'Alpha 對齊偏正向',
            'alpha_alignment_neutral': 'Alpha 對齊中性',
            'alpha_alignment_negative': 'Alpha 對齊偏負向',
            'alpha_alignment_unavailable': 'Alpha 對齊不可用',
            'alpha_alignment_no_material_delta': 'Alpha 對齊無重大變動',
            'regime_overlay_unavailable': '市場狀態覆蓋不可用',
            'no_explicit_risk_reduction_score': '沒有明確風險降低分數',
            'needs_more_out_of_sample_evidence': '需要更多樣本外證據',
            'cash_disguise_high_cash': '現金化過高警示',
            'cash_disguise_watch': '現金化觀察',
            'cash_disguise_single_cash_proxy': '單一現金代理集中',
            'constraint_warning': '約束警示',
            'soft_gold_min_pct': '黃金低於軟性下限',
            'soft_gold_target_pct': '黃金軟目標',
            'soft_gold_target_pct_source_funding': '黃金軟目標資金來源',
            'diagnostic_status': '診斷狀態',
            'clear_for_review_only_draft_check': '可檢查人工審閱草案',
            'watch_items_only': '僅有觀察項目',
            'formal_pass_conditions': '正式草案通過條件',
            'manual_approval_input': '人工 override 輸入',
            'trading_sizing': '交易 sizing',
            'formal_rebalance_draft_gate': '正式再平衡草案閘門',
            'manual_trade_ticket': '人工交易票據',
            'paper_trade_tracker': '紙上追蹤',
            'alpha_validation_not_passed': 'Alpha 驗證未通過',
            'no_further_research_candidates': '沒有進一步研究候選',
            'manual_override_disabled': '人工 override 未啟用',
            'missing_cash_balance': '現金餘額缺失',
            'incomplete_real_world_price_fetch': '價格資料未全部即時抓取',
            'minimum_trade_unit_not_met': '最小交易單位不合',
            'no_formal_rebalance_draft': '沒有正式再平衡草案',
            'no_manual_trade_ticket': '沒有人工交易票據',
            'no_paper_trade_tracking_items': '沒有紙上追蹤項目',
            'governance_not_clean_pass': '治理未完全通過',
            'walk_forward_evidence_limited': '樣本外證據有限',
            'blocker': '阻擋',
            'watch': '觀察',
            'Income': '收入'
        });
        function zhText(value) {
            if (value === null || value === undefined || value === '') return '—';
            if (Array.isArray(value)) return zhList(value);
            if (typeof value === 'boolean') return value ? '是' : '否';
            if (typeof value === 'number') return Number.isFinite(value) ? String(value) : '—';
            const raw = String(value);
            if (ZH_TEXT_MAP[raw] !== undefined) return ZH_TEXT_MAP[raw];
            const lower = raw.toLowerCase();
            if (ZH_TEXT_MAP[lower] !== undefined) return ZH_TEXT_MAP[lower];
            const upperSpaced = raw.replace(/_/g, ' ').toUpperCase();
            if (ZH_TEXT_MAP[upperSpaced] !== undefined) return ZH_TEXT_MAP[upperSpaced];

            const draftTrimMatch = raw.match(/^v3_0_v2_3_from_v2_2_trim_(.+)_(25|50|100)pct_to_BOXX$/);
            if (draftTrimMatch) {
                const asset = draftTrimMatch[1].replace(/_USD$/,'-USD').replace(/_/g, '-');
                return `v3.0｜v2.3 ${asset} 減碼 ${draftTrimMatch[2]}% 轉 BOXX`;
            }
            const v52TrimMatch = raw.match(/^v5_2_v2_3_from_v2_2_trim_(.+)_(25|50|100)pct_to_BOXX$/);
            if (v52TrimMatch) {
                const asset = v52TrimMatch[1].replace(/_USD$/,'-USD').replace(/_/g, '-');
                return `v5.2｜${asset} 減碼 ${v52TrimMatch[2]}% 轉 BOXX`;
            }
            const v52V21Match = raw.match(/^v5_2_v2_3_v2_1_(.+)$/);
            if (v52V21Match) return `v5.2｜${zhText(v52V21Match[1])}`;
            const v3CandidateMatch = raw.match(/^v3_0_v2_1_(.+)$/);
            if (v3CandidateMatch) return `v3.0｜v2.1 ${zhText(v3CandidateMatch[1])}`;
            const v2CandidateMatch = raw.match(/^v2_1_(.+)$/);
            if (v2CandidateMatch) return `v2.1 ${zhText(v2CandidateMatch[1])}`;

            let translated = raw;
            const phraseMap = {
                'three_year_window_unavailable': '3 年樣本視窗不可用',
                'neutral_or_no_edge_prior': '中性／無明確優勢先驗',
                'regime_watch_review_required': '市場狀態觀察｜需人工審核',
                'regime_watch_high_turnover': '市場狀態觀察｜高換手率',
                'watch_only_validation': '僅觀察驗證',
                'risk_off_liquidity_pressure': '避險／流動性壓力',
                'manual_approval_required': '需要人工確認',
                'not_trade_order': '非交易指令',
                'price_return_features_available': '價格報酬特徵可用',
                'fallback_metadata_only': '僅有備援中繼資料',
                'positive_research_prior': '正向研究先驗',
                'negative_research_prior': '負向研究先驗',
                'neutral_research_prior': '中性研究先驗',
                'insufficient_data': '資料不足',
                'further_research': '進一步研究',
                'observe_only': '僅供觀察',
                'observe_only_insufficient_data': '僅觀察｜資料不足',
                'observe_only_risk_penalty': '僅觀察｜風險懲罰',
                'negative_prior_observe': '負向先驗｜觀察',
                'exclude_constraint_violation': '排除｜違反約束',
                'exclude_high_turnover': '排除｜高換手率',
                'exclude_low_research_value': '排除｜研究價值不足',
                'observe_sample_quality': '僅觀察｜樣本品質受限',
                'blocked_governance': '治理阻擋',
                'constraint_warning:': '約束警示：',
                'constraint_violation:': '違反約束：',
                'regime_status:': '市場狀態：',
                'feature_status:': '特徵狀態：',
                'bucket:': '資產桶：',
                'band:': '區間：',
                'soft_gold_min_pct': '黃金低於軟性下限',
                'needs_more_out_of_sample_evidence': '需要更多樣本外證據',
                'alpha_alignment_positive': 'Alpha 對齊偏正向',
                'alpha_alignment_neutral': 'Alpha 對齊中性',
                'alpha_alignment_negative': 'Alpha 對齊偏負向',
                'turnover_low': '低換手率',
                'turnover_moderate': '中等換手率',
                'turnover_high_review': '高換手率警示',
                'turnover_too_high': '換手率過高',
                'research_validation_pass': '研究驗證通過',
                'watch_only_validation': '僅觀察驗證',
                'research_validation_failed': '研究驗證失敗',
                'blocked_by_validation_gate': '驗證閘門阻擋',
                'manual_research_proposal': '人工研究提案',
                'watch_only_proposal': '僅觀察提案',
                'blocked_by_alpha_validation_gate': 'Alpha 驗證閘門阻擋',
                'blocked_constraint': '約束阻擋',
                'watch_high_turnover': '高換手率觀察',
                'blocked_by_ranking': '排序層阻擋',
                'pre_execution_draft_available_for_manual_review': '預執行草案可供人工檢視',
                'no_manual_research_proposal': '無人工研究提案',
                'draftable_for_manual_entry_review': '可形成手動輸入前檢查草案',
                'g1_feature_coverage': '特徵覆蓋',
                'g2_alpha_research_exists': 'Alpha 研究資料存在',
                'g3_rebalance_ranking_exists': '調倉排序資料存在',
                'g4_walk_forward_sample': '滾動樣本外深度',
                'g5_model_governance': '模型治理',
                'g6_safety_flags': '安全旗標',
                'g7_candidate_availability': '研究候選可用性'
            };
            Object.entries(phraseMap).forEach(([from, to]) => {
                translated = translated.split(from).join(to);
            });
            if (translated !== raw) return translated;
            return raw;
        }
        function zhList(value) {
            if (!Array.isArray(value)) return zhText(value);
            if (!value.length) return '—';
            return value.map(item => zhText(item)).join('、');
        }
        function zhBool(value) {
            if (value === true || value === 'true' || value === 1) return '是';
            if (value === false || value === 'false' || value === 0) return '否';
            return zhText(value);
        }
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


       const humanApprovalLayer = ref(null);
       const humanApprovalLayerError = ref('');

       async function loadHumanApprovalLayer() {
    try {
        humanApprovalLayerError.value = '';
        const response = await fetch(`data/optimizer/human_approval_layer_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            humanApprovalLayer.value = null;
            humanApprovalLayerError.value = `尚未讀到 v2.4 Human Approval Layer (${response.status})`;
            return;
        }
        const data = await response.json();
        humanApprovalLayer.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        humanApprovalLayer.value = null;
        humanApprovalLayerError.value = err?.message || String(err);
    }
}

       const humanApprovalTickets = computed(() => {
    return Array.isArray(humanApprovalLayer.value?.approval_tickets) ? humanApprovalLayer.value.approval_tickets : [];
});

       const humanApprovalSummary = computed(() => {
    return humanApprovalLayer.value?.summary || {};
});

       const humanApprovalVisibleTickets = computed(() => {
    return humanApprovalTickets.value.slice(0, 12);
});

       const actionAuditTrail = ref(null);
       const actionAuditTrailError = ref('');

       async function loadActionAuditTrail() {
    try {
        actionAuditTrailError.value = '';
        const response = await fetch(`data/optimizer/action_audit_trail_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            actionAuditTrail.value = null;
            actionAuditTrailError.value = `尚未讀到 v2.5 Action Audit Trail (${response.status})`;
            return;
        }
        const data = await response.json();
        actionAuditTrail.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        actionAuditTrail.value = null;
        actionAuditTrailError.value = err?.message || String(err);
    }
}

       const actionAuditSummary = computed(() => {
    return actionAuditTrail.value?.summary || {};
});

       const actionAuditEvents = computed(() => {
    const rows = actionAuditTrail.value?.audit_events || actionAuditTrail.value?.events || [];
    return Array.isArray(rows) ? rows.slice(0, 12) : [];
});

       const regimeAwareOptimizer = ref(null);
       const regimeAwareError = ref('');

       async function loadRegimeAwareOptimizer() {
    try {
        regimeAwareError.value = '';
        const response = await fetch(`data/optimizer/regime_aware_optimizer_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            regimeAwareOptimizer.value = null;
            regimeAwareError.value = `尚未讀到 v3.0 Regime-Aware Optimizer (${response.status})`;
            return;
        }
        const data = await response.json();
        regimeAwareOptimizer.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        regimeAwareOptimizer.value = null;
        regimeAwareError.value = err?.message || String(err);
    }
}

       const regimeAwareSummary = computed(() => regimeAwareOptimizer.value?.summary || {});
       const regimeAwareRegime = computed(() => regimeAwareOptimizer.value?.regime || {});
       const regimeAwareActivePolicy = computed(() => regimeAwareOptimizer.value?.active_policy || {});
       const regimeAwareCovariancePolicy = computed(() => regimeAwareActivePolicy.value?.covariance_policy || {});
       const regimeAwareDrafts = computed(() => {
    const rows = regimeAwareOptimizer.value?.regime_aware_drafts || [];
    return Array.isArray(rows) ? rows : [];
});
       const regimeAwareVisibleDrafts = computed(() => regimeAwareDrafts.value.slice(0, 10));

       const blackLittermanSandbox = ref(null);
       const blackLittermanError = ref('');

       async function loadBlackLittermanSandbox() {
    try {
        blackLittermanError.value = '';
        const response = await fetch(`data/optimizer/black_litterman_sandbox_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            blackLittermanSandbox.value = null;
            blackLittermanError.value = `尚未讀到 v3.1 Black-Litterman Sandbox (${response.status})`;
            return;
        }
        const data = await response.json();
        blackLittermanSandbox.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        blackLittermanSandbox.value = null;
        blackLittermanError.value = err?.message || String(err);
    }
}

       const blackLittermanSummary = computed(() => blackLittermanSandbox.value?.summary || {});
       const blackLittermanViewEngine = computed(() => blackLittermanSandbox.value?.view_engine || {});
       const blackLittermanViews = computed(() => {
    const rows = blackLittermanSandbox.value?.views || [];
    return Array.isArray(rows) ? rows : [];
});
       const blackLittermanPosteriorCandidates = computed(() => {
    const rows = blackLittermanSandbox.value?.posterior_candidates || [];
    return Array.isArray(rows) ? rows : [];
});


       const expectedReturnModel = ref(null);
       const expectedReturnError = ref('');

       async function loadExpectedReturnModel() {
    try {
        expectedReturnError.value = '';
        const response = await fetch(`data/optimizer/expected_return_model_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            expectedReturnModel.value = null;
            expectedReturnError.value = `尚未讀到 v3.2 Expected Return Model (${response.status})`;
            return;
        }
        const data = await response.json();
        expectedReturnModel.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        expectedReturnModel.value = null;
        expectedReturnError.value = err?.message || String(err);
    }
}

       const expectedReturnSummary = computed(() => expectedReturnModel.value?.summary || {});
       const expectedReturnPolicy = computed(() => expectedReturnModel.value?.model_policy || {});
       const expectedReturnBucketPriors = computed(() => {
    const rows = expectedReturnModel.value?.bucket_priors || [];
    return Array.isArray(rows) ? rows : [];
});
       const expectedReturnAssetPriors = computed(() => {
    const rows = expectedReturnModel.value?.asset_expected_return_priors || [];
    return Array.isArray(rows) ? rows : [];
});
       const expectedReturnVisibleBuckets = computed(() => expectedReturnBucketPriors.value.slice(0, 10));
       const expectedReturnVisibleAssets = computed(() => expectedReturnAssetPriors.value.slice(0, 10));


       const forecastFeatureStore = ref(null);
       const forecastFeatureError = ref('');

       async function loadForecastFeatureStore() {
    try {
        forecastFeatureError.value = '';
        const response = await fetch(`data/alpha/feature_store_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            forecastFeatureStore.value = null;
            forecastFeatureError.value = `尚未讀到 v5.0 Forecast Feature Store (${response.status})`;
            return;
        }
        const data = await response.json();
        forecastFeatureStore.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        forecastFeatureStore.value = null;
        forecastFeatureError.value = err?.message || String(err);
    }
}

       const forecastFeatureSummary = computed(() => forecastFeatureStore.value?.summary || {});
       const forecastFeatureSample = computed(() => forecastFeatureStore.value?.sample || {});
       const forecastFeatureRows = computed(() => {
    const rows = forecastFeatureStore.value?.asset_features || [];
    return Array.isArray(rows) ? rows : [];
});
       const forecastFeatureVisibleRows = computed(() => forecastFeatureRows.value.slice(0, 10));

       const alphaResearchSandbox = ref(null);
       const alphaResearchError = ref('');

       async function loadAlphaResearchSandbox() {
    try {
        alphaResearchError.value = '';
        const response = await fetch(`data/alpha/alpha_research_sandbox_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            alphaResearchSandbox.value = null;
            alphaResearchError.value = `尚未讀到 v5.1 Alpha Research Sandbox (${response.status})`;
            return;
        }
        const data = await response.json();
        alphaResearchSandbox.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        alphaResearchSandbox.value = null;
        alphaResearchError.value = err?.message || String(err);
    }
}

       const alphaResearchSummary = computed(() => alphaResearchSandbox.value?.summary || {});
       const alphaResearchPolicy = computed(() => alphaResearchSandbox.value?.model_policy || {});
       const alphaResearchRows = computed(() => {
    const rows = alphaResearchSandbox.value?.asset_alpha_research || [];
    return Array.isArray(rows) ? rows : [];
});
       const alphaResearchVisibleRows = computed(() => alphaResearchRows.value.slice(0, 10));

       const rebalanceCandidateRanking = ref(null);
       const rebalanceRankingError = ref('');

       async function loadRebalanceCandidateRanking() {
    try {
        rebalanceRankingError.value = '';
        const response = await fetch(`data/alpha/rebalance_candidate_ranking_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            rebalanceCandidateRanking.value = null;
            rebalanceRankingError.value = `尚未讀到 v5.2 Rebalance Candidate Ranking (${response.status})`;
            return;
        }
        const data = await response.json();
        rebalanceCandidateRanking.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        rebalanceCandidateRanking.value = null;
        rebalanceRankingError.value = err?.message || String(err);
    }
}

       const rebalanceRankingSummary = computed(() => rebalanceCandidateRanking.value?.summary || {});
       const rebalanceRankingPolicy = computed(() => rebalanceCandidateRanking.value?.ranking_policy || {});
       const rebalanceRankingRows = computed(() => {
    const rows = rebalanceCandidateRanking.value?.ranking_rows || [];
    return Array.isArray(rows) ? rows : [];
});
       const rebalanceRankingVisibleRows = computed(() => rebalanceRankingRows.value.slice(0, 10));

       const alphaValidationGate = ref(null);
       const alphaValidationError = ref('');

       async function loadAlphaValidationGate() {
    try {
        alphaValidationError.value = '';
        const response = await fetch(`data/alpha/alpha_validation_gate_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            alphaValidationGate.value = null;
            alphaValidationError.value = `尚未讀到 v6.0 Alpha Validation Gate (${response.status})`;
            return;
        }
        const data = await response.json();
        alphaValidationGate.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        alphaValidationGate.value = null;
        alphaValidationError.value = err?.message || String(err);
    }
}

       const alphaValidationSummary = computed(() => alphaValidationGate.value?.summary || {});
       const alphaValidationGates = computed(() => {
    const rows = alphaValidationGate.value?.gates || [];
    return Array.isArray(rows) ? rows : [];
});
       const alphaValidationVisibleGates = computed(() => alphaValidationGates.value.slice(0, 8));

       const manualRebalanceProposal = ref(null);
       const manualProposalError = ref('');

       async function loadManualRebalanceProposal() {
    try {
        manualProposalError.value = '';
        const response = await fetch(`data/alpha/manual_rebalance_proposal_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            manualRebalanceProposal.value = null;
            manualProposalError.value = `尚未讀到 v7.0 Manual Rebalance Proposal (${response.status})`;
            return;
        }
        const data = await response.json();
        manualRebalanceProposal.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        manualRebalanceProposal.value = null;
        manualProposalError.value = err?.message || String(err);
    }
}

       const manualProposalSummary = computed(() => manualRebalanceProposal.value?.summary || {});
       const manualProposalRows = computed(() => {
    const rows = manualRebalanceProposal.value?.proposal_rows || [];
    return Array.isArray(rows) ? rows : [];
});
       const manualProposalVisibleRows = computed(() => manualProposalRows.value.slice(0, 8));

       const executionReadyDraft = ref(null);
       const executionDraftError = ref('');

       async function loadExecutionReadyDraft() {
    try {
        executionDraftError.value = '';
        const response = await fetch(`data/alpha/execution_ready_draft_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            executionReadyDraft.value = null;
            executionDraftError.value = `尚未讀到 v8.0 Execution-Ready Draft (${response.status})`;
            return;
        }
        const data = await response.json();
        executionReadyDraft.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        executionReadyDraft.value = null;
        executionDraftError.value = err?.message || String(err);
    }
}

       const executionDraftSummary = computed(() => executionReadyDraft.value?.summary || {});
       const executionDraftRows = computed(() => {
    const rows = executionReadyDraft.value?.draft_rows || [];
    return Array.isArray(rows) ? rows : [];
});
       const executionDraftVisibleRows = computed(() => executionDraftRows.value.slice(0, 5));



       const formalDraftPassConditions = ref(null);
       const formalDraftPassError = ref('');
       async function loadFormalDraftPassConditions() {
        formalDraftPassError.value = '';
        try {
            const response = await fetch('data/alpha/formal_draft_pass_conditions_latest.json?v=' + Date.now());
            if (!response.ok) { formalDraftPassConditions.value = null; formalDraftPassError.value = `尚未讀到 v8.1 Pass Conditions (${response.status})`; return; }
            const data = await response.json();
            formalDraftPassConditions.value = data && typeof data === 'object' ? data : null;
        } catch (err) { formalDraftPassConditions.value = null; formalDraftPassError.value = err?.message || String(err); }
       }
       const formalDraftPassSummary = computed(() => formalDraftPassConditions.value?.summary || {});

       const tradingConstraintsSnapshot = ref(null);
       const tradingConstraintsError = ref('');
       async function loadTradingConstraintsSnapshot() {
        tradingConstraintsError.value = '';
        try {
            const response = await fetch('data/alpha/trading_constraints_snapshot_latest.json?v=' + Date.now());
            if (!response.ok) { tradingConstraintsSnapshot.value = null; tradingConstraintsError.value = `尚未讀到交易 sizing 約束 (${response.status})`; return; }
            const data = await response.json();
            tradingConstraintsSnapshot.value = data && typeof data === 'object' ? data : null;
        } catch (err) { tradingConstraintsSnapshot.value = null; tradingConstraintsError.value = err?.message || String(err); }
       }
       const tradingConstraintsSummary = computed(() => tradingConstraintsSnapshot.value?.summary || {});
       const tradingConstraintsRows = computed(() => Array.isArray(tradingConstraintsSnapshot.value?.asset_rows) ? tradingConstraintsSnapshot.value.asset_rows : []);
       const tradingConstraintsVisibleRows = computed(() => tradingConstraintsRows.value.slice(0, 6));

       const paperTradeTracker = ref(null);
       const paperTradeError = ref('');
       async function loadPaperTradeTracker() {
        paperTradeError.value = '';
        try {
            const response = await fetch('data/alpha/paper_trade_tracker_latest.json?v=' + Date.now());
            if (!response.ok) { paperTradeTracker.value = null; paperTradeError.value = `尚未讀到紙上追蹤 (${response.status})`; return; }
            const data = await response.json();
            paperTradeTracker.value = data && typeof data === 'object' ? data : null;
        } catch (err) { paperTradeTracker.value = null; paperTradeError.value = err?.message || String(err); }
       }
       const paperTradeSummary = computed(() => paperTradeTracker.value?.summary || {});
       const paperTradeRows = computed(() => Array.isArray(paperTradeTracker.value?.paper_trade_rows) ? paperTradeTracker.value.paper_trade_rows : []);
       const paperTradeVisibleRows = computed(() => paperTradeRows.value.slice(0, 5));

       const tradeSizingDiagnostics = ref(null);
       const tradeSizingDiagnosticsError = ref('');
       async function loadTradeSizingDiagnostics() {
        tradeSizingDiagnosticsError.value = '';
        try {
            const response = await fetch('data/alpha/trade_sizing_diagnostics_latest.json?v=' + Date.now(), { cache: 'no-store' });
            if (!response.ok) { tradeSizingDiagnostics.value = null; tradeSizingDiagnosticsError.value = `尚未讀到 v9.3 阻擋診斷 (${response.status})`; return; }
            const data = await response.json();
            tradeSizingDiagnostics.value = data && typeof data === 'object' ? data : null;
        } catch (err) { tradeSizingDiagnostics.value = null; tradeSizingDiagnosticsError.value = err?.message || String(err); }
       }
       const tradeSizingDiagnosticsSummary = computed(() => tradeSizingDiagnostics.value?.summary || {});
       const tradeSizingDiagnosticsIssues = computed(() => Array.isArray(tradeSizingDiagnostics.value?.issues) ? tradeSizingDiagnostics.value.issues : []);
       const tradeSizingDiagnosticsVisibleIssues = computed(() => tradeSizingDiagnosticsIssues.value.slice(0, 8));
       const tradeSizingDiagnosticsNextActions = computed(() => Array.isArray(tradeSizingDiagnostics.value?.next_actions) ? tradeSizingDiagnostics.value.next_actions.slice(0, 6) : []);

       const formalRebalanceDraftGate = ref(null);
       const formalDraftGateError = ref('');

       async function loadFormalRebalanceDraftGate() {
    try {
        formalDraftGateError.value = '';
        const response = await fetch(`data/alpha/formal_rebalance_draft_gate_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            formalRebalanceDraftGate.value = null;
            formalDraftGateError.value = `尚未讀到 v8.1 Formal Rebalance Draft Gate (${response.status})`;
            return;
        }
        const data = await response.json();
        formalRebalanceDraftGate.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        formalRebalanceDraftGate.value = null;
        formalDraftGateError.value = err?.message || String(err);
    }
}

       const formalDraftGateSummary = computed(() => formalRebalanceDraftGate.value?.summary || {});
       const formalDraftRows = computed(() => {
    const rows = formalRebalanceDraftGate.value?.formal_draft_rows || [];
    return Array.isArray(rows) ? rows : [];
});
       const formalDraftVisibleRows = computed(() => formalDraftRows.value.slice(0, 5));

       const manualTradeTicket = ref(null);
       const manualTradeTicketError = ref('');

       async function loadManualTradeTicket() {
    try {
        manualTradeTicketError.value = '';
        const response = await fetch(`data/alpha/manual_trade_ticket_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            manualTradeTicket.value = null;
            manualTradeTicketError.value = `尚未讀到 v9.0 Manual Trade Ticket (${response.status})`;
            return;
        }
        const data = await response.json();
        manualTradeTicket.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        manualTradeTicket.value = null;
        manualTradeTicketError.value = err?.message || String(err);
    }
}

       const manualTradeTicketSummary = computed(() => manualTradeTicket.value?.summary || {});
       const manualTradeTicketRows = computed(() => {
    const rows = manualTradeTicket.value?.ticket_rows || [];
    return Array.isArray(rows) ? rows : [];
});
       const manualTradeTicketVisibleRows = computed(() => manualTradeTicketRows.value.slice(0, 5));

       const walkForwardBacktest = ref(null);
       const walkForwardError = ref('');

       async function loadWalkForwardBacktest() {
    try {
        walkForwardError.value = '';
        const response = await fetch(`data/optimizer/walk_forward_backtest_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            walkForwardBacktest.value = null;
            walkForwardError.value = `尚未讀到 v3.3 Walk-forward Backtest (${response.status})`;
            return;
        }
        const data = await response.json();
        walkForwardBacktest.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        walkForwardBacktest.value = null;
        walkForwardError.value = err?.message || String(err);
    }
}

       const walkForwardSummary = computed(() => walkForwardBacktest.value?.summary || {});
       const walkForwardAggregate = computed(() => {
    const rows = walkForwardBacktest.value?.aggregate_results || [];
    return Array.isArray(rows) ? rows : [];
});
       const walkForwardVisibleRows = computed(() => walkForwardAggregate.value.slice(0, 10));

       const modelGovernanceDashboard = ref(null);
       const modelGovernanceError = ref('');

       async function loadModelGovernanceDashboard() {
    try {
        modelGovernanceError.value = '';
        const response = await fetch(`data/optimizer/model_governance_dashboard_latest.json?v=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) {
            modelGovernanceDashboard.value = null;
            modelGovernanceError.value = `尚未讀到 v3.4 Model Governance Dashboard (${response.status})`;
            return;
        }
        const data = await response.json();
        modelGovernanceDashboard.value = data && typeof data === 'object' ? data : null;
    } catch (err) {
        modelGovernanceDashboard.value = null;
        modelGovernanceError.value = err?.message || String(err);
    }
}

       const modelGovernanceSummary = computed(() => modelGovernanceDashboard.value?.summary || {});
       const modelGovernanceRegistry = computed(() => {
    const rows = modelGovernanceDashboard.value?.model_registry || [];
    return Array.isArray(rows) ? rows : [];
});
       const modelGovernanceFlags = computed(() => {
    const rows = modelGovernanceDashboard.value?.governance_flags || [];
    return Array.isArray(rows) ? rows : [];
});
       const modelGovernanceVisibleRegistry = computed(() => modelGovernanceRegistry.value.slice(0, 16));
       const modelGovernanceVisibleFlags = computed(() => modelGovernanceFlags.value.slice(0, 10));

       function approvalBadgeClass(status) {
    const s = String(status || '').toLowerCase();
    if (s.includes('approved')) return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';
    if (s.includes('reject') || s.includes('blocked')) return 'border-red-500/30 bg-red-500/10 text-red-300';
    if (s.includes('watch')) return 'border-sky-500/30 bg-sky-500/10 text-sky-300';
    return 'border-amber-500/30 bg-amber-500/10 text-amber-300';
}

        function machineReviewLabel(item) {
            const data = item || {};
            const reasons = Array.isArray(data.reason_codes) ? data.reason_codes.map(x => String(x).toLowerCase()) : [];
            const flags = Array.isArray(data.constraint_flags) ? data.constraint_flags.map(x => String(x).toLowerCase()) : [];
            const modelStatus = String(data.model_status || '').toLowerCase();
            const constraintStatus = String(data.constraint_status || '').toLowerCase();
            const gate = String(data.gate || '').toLowerCase();
            const turnover = Number(data.turnover_vs_current_pct ?? data.turnover_pct ?? 0);

            if (data.execution_permission === true) return '治理阻擋';
            if (flags.length || constraintStatus.includes('violation') || modelStatus.includes('violation')) return '違反約束';
            if (turnover >= 30 || modelStatus.includes('high_turnover') || gate.includes('high_turnover')) return '高換手率警示';
            if (reasons.some(r => r.includes('sample') || r.includes('missing_data') || r.includes('three_year') || r.includes('proxy_only'))) return '樣本不足';
            if (modelStatus.includes('reject') || gate.includes('reject') || constraintStatus.includes('reject')) return '排除';
            if (constraintStatus.includes('pass') || modelStatus.includes('constraint_pass')) return '進一步研究';
            if (gate.includes('watch') || modelStatus.includes('watch')) return '僅供觀察';
            return '僅供觀察';
        }

        function machineReviewReason(item) {
            const data = item || {};
            const label = machineReviewLabel(data);
            const turnover = Number(data.turnover_vs_current_pct ?? data.turnover_pct ?? 0);
            if (label === '進一步研究') return `通過基本約束與換手率預審；僅代表研究候選，不代表買入或看多。`;
            if (label === '高換手率警示') return `換手率約 ${Number.isFinite(turnover) ? turnover.toFixed(1) : '—'}%，可能被交易成本、稅費或滑價抵消。`;
            if (label === '違反約束') return '觸及約束或風控旗標，暫不列入研究候選。';
            if (label === '樣本不足') return '資料品質或樣本外驗證不足，只能作為觀察。';
            if (label === '治理阻擋') return '治理旗標阻擋：不得自動執行，需先修正安全狀態。';
            if (label === '排除') return '模型狀態已被排除，不建議投入檢視時間。';
            return '有參考價值，但未達進一步研究門檻。';
        }

        function machineReviewBadgeClass(item) {
            const label = machineReviewLabel(item);
            if (label === '進一步研究') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';
            if (label === '僅供觀察') return 'border-sky-500/30 bg-sky-500/10 text-sky-300';
            if (label === '高換手率警示' || label === '樣本不足') return 'border-amber-500/30 bg-amber-500/10 text-amber-300';
            return 'border-red-500/30 bg-red-500/10 text-red-300';
        }

        onMounted(() => {
            updateStickyHeaderOffsets();

    window.addEventListener('resize', updateStickyHeaderOffsets);
    loadDataFromCloud();
    loadOptimizerSandboxOutput();
    loadRiskfolioSandboxOutput();
    loadOptimizerRobustnessOutput();
    loadOptimizerStressOutput();
    loadHumanApprovalLayer();
    loadActionAuditTrail();
    loadRegimeAwareOptimizer();
    loadBlackLittermanSandbox();
    loadExpectedReturnModel();
    loadWalkForwardBacktest();
    loadModelGovernanceDashboard();
    loadForecastFeatureStore();
    loadAlphaResearchSandbox();
    loadRebalanceCandidateRanking();
    loadAlphaValidationGate();
    loadManualRebalanceProposal();
    loadExecutionReadyDraft();
    loadFormalDraftPassConditions();
    loadTradingConstraintsSnapshot();
    loadFormalRebalanceDraftGate();
    loadManualTradeTicket();
    loadPaperTradeTracker();
    loadTradeSizingDiagnostics();

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

        watch(analyticsViewMode, async () => {
            await nextTick();
            updateStickyHeaderOffsets();
            resizeAllCharts();

            setTimeout(() => {
                updateStickyHeaderOffsets();
                resizeAllCharts();
            }, 120);
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
                    ctaLabel: '看風控',
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
            filteredHoldingsGroups, holdingsVisibleStats, analyticsViewMode, holdingsActionFilter, holdingsViewOptions, holdingsActionSummary, goToTab, historyIntegrityRisk, historyIntegrityBadge, alertCenterItems, alertCenterSections, tradeBufferBasePct, tradeBufferPresets, tradeBufferProfile, applyTradeBuffer, nudgeTradeBuffer, rebalanceCockpitRows, rebalanceCockpitBuckets, tradeBufferSummary, rebalancePostTradeEstimate, txPreview,
            currentTab, showHistoryModal, isUpdating,
            transactions, groupedHoldings, filteredGroupedHoldings, categoryTotals, riskTotals, portfolioStats, 
            totalStockValueTwd, totalStockCostTwd, totalStockUnrealizedPL, totalStockReturnRate, 
            reversedTransactions, txForm, historyForm, riskParams, stats, exchangeRate, 
            holdingsSearch, holdingsView, holdingsSort, filteredHoldingsCount, holdingsAlertCount, holdingsVisibleStats,
            txFlowMode, txTypeOptions, ledgerDraftPreview,
            sheetUrl, addTransaction, addHistoryRecord,
            removeTransaction, removeHistoryByDate, manualUpdate, updateMeta, fetchPrices, 
            exportAll, importData, getTypeColor, getCategoryColorCode, formatNumber, formatCurrency, formatPercent, 
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
            xrayStats, rebalanceMonitor, tailStatsLite, syntheticRiskMeta, optimizerDependencyStatus, optimizerDependencyPackages, optimizerSandboxOutput, optimizerSandboxError, optimizerSandboxPortfolios, optimizerSandboxBestByES, optimizerSandboxSkfolioWeights, optimizerSandboxCvarWeights, optimizerIntegratedComparison, loadOptimizerSandboxOutput, riskfolioSandboxOutput, riskfolioSandboxError, riskfolioSandboxPortfolios, loadRiskfolioSandboxOutput, unifiedOptimizerComparison, unifiedOptimizerBestByES, riskfolioMinVarWeights, riskfolioCvarWeights, selectedOptimizerBufferCandidateKey, optimizerBufferCandidateSummaries, selectedOptimizerBufferCandidate, selectedOptimizerBufferRows, optimizerBufferActionSummary, setOptimizerBufferCandidate, optimizerConstraintRules, optimizerConstraintPolicySummaries, selectedOptimizerConstraintPolicy, selectedOptimizerConstraintRows, selectedOptimizerConstraintIssues, optimizerRobustnessOutput, optimizerRobustnessError, optimizerRobustnessWindows, optimizerRobustnessMethods, optimizerMostStableMethod, optimizerUnstableMethods, loadOptimizerRobustnessOutput, optimizerStressOutput, optimizerStressError, optimizerStressScenarios, optimizerStressRows, optimizerStressWorstRows, optimizerStressBestWorst, optimizerStressMostFragile, selectedStressScenarioKey, selectedStressScenario, selectedStressScenarioRows, setStressScenario, loadOptimizerStressOutput, humanApprovalLayer, humanApprovalLayerError, humanApprovalTickets, humanApprovalSummary, humanApprovalVisibleTickets, loadHumanApprovalLayer, actionAuditTrail, actionAuditTrailError, actionAuditSummary, actionAuditEvents, loadActionAuditTrail, regimeAwareOptimizer, regimeAwareError, regimeAwareSummary, regimeAwareRegime, regimeAwareActivePolicy, regimeAwareCovariancePolicy, regimeAwareDrafts, regimeAwareVisibleDrafts, loadRegimeAwareOptimizer, blackLittermanSandbox, blackLittermanError, blackLittermanSummary, blackLittermanViewEngine, blackLittermanViews, blackLittermanPosteriorCandidates, loadBlackLittermanSandbox, expectedReturnModel, expectedReturnError, expectedReturnSummary, expectedReturnPolicy, expectedReturnBucketPriors, expectedReturnAssetPriors, expectedReturnVisibleBuckets, expectedReturnVisibleAssets, loadExpectedReturnModel, walkForwardBacktest, walkForwardError, walkForwardSummary, walkForwardAggregate, walkForwardVisibleRows, loadWalkForwardBacktest, modelGovernanceDashboard, modelGovernanceError, modelGovernanceSummary, modelGovernanceRegistry, modelGovernanceFlags, modelGovernanceVisibleRegistry, modelGovernanceVisibleFlags, loadModelGovernanceDashboard, forecastFeatureStore, forecastFeatureError, forecastFeatureSummary, forecastFeatureSample, forecastFeatureRows, forecastFeatureVisibleRows, loadForecastFeatureStore, alphaResearchSandbox, alphaResearchError, alphaResearchSummary, alphaResearchPolicy, alphaResearchRows, alphaResearchVisibleRows, loadAlphaResearchSandbox, rebalanceCandidateRanking, rebalanceRankingError, rebalanceRankingSummary, rebalanceRankingPolicy, rebalanceRankingRows, rebalanceRankingVisibleRows, loadRebalanceCandidateRanking, alphaValidationGate, alphaValidationError, alphaValidationSummary, alphaValidationGates, alphaValidationVisibleGates, loadAlphaValidationGate, manualRebalanceProposal, manualProposalError, manualProposalSummary, manualProposalRows, manualProposalVisibleRows, loadManualRebalanceProposal, executionReadyDraft, executionDraftError, executionDraftSummary, executionDraftRows, executionDraftVisibleRows, loadExecutionReadyDraft, formalDraftPassConditions, formalDraftPassError, formalDraftPassSummary, loadFormalDraftPassConditions, tradingConstraintsSnapshot, tradingConstraintsError, tradingConstraintsSummary, tradingConstraintsRows, tradingConstraintsVisibleRows, loadTradingConstraintsSnapshot, paperTradeTracker, paperTradeError, paperTradeSummary, paperTradeRows, paperTradeVisibleRows, loadPaperTradeTracker, tradeSizingDiagnostics, tradeSizingDiagnosticsError, tradeSizingDiagnosticsSummary, tradeSizingDiagnosticsIssues, tradeSizingDiagnosticsVisibleIssues, tradeSizingDiagnosticsNextActions, loadTradeSizingDiagnostics, formalRebalanceDraftGate, formalDraftGateError, formalDraftGateSummary, formalDraftRows, formalDraftVisibleRows, loadFormalRebalanceDraftGate, manualTradeTicket, manualTradeTicketError, manualTradeTicketSummary, manualTradeTicketRows, manualTradeTicketVisibleRows, loadManualTradeTicket, approvalBadgeClass, machineReviewLabel, machineReviewReason, machineReviewBadgeClass, zhText, zhList, zhBool, selectedOptimizerExplainKey, optimizerExplainabilityCandidates, selectedOptimizerExplainability, setOptimizerExplainCandidate, allocationGovernance, decisionCenter, cashBalance, totalPortfolioNav, cashBalance, totalPortfolioNav, isCashNegative, isCashTooHigh, isCashAlert            
        };
    }
}).mount('#app');
