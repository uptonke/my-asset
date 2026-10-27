from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
JS = ROOT / "assets/js/src/app.bundle.source.js"
INDEX = ROOT / "index.html"


def replace_required(text, old, new, label, count=1):
    found = text.count(old)
    if found < count:
        raise SystemExit(f"{label}: expected >= {count}, found {found}")
    return text.replace(old, new, count)


main = MAIN.read_text(encoding="utf-8")
js = JS.read_text(encoding="utf-8")
index = INDEX.read_text(encoding="utf-8")

helper_anchor = "def choose_stage(scores):\n"
if "MACRO_SIGNAL_SPECS = {" not in main:
    helper = textwrap.dedent(r'''
    MACRO_SIGNAL_SPECS = {
        "move_index": {"label": "利率隱含波動率（MOVE）", "raw": "move_index", "z": "move_z", "domain": "rates", "domain_label": "利率", "unit": ""},
        "yield_curve": {"label": "殖利率曲線", "raw": "yield_curve", "domain": "rates", "domain_label": "利率", "unit": "pp"},
        "sys_corr": {"label": "跨資產系統相關性", "raw": "sys_corr", "domain": "correlation", "domain_label": "相關性", "unit": ""},
        "vix": {"label": "權益隱含波動率（VIX）", "raw": "vix", "z": "vix_z", "domain": "volatility", "domain_label": "波動率", "unit": ""},
        "vxn": {"label": "Nasdaq 隱含波動率（VXN）", "raw": "vxn", "z": "vxn_z", "domain": "volatility", "domain_label": "波動率", "unit": ""},
        "vvix": {"label": "波動率的波動率（VVIX）", "raw": "vvix", "z": "vvix_z", "domain": "volatility", "domain_label": "波動率", "unit": ""},
        "put_call_ratio": {"label": "Put/Call Ratio", "raw": "put_call_ratio", "z": "pcr_z", "domain": "volatility", "domain_label": "波動率", "unit": ""},
        "rsp_spy_mom": {"label": "市場廣度（RSP/SPY）", "raw": "rsp_spy_mom", "domain": "breadth", "domain_label": "市場廣度", "unit": "%"},
        "soxx_spy_mom": {"label": "半導體相對動能（SOXX/SPY）", "raw": "soxx_spy_mom", "domain": "breadth", "domain_label": "市場廣度", "unit": "%"},
        "iwm_spy_mom": {"label": "小型股相對動能（IWM/SPY）", "raw": "iwm_spy_mom", "domain": "breadth", "domain_label": "市場廣度", "unit": "%"},
        "kre_spy_mom": {"label": "區域銀行相對動能（KRE/SPY）", "raw": "kre_spy_mom", "domain": "breadth", "domain_label": "市場廣度", "unit": "%"},
        "xlu_xly_mom": {"label": "防禦/循環相對動能（XLU/XLY）", "raw": "xlu_xly_mom", "domain": "breadth", "domain_label": "市場廣度", "unit": "%"},
        "hy_spread": {"label": "高收益債信用利差", "raw": "hy_spread", "domain": "credit", "domain_label": "信用", "unit": "%"},
        "hyg_tlt_mom": {"label": "信用/長債相對動能（HYG/TLT）", "raw": "hyg_tlt_mom", "domain": "credit", "domain_label": "信用", "unit": "%"},
        "liquidity_spread": {"label": "流動性利差", "raw": "liquidity_spread", "domain": "liquidity", "domain_label": "流動性/美元", "unit": ""},
        "dxy": {"label": "美元指數（DXY）", "raw": "dxy", "domain": "liquidity", "domain_label": "流動性/美元", "unit": ""},
        "aud_jpy_mom": {"label": "風險貨幣動能（AUD/JPY）", "raw": "aud_jpy_mom", "domain": "liquidity", "domain_label": "流動性/美元", "unit": "%"},
        "oil_price": {"label": "原油價格", "raw": "oil_price", "domain": "growth", "domain_label": "成長/通膨", "unit": ""},
        "dbc_mom": {"label": "商品動能（DBC）", "raw": "dbc_mom", "domain": "growth", "domain_label": "成長/通膨", "unit": "%"},
        "copper_gold_ratio": {"label": "銅金比", "raw": "copper_gold_ratio", "domain": "growth", "domain_label": "成長/通膨", "unit": ""},
        "btc_1m_mom": {"label": "比特幣 1M 動能", "raw": "btc_1m_mom", "domain": "crypto", "domain_label": "加密資產", "unit": "%"},
    }

    MACRO_DOMAIN_ORDER = {"rates": 0, "correlation": 1, "volatility": 2, "breadth": 3, "credit": 4, "liquidity": 5, "growth": 6, "crypto": 7}

    def _signal_status(key, value, z_score, score):
        if key == "sys_corr" and value is not None:
            if value < 0.30:
                return "低相關・分散較強"
            if value > 0.85:
                return "高相關・集中風險"
            if value > 0.70:
                return "相關性偏高"
            return "相關性中性"
        if z_score is not None:
            if z_score >= 2:
                return "異常偏高"
            if z_score >= 1:
                return "偏高"
            if z_score <= -2:
                return "異常偏低"
            if z_score <= -1:
                return "偏低"
        if score >= 2:
            return "模型偏正向（強）"
        if score == 1:
            return "模型偏正向"
        if score == 0:
            return "模型中性"
        if score == -1:
            return "模型偏壓力"
        return "模型壓力高"

    def build_signal_audit(raw, scores):
        rows = []
        for key, spec in MACRO_SIGNAL_SPECS.items():
            value = _num(raw.get(spec["raw"]))
            if value is None:
                continue
            z_score = _num(raw.get(spec.get("z"))) if spec.get("z") else None
            score = float(scores.get(key, 0) or 0)
            priority = abs(score) + (min(abs(z_score), 3.0) if z_score is not None else 0.0)
            unit = spec.get("unit", "")
            rows.append({
                "key": key,
                "label": spec["label"],
                "domain": spec["domain"],
                "domain_label": spec["domain_label"],
                "value": round(value, 6),
                "value_display": f"{value:.2f}{unit}",
                "z_score": None if z_score is None else round(z_score, 3),
                "model_score": score,
                "priority": round(priority, 3),
                "status": _signal_status(key, value, z_score, score),
                "selected_top4": False,
                "selection_rank": None,
                "selection_reason": "",
            })

        domain_best = {}
        for row in sorted(rows, key=lambda r: (-r["priority"], -abs(r["model_score"]), r["label"])):
            domain_best.setdefault(row["domain"], row)

        representatives = sorted(
            domain_best.values(),
            key=lambda r: (-r["priority"], MACRO_DOMAIN_ORDER.get(r["domain"], 99), r["label"]),
        )
        selected = representatives[:4]
        selected_keys = [row["key"] for row in selected]
        selected_by_domain = {row["domain"]: row for row in selected}
        cutoff = selected[-1]["priority"] if selected else 0

        for rank, row in enumerate(selected, 1):
            row["selected_top4"] = True
            row["selection_rank"] = rank
            row["selection_reason"] = f"Top {rank}：{row['domain_label']}類別代表訊號，priority={row['priority']:.2f}"

        for row in rows:
            if row["selected_top4"]:
                continue
            peer = selected_by_domain.get(row["domain"])
            if peer:
                row["selection_reason"] = f"未選入：同類別由「{peer['label']}」代表，避免重複計票。"
            else:
                row["selection_reason"] = f"未選入：priority {row['priority']:.2f} 低於本輪 Top 4 門檻 {cutoff:.2f}。"

        rows = sorted(
            rows,
            key=lambda r: (0 if r["selected_top4"] else 1, r["selection_rank"] or 99, -r["priority"], r["label"]),
        )
        secondary_keys = [
            r["key"]
            for r in sorted((r for r in rows if not r["selected_top4"]), key=lambda r: (-r["priority"], r["label"]))[:6]
        ]
        return rows, selected_keys, secondary_keys

    ''')
    if helper_anchor not in main:
        raise SystemExit("signal helper anchor not found")
    main = main.replace(helper_anchor, helper + helper_anchor, 1)

