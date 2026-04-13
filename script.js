const { createApp, ref, computed, onMounted, watch, nextTick } = Vue;

createApp({
    setup() {
        const blViews = ref([]); 
        
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
        // 🤖 量化觀點生成器 (Momentum Factor Generator)
        // ==========================================
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
        
        // 👉 初始化 Supabase 客戶端
        const supabaseUrl = 'https://yrccanqxzrcoknzabifz.supabase.co';
        const supabaseKey = 'sb_publishable_lDfwRDxgMhzRwVk0-Qu3vg_9HTmTFZy';
        const supabase = window.supabase.createClient(supabaseUrl, supabaseKey);

        const isAppReady = ref(false); 
        const showMCModal = ref(false); 
        const mcOptimal = ref(null); 

        // ==========================================
        // 🔒 Auth & Session Management (Vue 版)
        // ==========================================
        const isLoggedIn = ref(false);
        const loginEmail = ref('');
        const loginPassword = ref('');
        const loginError = ref('');
        const isAuthenticating = ref(false);

        const checkAuth = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (session) {
                isLoggedIn.value = true;
            } else {
                isAppReady.value = true; 
            }
        };

        const handleLogin = async () => {
            isAuthenticating.value = true;
            loginError.value = '';
            
            const { data, error } = await supabase.auth.signInWithPassword({
                email: loginEmail.value,
                password: loginPassword.value,
            });

            if (error) {
                loginError.value = 'Access Denied: ' + error.message;
            } else {
                isLoggedIn.value = true;
                isAppReady.value = false; 
                isAppReady.value = true; 
            }
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
        const isSimMode = ref(false);
        const lastUpdate = ref(null);
        
        const exchangeRate = ref(32.5);
        const sheetUrl = ref('');

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
        const mockHistoryData = ref([]);
        const priceMap = ref({});
        const stockMeta = ref({});

        // 🚀 v18.0: Supabase (PostgreSQL) + IndexedDB 企業級雙核資料流
        async function loadDataFromCloud() {
            isDbSyncing.value = true;
            try {
                const { data, error } = await supabase.from('portfolio_db').select('*').eq('id', 1).single();
                
                if (error && error.code !== 'PGRST116') throw error; 

                if (data) {
                    transactions.value = data.ledger_data || [];
                    realHistoryData.value = data.history_data || [];
                    stockMeta.value = data.stock_meta || {};
                    
                    // 👇👇👇 總經大腦模組 👇👇👇
                    if (data.macro_meta) {
                        const macroData = data.macro_meta;
                        console.group("🌍 量化總經大腦判定中...");
                        console.log(`10Y-2Y利差: ${macroData.yield_curve}%`);
                        console.log(`高收益債利差 (恐慌指標): ${macroData.hy_spread}%`);
                        console.log(`比特幣近期動能: ${macroData.btc_1m_mom}%`);

                        if (macroData.hy_spread > 5.0 && macroData.yield_curve < 0.5) {
                            macroRegime.value = 'Crisis';
                            console.log("⚠️ 判定結果：【金融危機 Crisis】");
                        } else if (macroData.hy_spread > 4.0 || macroData.btc_1m_mom < -15) {
                            macroRegime.value = 'Bear';
                            console.log("🐻 判定結果：【熊市 Bear】");
                        } else if (macroData.yield_curve > 0 && macroData.hy_spread < 3.5 && macroData.btc_1m_mom > 5) {
                            macroRegime.value = 'Bull';
                            console.log("🐂 判定結果：【牛市 Bull】");
                        } else {
                            macroRegime.value = 'Normal';
                            console.log("⚖️ 判定結果：【正常 Normal】");
                        }
                        console.groupEnd();
                    }
                    // 👆👆👆 總經大腦結束 👆👆👆

                    if (data.settings) {
                        if (data.settings.exchangeRate) exchangeRate.value = parseFloat(data.settings.exchangeRate);
                        if (data.settings.sheetUrl) sheetUrl.value = data.settings.sheetUrl;
                        if (data.settings.fireTargets) fireTargets.value = data.settings.fireTargets;
                        if (data.settings.priceMap) priceMap.value = data.settings.priceMap;
                    }
                } 

                await localforage.setItem('ledgerData', JSON.stringify(transactions.value));
                await localforage.setItem('historyData', JSON.stringify(realHistoryData.value));
                await localforage.setItem('stockMeta', JSON.stringify(stockMeta.value));
                await localforage.setItem('settings', JSON.stringify({
                    exchangeRate: exchangeRate.value, sheetUrl: sheetUrl.value, fireTargets: fireTargets.value, priceMap: priceMap.value
                }));

            } catch (err) {
                transactions.value = JSON.parse(await localforage.getItem('ledgerData') || '[]');
                realHistoryData.value = JSON.parse(await localforage.getItem('historyData') || '[]');
                stockMeta.value = JSON.parse(await localforage.getItem('stockMeta') || '{}');
                
                const localSettings = JSON.parse(await localforage.getItem('settings') || '{}');
                if(localSettings.exchangeRate) exchangeRate.value = localSettings.exchangeRate;
                if(localSettings.sheetUrl) sheetUrl.value = localSettings.sheetUrl;
                if(localSettings.fireTargets) fireTargets.value = localSettings.fireTargets;
                if(localSettings.priceMap) priceMap.value = localSettings.priceMap;
            } finally {
                isDbSyncing.value = false;
                isAppReady.value = true; 
                updateCharts();
            }
        }

        const txForm = ref({ date: new Date().toISOString().split('T')[0], type: 'Buy', category: '美股', ticker: '', price: null, shares: null });
        const historyForm = ref({ date: new Date().toISOString().split('T')[0], assets: null, cost: null });

        const displayHistory = computed(() => isSimMode.value ? mockHistoryData.value : realHistoryData.value);

        watch(displayHistory, (newVal) => {
            if (newVal.length > 0 && !quantStartDate.value) {
                const sorted = [...newVal].sort((a,b) => new Date(a.date) - new Date(b.date));
                quantStartDate.value = sorted[0].date;
            }
        }, { immediate: true });

        function toggleSimMode() {
            isSimMode.value = !isSimMode.value;
            if (isSimMode.value && mockHistoryData.value.length === 0) generateMonthlyMockData();
            updateCharts();
        }

        function updateMeta(stock) {
            if(stock.ticker) {
                stockMeta.value[stock.ticker] = {
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
                        updateCharts();
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

            holdingsFlat.value.forEach(h => {
                const rawPrice = priceMap.value[h.ticker];
                const isUSD = (h.category === '美股');
                const effectiveNativePrice = h.manualPrice || rawPrice || (h.totalCostTwd / h.shares / (isUSD ? exchangeRate.value : 1));
                const currentPriceTwd = effectiveNativePrice * (isUSD ? exchangeRate.value : 1);
                const mvTwd = h.shares * currentPriceTwd;

                grandTotal += mvTwd; 

                if (!groups[h.category]) groups[h.category] = { totalValue: 0, items: [] };
                
                const meta = stockMeta.value[h.ticker] || {};
                
                const item = { 
                    ...h, isUSD, 
                    riskLevel: meta.risk || 'High',
                    beta: meta.beta || 1.0,
                    stdDev: meta.std || 20.0,
                    fetchedPrice: rawPrice,
                    avgCostTwd: h.totalCostTwd / h.shares, 
                    currentPriceTwd: currentPriceTwd,
                    marketValueTwd: mvTwd, 
                    unrealizedPLTwd: mvTwd - h.totalCostTwd, 
                    returnRate: h.totalCostTwd ? (((mvTwd - h.totalCostTwd)/h.totalCostTwd)*100).toFixed(2) : 0 
                };
                
               groups[h.category].items.push(item);
               groups[h.category].totalValue += mvTwd;
            });

            for (const cat in groups) {
                groups[cat].items.forEach(item => {
                    item.totalWeight = grandTotal > 0 ? (item.marketValueTwd / grandTotal) : 0;
                    item.isOverweight = item.totalWeight > 0.15; 
                });
                groups[cat].items.sort((a,b) => b.marketValueTwd - a.marketValueTwd);
            }
            return groups;
        });

        const categoryTotals = computed(() => {
            const totals = {};
            for(const cat in groupedHoldings.value) totals[cat] = groupedHoldings.value[cat].totalValue;
            return totals;
        });

        const riskTotals = computed(() => {
            let high = 0; let low = 0;
            for(const cat in groupedHoldings.value) {
               groupedHoldings.value[cat].items.forEach(item => {
                    if(item.riskLevel === 'Low') low += item.marketValueTwd; else high += item.marketValueTwd;
                });
            }
            return { High: high, Low: low };
        });

        const totalStockValueTwd = computed(() => Object.values(categoryTotals.value).reduce((a,b)=>a+b,0));
        
        const portfolioStats = ref({ beta: 0, std: 0 });

        watch([groupedHoldings, totalStockValueTwd], () => {
            let totalBeta = 0; let totalStd = 0;
            const totalVal = totalStockValueTwd.value;
            if(totalVal > 0) {
                for(const cat in groupedHoldings.value) {
                   groupedHoldings.value[cat].items.forEach(item => {
                        const weight = item.marketValueTwd / totalVal;
                        totalBeta += weight * item.beta;
                        totalStd += weight * item.stdDev;
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

        // ==========================================
        // 🌟 升級版 1: 機構級 TWR 現金流精算引擎
        // 徹底解決因花費/出金導致的績效失真斷層
        // ==========================================
        const enrichedHistory = computed(() => {
            const sorted = [...filteredHistory.value].sort((a,b) => new Date(a.date) - new Date(b.date));
            return sorted.map((item, index) => {
                let dailyReturn = null;
                if (index > 0) {
                    const prev = sorted[index - 1];
                    let injection = 0;
                    let hasTx = false;
                    
                    // 精確掃描快照期間的所有交易，計算真實資金進出
                    transactions.value.forEach(tx => {
                        const txDate = new Date(tx.date);
                        if (txDate > new Date(prev.date) && txDate <= new Date(item.date)) {
                            // 買入股票 = 外部資金注入系統 (-cashFlow)
                            // 賣出股票 = 資金抽出系統供日常花費 (+cashFlow)
                            injection += -tx.totalCashFlow;
                            hasTx = true;
                        }
                    });
                    
                    // 💡 物理隔離：4/11 以前的合成數據強制使用粗算，避免歷史流水帳衝突
                    const netFlow = (new Date(item.date) <= new Date('2026-04-11')) 
                        ? (item.cost - prev.cost) 
                        : (hasTx ? injection : (item.cost - prev.cost));
                    const denom = prev.assets + (netFlow / 2);
                    
                    if (denom > 0) dailyReturn = (item.assets - prev.assets - netFlow) / denom;
                    else dailyReturn = 0;
                }
                return { ...item, dailyReturn };
            }).reverse();
        });

        const stats = ref({ annRet:'-', annVol:'-', sharpe:'-', sortino:'-', treynor:'-', alpha:'-', var95:'-', cvar95:'-', mdd:'-', calmar:'-', skew:'-', kurt:'-' });

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
                if (expectedDrop > 100) expectedDrop = 100;

                return {
                    ...scenario,
                    portDrop: expectedDrop.toFixed(1),
                    valueLost: (totalStockValueTwd.value * Math.abs(expectedDrop) / 100)
                };
            });
        });

        // ==========================================
        // 🌟 升級版 2: 獨立 HWM (High Water Mark) 引擎
        // 解決 MDD 因為出金而被無意義放大的致命問題
        // ==========================================
        watch([enrichedHistory, riskParams, dataFrequency], () => {
             const empty = { annRet:'-', annVol:'-', sharpe:'-', sortino:'-', treynor:'-', alpha:'-', var95:'-', cvar95:'-', mdd:'-', calmar:'-', skew:'-', kurt:'-' };
             const h = [...enrichedHistory.value].reverse(); // 轉回時間正序
             if (h.length < 3) { stats.value = empty; return; }

             // 直接取用精算過、已剝離現金干擾的純淨報酬率
             const returns = h.slice(1).map(item => item.dailyReturn);

             // HWM 累積淨值指數 (起始為 1.0)
             let cumIndex = 1.0;
             let peakIndex = 1.0;
             let maxDrawdown = 0;

             returns.forEach(r => {
                 cumIndex = cumIndex * (1 + r);
                 if (cumIndex > peakIndex) peakIndex = cumIndex;
                 const dd = peakIndex > 0 ? (cumIndex - peakIndex) / peakIndex : 0;
                 if (dd < maxDrawdown) maxDrawdown = dd; // 這裡算出的 MDD 絕對純淨
             });

             const cumTwr = returns.reduce((acc, r) => acc * (1 + r), 1) - 1;
             const factor = dataFrequency.value === 'Weekly' ? Math.sqrt(52) : Math.sqrt(252);
             const years = returns.length / (dataFrequency.value === 'Weekly' ? 52 : 252);
             const annRet = years > 0 ? (Math.pow(1 + cumTwr, 1 / years) - 1) : 0;

             const avgR = returns.reduce((a,b)=>a+b,0)/returns.length;
             const stdSample = Math.sqrt(returns.reduce((a,b) => a + Math.pow(b-avgR, 2), 0) / (returns.length - 1));
             const annVol = stdSample * factor;

             const rf = riskParams.value.rf / 100;
             const rm = riskParams.value.rm / 100;
             const beta = riskParams.value.beta || 1;

             const sharpe = annVol > 0 ? (annRet - rf) / annVol : 0;
             const treynor = beta !== 0 ? (annRet - rf) / beta : 0;
             
             const downsideReturns = returns.filter(r => r < 0);
             const downsideDev = Math.sqrt(downsideReturns.length > 0 ? downsideReturns.reduce((a,b) => a + Math.pow(b, 2), 0) / returns.length : 0) * factor; 
             const sortino = downsideDev > 0 ? (annRet - rf) / downsideDev : 0;

             const calmar = Math.abs(maxDrawdown) > 0 ? annRet / Math.abs(maxDrawdown) : 0;

             const expectedRet = rf + beta * (rm - rf);
             const alpha = annRet - expectedRet;

             const sortedReturns = [...returns].sort((a,b) => a-b);
             const idx95 = Math.floor(sortedReturns.length * 0.05);
             const var95 = sortedReturns[idx95] || 0;
             
             let cvar95 = 0;
             if (idx95 > 0) {
                 const worstReturns = sortedReturns.slice(0, idx95);
                 cvar95 = worstReturns.reduce((a,b) => a+b, 0) / worstReturns.length;
             } else {
                 cvar95 = var95;
             }

             const n = returns.length;
             const stdPop = Math.sqrt(returns.reduce((a,b)=>a+Math.pow(b-avgR, 2),0)/n);
             
             let sumCubed = 0; let sumQuart = 0;
             returns.forEach(r => { sumCubed += Math.pow(r - avgR, 3); sumQuart += Math.pow(r - avgR, 4); });

             stats.value = { 
                 annRet: (annRet*100).toFixed(2), 
                 annVol: (annVol*100).toFixed(2), 
                 sharpe: sharpe.toFixed(2), 
                 sortino: sortino.toFixed(2), 
                 treynor: (treynor * 100).toFixed(2),
                 alpha: (alpha * 100).toFixed(2),
                 var95: (var95 * 100).toFixed(2),
                 cvar95: (cvar95 * 100).toFixed(2), 
                 mdd: (maxDrawdown * 100).toFixed(2), 
                 calmar: calmar.toFixed(2), 
                 skew: ((sumCubed / n) / Math.pow(stdPop, 3)).toFixed(2),
                 kurt: (((sumQuart / n) / Math.pow(stdPop, 4)) - 3).toFixed(2)
             }; 
        }, { deep: true, immediate: true });

        const aiInsights = computed(() => {
            const val = totalStockValueTwd.value;
            const ret = parseFloat(totalStockReturnRate.value);
            const beta = parseFloat(portfolioStats.value.beta);
            
            const sharpe = parseFloat(stats.value.sharpe);
            const annRet = parseFloat(stats.value.annRet);
            const annVol = parseFloat(stats.value.annVol);
            const var95 = parseFloat(stats.value.var95);
            
            if (val === 0) return { summary: '尚無庫存資料，請先新增交易紀錄。', details: [] };

            const details = [];
            let score = 100; 

            if (!isNaN(annRet) && !isNaN(annVol)) {
                details.push({ icon: '📊', color: 'text-blue-400', title: '量化表現總結', desc: `目前投組年化報酬率約 ${annRet.toFixed(2)}%，年化波動度 ${annVol.toFixed(2)}%。在 95% 信心水準下，單期最大潛在損失 (VaR) 約為 ${Math.abs(var95).toFixed(2)}%。` });
            }

            if (ret >= 20) {
                details.push({ icon: '🎉', color: 'text-green-400', title: '獲利豐厚', desc: `未實現報酬達 ${ret}%。建議可評估啟動動態停利 (Trailing Stop)，或將部分資金轉入低波動資產鎖住 Alpha。` });
            } else if (ret <= -15) {
                score -= 15;
                details.push({ icon: '⚠️', color: 'text-red-400', title: '回撤警戒', desc: `目前虧損 ${ret}%，請嚴格執行停損紀律，確認是否跌破原始投資 Due Diligence 的護城河。` });
            }

            let overweights = [];
            for (const cat in groupedHoldings.value) {
                groupedHoldings.value[cat].items.forEach(item => {
                    if (item.totalWeight > 0.15) overweights.push(item.ticker);
                });
            }
            if (overweights.length > 0) {
                score -= 20;
                details.push({ icon: '🎯', color: 'text-orange-400', title: '集中度風險過高', desc: `[ ${overweights.join(', ')} ] 佔總資產權重過高 (>15%)。強烈建議點擊下方【MC 最佳化】，透過蒙地卡羅模擬找出最大夏普權重並進行 Rebalance。` });
            }

            if (beta > 1.2) {
                score -= 5;
                details.push({ icon: '🔥', color: 'text-red-400', title: '攻擊型配置 (High Beta)', desc: `組合 Beta 達 ${beta}。大盤多頭時具備強大爆發力，但總經下行時回撤極深，請確保 Dry Powder 充足。` });
            } else if (beta > 0 && beta < 0.8) {
                details.push({ icon: '🛡️', color: 'text-blue-400', title: '防禦型配置 (Low Beta)', desc: `組合 Beta 僅 ${beta}。抗跌能力極佳，但可能會錯失牛市行情。` });
            }

            if (!isNaN(sharpe)) {
                if (sharpe < 0.8 && sharpe > 0) {
                    score -= 15;
                    details.push({ icon: '📉', color: 'text-yellow-400', title: '風險報酬比偏低', desc: `夏普值 ${sharpe} 偏低。你承擔了過多波動，卻沒換來對應的超額報酬。建議立刻跑一次 Monte Carlo 模型優化資產比例。` });
                } else if (sharpe >= 1.5) {
                    score += 10;
                    details.push({ icon: '🌟', color: 'text-yellow-400', title: '卓越的資金效率', desc: `夏普值高達 ${sharpe}！投組完美平衡了波動風險與超額報酬，請繼續保持。` });
                }
            }

            if (details.length === 1 && score === 100) {
                 details.push({ icon: '✅', color: 'text-green-400', title: '配置極度健康', desc: `目前的投資組合沒有觸發任何集中度與風險警報！波動度適中，資產分散且無明顯死角。` });
            }

            let summary = '';
            if (score >= 95) summary = `狀態極佳 (評分: ${Math.min(score, 100)})：資產配置極度健康，資金效率與 Sharpe 表現卓越。`;
            else if (score >= 75) summary = `狀態良好 (評分: ${score})：投組穩健，但可點此展開檢視 VaR 風險或部分部位之集中度。`;
            else summary = `需要注意 (評分: ${score})：偵測到非系統性風險或低夏普值，強烈建議展開報告並執行 MC 最佳化。`;

            return { summary, details };
        });

        function addFireTarget() {
            const last = fireTargets.value[fireTargets.value.length - 1];
            fireTargets.value.push({
                age: last ? last.age + 5 : 30,
                year: last ? last.year + 5 : new Date().getFullYear() + 5,
                amount: last ? last.amount * 1.5 : 5000000
            });
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

        async function manualUpdate(stock) { 
            if(stock.manualPrice) { 
                priceMap.value[stock.ticker] = stock.manualPrice; 
                saveData(); 
            } 
        }
        
        function removeTransaction(txToRemove) { 
            if(confirm('確認刪除此筆交易?')) { 
                const idx = transactions.value.indexOf(txToRemove);
                if (idx > -1) {
                    transactions.value.splice(idx, 1); 
                    saveData(); 
                    updateCharts(); 
                }
            } 
        }
        
        function removeHistoryByDate(date) { 
            if(confirm('確定刪除此快照?')) { 
                realHistoryData.value = realHistoryData.value.filter(h=>h.date!==date); 
                saveData();
                updateCharts(); 
            } 
        }

        let syncTimer = null;
        async function saveData() { 
            await localforage.setItem('ledgerData', JSON.stringify(transactions.value)); 
            await localforage.setItem('historyData', JSON.stringify(realHistoryData.value));
            await localforage.setItem('stockMeta', JSON.stringify(stockMeta.value));
            await localforage.setItem('settings', JSON.stringify({
                exchangeRate: exchangeRate.value, sheetUrl: sheetUrl.value, fireTargets: fireTargets.value, priceMap: priceMap.value
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
                            priceMap: priceMap.value
                        }
                    }, { onConflict: 'id' }); 

                    if (error) throw error;
                    console.log("🚀 Supabase 雲端同步完成 (Debounced Sync)");
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

            transactions.value.push({ 
                date, type, category, 
                ticker: ticker?.toUpperCase(), 
                price, 
                shares, 
                totalCashFlow: finalFlow 
            }); 
            saveData(); 
            txForm.value.ticker=''; 
            updateCharts(); 
        }

        function snapshotToHistory() {
            const date = snapshotDate.value || new Date().toISOString().split('T')[0];
            const assets = Math.round(totalStockValueTwd.value);
            const cost = Math.round(totalStockCostTwd.value);

            const idx = realHistoryData.value.findIndex(h => h.date === date);
            if (idx >= 0) {
                if(confirm(`日期 (${date}) 已有紀錄，要覆蓋嗎？`)) {
                    realHistoryData.value[idx] = { date, assets, cost };
                } else return;
            } else {
                realHistoryData.value.push({ date, assets, cost });
            }
            
            saveData();
            updateCharts();
            if(!quantStartDate.value) quantStartDate.value = date;
        }

        const quantDays = computed(() => {
             const h = filteredHistory.value;
             if(h.length < 2) return 0;
             const sorted = [...h].sort((a,b) => new Date(a.date) - new Date(b.date));
             const start = new Date(sorted[0].date);
             const end = new Date(sorted[sorted.length-1].date);
             return Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        });

        function addHistoryRecord() { const { date, assets, cost } = historyForm.value; realHistoryData.value.push({ date, assets, cost }); saveData(); updateCharts(); }
        
        function generateMonthlyMockData() { 
             mockHistoryData.value = [];
             let val = 1000000; let cost = 1000000;
             for(let i=0; i<12; i++) {
                 const date = `2024-${String(i+1).padStart(2,'0')}-01`;
                 val = val * (1 + (Math.random()*0.1 - 0.03)); 
                 if(i%3===0) { cost += 10000; val += 10000; } 
                 mockHistoryData.value.push({ date, assets: Math.round(val), cost: Math.round(cost) });
             }
        }

        function openMonteCarlo() {
            showMCModal.value = true;
            mcOptimal.value = null; 
            nextTick(() => {
                runMonteCarlo();
            });
        }

        const mcRisk = ref('neutral'); 
        const macroRegime = ref('Normal'); 
        const enableBlackSwan = ref(false); 
        const enableInflation = ref(false);
        function calculateBlackLitterman(assets, rm, rf, sm, views = []) {
            const n = assets.length;
            const math = window.math;

            const varianceM = Math.pow(sm, 2);
            let covMatrix = [];
            for (let i = 0; i < n; i++) {
                covMatrix[i] = [];
                for (let j = 0; j < n; j++) {
                    covMatrix[i][j] = (i === j) ? Math.pow(assets[i].stdDev / 100, 2) : assets[i].beta * assets[j].beta * varianceM;
                }
            }
            const lambda = (rm - rf) / varianceM;
            const wkt = assets.map(a => a.totalWeight);
            const Sigma = math.matrix(covMatrix);
            const Pi_excess = math.multiply(lambda, math.multiply(Sigma, wkt)).toArray();

            if (!views || views.length === 0) return Pi_excess.map(p => p + rf);

            const tau = 0.05; 
            const tauSigma = math.multiply(tau, Sigma);
            const invTauSigma = math.inv(tauSigma);

            const K = views.length;
            let P = math.zeros([K, n]);
            let Q = [];

            views.forEach((v, k) => {
                const idx1 = assets.findIndex(a => a.ticker === v.asset1);
                if (idx1 < 0) return; 

                if (v.type === 'absolute') {
                    P[k][idx1] = 1;
                    Q.push((v.value / 100) - rf); 
                } else if (v.type === 'relative') {
                    const idx2 = assets.findIndex(a => a.ticker === v.asset2);
                    if (idx2 >= 0) {
                        P[k][idx1] = 1;
                        P[k][idx2] = -1;
                        Q.push(v.value / 100); 
                    }
                }
            });

            const P_mat = math.matrix(P);
            const Q_vec = math.matrix(Q);

            let Omega = math.zeros([K, K]);
            const P_tauSigma_Pt = math.multiply(math.multiply(P_mat, tauSigma), math.transpose(P_mat)).toArray();
            for(let k=0; k<K; k++) {
                Omega[k][k] = P_tauSigma_Pt[k][k]; 
                if(Omega[k][k] === 0) Omega[k][k] = 0.0001; 
            }
            const invOmega = math.inv(math.matrix(Omega));

            const Pt_invOmega_P = math.multiply(math.multiply(math.transpose(P_mat), invOmega), P_mat);
            const term1 = math.inv(math.add(invTauSigma, Pt_invOmega_P));

            const partA = math.multiply(invTauSigma, Pi_excess);
            const partB = math.multiply(math.multiply(math.transpose(P_mat), invOmega), Q_vec);
            const term2 = math.add(partA, partB);

            const posterior_excess = math.multiply(term1, term2).toArray();

            return posterior_excess.map(p => p + rf);
        }

        function runMonteCarlo() {
            const ctx = document.getElementById('mcChart');
            if(chartMC) chartMC.destroy(); 

            const assets = mcAvailableAssets.value;
            
            if(assets.length === 0) {
                alert("請先在「庫存」分頁填寫標的的 Beta 與 標準差 (不能為0)");
                showMCModal.value = false; return;
            }

            const n_assets = assets.length;
            const minWeight = 0.05; 
            if (n_assets * minWeight > 1.0) {
                alert(`標的數量 (${n_assets} 檔) 過多，無法滿足每檔最低 ${minWeight * 100}% 的限制！`);
                showMCModal.value = false; return;
            }
            const remainingWeight = 1.0 - (n_assets * minWeight);
            const n_portfolios = 5000;

            const regimeParams = {
                Normal: { rm: riskParams.value.rm / 100, sm: riskParams.value.sm / 100, rf: riskParams.value.rf / 100, stressCorr: 0, m_skew: -0.5, m_kurt_ex: 1.0 },
                Bull:   { rm: 0.15,  sm: 0.12, rf: 0.02,  stressCorr: 0,   m_skew: 0.2,  m_kurt_ex: 0.5 },
                Bear:   { rm: -0.10, sm: 0.25, rf: 0.01,  stressCorr: 0.5, m_skew: -1.0, m_kurt_ex: 2.0 },
                Crisis: { rm: -0.25, sm: 0.40, rf: 0.001, stressCorr: 1.0, m_skew: -2.5, m_kurt_ex: 5.0 }
            };
            const { rm, sm, rf, stressCorr, m_skew, m_kurt_ex } = regimeParams[macroRegime.value];

            const bl_expected_returns = calculateBlackLitterman(assets, rm, rf, sm, blViews.value);

            const mcPoints = [];
            let bestScore = -99999;
            let maxScoreForColor = -99999;
            let minScoreForColor = 99999;
            let bestPort = null;

            let riskAversionA = 0;
            if (mcRisk.value === 'averse') riskAversionA = 10;      
            else if (mcRisk.value === 'aggressive') riskAversionA = 1; 

            for (let p = 0; p < n_portfolios; p++) {
                let randWeights = Array.from({length: n_assets}, () => Math.random());
                const sumRand = randWeights.reduce((a,b)=>a+b, 0);
                let weights = randWeights.map(w => minWeight + (w / sumRand) * remainingWeight);

                let p_ret = 0;
                let p_beta = 0;
                let weighted_vol_sum = 0; 

                weights.forEach((w, i) => {
                    const e_r = bl_expected_returns[i]; 
                    p_ret += w * e_r;
                    p_beta += w * assets[i].beta;
                    weighted_vol_sum += w * (assets[i].stdDev / 100);
                });

                let sys_var = Math.pow(p_beta, 2) * Math.pow(sm, 2);
                let idio_var = 0;
                weights.forEach((w, i) => {
                    const sig_i = assets[i].stdDev / 100;
                    let idio_i = Math.pow(sig_i, 2) - Math.pow(assets[i].beta * sm, 2);
                    if(idio_i < 0) idio_i = 0; 
                    idio_var += Math.pow(w, 2) * idio_i;
                });
                
                let standard_vol = Math.sqrt(sys_var + idio_var);
                let p_vol = standard_vol * (1 - stressCorr) + weighted_vol_sum * stressCorr;

                let p_skew = p_vol > 0 ? (Math.pow(p_beta, 3) * Math.pow(sm, 3) * m_skew) / Math.pow(p_vol, 3) : 0;
                let p_kurt_ex = p_vol > 0 ? (Math.pow(p_beta, 4) * Math.pow(sm, 4) * m_kurt_ex) / Math.pow(p_vol, 4) : 0;

                if (enableBlackSwan.value) {
                    const jump_prob_daily = 0.005;
                    const expected_jumps_yr = jump_prob_daily * 252; 
                    const jump_mean = -0.15; 
                    const jump_std = 0.05;   
                    
                    p_ret = p_ret + (expected_jumps_yr * jump_mean);
                    p_vol = Math.sqrt(Math.pow(p_vol, 2) + expected_jumps_yr * (Math.pow(jump_mean, 2) + Math.pow(jump_std, 2)));
                    p_skew -= 1.5; 
                    p_kurt_ex += 4.0;
                }

                let rf_effective = rf; 
                if (enableInflation.value) {
                    const inf_mean = 0.025; 
                    const inf_std = 0.015;  
                    p_ret = p_ret - inf_mean; 
                    p_vol = Math.sqrt(Math.pow(p_vol, 2) + Math.pow(inf_std, 2)); 
                    rf_effective = rf - inf_mean; 
                }

                const p_sharpe = p_vol > 0 ? (p_ret - rf_effective) / p_vol : 0;
                const p_asr = p_sharpe * (1 + (p_skew / 6) * p_sharpe - (p_kurt_ex / 24) * Math.pow(p_sharpe, 2));

                let currentScore = 0;
                if (mcRisk.value === 'neutral') {
                    currentScore = p_asr; 
                } else if (mcRisk.value === 'averse') {
                    currentScore = p_ret - (0.5 * riskAversionA * Math.pow(p_vol, 2)) + (0.05 * p_skew) - (0.02 * p_kurt_ex);
                } else {
                    currentScore = p_ret - (0.5 * riskAversionA * Math.pow(p_vol, 2)) + (0.02 * p_skew);
                }

                mcPoints.push({ x: p_vol * 100, y: p_ret * 100, sharpe: p_asr, score: currentScore, weights });

                if (currentScore > maxScoreForColor) maxScoreForColor = currentScore;
                if (currentScore < minScoreForColor) minScoreForColor = currentScore;

                if (currentScore > bestScore) {
                    bestScore = currentScore;
                    bestPort = { ret: p_ret, vol: p_vol, sharpe: p_asr, skew: p_skew, kurt: p_kurt_ex, weights };
                }
            }

            if(bestPort) {
                const wList = [];
                const totalVal = totalStockValueTwd.value; 
                bestPort.weights.forEach((w, i) => { 
                    const optW = w * 100;
                    const curW = totalVal > 0 ? (assets[i].marketValueTwd / totalVal) * 100 : 0;
                    wList.push({
                        ticker: assets[i].ticker,
                        opt: optW.toFixed(2),
                        cur: curW.toFixed(2),
                        diff: (optW - curW).toFixed(2)
                    }); 
                });
                wList.sort((a,b) => parseFloat(b.opt) - parseFloat(a.opt));

                mcOptimal.value = {
                    ret: (bestPort.ret * 100).toFixed(2),
                    vol: (bestPort.vol * 100).toFixed(2),
                    sharpe: bestPort.sharpe.toFixed(3),
                    skew: bestPort.skew.toFixed(2),
                    kurt: bestPort.kurt.toFixed(2),
                    weights: wList
                };
            }

            chartMC = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [
                        {
                            label: 'Simulated Portfolios',
                            data: mcPoints,
                            backgroundColor: (context) => {
                                const val = context.raw?.score;
                                if (val === undefined) return '#3b82f6';
                                const ratio = Math.max(0, Math.min(1, (val - minScoreForColor) / (maxScoreForColor - minScoreForColor))); 
                                return `rgba(${Math.round(255*ratio)}, ${Math.round(150*ratio)}, 200, 0.4)`;
                            },
                            pointRadius: 2
                        },
                        {
                            label: 'Optimal Portfolio (ASR)',
                            data: [{ x: bestPort.vol * 100, y: bestPort.ret * 100 }],
                            backgroundColor: '#fbbf24', pointRadius: 8, borderColor: '#fff', borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { tooltip: { callbacks: { label: (ctx) => `Vol: ${ctx.raw.x.toFixed(2)}%, Ret: ${ctx.raw.y.toFixed(2)}%` } } },
                    scales: { x: { title: {display: true, text: 'Volatility (σ%)'} }, y: { title: {display: true, text: 'Expected Return (%)'} } }
                }
            });
        }
        
        function getTypeColor(type) { return type==='Buy'?'text-red-400':'text-green-400'; }
        function getCategoryColorCode(cat) { return '#3b82f6'; }
        function formatNumber(n) { return new Intl.NumberFormat('zh-TW', {maximumFractionDigits:0}).format(n||0); }
        function formatPercent(n) { return ((n||0)*100).toFixed(1) + '%'; }

        let chartSML, chartCML, chartAlloc, chartHist, chartRolling, chartMC, chartFire;

        function initCharts() {
            Chart.defaults.color = '#94a3b8'; Chart.defaults.borderColor = '#334155';

            const allocCtx = document.getElementById('allocationChart');
            if(allocCtx && !chartAlloc) {
                chartAlloc = new Chart(allocCtx, { type: 'doughnut', data: { labels: [], datasets: [{data:[]}] }, options: { responsive: true, maintainAspectRatio: false } });
            }

            const histCtx = document.getElementById('historyChart');
            if(histCtx && !chartHist) {
                chartHist = new Chart(histCtx, { type: 'line', data: { labels: [], datasets: [{data:[]},{data:[]}] }, options: { responsive: true, maintainAspectRatio: false } });
            }

            const smlCtx = document.getElementById('smlChart');
            if(smlCtx && !chartSML) {
                chartSML = new Chart(smlCtx, {
                    type: 'scatter', data: { datasets: [] },
                    options: { 
                        responsive: true, maintainAspectRatio: false,
                        scales: { x: { title: {display:true, text:'Beta (β)'}, min: 0, max: 2 }, y: { title: {display:true, text:'Expected Return (%)'} } },
                        plugins: { tooltip: { callbacks: { label: (ctx) => `${ctx.raw.name}: (${ctx.raw.x}, ${ctx.raw.y}%)` } } }
                    }
                });
            }

            const cmlCtx = document.getElementById('cmlChart');
            if(cmlCtx && !chartCML) {
                chartCML = new Chart(cmlCtx, {
                    type: 'scatter', data: { datasets: [] },
                    options: { 
                        responsive: true, maintainAspectRatio: false,
                        scales: { x: { title: {display:true, text:'StdDev (σ)'}, min: 0 }, y: { title: {display:true, text:'Expected Return (%)'} } }
                    }
                });
            }

            const rollingCtx = document.getElementById('rollingChart');
            if(rollingCtx && !chartRolling) {
                chartRolling = new Chart(rollingCtx, {
                    type: 'line', data: { labels: [], datasets: [] },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        scales: {
                            y: { type: 'linear', display: true, position: 'left', title: {display: true, text: 'Sharpe Ratio'} },
                            y1: { type: 'linear', display: true, position: 'right', grid: {drawOnChartArea: false}, title: {display: true, text: 'Volatility (%)'} }
                        }
                    }
                });
            }
            
            const fireCtx = document.getElementById('fireChart');
            if(fireCtx && !chartFire) {
                chartFire = new Chart(fireCtx, {
                    type: 'line', data: { labels: [], datasets: [] },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        scales: { 
                            x: { title: {display:true, text:'年份'} }, 
                            y: { title: {display:true, text:'總淨值 (TWD)'}, beginAtZero: true } 
                        },
                        plugins: { 
                            tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: NT$ ${new Intl.NumberFormat('zh-TW').format(ctx.raw)}` } },
                            legend: { labels: { color: '#e2e8f0' } }
                        }
                    }
                });
            }
        }

        function updateCharts() {
            requestAnimationFrame(() => {
                initCharts(); 

                if (chartAlloc) {
                    const cats = categoryTotals.value;
                    chartAlloc.data.labels = Object.keys(cats); chartAlloc.data.datasets[0].data = Object.values(cats); 
                    chartAlloc.data.datasets[0].backgroundColor = ['#f59e0b','#3b82f6','#10b981','#a855f7'];
                    chartAlloc.update();
                }
                
                if (chartHist) {
                    const history = displayHistory.value; const sorted = [...history].sort((a,b)=>new Date(a.date)-new Date(b.date));
                    chartHist.data.labels = sorted.map(h=>h.date);
                    chartHist.data.datasets[0] = { label: 'NAV', data: sorted.map(h=>h.assets), borderColor: '#3b82f6', fill: true, backgroundColor: 'rgba(59,130,246,0.1)', tension: 0.1 };
                    chartHist.data.datasets[1] = { label: 'Cost', data: sorted.map(h=>h.cost), borderColor: '#10b981', borderDash:[5,5], tension: 0.1 };
                    
                    if (chartHist.data.datasets.length > 2) {
                        chartHist.data.datasets.splice(2);
                    }
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
                        if (y === startYear && history.filter(h => h.date.startsWith(startYear.toString())).length === 0) return 0;
                        
                        const recordsInYear = history.filter(h => h.date.startsWith(y.toString()));
                        if (recordsInYear.length > 0) {
                            recordsInYear.sort((a, b) => new Date(a.date) - new Date(b.date));
                            lastKnownAsset = recordsInYear[recordsInYear.length - 1].assets;
                            return lastKnownAsset;
                        }
                        return (y <= currentYear && lastKnownAsset > 0) ? lastKnownAsset : null;
                    });

                    chartFire.data.labels = labels;
                    chartFire.data.datasets = [
                        { label: '🎯 FIRE 目標', data: targetData, borderColor: '#fbbf24', borderDash: [5, 5], spanGaps: true, tension: 0, pointBackgroundColor: '#fbbf24', pointRadius: (ctx) => ctx.raw !== null ? 4 : 0 },
                        { label: '💰 實際水位 (NAV)', data: actualData, borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', fill: true, spanGaps: true, tension: 0.3, pointRadius: 3 }
                    ];
                    chartFire.update();
                }

                if (chartSML && chartCML) {
                    const rf = riskParams.value.rf;
                    const rm = riskParams.value.rm;
                    const sm = riskParams.value.sm;
                    
                    const smlLine = [ {x:0, y:rf}, {x:2, y: rf + 2*(rm-rf)} ];
                    const slope = (rm - rf) / sm;
                    const maxX = sm * 2.5; 
                    const cmlLine = [ { x: 0, y: rf }, { x: sm, y: rm }, { x: maxX, y: rf + slope * maxX } ];

                    const portRet = parseFloat(stats.value.annRet) || 0;
                    const portVol = parseFloat(stats.value.annVol) || 0;
                    const portBeta = parseFloat(riskParams.value.beta) || 0;

                    const portPoint = { x: portBeta, y: portRet, name: 'Portfolio' };
                    const portPointCML = { x: portVol, y: portRet, name: 'Portfolio' };
                    const marketPoint = { x: sm, y: rm, name: 'Market Index' };

                    const assetPoints = [];
                    for(const cat in groupedHoldings.value) {
                       groupedHoldings.value[cat].items.forEach(i => {
                            assetPoints.push({ x: i.beta, y: parseFloat(i.returnRate), name: i.ticker });
                        });
                    }

                    chartSML.data.datasets = [
                        { type: 'line', label: 'SML', data: smlLine, borderColor: '#94a3b8', borderWidth: 2, pointRadius: 0 },
                        { type: 'scatter', label: 'Holdings', data: assetPoints, backgroundColor: '#f59e0b' },
                        { type: 'scatter', label: 'Portfolio', data: [portPoint], backgroundColor: '#ef4444', pointRadius: 8 }
                    ];
                    chartSML.update();

                    chartCML.data.datasets = [
                        { type: 'line', label: 'CML', data: cmlLine, borderColor: '#94a3b8', borderWidth: 2, pointRadius: 0 },
                        { type: 'scatter', label: 'Market', data: [marketPoint], backgroundColor: '#10b981', pointRadius: 6 },
                        { type: 'scatter', label: 'Portfolio', data: [portPointCML], backgroundColor: '#ef4444', pointRadius: 8 }
                    ];
                    chartCML.update();
                }

                // ==========================================
                // 🌟 升級版 3: 滾動圖表掛載純淨報酬率
                // ==========================================
                if (chartRolling) {
                    const h = [...enrichedHistory.value].reverse(); // 轉回正序
                    const periodReturns = [];
                    const dates = [];
                    
                    for(let i=1; i<h.length; i++) {
                        periodReturns.push(h[i].dailyReturn);
                        dates.push(h[i].date);
                    }

                    const windowSize = 52; 
                    const factor = Math.sqrt(52);
                    const rf = riskParams.value.rf / 100;
                    
                    const rollLabels = [];
                    const rollSharpe = [];
                    const rollVol = [];

                    if (periodReturns.length >= windowSize) {
                        for (let i = windowSize; i <= periodReturns.length; i++) {
                            const windowR = periodReturns.slice(i - windowSize, i);
                            const avgR = windowR.reduce((a,b)=>a+b,0) / windowSize;
                            const varR = windowR.reduce((a,b)=>a+Math.pow(b-avgR,2),0) / (windowSize-1);
                            
                            const annVol = Math.sqrt(varR) * factor;
                            const cumTwr = windowR.reduce((acc, r) => acc * (1 + r), 1) - 1;
                            
                            const sharpe = annVol > 0 ? (cumTwr - rf) / annVol : 0;
                            
                            rollLabels.push(dates[i-1]);
                            rollSharpe.push(sharpe.toFixed(2));
                            rollVol.push((annVol*100).toFixed(2));
                        }
                    }

                    chartRolling.data.labels = rollLabels;
                    chartRolling.data.datasets = [
                        { label: 'Rolling Sharpe', data: rollSharpe, borderColor: '#fbbf24', yAxisID: 'y', tension: 0.3, pointRadius: 1 },
                        { label: 'Rolling Volatility (%)', data: rollVol, borderColor: '#ef4444', borderDash: [5,5], yAxisID: 'y1', tension: 0.3, pointRadius: 1 }
                    ];
                    chartRolling.update();
                }
            });
        }
        
        onMounted(() => { 
            loadDataFromCloud(); 
        });
        
        watch(currentTab, () => { 
            nextTick(() => { updateCharts(); });
        });

        watch([exchangeRate, sheetUrl, isSimMode, riskParams, quantStartDate, dataFrequency, fireTargets], () => updateCharts(), {deep:true});

        return { 
            currentTab, showHistoryModal, isUpdating, isSimMode, toggleSimMode, 
            transactions, groupedHoldings, categoryTotals, riskTotals, portfolioStats, 
            totalStockValueTwd, totalStockCostTwd, totalStockUnrealizedPL, totalStockReturnRate, 
            reversedTransactions, txForm, historyForm, riskParams, stats, exchangeRate, 
            sheetUrl, addTransaction, addHistoryRecord, generateMonthlyMockData, 
            removeTransaction, removeHistoryByDate, manualUpdate, updateMeta, fetchPrices, 
            exportAll, importData, getTypeColor, getCategoryColorCode, formatNumber, formatPercent, 
            lastUpdate, displayHistory, enrichedHistory, quantStartDate, dataFrequency, 
            snapshotToHistory, snapshotDate, isDbSyncing, 
            isAppReady, showMCModal, mcOptimal, openMonteCarlo, aiInsights, isAiExpanded, quantDays,
            fireTargets, activeFireStageIndex, activeFireTarget, isLoggedIn, loginEmail, loginPassword, loginError, 
            isAuthenticating, handleLogin, handleLogout, checkAuth, fireProgress, 
            updateCharts, addFireTarget, macroRegime, enableBlackSwan, mcRisk, blViews, mcAvailableAssets, addBlView, enableInflation,
            generateAutoViews, runMonteCarlo, stressTestResults
        };
    }
}).mount('#app');
