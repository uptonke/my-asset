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

