from pathlib import Path
import re

MAIN = Path('main.py')
INDEX = Path('index.html')

main = MAIN.read_text(encoding='utf-8')
index = INDEX.read_text(encoding='utf-8')


def sub_once(pattern, repl, text, label, flags=0):
    compiled = re.compile(pattern, flags)
    out, count = compiled.subn(lambda _m: repl, text, count=1)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 replacement, got {count}')
    return out


replacement = '''def _portfolio_relevance_from_row(row):
    """Build portfolio relevance from the best current-weight source available.

    Source order:
    1) synthetic portfolio risk coverage current_weight_pct (authoritative current weights)
    2) per-ticker stock_meta.market_value_twd
    3) active ledger shares * stock_meta last_price * settings.exchangeRate fallback

    Unavailable is represented explicitly; it must never be silently coerced to 0% relevance.
    """
    empty = {
        "available": False,
        "source": "unavailable",
        "asset_count": 0,
        "covered_asset_count": 0,
        "signal_relevance": {},
        "bucket_weights": {},
    }
    if not isinstance(row, dict):
        return empty

    ledger = row.get("ledger_data", []) or []
    raw_meta = row.get("stock_meta", {}) or {}
    settings = row.get("settings", {}) if isinstance(row.get("settings"), dict) else {}
    if not isinstance(raw_meta, dict):
        raw_meta = {}

    meta = {}
    for raw_ticker, raw_value in raw_meta.items():
        if str(raw_ticker).startswith("__") or not isinstance(raw_value, dict):
            continue
        ticker = normalize_ticker_symbol(raw_ticker)
        if ticker:
            meta.setdefault(ticker, {}).update(raw_value)

    shares = {}
    holding_category = {}
    for tx in ledger:
        if not isinstance(tx, dict):
            continue
        ticker = normalize_ticker_symbol(tx.get("ticker"))
        if not ticker:
            continue
        qty = _num(tx.get("shares"), 0.0) or 0.0
        side = str(tx.get("type", "buy")).strip().lower()
        if side in {"sell", "賣出"}:
            qty = -qty
        elif side not in {"buy", "買入", ""}:
            continue
        shares[ticker] = shares.get(ticker, 0.0) + qty
        category = str(tx.get("category") or "").strip()
        if category:
            holding_category[ticker] = category

    active = {ticker: qty for ticker, qty in shares.items() if qty > 0.0001}
    if not active:
        return {**empty, "source": "no_active_holdings"}

    # 1) Authoritative risk-engine current weights.
    weights = {}
    risk_meta = raw_meta.get("__synthetic_portfolio_risk__", {})
    coverage = risk_meta.get("coverage", {}) if isinstance(risk_meta, dict) else {}
    by_asset = coverage.get("by_asset", []) if isinstance(coverage, dict) else []
    if isinstance(by_asset, list):
        for item in by_asset:
            if not isinstance(item, dict):
                continue
            ticker = normalize_ticker_symbol(item.get("ticker"))
            if not ticker or ticker not in active:
                continue
            weight_pct = _num(item.get("current_weight_pct"))
            if weight_pct is not None and weight_pct > 0:
                weights[ticker] = weight_pct / 100.0
            if ticker not in meta:
                meta[ticker] = {}
            for key in ("category", "name", "asset_class", "currency"):
                if item.get(key) not in (None, "") and not meta[ticker].get(key):
                    meta[ticker][key] = item.get(key)

    weight_source = None
    if weights:
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {ticker: value / total_weight for ticker, value in weights.items() if value > 0}
            weight_source = "synthetic_risk_coverage_current_weight_pct"

    # 2) Per-ticker current market value.
    if not weights:
        values = {}
        for ticker in active:
            mv = _num((meta.get(ticker) or {}).get("market_value_twd"))
            if mv is not None and mv > 0:
                values[ticker] = mv
        total_value = sum(values.values())
        if total_value > 0:
            weights = {ticker: value / total_value for ticker, value in values.items()}
            weight_source = "stock_meta_market_value_twd"

    # 3) Last-resort deterministic valuation from ledger * last_price * FX.
    if not weights:
        fx = _num(settings.get("exchangeRate"), 31.5) or 31.5
        values = {}
        for ticker, qty in active.items():
            m = meta.get(ticker) or {}
            price = _num(m.get("last_price"))
            if price is None or price <= 0:
                continue
            category = str(m.get("category") or holding_category.get(ticker) or "")
            currency = str(m.get("currency") or "").upper().strip()
            t = ticker.upper()
            is_twd = currency == "TWD" or bool(re.fullmatch(r"[0-9]{4,6}[A-Z]?", t)) or "台股" in category or "台灣" in category
            multiplier = 1.0 if is_twd else fx
            values[ticker] = qty * price * multiplier
        total_value = sum(v for v in values.values() if v > 0)
        if total_value > 0:
            weights = {ticker: value / total_value for ticker, value in values.items() if value > 0}
            weight_source = "ledger_last_price_fx_fallback"

    if not weights:
        return {
            **empty,
            "asset_count": len(active),
            "source": "unavailable_no_current_weights",
        }

    buckets = {
        "equity": 0.0, "tech": 0.0, "smallcap": 0.0, "banks": 0.0,
        "crypto": 0.0, "credit": 0.0, "rates": 0.0, "gold": 0.0,
        "commodity": 0.0, "usd": 0.0,
    }

    tech_tickers = {"QQQ", "QQQM", "SOXX", "SMH", "XLK", "VGT", "SRVR", "GRID", "2317", "2382", "00981A"}
    small_tickers = {"AVUV", "IWM", "VB", "VBR", "SCHA"}
    bank_tickers = {"KRE", "XLF", "KBE"}
    credit_tickers = {"HYG", "JNK", "LQD", "VCIT", "USHY"}
    rates_tickers = {"SHY", "BIL", "SGOV", "TLT", "IEF", "BOXX"}
    gold_tickers = {"GLDM", "GLD", "IAU"}
    commodity_tickers = {"DBC", "PICK", "COPX", "XLE", "USO", "IFRA"}

    for ticker, w in weights.items():
        m = meta.get(ticker) or {}
        category = str(m.get("category") or holding_category.get(ticker) or "")
        text = " ".join([
            category,
            str(m.get("theme_tag", "")), str(m.get("name", "")),
            str(m.get("asset_class", "")),
        ]).lower()
        t = ticker.upper()
        currency = str(m.get("currency") or "").upper().strip()

        is_crypto = t.endswith("-USD") or t in {"BTC", "ETH", "BTC-USD", "ETH-USD"} or "加密" in text or "crypto" in text
        is_gold = t in gold_tickers or "黃金" in text or "gold" in text
        is_rates = t in rates_tickers or "短債" in text or "cash" in text or "現金" in text or "treasury" in text
        is_credit = t in credit_tickers or "high yield" in text or "信用債" in text or "高收益" in text
        is_tech = t in tech_tickers or any(k in text for k in ["科技", "半導體", "technology", "semiconductor", "人工智慧"])
        is_small = t in small_tickers or "small cap" in text or "小型" in text
        is_bank = t in bank_tickers or any(k in text for k in ["銀行", "bank", "金融"])
        is_commodity = t in commodity_tickers or any(k in text for k in ["商品", "commodity", "礦業", "金屬", "能源", "基礎建設"])
        is_twd = currency == "TWD" or bool(re.fullmatch(r"[0-9]{4,6}[A-Z]?", t)) or "台股" in text or "台灣" in text
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
        if not is_twd: buckets["usd"] += w

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
            "reason": f"來源={weight_source}；主要持倉桶：{top_bucket_text}",
        }
        for key, score in relevance.items()
    }
    return {
        "available": True,
        "source": weight_source,
        "asset_count": len(active),
        "covered_asset_count": len(weights),
        "signal_relevance": signal_relevance,
        "bucket_weights": {k: round(v, 4) for k, v in buckets.items()},
    }


def load_portfolio_relevance_context():
    try:
        resp = supabase.table("portfolio_db").select("ledger_data,stock_meta,settings").limit(1).execute()
        if not resp.data:
            return _portfolio_relevance_from_row({})
        return _portfolio_relevance_from_row(resp.data[0])
    except Exception as exc:
        print(f"⚠️ Portfolio relevance snapshot unavailable: {exc}", flush=True)
        return {
            "available": False,
            "source": "supabase_read_failed",
            "asset_count": 0,
            "covered_asset_count": 0,
            "signal_relevance": {},
            "bucket_weights": {},
        }


'''

