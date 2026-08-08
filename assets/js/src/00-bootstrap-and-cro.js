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

            const twrNum = Number(stats.value.annRet);
            const mwrNum = Number(stats.value.mwr);
            const payload = {
    report_metadata: {
        purpose: 'diagnostic_and_rebalance_review_only',
        not_an_execution_order: true,
        data_frequency: dataFrequency.value,
        tail_comparison_horizon_weeks: tailStatsLite.value.jdHorizonWeeks
    },
    return_metrics: {
        time_weighted_return_twr_annualized: stats.value.annRet + '%',
        money_weighted_return_mwr_xirr_annualized: stats.value.mwr === '-' ? 'N/A' : stats.value.mwr + '%',
        mwr_minus_twr_percentage_points: Number.isFinite(twrNum) && Number.isFinite(mwrNum)
            ? (mwrNum - twrNum).toFixed(2) + 'pp'
            : 'N/A',
        capm_alpha_proxy: stats.value.alpha + '%',
        capm_alpha_method: 'annualized_TWR_minus_[rf_plus_current_metadata_beta_times_market_risk_premium]',
        realized_jensen_alpha_method: alphaRegressionStats.value.method || 'N/A',
        realized_jensen_benchmark_policy: alphaRegressionStats.value.benchmarkPolicy || 'N/A',
        realized_jensen_vs_spy: {
            alpha_annualized_pct: alphaRegressionStats.value.spy.alphaAnnualPct,
            hac_t_stat: alphaRegressionStats.value.spy.tStat,
            hac_p_value: alphaRegressionStats.value.spy.pValue,
            ci95_annualized_pct: [alphaRegressionStats.value.spy.ciLow, alphaRegressionStats.value.spy.ciHigh],
            beta: alphaRegressionStats.value.spy.beta,
            r_squared: alphaRegressionStats.value.spy.rSquared,
            n: alphaRegressionStats.value.spy.n,
            evidence_5pct: alphaRegressionStats.value.spy.evidence
        },
        realized_jensen_vs_twii: {
            alpha_annualized_pct: alphaRegressionStats.value.twii.alphaAnnualPct,
            hac_t_stat: alphaRegressionStats.value.twii.tStat,
            hac_p_value: alphaRegressionStats.value.twii.pValue,
            ci95_annualized_pct: [alphaRegressionStats.value.twii.ciLow, alphaRegressionStats.value.twii.ciHigh],
            beta: alphaRegressionStats.value.twii.beta,
            r_squared: alphaRegressionStats.value.twii.rSquared,
            n: alphaRegressionStats.value.twii.n,
            evidence_5pct: alphaRegressionStats.value.twii.evidence
        },
        realized_jensen_benchmark_alpha_spread_pp: alphaRegressionStats.value.benchmarkAlphaSpreadPp,
        alpha_selection_attribution: 'Not isolated: realized Jensen alpha combines security selection, asset allocation, and timing effects after external cash-flow adjustment.'
    },
    risk_efficiency: {
        portfolio_beta: riskParams.value.beta,
        portfolio_volatility: stats.value.annVol + '%',
        historical_sharpe: stats.value.sharpe,
        historical_psr: stats.value.psr === '-' ? 'N/A' : stats.value.psr + '%',
        historical_psr_benchmark_sharpe: 0,
        historical_psr_method_note: 'Approximate probability that period Sharpe exceeds 0; below 95% means insufficient high-confidence evidence, not proof of randomness.',
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
        recommended_buffer: mcOptimal.value?.recommendedBuffer ? mcOptimal.value.recommendedBuffer + '%' : 'N/A',
        method_note: 'Sizing reference only; it does not override tail-risk, liquidity, or policy constraints.'
    },
    asymmetry_and_win_rate: {
        omega_ratio: stats.value.omega,
        profit_factor_pf: stats.value.profitFactor,
        skewness: stats.value.skew,
        excess_kurtosis: stats.value.kurt
    },
    catastrophic_risk_from_nav_history: {
        max_drawdown_mdd: stats.value.mdd + '%',
        ulcer_index_ui: stats.value.ulcer,
        time_under_water_tuw_days: stats.value.tuw,
        calmar_ratio: stats.value.calmar,
        single_period_var95: stats.value.var95 + '%',
        single_period_cvar95: stats.value.cvar95 + '%',
        note: 'These are based on actual NAV snapshot periods and are not automatically comparable with a 13-week simulation.'
    },
    systemic_correlation: sysCorr.value.toFixed(2),

    regime_rebalance_monitor: {
        overweight_trim_candidates: rebalanceMonitor.value.trimCount,
        underweight_add_candidates: rebalanceMonitor.value.addCount,
        total_target_drift_candidates: rebalanceMonitor.value.driftCount,
        concentration_candidates_over_20pct: rebalanceMonitor.value.concentrationCount,
        high_priority_alerts: rebalanceMonitor.value.alertCount,
        leverage_vol_drag_30d: rebalanceMonitor.value.volDrag30d + '%',
        leverage_vol_drag_90d: rebalanceMonitor.value.volDrag90d + '%',
        buffer_floor_pct: rebalanceMonitor.value.bufferFloorPct + '%',
        current_buffer_pct: rebalanceMonitor.value.currentBufferPct + '%',
        buffer_gap_pct: rebalanceMonitor.value.bufferGapPct + '%',
        buffer_blocking_risk_buys: rebalanceMonitor.value.bufferBlockingRiskBuys ? 'YES' : 'NO',
        buffer_floor_status: Number(rebalanceMonitor.value.bufferFloorPct) <= 0
            ? 'DISABLED_ZERO_FLOOR'
            : 'ACTIVE',
        hard_buffer_tickers: (rebalanceMonitor.value.hardBufferTickers || []).join(' + '),
        rebalance_alerts_with_direction: rebalanceMonitor.value.alerts.slice(0, 8)
    },

    portfolio_xray: {
        pc1_explained: xrayStats.value.pca.pc1Explained === '-' ? 'N/A' : xrayStats.value.pca.pc1Explained + '%',
        pc1_to_pc3_cumulative: xrayStats.value.pca.pc3CumExplained === '-' ? 'N/A' : xrayStats.value.pca.pc3CumExplained + '%',
        usd_exposure_pct: xrayStats.value.fx.netFxExposurePct === '-' ? 'N/A' : xrayStats.value.fx.netFxExposurePct + '%',
        fx_1pct_nav_impact_twd: xrayStats.value.fx.usdNavImpact1pct,
        top_risk_contributors: xrayStats.value.mrcTable.slice(0, 5),
        etf_lookthrough_status: xrayStats.value.lookthrough?.status || 'unknown',
        etf_lookthrough_note: xrayStats.value.lookthrough?.note || '',
        etf_supported_sleeve_pct_of_portfolio: xrayStats.value.lookthrough?.heldSupportedEtfSleevePct,
        etf_mapped_underlying_pct_of_portfolio: xrayStats.value.lookthrough?.mappedEquityPortfolioPct,
        etf_supported_sleeve_equity_coverage_pct: xrayStats.value.lookthrough?.heldSupportedSleeveCoveragePct,
        etf_top5_underlying_pct_of_portfolio: xrayStats.value.lookthrough?.top5UnderlyingPortfolioPct,
        etf_top_underlying: (xrayStats.value.lookthrough?.topUnderlying || []).slice(0, 10),
        etf_pairwise_constituent_overlap: (xrayStats.value.lookthrough?.pairwiseOverlap || []).slice(0, 10),
        etf_loaded_funds: xrayStats.value.lookthrough?.loadedFunds || [],
        etf_missing_funds: xrayStats.value.lookthrough?.missingFunds || [],
        etf_nonofficial_source_funds: xrayStats.value.lookthrough?.nonofficialFunds || [],
        etf_stale_funds: xrayStats.value.lookthrough?.staleFunds || []
    },

    tail_crash_radar_1w: {
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

    same_horizon_tail_comparison: {
        horizon_weeks: tailStatsLite.value.jdHorizonWeeks,
        historical_current_weight_var95: tailStatsLite.value.historicalHorizonVar95 === '-' ? 'N/A' : tailStatsLite.value.historicalHorizonVar95 + '%',
        historical_current_weight_es95: tailStatsLite.value.historicalHorizonEs95 === '-' ? 'N/A' : tailStatsLite.value.historicalHorizonEs95 + '%',
        historical_sample_count: tailStatsLite.value.historicalHorizonSampleCount,
        historical_method: tailStatsLite.value.historicalHorizonMethod,
        jump_stress_var95: tailStatsLite.value.jdVar95 === '-' ? 'N/A' : tailStatsLite.value.jdVar95 + '%',
        jump_stress_es95: tailStatsLite.value.jdEs95 === '-' ? 'N/A' : tailStatsLite.value.jdEs95 + '%',
        jump_stress_probability_below_threshold: tailStatsLite.value.jdCrashProb === '-' ? 'N/A' : tailStatsLite.value.jdCrashProb + '%',
        jump_stress_threshold: tailStatsLite.value.jdCrashThresholdPct === '-' ? 'N/A' : tailStatsLite.value.jdCrashThresholdPct + '%',
        note: 'Historical and jump-stress metrics in this object use the same horizon and current-weight synthetic portfolio. Historical observations are overlapping and therefore not independent.'
    },

    jump_stress_scenario: {
        model_type: tailStatsLite.value.jdModelType,
        parameter_source: tailStatsLite.value.jdParameterSource,
        jump_aggregation: tailStatsLite.value.jdJumpAggregation,
        drift_compensated: tailStatsLite.value.jdDriftCompensated,
        simulation_count: tailStatsLite.value.jdSimulationCount,
        effective_annual_jump_frequency: tailStatsLite.value.jdEffectiveLambda,
        weighted_jump_mean_assumption: tailStatsLite.value.jdEffectiveJumpMean,
        weighted_jump_std_assumption: tailStatsLite.value.jdEffectiveJumpStd,
        expected_jump_drag_weekly_pct: tailStatsLite.value.jdExpectedJumpDragWeeklyPct,
        es_absolute_value_duplicate: tailStatsLite.value.jdTailLoss === '-' ? 'N/A' : tailStatsLite.value.jdTailLoss + '%'
    },

    evt_tail_1w: {
        evt_var95: tailStatsLite.value.evtVar95 === '-' ? 'N/A' : tailStatsLite.value.evtVar95 + '%',
        evt_es95: tailStatsLite.value.evtEs95 === '-' ? 'N/A' : tailStatsLite.value.evtEs95 + '%',
        evt_shape_xi: tailStatsLite.value.evtShapeXi,
        evt_scale_beta: tailStatsLite.value.evtScaleBeta,
        evt_threshold: tailStatsLite.value.evtThreshold === '-' ? 'N/A' : tailStatsLite.value.evtThreshold + '%',
        evt_exceedance_count: tailStatsLite.value.evtExceedanceCount,
        evt_alpha_conf: tailStatsLite.value.evtAlphaConf === '-' ? 'N/A' : 'P' + tailStatsLite.value.evtAlphaConf,
        horizon_weeks: tailStatsLite.value.evtHorizonWeeks,
        directly_comparable_to_jump_stress: tailStatsLite.value.evtComparableToJd,
        comparison_note: tailStatsLite.value.evtComparisonNote
    }
};

            const promptText = `
[SYSTEM_DIRECTIVE]
Task: Act as an evidence-disciplined Quant Chief Risk Officer for a family office.
Tone: Direct, analytical, and proportionate to the evidence. Avoid dramatic language, certainty inflation, and moral judgments about the investor.
Constraint: Output strictly in Traditional Chinese. Maximum 8 bullets. No pleasantries.

[EVIDENCE RULES]
- Separate measured historical results, model estimates, heuristic stress assumptions, and policy thresholds. Never present one category as another.
- Compare VaR/ES values only when horizon, portfolio construction, confidence level, and return definition are aligned.
- The object same_horizon_tail_comparison is the valid comparison for historical versus jump-stress tail risk.
- evt_tail_1w is a one-week POT-GPD diagnostic. Do not compare its magnitude directly with a 13-week jump-stress result.
- jump_stress_scenario uses asset-class policy assumptions and independent asset-level Poisson jumps. It is a stress scenario, not a historically fitted crash probability model.
- jd_tail_loss is the absolute value of jd_es95 and is not independent corroborating evidence.
- Interpret jd_crash_prob only as the probability that the simulated horizon return breaches the stated jump_stress_threshold.
- If EVT xi < 0, say only that the fitted POT-GPD tail is bounded under the current threshold/sample and does not provide evidence for an xi > 0 heavy-tail regime. Do NOT conclude that the true return distribution 'is not heavy-tailed' or rule out heavy tails. If exceedance count is small, state that xi and ES are unstable and tail-classification evidence is weak.
- Small tail/crisis samples are preliminary evidence, not an "extremely clear" signal. Do not claim statistical certainty without confidence intervals.
- Historical PSR uses benchmark Sharpe 0. Interpret PSR as the estimated probability/confidence that the true Sharpe exceeds 0 under the PSR model. A value below 95% means it has not met a strict 95% credibility threshold. Never describe PSR as a test of whether returns are random, and do not infer survivor bias from it.
- MWR > TWR may indicate favorable cash-flow timing. It does not prove security selection skill.
- capm_alpha_proxy is not regression-estimated Jensen alpha and has no t-stat. Do not claim persistent selection alpha from the proxy.
- realized_jensen_vs_spy and realized_jensen_vs_twii are OLS CAPM regressions on realized cash-flow-adjusted NAV snapshot returns with HAC/Newey-West inference. Treat alpha as benchmark-dependent. If the 95% CI includes zero or HAC p-value >= 0.05, say alpha is not statistically distinguishable from zero under that benchmark. Even when significant, do not call it pure security-selection skill because allocation and timing effects remain inside realized portfolio returns.
- Compare SPY and ^TWII results. A material benchmark alpha spread is evidence of benchmark sensitivity/model specification risk, not a second independent alpha signal.
- Rebalance alerts include current weight, target weight, signed drift, and candidate action. Never infer Trim from an underweight alert.
- If buffer_floor_status is DISABLED_ZERO_FLOOR, say the hard floor is inactive; do not praise compliance with a zero constraint.
- BOXX and SHY may reduce risk-asset exposure but retain USD and instrument-specific risk for a TWD investor. Do not call them literally risk-free.
- If ETF look-through is unavailable, state that constituent overlap cannot be directly quantified. PCA and MRC reflect price covariance / risk contribution only; they may reveal correlated concentration indirectly but do not measure shared constituent holdings. If look-through is available, use the reported top underlying and pairwise constituent overlap directly, state coverage/source limits, and do not extrapolate uncovered assets.
- Do not infer "discipline failure" from a single snapshot. Describe observed drift and the rule that triggered it.

[ANALYSIS TASKS]
1. 【資金效率 / Alpha】Compare TWR, MWR, the CAPM alpha proxy, and realized Jensen alpha vs SPY / ^TWII. Report HAC t-stat, p-value and 95% CI when available; explicitly discuss benchmark sensitivity and do not equate regression alpha with pure selection skill.
2. 【風險報酬可信度】Assess Sharpe, PSR/DSR, volatility, Sortino and Treynor. State PSR as confidence/probability that the true Sharpe exceeds its benchmark; never phrase it as confirming that returns are non-random.
3. 【Portfolio X-Ray】Assess concentration, risk contribution, PCA, USD exposure and look-through coverage. Explicitly distinguish covariance-based concentration from constituent overlap: PCA/MRC do not directly measure shared ETF holdings. Use "risk concentration" rather than "leverage" unless actual leverage exists.
4. 【再平衡監控】Distinguish Trim, Add, general drift and concentration candidates. State the exact direction of major alerts.
5. 【Tail / Crash Radar】Assess crisis correlation and downside behavior while explicitly qualifying small samples.
6. 【13週尾部風險】Inspect same_horizon_tail_comparison. If historical_current_weight_var95 and historical_current_weight_es95 are both available, title the bullet 【13週同期間尾部比較】 and compare them with jump-stress on the same horizon. If either historical metric is N/A, title the bullet 【13週跳躍壓力測試】, report the jump-stress scenario only, and state that a same-horizon historical comparison is unavailable. Never label a jump-only paragraph as a same-horizon comparison.
7. 【EVT】Discuss the one-week EVT result separately, including xi sign, threshold, exceedance count and lack of direct 13-week comparability. A negative xi with a small exceedance sample must not be used to classify the true return distribution as non-heavy-tailed.
8. 【CRO 最終指令】Choose one of Review / Hold / Conditional Trim / Trim / Raise Cash. Use Trim or Raise Cash only when an explicit target band, concentration cap, buffer constraint, or risk-budget breach is shown. Otherwise use Review or Conditional Trim and state the trigger.

[OUTPUT_FORMAT]
- **[維度名稱]**: [結論、證據限制、具體下一步]

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

