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
    const { date, type, category, ticker, price, shares, amount } = txForm.value;
    if (!date) return;

    let finalPrice = null;
    let finalShares = null;
    let actualTotal = null;
    let finalFlow = 0;

    if (type === 'Buy' || type === 'Sell') {
        finalShares = Number(shares);

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
        
