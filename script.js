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
        sharpe_ratio: stats.value.sharpe,
        sortino_ratio: stats.value.sortino,
        treynor_ratio: stats.value.treynor
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
    buffer_blocking_risk_buys: rebalanceMonitor.value.bufferBlockingRiskBuys ? 'YES' : 'NO',
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

[ANALYSIS_RULES]
You MUST analyze the portfolio holistically using all modules below:

1. 【資金效率與選股】Compare TWR vs MWR and Jensen's Alpha. Judge whether timing and selection are adding value or destroying value.
2. 【風險報酬定價】Use Sharpe, Sortino, Treynor, Beta, and Volatility. State whether the portfolio is being paid enough for the risk it is taking.
3. 【Portfolio X-Ray】Use PC1 explained, PC1-3 cumulative explained, USD exposure, FX impact, and top risk contributors. Judge whether the portfolio is truly diversified or only appears diversified.
4. 【Regime / Rebalance Monitor】Use trim candidates, high-priority alerts, leverage volatility drag, buffer_floor_pct, current_buffer_pct, buffer_gap_pct, buffer_blocking_risk_buys, hard_buffer_tickers, and rebalance alerts. Judge whether risk is drifting because the user failed to rebalance, and whether the portfolio is currently constrained by a Buffer Floor shortfall.
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
            annRet:'0.00', annLogRet:'0.00', mwr:'0.00', annVol:'0.00', sharpe:'0.00', sortino:'0.00', treynor:'0.00', 
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

                        if (macroData.hy_spread > 5.0 && macroData.yield_curve < 0.5) macroRegime.value = 'Crisis';
                        else if (macroData.hy_spread > 4.0 || macroData.btc_1m_mom < -15) macroRegime.value = 'Bear';
                        else if (macroData.yield_curve > 0 && macroData.hy_spread < 3.5 && macroData.btc_1m_mom > 5) macroRegime.value = 'Bull';
                        else macroRegime.value = 'Normal';

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

        const txForm = ref({ date: new Date().toISOString().split('T')[0], type: 'Buy', category: '美股', ticker: '', price: null, shares: null });
        const historyForm = ref({ date: new Date().toISOString().split('T')[0], assets: null, cost: null });

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
                const daysHeld = Math.max(1, (today - txDate) / (1000 * 60 * 60 * 24)); 
                const investedAmount = Math.abs(tx.totalCashFlow);

                if (!holdingDaysMap[t]) holdingDaysMap[t] = { totalInvested: 0, weightedDaysSum: 0 };
                holdingDaysMap[t].totalInvested += investedAmount;
                holdingDaysMap[t].weightedDaysSum += (investedAmount * daysHeld);
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

                groups[h.category].items.push({
                    ...h,
                    isUSD,
                    riskLevel: meta.risk || 'High',
                    beta: meta.beta || 1.0,
                    stdDev: meta.std || 20.0,
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

                    // 累加該分類下的總投入資金與加權持有天數
                    if (holdingDaysMap[item.ticker]) {
                        groupTotalInvested += holdingDaysMap[item.ticker].totalInvested;
                        groupWeightedDaysSum += holdingDaysMap[item.ticker].weightedDaysSum;
                    }
                });
                
                groups[cat].items.sort((a,b) => b.marketValueTwd - a.marketValueTwd);
                groups[cat].unrealizedPL = groups[cat].totalValue - groups[cat].totalCost;
                
                // 計算分類累積報酬率
                const groupCumulativeReturn = groups[cat].totalCost > 0 ? (groups[cat].unrealizedPL / groups[cat].totalCost) : 0;
                groups[cat].returnRate = groupCumulativeReturn * 100;

                // 計算分類年化報酬率 (CAGR)
                let groupAnnualizedReturn = groupCumulativeReturn; 
                if (groupTotalInvested > 0) {
                    const groupAvgDaysHeld = groupWeightedDaysSum / groupTotalInvested;
                    if (groupAvgDaysHeld > 7) {
                        const groupYearsHeld = groupAvgDaysHeld / 365;
                        groupAnnualizedReturn = Math.pow(1 + groupCumulativeReturn, 1 / groupYearsHeld) - 1;
                    }
                }
                
                // 離群值封頂限制 (最高 500%, 最低 -100%)
                if (groupAnnualizedReturn > 5) groupAnnualizedReturn = 5;
                if (groupAnnualizedReturn < -1) groupAnnualizedReturn = -1;

                groups[cat].annualizedReturnRate = groupAnnualizedReturn * 100;
            }
            return groups;
        });

        const categoryTotals = computed(() => { const totals = {}; for(const cat in groupedHoldings.value) totals[cat] = groupedHoldings.value[cat].totalValue; return totals; });
        const riskTotals = computed(() => { let high = 0; let low = 0; for(const cat in groupedHoldings.value) { groupedHoldings.value[cat].items.forEach(item => { if(item.riskLevel === 'Low') low += item.marketValueTwd; else high += item.marketValueTwd; }); } return { High: high, Low: low }; });
        const totalStockValueTwd = computed(() => Object.values(categoryTotals.value).reduce((a,b)=>a+b,0));
        const portfolioStats = ref({ beta: 0, std: 0 });

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
        const reversedTransactions = computed(() => [...transactions.value].reverse());

        const filteredHistory = computed(() => {
            const data = displayHistory.value;
            if(!quantStartDate.value) return data;
            return data.filter(h => new Date(h.date) >= new Date(quantStartDate.value));
        });

        const enrichedHistory = computed(() => {
    const sorted = [...filteredHistory.value].sort((a, b) => new Date(a.date) - new Date(b.date));

    return sorted.map((item, index) => {
        let dailyReturn = null;
        let withdrawal = 0;

        if (index > 0) {
            const prev = sorted[index - 1];

            // 假設：Cost_{t-1} - Cost_t = 當期「外部現金流」
            // 正值 = 提領 / Withdraw
            // 負值 = 入金 / Deposit
            // 因此本欄位不是單純 NAV return，而是 cash-flow-adjusted period return
            withdrawal = (prev.cost || 0) - (item.cost || 0);

            dailyReturn = prev.assets > 0
                ? ((item.assets + withdrawal) / prev.assets) - 1
                : 0;
        }

        return {
            ...item,
            dailyReturn,
            withdrawal
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

// === 真 MWR / XIRR ===
let mwr = null;
const cashflows = [];

if (h.length >= 2) {
    // 初始投入
    cashflows.push({
        date: h[0].date,
        amount: -(h[0].cost || 0)
    });

    // 中間提領 / 入金
    for (let i = 1; i < h.length; i++) {
        const cf = (h[i - 1].cost || 0) - (h[i].cost || 0);
        if (Math.abs(cf) > 0) {
            cashflows.push({
                date: h[i].date,
                amount: cf
            });
        }
    }

    // 最後 NAV 加到最後一期
    const endDate = h[h.length - 1].date;
    const endVal = h[h.length - 1].assets || 0;

    if (cashflows.length > 0 && cashflows[cashflows.length - 1].date === endDate) {
        cashflows[cashflows.length - 1].amount += endVal;
    } else {
        cashflows.push({
            date: endDate,
            amount: endVal
        });
    }

    mwr = xirr(cashflows, 0.10);
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

             stats.value = { 
                 annRet: (annRet*100).toFixed(2), 
                 annLogRet: (annLogRet*100).toFixed(2), 
                 mwr: mwr === null ? '-' : (mwr * 100).toFixed(2),            
                 annVol: (annVol*100).toFixed(2), 
                 sharpe: sharpe.toFixed(2), 
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
    const n = Number(val);
    return Number.isFinite(n) ? n.toFixed(digits) : '-';
}

function fmtPctMaybe(val, digits = 2) {
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
        
        function addTransaction() { 
            const { date, type, category, ticker, price, shares } = txForm.value; 
            if(!date) return; 
            const finalFlow = (type === 'Buy' ? -1 : 1) * price * shares;
            transactions.value.push({ date, type, category, ticker: ticker?.toUpperCase(), price, shares, totalCashFlow: finalFlow }); 
            saveData(); txForm.value.ticker=''; updateCharts(); 
        }

        function snapshotToHistory() {
            const date = snapshotDate.value || new Date().toISOString().split('T')[0];
            const assets = Math.round(totalStockValueTwd.value);
            const cost = Math.round(totalStockCostTwd.value);

            const idx = realHistoryData.value.findIndex(h => h.date === date);
            if (idx >= 0) {
                if(confirm(`日期 (${date}) 已有紀錄，要覆蓋嗎？`)) realHistoryData.value[idx] = { date, assets, cost };
                else return;
            } else realHistoryData.value.push({ date, assets, cost });
            
            saveData(); updateCharts();
            if(!quantStartDate.value) quantStartDate.value = date;
        }

        const quantDays = computed(() => {
             const h = filteredHistory.value; if(h.length < 2) return 0;
             const sorted = [...h].sort((a,b) => new Date(a.date) - new Date(b.date));
             const start = new Date(sorted[0].date); const end = new Date(sorted[sorted.length-1].date);
             return Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        });

        function addHistoryRecord() { const { date, assets, cost } = historyForm.value; realHistoryData.value.push({ date, assets, cost }); saveData(); updateCharts(); }

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
            const randValues = Array.from({ length: n_assets }, () => Math.pow(Math.random(), 3));
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

    // 原本 p_ret / p_vol 是年化，先轉成週頻
    const muWeekly = p_ret / 52;
    const sigmaWeekly = p_vol / Math.sqrt(52);

    const jdSim = simulateJumpDiffusionMoments({
        muWeekly,
        sigmaWeekly,
        jumpLambdaAnnual: jp.lambda,
        jumpMean: jp.mean,
        jumpStd: jp.std,
        horizonWeeks: 13,
        nSims: 300,
        seed: 42
    });

    // 13 週分布 → 年化近似
    p_ret = Math.pow(1 + jdSim.mean, 52 / 13) - 1;
    p_vol = jdSim.std * Math.sqrt(52 / 13);
    p_skew = jdSim.skew;
    p_kurt_ex = jdSim.kurtEx;

    jumpTailLoss = Math.abs(Math.min(jdSim.mean, 0));
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
                    sharpe: p_asr,
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

    mcOptimal.value = {
        ret: (bestPort.ret * 100).toFixed(2),
        vol: (bestPort.vol * 100).toFixed(2),
        sharpe: bestPort.sharpe.toFixed(3),
        skew: bestPort.skew.toFixed(2),
        kurt: bestPort.kurt.toFixed(2),
        weights: wList,

        hardBufferTargetPct: (bestPort.hardBufferTargetWeight * 100).toFixed(2),
        hardBufferCurrentPct: (bestPort.hardBufferCurrentWeight * 100).toFixed(2),
        hardBufferGapPct: ((bestPort.hardBufferTargetWeight - bestPort.hardBufferCurrentWeight) * 100).toFixed(2),
        defensiveSleevePct: (bestPort.defensiveCurrentWeight * 100).toFixed(2),
        bufferFloorRespected: bestPort.hardBufferCurrentWeight >= bestPort.hardBufferTargetWeight - 1e-6,
        jumpTailLossPct: (bestPort.jumpTailLoss * 100).toFixed(2)
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
        
        function getTypeColor(type) { return type==='Buy'?'text-red-400':'text-green-400'; }
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

        // 🚨 終極修正：將所有在 HTML 呼叫的函數與變數都暴露給 Vue
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
            xrayStats, rebalanceMonitor, tailStatsLite
        };
    }
}).mount('#app');