old_return = '''    stage = choose_stage(scores)
    return {"raw": raw, "scores": scores, "stage_candidate": stage, "total_score": sum(scores.values()), "confidence_hint": 0.85}
'''
new_return = '''    stage = choose_stage(scores)
    signal_audit, top_signal_keys, secondary_signal_keys = build_signal_audit(raw, scores)
    return {"raw": raw, "scores": scores, "stage_candidate": stage, "total_score": sum(scores.values()), "confidence_hint": 0.85, "top_signal_keys": top_signal_keys, "secondary_signal_keys": secondary_signal_keys, "signal_audit": signal_audit}
'''
main = replace_required(main, old_return, new_return, "regime packet audit return")

main = replace_required(
    main,
    '''            Task: Transform deterministic macro signals into aggressive tactical trading metadata.
            Tone: High-Alpha Quant, Contrarian, Extreme Aggressive (Risk = Opportunity). Focus deeply on Z-Scores and `sys_corr`.
''',
    '''            Task: Transform deterministic macro signals into evidence-grounded portfolio diagnostic metadata.
            Tone: Institutional Quant, evidence-first, concise, non-sensational. Quantitative evidence outranks narrative.
''',
    "macro task tone",
)
main = replace_required(
    main,
    '''            2. SUMMARY: 1 sentence. MUST START WITH "[目前總經形勢: 翻譯後的STAGE]". Map stage to a max-alpha strategy.
            3. DETAILS.TITLE: Traditional Chinese metric name.
            4. DETAILS.DESC: Max 35 chars. Explicitly cite specific numeric values (Z-Scores).
            5. DETAILS.COLOR: "text-green-400", "text-red-400", "text-gray-400".
            6. DETAILS.ICON: Single emoji.
''',
    '''            2. SUMMARY: 1 sentence. MUST START WITH "[目前總經形勢: 翻譯後的STAGE]". Describe diagnosis and portfolio implications only; do not invent trades or mispricing.
            3. DETAILS: Return EXACTLY 4 items, one for each key in `top_signal_keys`, in the same order. Include `signal_key`.
            4. DETAILS.TITLE: Traditional Chinese metric name.
            5. DETAILS.DESC: Max 45 chars. Cite the supplied raw value and Z-score when available. Do not infer facts not present in INPUT_DATA.
            6. DETAILS.COLOR: "text-green-400", "text-red-400", "text-gray-400".
            7. DETAILS.ICON: Single emoji.
''',
    "macro transformation rules",
)
main = replace_required(
    main,
    '            - Use measured language. Avoid 崩潰、失效、強行榨取、血洗、暴力殺盤 unless the supplied quantitative evidence explicitly meets the rules above.\n',
    '            - Use measured language. Avoid 崩潰、失效、強行榨取、血洗、暴力殺盤 unless the supplied quantitative evidence explicitly meets the rules above.\n            - Diagnostic signals alone cannot justify overweight, pair trades, arbitrage, mispricing, or Alpha-seeking actions without explicit portfolio/ranking/valuation evidence.\n',
    "diagnostic action guardrail",
)
main = replace_required(
    main,
    '{{"summary": "<string>", "details": [{{"icon": "<emoji>", "color": "<string_class>", "title": "<string>", "desc": "<string>"}}]}}',
    '{{"summary": "<string>", "details": [{{"signal_key": "<one_of_top_signal_keys>", "icon": "<emoji>", "color": "<string_class>", "title": "<string>", "desc": "<string>"}}]}}',
    "macro output schema",
)

