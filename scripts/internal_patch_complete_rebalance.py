from pathlib import Path


def force_crlf(path):
    p = Path(path)
    raw = p.read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    p.write_bytes(raw.replace(b'\n', b'\r\n'))


def replace_once(path, old, new, label, *, crlf=False):
    p = Path(path)
    s = p.read_text(encoding='utf-8')
    if old not in s:
        raise SystemExit(f'{path}: missing anchor {label}')
    s = s.replace(old, new, 1)
    p.write_text(s, encoding='utf-8')
    if crlf:
        force_crlf(p)


# Complete target sync: lazy Supabase import + explicit zero targets.
p = Path('scripts/sync_rebalance_from_delegated_target.py')
s = p.read_text(encoding='utf-8')
s = s.replace('from supabase import create_client\n\n', '', 1)
old = """    row_map: Dict[str, Dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        t = str(raw.get("ticker") or "").strip()
        if t:
            row_map[t] = dict(raw)

    cash_target_pct"""
new = """    row_map: Dict[str, Dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        t = str(raw.get("ticker") or "").strip()
        if not t:
            continue
        row_map[t] = dict(raw)
        if t not in weights:
            zero_or_machine = raw.get("machine_target_weight_pct", raw.get("final_suggested_weight_pct"))
            if zero_or_machine is not None:
                w = _num(zero_or_machine, -1.0)
                if w < 0:
                    raise RuntimeError(f"invalid machine target weight for {t}: {zero_or_machine}")
                weights[t] = w

    cash_target_pct"""
if old not in s:
    raise SystemExit('sync script: row_map anchor missing')
s = s.replace(old, new, 1)
old = """    supabase = create_client(url, key)
    response = supabase.table(TABLE).select("stock_meta")"""
new = """    from supabase import create_client

    supabase = create_client(url, key)
    response = supabase.table(TABLE).select("stock_meta")"""
