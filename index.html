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
        