old_parse = '''                        macro_payload['ai_analysis'] = json.loads(match.group(0))
                        macro_payload['ai_analysis']['calculated_stage'] = regime_packet["stage_candidate"]
                        print(f"✅ AI 格式轉換成功！(使用模型: {model_name})")'''
new_parse = '''                        parsed_ai = json.loads(match.group(0))
                        audit_by_key = {row['key']: row for row in regime_packet['signal_audit']}
                        raw_details = parsed_ai.get('details') if isinstance(parsed_ai.get('details'), list) else []
                        detail_by_key = {str(d.get('signal_key')): d for d in raw_details if isinstance(d, dict) and d.get('signal_key')}
                        ordered_details = []
                        for signal_key in regime_packet['top_signal_keys']:
                            row = audit_by_key[signal_key]
                            detail = detail_by_key.get(signal_key) or {
                                'signal_key': signal_key,
                                'icon': '📊',
                                'color': 'text-green-400' if row['model_score'] > 0 else ('text-red-400' if row['model_score'] < 0 else 'text-gray-400'),
                                'title': row['label'],
                                'desc': f"{row['value_display']}；{row['status']}",
                            }
                            detail['signal_key'] = signal_key
                            ordered_details.append(detail)
                        parsed_ai['details'] = ordered_details
                        parsed_ai['signal_audit'] = regime_packet['signal_audit']
                        parsed_ai['secondary_signals'] = [audit_by_key[k] for k in regime_packet['secondary_signal_keys'] if k in audit_by_key]
                        parsed_ai['selection_method'] = 'deterministic_domain_dedup_priority_v1'
                        parsed_ai['calculated_stage'] = regime_packet['stage_candidate']
                        parsed_ai['model_name'] = model_name
                        macro_payload['ai_analysis'] = parsed_ai
                        print(f"✅ AI 格式轉換成功！(使用模型: {model_name})")'''