if old not in s:
    raise SystemExit('sync script: client anchor missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# Holdings target: prefer complete delegated/blended vector.
replace_once(
    'assets/js/src/20-holdings-performance.js',
    """                const cloudTargetWeight = meta.target_weight ? (meta.target_weight * 100) : 0;
                let mcWeight = 0;
                if (mcOptimal.value && mcOptimal.value.weights) {
                    const match = mcOptimal.value.weights.find(w => w.ticker === h.ticker);
                    if (match) mcWeight = parseFloat(match.opt);
                }
                let finalBlendedWeight = cloudTargetWeight;
                if (mcOptimal.value) finalBlendedWeight = (cloudTargetWeight * 0.5) + (mcWeight * 0.5);""",
    """                const cloudTargetWeight = meta.target_weight ? (meta.target_weight * 100) : 0;
                const completeTargetMap = (
                    cloudRebalanceMeta.value?.target_vector_complete === true &&
                    cloudRebalanceMeta.value?.target_weights_pct &&
                    typeof cloudRebalanceMeta.value.target_weights_pct === 'object'
                ) ? cloudRebalanceMeta.value.target_weights_pct : null;
                const completeTargetRaw = completeTargetMap ? Number(completeTargetMap[h.ticker]) : NaN;
                const hasCompleteRebalanceTarget = Number.isFinite(completeTargetRaw);
                const rebalanceTargetWeight = hasCompleteRebalanceTarget ? completeTargetRaw : cloudTargetWeight;
                let mcWeight = 0;
                if (mcOptimal.value && mcOptimal.value.weights) {
                    const match = mcOptimal.value.weights.find(w => w.ticker === h.ticker);
                    if (match) mcWeight = parseFloat(match.opt);
                }
                let finalBlendedWeight = rebalanceTargetWeight;
                if (!hasCompleteRebalanceTarget && mcOptimal.value) {
                    finalBlendedWeight = (cloudTargetWeight * 0.5) + (mcWeight * 0.5);
                }""",
    'target logic',
    crlf=True,
)
replace_once(
    'assets/js/src/20-holdings-performance.js',
    """                    targetWeight: cloudTargetWeight,
                    mcWeight: mcWeight,
                    blendedWeight: finalBlendedWeight""",
    """                    targetWeight: cloudTargetWeight,
                    rebalanceTargetWeight: rebalanceTargetWeight,
                    rebalanceTargetSource: hasCompleteRebalanceTarget
                        ? 'dual_blend_cloud_target_and_v105_native_target'
                        : (mcOptimal.value ? 'legacy_cloud_plus_browser_mc' : 'stock_meta.target_weight'),
                    mcWeight: mcWeight,
                    blendedWeight: finalBlendedWeight""",
    'target output fields',
    crlf=True,
)

# Rebalance metadata exposed to frontend/CRO.
replace_once(
    'assets/js/src/30-risk-xray-tail.js',
    """    universePolicy: '',
    ruleThresholdPp: 1,
    economicDustTickers: [],""",
    """    universePolicy: '',
    ruleThresholdPp: 1,
    targetWeightSource: '',
    targetVectorComplete: false,
    targetAssetWeightSumPct: null,
    cashTargetWeightPct: null,
    targetSourceGeneratedAt: '',
    economicDustTickers: [],""",
    'rebalance state',
)
replace_once(
    'assets/js/src/30-risk-xray-tail.js',
    """        universePolicy: backendRebalance.universe_policy || '',
        ruleThresholdPp: Number(backendRebalance.rule_threshold_pp || 1),
        economicDustTickers: Array.isArray(backendRebalance.economic_dust_tickers_excluded)""",
    """        universePolicy: backendRebalance.universe_policy || '',
        ruleThresholdPp: Number(backendRebalance.rule_threshold_pp || 1),
        targetWeightSource: backendRebalance.target_weight_source || '',
        targetVectorComplete: backendRebalance.target_vector_complete === true,
        targetAssetWeightSumPct: Number.isFinite(Number(backendRebalance.target_asset_weight_sum_pct))
            ? Number(backendRebalance.target_asset_weight_sum_pct) : null,
        cashTargetWeightPct: Number.isFinite(Number(backendRebalance.cash_target_weight_pct))
            ? Number(backendRebalance.cash_target_weight_pct) : null,
        targetSourceGeneratedAt: backendRebalance.target_source_generated_at || '',
        economicDustTickers: Array.isArray(backendRebalance.economic_dust_tickers_excluded)""",
    'rebalance final object',
)

# CRO: use visible cockpit threshold/counts and explain complete target/cash semantics.
replace_once(
    'assets/js/src/00-bootstrap-and-cro.js',
    """        overweight_trim_candidates: rebalanceMonitor.value.trimCount,
        underweight_add_candidates_actionable: rebalanceMonitor.value.addCount,
        underweight_add_candidates_blocked_by_buffer: rebalanceMonitor.value.blockedAddCount,
        total_target_drift_candidates: rebalanceMonitor.value.driftCount,
        concentration_candidates_over_20pct: rebalanceMonitor.value.concentrationCount,
        rule_engine_alerts: rebalanceMonitor.value.alertCount,""",
    """        overweight_trim_candidates: (rebalanceCockpitBuckets.value?.trim || []).length,
        underweight_add_candidates_actionable: (rebalanceCockpitBuckets.value?.add || []).length,
        underweight_add_candidates_blocked_by_buffer: (rebalanceCockpitBuckets.value?.pending || []).length,
        total_target_drift_candidates: (rebalanceCockpitBuckets.value?.trim || []).length
            + (rebalanceCockpitBuckets.value?.add || []).length
            + (rebalanceCockpitBuckets.value?.pending || []).length,
        concentration_candidates_over_20pct: rebalanceMonitor.value.concentrationCount,
        rule_engine_alerts: (rebalanceCockpitBuckets.value?.trim || []).length
            + (rebalanceCockpitBuckets.value?.add || []).length
            + (rebalanceCockpitBuckets.value?.pending || []).length,""",
    'CRO visible counts',
)
replace_once(
    'assets/js/src/00-bootstrap-and-cro.js',
    """        universe_policy: rebalanceMonitor.value.universePolicy || 'frontend_fallback',
        rule_threshold_pp: rebalanceMonitor.value.ruleThresholdPp,
        economic_dust_tickers_excluded: rebalanceMonitor.value.economicDustTickers || [],
        sheet_only_tickers_excluded: rebalanceMonitor.value.sheetOnlyTickersExcluded || [],
        backend_actionable_signal_count: rebalanceMonitor.value.backendSignalCount || 0,
        rebalance_alerts_with_direction: rebalanceMonitor.value.alerts.slice(0, 10)""",
    """        universe_policy: rebalanceMonitor.value.universePolicy || 'frontend_fallback',
        rule_threshold_pp: Number(tradeBufferBasePct.value || 3),
        backend_rule_threshold_pp: rebalanceMonitor.value.ruleThresholdPp,
        target_weight_source: rebalanceMonitor.value.targetWeightSource || 'unknown',
        target_vector_complete: Boolean(rebalanceMonitor.value.targetVectorComplete),
        target_asset_weight_sum_pct: rebalanceMonitor.value.targetAssetWeightSumPct,
        cash_target_weight_pct: rebalanceMonitor.value.cashTargetWeightPct,
        target_source_generated_at: rebalanceMonitor.value.targetSourceGeneratedAt || '',
        economic_dust_tickers_excluded: rebalanceMonitor.value.economicDustTickers || [],
        sheet_only_tickers_excluded: rebalanceMonitor.value.sheetOnlyTickersExcluded || [],
        backend_actionable_signal_count: rebalanceMonitor.value.backendSignalCount || 0,
        rebalance_alerts_with_direction: (rebalanceCockpitRows.value || [])
            .filter(row => row.bucket !== 'hold')
            .slice(0, 20)
            .map(row => ({
                ticker: row.ticker,
                direction: row.bucket === 'trim' ? 'TRIM' : 'ADD',
                execution_status: row.bucket === 'pending' ? 'BLOCKED_BY_CRO' : 'ACTIONABLE',
                current_weight_pct: row.currentWeightPct,
                target_weight_pct: row.targetWeightPct,
                signed_drift_pp: -Number(row.driftPct || 0),
                delta_to_target_pp: Number(row.driftPct || 0),
                visible_buffer_pp: Number(tradeBufferBasePct.value || 3)
            })),
        backend_rebalance_alerts_for_audit: rebalanceMonitor.value.alerts.slice(0, 20)""",
    'CRO visible action payload',
)
anchor = "- Reconcile action counts before writing: the number of actionable TRIM / ADD / BLOCKED items stated in prose must equal the items actually listed. Keep concentration-only, general-drift, and informational alerts separate from actionable trade counts."
extra = anchor + "\n- Rebalance action counts and listed actions in the report must use the same visible no-trade buffer (rule_threshold_pp) as the Rebalance Monitor cockpit. backend_rule_threshold_pp and backend_rebalance_alerts_for_audit are audit-only and must not replace the visible cockpit action count.\n- If target_vector_complete is true, the Rebalance Monitor target is a portfolio-complete delegated/blended allocation. Do not imply TRIM proceeds should remain as cash unless cash_target_weight_pct is positive; interpret simultaneous TRIM and ADD signals as internal reallocation toward the complete target vector."
replace_once('assets/js/src/00-bootstrap-and-cro.js', anchor, extra, 'CRO prompt rules')

# Daily pipeline rebuilds and syncs the complete vector after live portfolio refresh.
replace_once(
    '.github/workflows/daily_update.yml',
    """      - name: 🧭 更新 Phase 3 Market Compass
        env:
""",
    """      - name: 🎯 重建完整 delegated / blended target
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          SUPABASE_TABLE: portfolio_db
          PORTFOLIO_ROW_ID: '1'
        run: |
          python scripts/build_trading_constraints_snapshot.py
          python scripts/build_daily_quant_monte_carlo_reference.py
          python scripts/build_delegated_target_weight_draft_generator.py

      - name: 🔄 同步完整目標至 Rebalance Monitor
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          SUPABASE_TABLE: portfolio_db
          PORTFOLIO_ROW_ID: '1'
        run: python scripts/sync_rebalance_from_delegated_target.py

      - name: 🧭 更新 Phase 3 Market Compass
        env:
""",
    'daily complete-target sync',
)
