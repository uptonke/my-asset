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

