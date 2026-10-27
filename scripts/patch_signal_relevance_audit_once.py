from pathlib import Path
import re

MAIN = Path('main.py')
INDEX = Path('index.html')

main = MAIN.read_text(encoding='utf-8')
index = INDEX.read_text(encoding='utf-8')


def sub_once(pattern, repl, text, label, flags=0):
    out, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 replacement, got {count}')
    return out


# 1) Make status semantics explicit: risk-asset environment vs generic "positive".
main = sub_once(
    r'def _signal_status\(key, value, z_score, score\):\n.*?\n(?=def build_signal_audit)',
    '''def _signal_status(key, value, z_score, score):
    if key == "sys_corr" and value is not None:
        if value < 0.30:
            return "低相關・分散環境有利"
        if value > 0.85:
            return "高相關・集中風險高"
        if value > 0.70:
            return "相關性偏高・分散效益下降"
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
        return "風險資產環境偏正向（強）"
    if score == 1:
        return "風險資產環境偏正向"
    if score == 0:
        return "模型中性"
    if score == -1:
        return "風險資產環境承壓"
    return "風險資產壓力高"


def _clamp01(value):
    try:
        return max(0.0, min(float(value), 1.0))
    except Exception:
        return 0.0


def load_portfolio_relevance_context():
    """Build deterministic signal relevance from ACTIVE ledger holdings and TWD market values.

    This is only a ranking tie-break / small bonus. It never changes the raw macro signal,
    model score, Z-score, or regime classification.
    """
    empty = {
        "source": "unavailable",
        "asset_count": 0,
        "covered_asset_count": 0,
        "signal_relevance": {},
        "bucket_weights": {},
    }
    try:
        resp = supabase.table("portfolio_db").select("ledger_data,stock_meta").limit(1).execute()
        if not resp.data:
            return empty
        row = resp.data[0]
        ledger = row.get("ledger_data", []) or []
        raw_meta = row.get("stock_meta", {}) or {}

        meta = {}
        if isinstance(raw_meta, dict):
            for raw_ticker, raw_value in raw_meta.items():
                ticker = normalize_ticker_symbol(raw_ticker)
                if ticker and isinstance(raw_value, dict):
                    meta.setdefault(ticker, {}).update(raw_value)

        shares = {}
        for tx in ledger:
            if not isinstance(tx, dict):
                continue
            ticker = normalize_ticker_symbol(tx.get("ticker"))
            if not ticker:
                continue
            raw_shares = tx.get("shares")
            qty = _num(raw_shares, 0.0) or 0.0
            side = str(tx.get("type", "buy")).lower()
            shares[ticker] = shares.get(ticker, 0.0) + qty * (-1.0 if side in {"sell", "賣出"} else 1.0)

        active = [ticker for ticker, qty in shares.items() if qty > 0.0001]
        values = {}
        for ticker in active:
            mv = _num((meta.get(ticker) or {}).get("market_value_twd"))
            if mv is not None and mv > 0:
                values[ticker] = mv

        total = sum(values.values())
        if total <= 0:
            return {**empty, "asset_count": len(active), "source": "active_ledger_no_twd_market_values"}

        buckets = {
            "equity": 0.0, "tech": 0.0, "smallcap": 0.0, "banks": 0.0,
            "crypto": 0.0, "credit": 0.0, "rates": 0.0, "gold": 0.0,
            "commodity": 0.0, "usd": 0.0,
        }

        tech_tickers = {"QQQ", "QQQM", "SOXX", "SMH", "XLK", "VGT", "SRVR", "GRID", "2317", "2382", "00981A"}
        small_tickers = {"AVUV", "IWM", "VB", "VBR", "SCHA"}
        bank_tickers = {"KRE", "XLF", "KBE", "KRE"}
        credit_tickers = {"HYG", "JNK", "LQD", "VCIT", "USHY"}
        rates_tickers = {"SHY", "BIL", "SGOV", "TLT", "IEF", "BOXX"}
        gold_tickers = {"GLDM", "GLD", "IAU"}
        commodity_tickers = {"DBC", "PICK", "COPX", "XLE", "USO", "IFRA"}

        for ticker, mv in values.items():
            w = mv / total
            m = meta.get(ticker) or {}
            text = " ".join([
                str(m.get("category", "")), str(m.get("theme_tag", "")),
                str(m.get("name", "")), str(m.get("asset_class", "")),
            ]).lower()
            t = ticker.upper()

            is_crypto = t.endswith("-USD") or t in {"BTC", "ETH", "BTC-USD", "ETH-USD"} or "加密" in text or "crypto" in text
            is_gold = t in gold_tickers or "黃金" in text or "gold" in text
            is_rates = t in rates_tickers or "債" in text or "bond" in text or "cash" in text or "現金" in text
            is_credit = t in credit_tickers or "high yield" in text or "信用債" in text or "高收益" in text
            is_tech = t in tech_tickers or any(k in text for k in ["科技", "半導體", "technology", "semiconductor", "ai ", "人工智慧"])
            is_small = t in small_tickers or "small cap" in text or "小型" in text
            is_bank = t in bank_tickers or any(k in text for k in ["銀行", "bank", "金融"])
            is_commodity = t in commodity_tickers or any(k in text for k in ["商品", "commodity", "礦業", "金屬", "能源", "基礎建設"])
            is_tw = bool(re.fullmatch(r"\d{4,6}[A-Z]?", t)) or "台股" in text or "taiwan" in text
            is_equity = not (is_crypto or is_gold or is_rates or is_credit)

            if is_equity: buckets["equity"] += w
            if is_tech: buckets["tech"] += w
            if is_small: buckets["smallcap"] += w
            if is_bank: buckets["banks"] += w
            if is_crypto: buckets["crypto"] += w
            if is_credit: buckets["credit"] += w
            if is_rates: buckets["rates"] += w
            if is_gold: buckets["gold"] += w
            if is_commodity: buckets["commodity"] += w
            if not is_tw: buckets["usd"] += w

        e = buckets["equity"]
        tech = buckets["tech"]
        small = buckets["smallcap"]
        banks = buckets["banks"]
        crypto = buckets["crypto"]
        credit = buckets["credit"]
        rates = buckets["rates"]
        gold = buckets["gold"]
        commodity = buckets["commodity"]
        usd = buckets["usd"]
        risk_assets = _clamp01(e + crypto)

        relevance = {
            "move_index": _clamp01(0.20 + 0.45 * e + 0.35 * tech + 0.45 * rates + 0.20 * gold),
            "yield_curve": _clamp01(0.15 + 0.35 * e + 0.30 * tech + 0.55 * rates + 0.15 * gold),
            "sys_corr": 1.0,
            "vix": _clamp01(e + 0.35 * crypto),
            "vxn": _clamp01(tech + 0.20 * e),
            "vvix": _clamp01(0.75 * e + 0.30 * crypto),
            "put_call_ratio": _clamp01(0.80 * e + 0.20 * crypto),
            "rsp_spy_mom": _clamp01(e),
            "soxx_spy_mom": _clamp01(tech + 0.20 * e),
            "iwm_spy_mom": _clamp01(small + 0.15 * e),
            "kre_spy_mom": _clamp01(banks + 0.10 * e),
            "xlu_xly_mom": _clamp01(0.75 * e),
            "hy_spread": _clamp01(credit + 0.50 * risk_assets),
            "hyg_tlt_mom": _clamp01(credit + 0.55 * risk_assets),
            "liquidity_spread": _clamp01(0.60 * usd + 0.45 * risk_assets),
            "dxy": _clamp01(usd + 0.20 * crypto),
            "aud_jpy_mom": _clamp01(0.45 * risk_assets + 0.35 * usd),
            "oil_price": _clamp01(commodity + 0.20 * e),
            "dbc_mom": _clamp01(commodity + 0.15 * e),
            "copper_gold_ratio": _clamp01(commodity + 0.35 * gold + 0.10 * e),
            "btc_1m_mom": _clamp01(crypto),
        }

        bucket_labels = {
            "equity": "股票", "tech": "科技/半導體", "smallcap": "小型股", "banks": "金融",
            "crypto": "加密資產", "credit": "信用債", "rates": "利率/短債", "gold": "黃金",
            "commodity": "商品/實物資產", "usd": "非台幣資產",
        }
        ranked_buckets = sorted(buckets.items(), key=lambda kv: kv[1], reverse=True)
        top_bucket_text = "、".join(
            f"{bucket_labels[k]} {v*100:.1f}%" for k, v in ranked_buckets[:3] if v > 0.01
        ) or "持倉曝險資料有限"

        signal_relevance = {
            key: {
                "score": round(_clamp01(score), 4),
                "reason": f"依目前持倉曝險估計；主要桶：{top_bucket_text}",
            }
            for key, score in relevance.items()
        }
        return {
            "source": "active_ledger_plus_stock_meta_market_value_twd",
            "asset_count": len(active),
            "covered_asset_count": len(values),
            "signal_relevance": signal_relevance,
            "bucket_weights": {k: round(v, 4) for k, v in buckets.items()},
        }
    except Exception as exc:
        print(f"⚠️ Portfolio relevance snapshot unavailable: {exc}", flush=True)
        return empty


def build_signal_audit''',
    main,
    'status + relevance helper insertion',
    flags=re.S,
)