main = replace_required(main, old_parse, new_parse, "AI audit post-processing")

js = replace_required(
    js,
    "if (val === 0) return { summary: '尚無庫存資料，請先新增交易紀錄。', details: [] };",
    "if (val === 0) return { summary: '尚無庫存資料，請先新增交易紀錄。', details: [], secondarySignals: [], auditSignals: [] };",
    "AI zero-state arrays",
)
js = replace_required(
    js,
    '''            let finalSummary = ""; const finalDetails = [];
            if (cloudAiAnalysis.value && cloudAiAnalysis.value.summary) {''',
    '''            let finalSummary = ""; const finalDetails = [];
            const auditSignals = Array.isArray(cloudAiAnalysis.value?.signal_audit) ? cloudAiAnalysis.value.signal_audit : [];
            const secondarySignals = Array.isArray(cloudAiAnalysis.value?.secondary_signals) ? cloudAiAnalysis.value.secondary_signals : auditSignals.filter(row => !row?.selected_top4).slice(0, 6);
            if (cloudAiAnalysis.value && cloudAiAnalysis.value.summary) {''',
    "AI audit arrays",
)
js = replace_required(
    js,
    '''            return { summary: finalSummary, details: finalDetails };
        });''',
    '''            return { summary: finalSummary, details: finalDetails, secondarySignals, auditSignals };
        });''',
    "AI computed return",
)

ai_list_anchor = '''                    <div class="min-w-0">
                        <div class="font-bold tracking-wide mb-1" :class="insight.color">
                            {{ insight.title }}
                        </div>
                        <div class="text-gray-300 leading-relaxed">
                            {{ insight.desc }}
                        </div>
                    </div>
                </li>
            </ul>
        </div>'''

