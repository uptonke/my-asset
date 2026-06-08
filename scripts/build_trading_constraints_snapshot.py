#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "alpha"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST_JSON = OUT_DIR / "trading_constraints_snapshot_latest.json"
SUMMARY_MD = OUT_DIR / "trading_constraints_snapshot_summary.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def read_json(rel: str, default: Any = None) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default

def finite_float(v: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if v is None or v == "": return default
        x = float(v)
        return x if math.isfinite(x) else default
    except Exception:
        return default

def latest_backup_row() -> Dict[str, Any]:
    paths = sorted((ROOT / "backups").glob("portfolio_backup_*.json"))
    if not paths:
        return {}
    try:
        data = json.loads(paths[-1].read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
    except Exception:
        return {}
    return {}

def fetch_supabase_row() -> Tuple[Dict[str, Any], str]:
    # Prefer current live Supabase portfolio row when secrets are available.
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    table = os.getenv("SUPABASE_TABLE", "portfolio_db")
    row_id = os.getenv("PORTFOLIO_ROW_ID", "1")
    if not url or not key:
        return {}, "supabase_env_missing"
    try:
        from supabase import create_client  # type: ignore
        client = create_client(url, key)
        resp = client.table(table).select("*").eq("id", int(row_id)).single().execute()
        if resp.data:
            return resp.data, "supabase_live"
    except Exception as exc:
        return {}, f"supabase_error:{exc}"
    return {}, "supabase_empty"

def active_holdings_from_ledger(ledger: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for tx in ledger or []:
        ticker = str(tx.get("ticker") or "").strip().upper()
        if not ticker:
            continue
        typ = str(tx.get("type") or "").strip().lower()
        if typ not in {"buy", "sell"}:
            continue
        shares = finite_float(tx.get("shares"), 0.0) or 0.0
        if shares == 0:
            continue
        if ticker not in out:
            out[ticker] = {"ticker": ticker, "shares": 0.0, "category": str(tx.get("category") or ""), "last_tx_date": str(tx.get("date") or "")}
        out[ticker]["shares"] += shares if typ == "buy" else -shares
        out[ticker]["category"] = str(tx.get("category") or out[ticker].get("category") or "")
        out[ticker]["last_tx_date"] = str(tx.get("date") or out[ticker].get("last_tx_date") or "")
    return {k:v for k,v in out.items() if (v.get("shares") or 0) > 1e-9}

def get_map() -> Dict[str, Any]:
    data = read_json("data/quant_ticker_map.json", {}) or {}
    return {str(k).upper(): v for k,v in data.items()} if isinstance(data, dict) else {}

def asset_kind(ticker: str, category: str) -> str:
    t = ticker.upper()
    c = str(category or "")
    if "加密" in c or t in {"BTC-USD", "ETH-USD", "SOL-USD"} or t.endswith("-USD") and t.split("-")[0] in {"BTC", "ETH", "SOL"}:
        return "crypto"
    if "台" in c or t.replace(".TW", "").isdigit() or t.endswith(".TW") or t.endswith(".TWO"):
        return "taiwan"
    if t in {"CASH", "TWD", "NTD", "USD"}:
        return "cash"
    return "us"

def yahoo_symbol(ticker: str, category: str, ticker_map: Dict[str, Any]) -> str:
    mapped = ticker_map.get(ticker.upper(), {}) if isinstance(ticker_map, dict) else {}
    if isinstance(mapped, dict) and mapped.get("yf_symbol"):
        return str(mapped["yf_symbol"])
    kind = asset_kind(ticker, category)
    if kind == "taiwan":
        base = ticker.upper().replace(".TW", "").replace(".TWO", "")
        return f"{base}.TW"
    return ticker.upper()

def fetch_yahoo_latest(symbol: str, timeout: int = 4) -> Dict[str, Any]:
    if os.getenv("SKIP_REAL_WORLD_FETCH_FOR_LOCAL_TEST") == "1":
        raise RuntimeError("real_world_fetch_skipped_for_local_test")
    enc = urllib.parse.quote(symbol, safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{enc}?range=5d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    result = (((data or {}).get("chart") or {}).get("result") or [None])[0]
    if not result:
        raise ValueError("empty_yahoo_result")
    meta = result.get("meta") or {}
    close = ((result.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    timestamps = result.get("timestamp") or []
    price = None
    ts = None
    for i in range(len(close)-1, -1, -1):
        val = close[i]
        if val is not None:
            price = float(val)
            ts = timestamps[i] if i < len(timestamps) else None
            break
    if price is None:
        mp = meta.get("regularMarketPrice")
        if mp is None:
            raise ValueError("no_price")
        price = float(mp)
        ts = meta.get("regularMarketTime")
    return {
        "price": price,
        "currency": meta.get("currency") or "USD",
        "provider": "yahoo_chart_api",
        "provider_url": url,
        "market_time_unix": ts,
        "regular_market_price": meta.get("regularMarketPrice"),
    }

def trade_rules(kind: str) -> Dict[str, Any]:
    if kind == "taiwan":
        return {"market": "TW", "min_trade_unit": 1, "unit_name": "share", "odd_lot_or_fractional_allowed": True, "fractional_shares_allowed": False, "rule_note": "台股允許零股；系統以 1 股為最小檢查單位。"}
    if kind == "crypto":
        return {"market": "CRYPTO", "min_trade_unit": 1, "unit_name": "coin", "odd_lot_or_fractional_allowed": False, "fractional_shares_allowed": False, "rule_note": "依使用者約束，不允許加密小數交易；少於 1 顆不列為可交易單位。"}
    if kind == "cash":
        return {"market": "CASH", "min_trade_unit": 1, "unit_name": "currency_unit", "odd_lot_or_fractional_allowed": True, "fractional_shares_allowed": True, "rule_note": "現金餘額作為買入預算約束，不是證券交易單位。"}
    return {"market": "US", "min_trade_unit": 1, "unit_name": "share", "odd_lot_or_fractional_allowed": False, "fractional_shares_allowed": False, "rule_note": "美股不接受 fractional shares；系統以 1 股為最小檢查單位。"}

def get_cash_balance(row: Dict[str, Any], manual_input: Dict[str, Any]) -> Tuple[Optional[float], str]:
    override = manual_input.get("cash_balance_twd_override")
    x = finite_float(override, None)
    if x is not None:
        return x, "manual_approval_override"
    cfg = read_json("config/manual_approval_override.json", {}) or {}
    x = finite_float(cfg.get("cash_balance_twd"), None)
    if x is not None:
        return x, "config_manual_approval_override"
    settings = row.get("settings") or {}
    for key in ["cashBalanceTwd", "cash_balance_twd", "cashBalance", "cash_balance", "availableCashTwd"]:
        x = finite_float(settings.get(key), None)
        if x is not None:
            return x, f"settings.{key}"
    return None, "missing_cash_balance"

def main() -> None:
    manual_input = read_json("data/alpha/manual_approval_input_latest.json", {}) or {}
    supa_row, supa_status = fetch_supabase_row()
    row = supa_row or latest_backup_row()
    row_source = supa_status if supa_row else "latest_backup_fallback"
    ledger = row.get("ledger_data") or []
    settings = row.get("settings") or {}
    price_map = settings.get("priceMap") or {}
    ticker_map = get_map()
    holdings = active_holdings_from_ledger(ledger)

    cash_balance, cash_source = get_cash_balance(row, manual_input)
    trade_budget_override = finite_float(manual_input.get("max_trade_budget_twd"), None)
    fx = None
    fx_source = "missing"
    try:
        q = fetch_yahoo_latest("TWD=X")
        fx = finite_float(q.get("price"), None)
        fx_source = "yahoo_chart_api:TWD=X"
    except Exception:
        fx = finite_float(settings.get("exchangeRate"), None)
        fx_source = "settings.exchangeRate_fallback" if fx else "missing"

    rows = []
    live_success = 0
    live_failed = 0
    for ticker, h in sorted(holdings.items()):
        category = h.get("category") or ""
        kind = asset_kind(ticker, category)
        rules = trade_rules(kind)
        symbol = yahoo_symbol(ticker, category, ticker_map)
        price = None
        currency = "TWD" if kind == "taiwan" else "USD"
        provider = "unavailable"
        provider_url = None
        fetch_error = None
        try:
            q = fetch_yahoo_latest(symbol)
            price = finite_float(q.get("price"), None)
            currency = str(q.get("currency") or currency)
            provider = str(q.get("provider") or "yahoo_chart_api")
            provider_url = q.get("provider_url")
            live_success += 1
        except Exception as exc:
            fetch_error = str(exc)
            # Stored price fallback is explicitly marked as non-real-time, so downstream gates can block if needed.
            price = finite_float(price_map.get(ticker) or price_map.get(symbol), None)
            provider = "stored_price_fallback_not_real_time" if price is not None else "unavailable"
            live_failed += 1
        shares = finite_float(h.get("shares"), 0) or 0.0
        price_twd = None
        if price is not None:
            if str(currency).upper() == "TWD" or kind == "taiwan":
                price_twd = price
            elif fx is not None:
                price_twd = price * fx
        market_value_twd = price_twd * shares if price_twd is not None else None
        min_unit = finite_float(rules.get("min_trade_unit"), 1) or 1
        whole_units_available = math.floor(shares / min_unit) * min_unit if min_unit > 0 else shares
        rows.append({
            "ticker": ticker,
            "category": category,
            "asset_kind": kind,
            "shares": round(shares, 8),
            "quote_symbol": symbol,
            "latest_price": price,
            "quote_currency": currency,
            "usd_twd_fx": fx,
            "price_twd": round(price_twd, 6) if price_twd is not None else None,
            "market_value_twd": round(market_value_twd, 2) if market_value_twd is not None else None,
            "max_sellable_amount_twd": round(market_value_twd, 2) if market_value_twd is not None else None,
            "max_buy_amount_twd": cash_balance if cash_balance is not None else None,
            "max_trade_budget_twd": trade_budget_override if trade_budget_override is not None else cash_balance,
            "minimum_trade_unit": rules["min_trade_unit"],
            "unit_name": rules["unit_name"],
            "odd_lot_or_fractional_allowed": rules["odd_lot_or_fractional_allowed"],
            "fractional_shares_allowed": rules["fractional_shares_allowed"],
            "whole_units_available_under_rule": round(whole_units_available, 8),
            "is_position_tradable_under_unit_rule": whole_units_available >= min_unit,
            "trade_rule_note": rules["rule_note"],
            "price_provider": provider,
            "price_provider_url": provider_url,
            "real_world_price_fetched": provider == "yahoo_chart_api",
            "fetch_error": fetch_error,
        })

    total_mv = sum((r.get("market_value_twd") or 0) for r in rows)
    output = {
        "version": "v8.1-trading-constraints-snapshot",
        "status": "OK",
        "generated_at": now_iso(),
        "mode": "trading_constraints_snapshot",
        "safe_mode": True,
        "research_only": True,
        "trade_signal_enabled": False,
        "execution_permission": False,
        "broker_submission_enabled": False,
        "official_rebalance_enabled": False,
        "not_trade_order": True,
        "real_world_data_policy": {
            "price_fetch_method": "Python urllib requests to Yahoo Finance chart API; no browser scraping; stored price fallback is marked non-real-time and blocks execution readiness.",
            "cash_balance_source_priority": ["config/manual_approval_override.json", "Supabase settings fields", "missing"],
            "no_fabricated_prices": True,
        },
        "portfolio_source": row_source,
        "cash_balance": {"cash_balance_twd": cash_balance, "source": cash_source},
        "fx": {"usd_twd": fx, "source": fx_source},
        "summary": {
            "asset_count": len(rows),
            "real_world_price_success_count": live_success,
            "price_fallback_or_failed_count": live_failed,
            "total_market_value_twd": round(total_mv, 2),
            "cash_balance_twd": cash_balance,
            "cash_balance_available": cash_balance is not None,
            "all_prices_real_world": live_failed == 0 and live_success == len(rows),
        },
        "constraints": {
            "us_fractional_shares_allowed": False,
            "taiwan_odd_lot_or_fractional_allowed": True,
            "crypto_fractional_trading_allowed": False,
            "minimum_trade_unit_policy": "US=1 share; Taiwan=1 share odd-lot; Crypto=1 coin; cash balance must be explicitly available for buys.",
        },
        "asset_rows": rows,
        "safety_boundary": [
            "Trading constraints snapshot supplies real-world price and sizing constraints only.",
            "It does not generate buy/sell instructions and does not approve execution.",
            "If live price or cash balance is missing, downstream ticket generation must block or mark incomplete.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARY_MD.write_text("\n".join([
        "# v8.1 Trading Constraints Snapshot",
        "",
        f"- Generated: `{output['generated_at']}`",
        f"- Portfolio source: `{row_source}`",
        f"- Assets: `{len(rows)}`",
        f"- Real-world price success: `{live_success}`",
        f"- Price fallback/failed: `{live_failed}`",
        f"- Cash balance: `{cash_balance}` / `{cash_source}`",
        f"- Total market value TWD: `{round(total_mv,2)}`",
        "",
        "## Real-world data policy",
        "- Uses Python requests to Yahoo Finance chart API for current prices and USD/TWD FX.",
        "- Stored prices are fallback only and are marked non-real-time.",
    ]) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Asset constraints: {len(rows)}")
    print(f"Real-world price success: {live_success}")
    print(f"Cash balance: {cash_balance} ({cash_source})")

if __name__ == "__main__":
    main()