# 2) Upgrade signal ranking: signal strength remains visible; portfolio relevance is a capped small bonus.
main = sub_once(
    r'def build_signal_audit\(raw, scores\):\n.*?\n    return rows, selected_keys, secondary_keys\n',
    '''def build_signal_audit(raw, scores, portfolio_context=None):
    portfolio_context = portfolio_context or {}
    relevance_map = portfolio_context.get("signal_relevance", {}) if isinstance(portfolio_context, dict) else {}
    rows = []
    for key, spec in MACRO_SIGNAL_SPECS.items():
        value = _num(raw.get(spec["raw"]))
        if value is None:
            continue
        z_score = _num(raw.get(spec.get("z"))) if spec.get("z") else None
        score = float(scores.get(key, 0) or 0)
        signal_strength = abs(score) + (min(abs(z_score), 3.0) if z_score is not None else 0.0)
        relevance_item = relevance_map.get(key, {}) if isinstance(relevance_map, dict) else {}
        if isinstance(relevance_item, dict):
            portfolio_relevance = _clamp01(relevance_item.get("score", 0.0))
            relevance_reason = str(relevance_item.get("reason", ""))
        else:
            portfolio_relevance = _clamp01(relevance_item)
            relevance_reason = ""
        relevance_bonus = 0.35 * portfolio_relevance
        selection_score = signal_strength + relevance_bonus
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
            "priority": round(signal_strength, 3),
            "portfolio_relevance": round(portfolio_relevance, 3),
            "portfolio_relevance_bonus": round(relevance_bonus, 3),
            "portfolio_relevance_reason": relevance_reason,
            "selection_score": round(selection_score, 3),
            "status": _signal_status(key, value, z_score, score),
            "selected_top4": False,
            "selection_rank": None,
            "selection_reason": "",
        })

    # First choose one representative per domain, then choose Top 4 domains.
    # Portfolio relevance is deliberately capped at +0.35 so it is a tie-break / small nudge,
    # never a substitute for signal severity or Z-score abnormality.
    domain_best = {}
    for row in sorted(
        rows,
        key=lambda r: (-r["selection_score"], -r["priority"], -abs(r["model_score"]), r["label"]),
    ):
        domain_best.setdefault(row["domain"], row)

    representatives = sorted(
        domain_best.values(),
        key=lambda r: (-r["selection_score"], -r["priority"], MACRO_DOMAIN_ORDER.get(r["domain"], 99), r["label"]),
    )
    selected = representatives[:4]
    selected_keys = [row["key"] for row in selected]
    selected_by_domain = {row["domain"]: row for row in selected}
    cutoff = selected[-1]["selection_score"] if selected else 0

    for rank, row in enumerate(selected, 1):
        row["selected_top4"] = True
        row["selection_rank"] = rank
        row["selection_reason"] = (
            f"Top {rank}：{row['domain_label']}代表；訊號強度 {row['priority']:.2f} + "
            f"持倉關聯加分 {row['portfolio_relevance_bonus']:.2f} = 選擇分數 {row['selection_score']:.2f}。"
        )

    for row in rows:
        if row["selected_top4"]:
            continue
        peer = selected_by_domain.get(row["domain"])
        if peer:
            row["selection_reason"] = (
                f"未選入：同類別由「{peer['label']}」以選擇分數 {peer['selection_score']:.2f} 代表，避免重複計票。"
            )
        else:
            row["selection_reason"] = (
                f"未選入：選擇分數 {row['selection_score']:.2f}；本輪 Top 4 排序基準 {cutoff:.2f}，未進入前四。"
            )

    rows = sorted(
        rows,
        key=lambda r: (0 if r["selected_top4"] else 1, r["selection_rank"] or 99, -r["selection_score"], -r["priority"], r["label"]),
    )
    secondary_keys = [
        r["key"]
        for r in sorted(
            (r for r in rows if not r["selected_top4"]),
            key=lambda r: (-r["selection_score"], -r["priority"], r["label"]),
        )[:6]
    ]
    return rows, selected_keys, secondary_keys
''',
    main,
    'signal ranking upgrade',
    flags=re.S,
)