audit_markup = '''

        <div v-if="(aiInsights?.secondarySignals || []).length > 0" class="mt-4 rounded-2xl border border-white/10 bg-black/20 overflow-hidden">
            <div class="px-4 py-3 border-b border-white/10 bg-white/[0.03] flex items-center justify-between">
                <div class="text-sm font-bold text-white flex items-center gap-2"><i class="fas fa-list-check text-cyan-400"></i>次要訊號</div>
                <div class="text-[11px] text-gray-500">未列入 Top 4</div>
            </div>
            <div class="p-4 flex flex-wrap gap-2">
                <div v-for="signal in (aiInsights?.secondarySignals || [])" :key="'secondary-' + signal.key" class="rounded-xl border border-white/10 bg-white/[0.025] px-3 py-2 text-xs">
                    <div class="font-bold text-gray-200">{{ signal.label }}</div>
                    <div class="mt-1 text-gray-400"><span class="font-mono text-cyan-300">{{ signal.value_display }}</span><span v-if="signal.z_score !== null && signal.z_score !== undefined"> · Z {{ Number(signal.z_score).toFixed(2) }}</span> · {{ signal.status }}</div>
                </div>
            </div>
        </div>

        <details v-if="(aiInsights?.auditSignals || []).length > 0" class="mt-4 rounded-2xl border border-indigo-500/20 bg-indigo-950/10 overflow-hidden">
            <summary class="cursor-pointer px-4 py-3 flex items-center justify-between gap-3 text-sm font-bold text-indigo-200 hover:text-white">
                <span class="flex items-center gap-2"><i class="fas fa-magnifying-glass-chart"></i>查看全部量化依據</span>
                <span class="text-[11px] text-gray-500 font-normal">{{ (aiInsights?.auditSignals || []).length }} signals · deterministic audit</span>
            </summary>
            <div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-3 border-t border-white/10">
                <div v-for="signal in (aiInsights?.auditSignals || [])" :key="'audit-' + signal.key" class="rounded-xl border px-3 py-3" :class="signal.selected_top4 ? 'border-indigo-400/30 bg-indigo-500/10' : 'border-white/10 bg-white/[0.02]'">
                    <div class="flex items-start justify-between gap-2">
                        <div class="font-bold text-sm text-white">{{ signal.label }}</div>
                        <span v-if="signal.selected_top4" class="text-[10px] px-2 py-0.5 rounded-full border border-indigo-400/30 text-indigo-300">Top {{ signal.selection_rank }}</span>
                    </div>
                    <div class="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-gray-400">
                        <div>原始值 <span class="font-mono text-gray-200">{{ signal.value_display }}</span></div>
                        <div>Z-score <span class="font-mono text-gray-200">{{ signal.z_score === null || signal.z_score === undefined ? '—' : Number(signal.z_score).toFixed(2) }}</span></div>
                        <div>模型分數 <span class="font-mono text-gray-200">{{ signal.model_score }}</span></div>
                        <div>Priority <span class="font-mono text-gray-200">{{ Number(signal.priority).toFixed(2) }}</span></div>
                    </div>
                    <div class="mt-2 text-xs text-gray-300">{{ signal.status }}</div>
                    <div class="mt-1 text-[11px] leading-relaxed text-gray-500">{{ signal.selection_reason }}</div>
                </div>
            </div>
        </details>'''
if ai_list_anchor not in index:
    raise SystemExit("AI insight list anchor not found")
index = index.replace(ai_list_anchor, ai_list_anchor + audit_markup, 1)
index = replace_required(index, "assets/js/app.bundle.js?v=factor-alpha-hac-v1", "assets/js/app.bundle.js?v=ai-signal-audit-v1", "bundle cache bust")

MAIN.write_text("\n".join(line.rstrip() for line in main.splitlines()) + "\n", encoding="utf-8")
JS.write_text("\n".join(line.rstrip() for line in js.splitlines()) + "\n", encoding="utf-8")
INDEX.write_text("\n".join(line.rstrip() for line in index.splitlines()) + "\n", encoding="utf-8")
print("Applied AI signal audit patch")
