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