# 3) Thread relevance context through regime packet and Gemini payload.
main = main.replace('def build_regime_packet(macro_payload):', 'def build_regime_packet(macro_payload, portfolio_context=None):', 1)
main = main.replace(
    'signal_audit, top_signal_keys, secondary_signal_keys = build_signal_audit(raw, scores)',
    'signal_audit, top_signal_keys, secondary_signal_keys = build_signal_audit(raw, scores, portfolio_context=portfolio_context)',
    1,
)
old_return = 'return {"raw": raw, "scores": scores, "stage_candidate": stage, "total_score": sum(scores.values()), "confidence_hint": 0.85, "top_signal_keys": top_signal_keys, "secondary_signal_keys": secondary_signal_keys, "signal_audit": signal_audit}'
new_return = 'return {"raw": raw, "scores": scores, "stage_candidate": stage, "total_score": sum(scores.values()), "confidence_hint": 0.85, "top_signal_keys": top_signal_keys, "secondary_signal_keys": secondary_signal_keys, "signal_audit": signal_audit, "portfolio_relevance": portfolio_context or {}}'
if old_return not in main:
    raise SystemExit('regime packet return anchor not found')
main = main.replace(old_return, new_return, 1)
main = main.replace(
    'regime_packet = build_regime_packet(macro_payload)',
    'portfolio_relevance_context = load_portfolio_relevance_context()\n    regime_packet = build_regime_packet(macro_payload, portfolio_context=portfolio_relevance_context)',
    1,
)
main = main.replace(
    "parsed_ai['selection_method'] = 'deterministic_domain_dedup_priority_v1'",
    "parsed_ai['selection_method'] = 'deterministic_domain_dedup_signal_strength_plus_portfolio_relevance_v2'",
    1,
)