main = sub_once(
    r'def load_portfolio_relevance_context\(\):\n.*?\n\n(?=def build_signal_audit)',
    replacement,
    main,
    'portfolio relevance loader',
    flags=re.S,
)

old = '''        relevance_item = relevance_map.get(key, {}) if isinstance(relevance_map, dict) else {}
        if isinstance(relevance_item, dict):
            portfolio_relevance = _clamp01(relevance_item.get("score", 0.0))
            relevance_reason = str(relevance_item.get("reason", ""))
        else:
            portfolio_relevance = _clamp01(relevance_item)
            relevance_reason = ""
        relevance_bonus = 0.35 * portfolio_relevance
        selection_score = signal_strength + relevance_bonus
'''
new = '''        relevance_item = relevance_map.get(key) if isinstance(relevance_map, dict) else None
        portfolio_relevance = None
        relevance_reason = ""
        if isinstance(relevance_item, dict):
            raw_relevance = _num(relevance_item.get("score"))
            if raw_relevance is not None:
                portfolio_relevance = _clamp01(raw_relevance)
            relevance_reason = str(relevance_item.get("reason", ""))
        elif relevance_item is not None:
            raw_relevance = _num(relevance_item)
            if raw_relevance is not None:
                portfolio_relevance = _clamp01(raw_relevance)
        relevance_bonus = None if portfolio_relevance is None else 0.35 * portfolio_relevance
        selection_score = signal_strength + (relevance_bonus or 0.0)
        if portfolio_relevance is None and not relevance_reason:
            relevance_reason = "持倉關聯資料不足，本輪不加分。"
'''
if old not in main:
    raise SystemExit('build_signal_audit relevance block anchor missing')