# 4) Compact audit UI: every signal is a one-line disclosure by default.
old_ui_pattern = re.compile(
    r'''            <div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-3 border-t border-white/10">\n                <div v-for="signal in \(aiInsights\?\.auditSignals \|\| \[\]\)".*?\n                </div>\n            </div>''',
    re.S,
)
new_ui = '''            <div class="p-3 space-y-2 border-t border-white/10">
                <details v-for="signal in (aiInsights?.auditSignals || [])"
                         :key="'audit-' + signal.key"
                         class="group rounded-xl border overflow-hidden"
                         :class="signal.selected_top4 ? 'border-indigo-400/30 bg-indigo-500/10' : 'border-white/10 bg-white/[0.02]'">
                    <summary class="cursor-pointer list-none px-3 py-3 flex items-center justify-between gap-3">
                        <div class="min-w-0">
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="font-bold text-sm text-white">{{ signal.label }}</span>
                                <span v-if="signal.selected_top4" class="text-[10px] px-2 py-0.5 rounded-full border border-indigo-400/30 text-indigo-300">Top {{ signal.selection_rank }}</span>
                            </div>
                            <div class="mt-1 text-[11px] text-gray-400 truncate">{{ signal.status }}</div>
                        </div>
                        <div class="shrink-0 text-right">
                            <div class="font-mono text-xs text-indigo-200">Sel {{ Number(signal.selection_score ?? signal.priority ?? 0).toFixed(2) }}</div>
                            <div class="mt-0.5 text-[10px] text-gray-500">展開</div>
                        </div>
                    </summary>
                    <div class="px-3 pb-3 pt-1 border-t border-white/8">
                        <div class="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-gray-400 mt-2">
                            <div>原始值 <span class="font-mono text-gray-200">{{ signal.value_display }}</span></div>
                            <div>Z-score <span class="font-mono text-gray-200">{{ signal.z_score === null || signal.z_score === undefined ? '—' : Number(signal.z_score).toFixed(2) }}</span></div>
                            <div>模型分數 <span class="font-mono text-gray-200">{{ signal.model_score }}</span></div>
                            <div>訊號強度 <span class="font-mono text-gray-200">{{ Number(signal.priority ?? 0).toFixed(2) }}</span></div>
                            <div>持倉關聯 <span class="font-mono text-cyan-300">{{ Math.round(Number(signal.portfolio_relevance ?? 0) * 100) }}%</span></div>
                            <div>選擇分數 <span class="font-mono text-indigo-200">{{ Number(signal.selection_score ?? signal.priority ?? 0).toFixed(2) }}</span></div>
                        </div>
                        <div v-if="signal.portfolio_relevance_reason" class="mt-2 text-[11px] leading-relaxed text-cyan-200/70">{{ signal.portfolio_relevance_reason }}</div>
                        <div class="mt-2 text-[11px] leading-relaxed text-gray-500">{{ signal.selection_reason }}</div>
                    </div>
                </details>
            </div>'''
index, ui_count = old_ui_pattern.subn(new_ui, index, count=1)
if ui_count != 1:
    raise SystemExit(f'audit UI replacement failed: {ui_count}')

index = index.replace('signals · deterministic audit', 'signals · 點選查看細節', 1)

# Normalize trailing whitespace only in touched files.
main = '\n'.join(line.rstrip() for line in main.splitlines()) + '\n'
index = '\n'.join(line.rstrip() for line in index.splitlines()) + '\n'

MAIN.write_text(main, encoding='utf-8')
INDEX.write_text(index, encoding='utf-8')
print('Applied portfolio relevance ranking + compact audit UI patch')