main = main.replace(old, new, 1)

old = '''            "portfolio_relevance": round(portfolio_relevance, 3),
            "portfolio_relevance_bonus": round(relevance_bonus, 3),
'''
new = '''            "portfolio_relevance": None if portfolio_relevance is None else round(portfolio_relevance, 3),
            "portfolio_relevance_bonus": None if relevance_bonus is None else round(relevance_bonus, 3),
'''
if old not in main:
    raise SystemExit('audit row relevance fields anchor missing')
main = main.replace(old, new, 1)

main = sub_once(
    r'    for rank, row in enumerate\(selected, 1\):\n.*?\n\n(?=    for row in rows:)',
    '''    for rank, row in enumerate(selected, 1):
        row["selected_top4"] = True
        row["selection_rank"] = rank
        bonus = row.get("portfolio_relevance_bonus")
        bonus_text = f"{bonus:.2f}" if bonus is not None else "—（資料不足）"
        row["selection_reason"] = (
            f"Top {rank}：{row['domain_label']}代表；訊號強度 {row['priority']:.2f} + "
            f"持倉關聯加分 {bonus_text} = 選擇分數 {row['selection_score']:.2f}。"
        )

''',
    main,
    'top4 relevance reason',
    flags=re.S,
)

main = main.replace(
    'deterministic_domain_dedup_signal_strength_plus_portfolio_relevance_v2',
    'deterministic_domain_dedup_signal_strength_plus_portfolio_relevance_v3_resilient_weights',
)

old_ui = '''<div>持倉關聯 <span class="font-mono text-cyan-300">{{ Math.round(Number(signal.portfolio_relevance ?? 0) * 100) }}%</span></div>'''
new_ui = '''<div>持倉關聯 <span class="font-mono text-cyan-300">{{ signal.portfolio_relevance === null || signal.portfolio_relevance === undefined ? '—' : Math.round(Number(signal.portfolio_relevance) * 100) + '%' }}</span></div>'''
if old_ui not in index:
    raise SystemExit('portfolio relevance UI anchor missing')
index = index.replace(old_ui, new_ui, 1)

MAIN.write_text(main, encoding='utf-8')
INDEX.write_text(index, encoding='utf-8')
print('Applied resilient portfolio relevance source patch')
