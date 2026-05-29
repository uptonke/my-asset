#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests
from supabase import create_client

TAIPEI_TZ = timezone(timedelta(hours=8))
TODAY_TPE = datetime.now(TAIPEI_TZ).date()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_SECRET_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "portfolio_db")
PORTFOLIO_ROW_ID = int(os.getenv("PORTFOLIO_ROW_ID", "1"))
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

YAHOO_SYMBOLS = [
    "SPY", "QQQ", "RSP", "IWM", "HYG", "JNK", "LQD", "TLT", "IEF", "SHY",
    "^VIX", "^VXN", "^MOVE", "DX-Y.NYB", "^TNX", "GC=F", "CL=F", "BTC-USD",
]

FRED_SERIES = {
    "hy_oas": "BAMLH0A0HYM2",
    "ig_oas": "BAMLC0A0CM",
    "financial_stress": "STLFSI4",
    "nfci": "NFCI",
    "dgs10": "DGS10",
    "dgs2": "DGS2",
    "real_10y": "DFII10",
    "breakeven_10y": "T10YIE",
    "fed_balance_sheet": "WALCL",
    "reverse_repo": "RRPONTSYD",
}


def finite(x: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) else default
    except Exception:
        return default


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(x)))


def pct_change(series: pd.Series, periods: int) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) <= periods:
        return None
    base = finite(s.iloc[-periods - 1])
    last = finite(s.iloc[-1])
    if base is None or base == 0 or last is None:
        return None
    return (last / base - 1.0) * 100.0


def last_value(series: pd.Series) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return finite(s.iloc[-1]) if len(s) else None


def hv20(series: pd.Series) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 25:
        return None
    ret = s.pct_change().dropna().tail(20)
    if ret.empty:
        return None
    return float(ret.std() * math.sqrt(252) * 100.0)


def moving_average(series: pd.Series, window: int) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < window:
        return None
    return finite(s.tail(window).mean())


def fetch_yahoo_chart(symbol: str, days: int = 430) -> pd.Series:
    now = int(datetime.now(timezone.utc).timestamp())
    start = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"period1": start, "period2": now, "interval": "1d", "events": "history"}
    resp = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=25)
    resp.raise_for_status()
    result = (((resp.json().get("chart") or {}).get("result") or [])[:1])
    if not result:
        raise RuntimeError(f"YahooChart empty for {symbol}")
    r = result[0]
    ts = r.get("timestamp") or []
    quote = ((((r.get("indicators") or {}).get("quote") or [])[:1]) or [{}])[0]
    close = quote.get("close") or []
    if not ts or not close:
        raise RuntimeError(f"YahooChart malformed for {symbol}")
    s = pd.Series(pd.to_numeric(close, errors="coerce"), index=pd.to_datetime(ts, unit="s"), name=symbol)
    return s.dropna().sort_index()


def fetch_fred_series(series_id: str, days: int = 760) -> pd.Series:
    if not FRED_API_KEY:
        raise RuntimeError("FRED_API_KEY missing")
    start = TODAY_TPE - timedelta(days=days)
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": str(start),
    }
    resp = requests.get(url, params=params, timeout=25)
    resp.raise_for_status()
    obs = resp.json().get("observations") or []
    rows = []
    for o in obs:
        val = o.get("value")
        if val in {None, "", "."}:
            continue
        v = finite(val)
        if v is None:
            continue
        rows.append((pd.to_datetime(o.get("date")), v))
    if not rows:
        raise RuntimeError(f"FRED empty for {series_id}")
    return pd.Series([v for _, v in rows], index=[d for d, _ in rows], name=series_id).sort_index()


def z_score(series: pd.Series, window: int = 252) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna().tail(window)
    if len(s) < 30:
        return None
    std = float(s.std())
    if std <= 0:
        return 0.0
    return float((s.iloc[-1] - s.mean()) / std)


def score_trend(prices: Dict[str, pd.Series]) -> Dict[str, Any]:
    parts = []
    notes = []
    details = {}
    for sym in ["SPY", "QQQ"]:
        s = prices.get(sym, pd.Series(dtype=float))
        last = last_value(s)
        ma50 = moving_average(s, 50)
        ma200 = moving_average(s, 200)
        m20 = pct_change(s, 20)
        m63 = pct_change(s, 63)
        score = 50.0
        if last is not None and ma50 is not None:
            score += 12 if last > ma50 else -12
        if last is not None and ma200 is not None:
            score += 18 if last > ma200 else -18
        if m20 is not None:
            score += max(-10, min(10, m20 * 1.5))
        if m63 is not None:
            score += max(-10, min(10, m63 * 0.8))
        score = clamp(score)
        parts.append(score)
        details[sym] = {"last": last, "ma50": ma50, "ma200": ma200, "mom20d": m20, "mom63d": m63, "score": round(score, 2)}
        notes.append(f"{sym} 20D {m20:+.1f}%" if m20 is not None else f"{sym} 20D N/A")
    final = float(np.mean(parts)) if parts else 50.0
    return {"score": round(final, 2), "label": label_score(final), "details": details, "note": "；".join(notes)}


def score_breadth(prices: Dict[str, pd.Series]) -> Dict[str, Any]:
    details = {}
    comps = [("RSP", "SPY"), ("IWM", "SPY")]
    scores = []
    notes = []
    for a, b in comps:
        if a not in prices or b not in prices:
            continue
        rel = (prices[a] / prices[b]).dropna()
        m20 = pct_change(rel, 20)
        m63 = pct_change(rel, 63)
        score = 50.0
        if m20 is not None:
            score += max(-25, min(25, m20 * 8.0))
        if m63 is not None:
            score += max(-15, min(15, m63 * 4.0))
        score = clamp(score)
        scores.append(score)
        details[f"{a}/{b}"] = {"rel_20d": m20, "rel_63d": m63, "score": round(score, 2)}
        notes.append(f"{a}/{b} 20D {m20:+.2f}%" if m20 is not None else f"{a}/{b} N/A")
    final = float(np.mean(scores)) if scores else 50.0
    return {"score": round(final, 2), "label": label_score(final), "details": details, "note": "；".join(notes)}


def score_credit(prices: Dict[str, pd.Series], fred: Dict[str, pd.Series]) -> Dict[str, Any]:
    details = {}
    scores = []
    notes = []
    for a, b in [("HYG", "TLT"), ("JNK", "LQD")]:
        if a in prices and b in prices:
            rel = (prices[a] / prices[b]).dropna()
            m20 = pct_change(rel, 20)
            score = 50.0 + (max(-25, min(25, m20 * 10.0)) if m20 is not None else 0.0)
            scores.append(clamp(score))
            details[f"{a}/{b}"] = {"rel_20d": m20, "score": round(clamp(score), 2)}
            notes.append(f"{a}/{b} 20D {m20:+.2f}%" if m20 is not None else f"{a}/{b} N/A")
    hy = fred.get("hy_oas")
    if hy is not None and not hy.empty:
        val = last_value(hy)
        z = z_score(hy)
        score = 70.0
        if val is not None:
            if val > 6.0: score -= 35
            elif val > 4.5: score -= 20
            elif val > 3.5: score -= 10
            elif val < 3.0: score += 10
        if z is not None:
            score -= max(-15, min(20, z * 8.0))
        score = clamp(score)
        scores.append(score)
        details["HY_OAS"] = {"value": val, "z": z, "score": round(score, 2), "series": FRED_SERIES["hy_oas"]}
        notes.append(f"HY OAS {val:.2f}%" if val is not None else "HY OAS N/A")
    final = float(np.mean(scores)) if scores else 50.0
    return {"score": round(final, 2), "label": label_score(final), "details": details, "note": "；".join(notes)}


def score_volatility(prices: Dict[str, pd.Series]) -> Dict[str, Any]:
    details = {}
    scores = []
    notes = []
    vix = last_value(prices.get("^VIX", pd.Series(dtype=float)))
    vxn = last_value(prices.get("^VXN", pd.Series(dtype=float)))
    move = last_value(prices.get("^MOVE", pd.Series(dtype=float)))
    spy_hv = hv20(prices.get("SPY", pd.Series(dtype=float)))
    qqq_hv = hv20(prices.get("QQQ", pd.Series(dtype=float)))

    def vol_to_score(v: Optional[float], low: float, high: float) -> Optional[float]:
        if v is None:
            return None
        return clamp(100.0 - (v - low) / (high - low) * 70.0)

    for name, val, low, high in [("VIX", vix, 12, 35), ("VXN", vxn, 16, 45), ("MOVE", move, 80, 160), ("SPY_HV20", spy_hv, 10, 35), ("QQQ_HV20", qqq_hv, 15, 45)]:
        sc = vol_to_score(val, low, high)
        if sc is not None:
            scores.append(sc)
        details[name] = {"value": val, "score": round(sc, 2) if sc is not None else None}
    if vix is not None:
        notes.append(f"VIX {vix:.1f}")
    if spy_hv is not None:
        notes.append(f"SPY HV20 {spy_hv:.1f}%")
    final = float(np.mean(scores)) if scores else 50.0
    return {"score": round(final, 2), "label": label_score(final), "details": details, "note": "；".join(notes)}


def score_liquidity(prices: Dict[str, pd.Series], fred: Dict[str, pd.Series]) -> Dict[str, Any]:
    details = {}
    scores = []
    notes = []
    dxy_m20 = pct_change(prices.get("DX-Y.NYB", pd.Series(dtype=float)), 20)
    tnx_m20 = pct_change(prices.get("^TNX", pd.Series(dtype=float)), 20)
    gold_m20 = pct_change(prices.get("GC=F", pd.Series(dtype=float)), 20)
    btc_m20 = pct_change(prices.get("BTC-USD", pd.Series(dtype=float)), 20)

    dxy_score = 50.0 - (max(-20, min(20, dxy_m20 * 6.0)) if dxy_m20 is not None else 0.0)
    tnx_score = 50.0 - (max(-15, min(15, tnx_m20 * 1.5)) if tnx_m20 is not None else 0.0)
    scores.extend([clamp(dxy_score), clamp(tnx_score)])
    details.update({
        "DXY_20D": {"value": dxy_m20, "score": round(clamp(dxy_score), 2)},
        "TNX_20D": {"value": tnx_m20, "score": round(clamp(tnx_score), 2)},
        "Gold_20D": {"value": gold_m20},
        "BTC_20D": {"value": btc_m20},
    })

    for key in ["financial_stress", "nfci", "real_10y"]:
        s = fred.get(key)
        if s is None or s.empty:
            continue
        val = last_value(s)
        z = z_score(s)
        score = 55.0
        if z is not None:
            score -= max(-20, min(25, z * 10.0))
        if key == "real_10y" and val is not None:
            score -= max(-10, min(10, (val - 1.5) * 5.0))
        score = clamp(score)
        scores.append(score)
        details[key] = {"value": val, "z": z, "score": round(score, 2), "series": FRED_SERIES[key]}
    if dxy_m20 is not None:
        notes.append(f"DXY 20D {dxy_m20:+.1f}%")
    if "financial_stress" in details and details["financial_stress"].get("value") is not None:
        notes.append(f"STLFSI {details['financial_stress']['value']:.2f}")
    final = float(np.mean(scores)) if scores else 50.0
    return {"score": round(final, 2), "label": label_score(final), "details": details, "note": "；".join(notes)}


def score_cross_asset(prices: Dict[str, pd.Series], fred: Dict[str, pd.Series]) -> Dict[str, Any]:
    gold = pct_change(prices.get("GC=F", pd.Series(dtype=float)), 20)
    oil = pct_change(prices.get("CL=F", pd.Series(dtype=float)), 20)
    btc = pct_change(prices.get("BTC-USD", pd.Series(dtype=float)), 20)
    breakeven = fred.get("breakeven_10y")
    breakeven_val = last_value(breakeven) if breakeven is not None else None
    breakeven_m = pct_change(breakeven, 20) if breakeven is not None else None
    score = 50.0
    if btc is not None:
        score += max(-15, min(15, btc * 0.8))
    if gold is not None and btc is not None and gold > 3 and btc < 0:
        score -= 8
    if oil is not None and oil > 8:
        score -= 6
    if breakeven_m is not None and breakeven_m > 3:
        score -= 5
    score = clamp(score)
    details = {"Gold_20D": gold, "Oil_20D": oil, "BTC_20D": btc, "Breakeven10Y": breakeven_val, "Breakeven10Y_20D": breakeven_m}
    note = "；".join([x for x in [f"BTC 20D {btc:+.1f}%" if btc is not None else None, f"Gold 20D {gold:+.1f}%" if gold is not None else None] if x])
    return {"score": round(score, 2), "label": label_score(score), "details": details, "note": note}


def label_score(score: float) -> str:
    if score < 20:
        return "系統性危機"
    if score < 40:
        return "偏空防守"
    if score < 55:
        return "觀望"
    if score < 70:
        return "偏多"
    if score < 85:
        return "Risk-on"
    return "過熱"


def regime(score: float, modules: Dict[str, Dict[str, Any]]) -> str:
    vol = modules.get("volatility", {}).get("score", 50)
    credit = modules.get("credit", {}).get("score", 50)
    breadth = modules.get("breadth", {}).get("score", 50)
    trend = modules.get("trend", {}).get("score", 50)
    liquidity = modules.get("liquidity", {}).get("score", 50)
    if credit < 30 or volatility_score_is_stress(vol) or liquidity < 25:
        return "系統性警戒"
    if score < 40:
        return "偏空防守"
    if score < 55:
        return "觀望"
    if trend >= 60 and credit >= 55 and breadth >= 50 and score >= 65:
        return "偏多可承擔風險"
    if score >= 80 and vol >= 70:
        return "強勢但留意過熱"
    return "中性偏多" if score >= 55 else "中性"


def volatility_score_is_stress(vol_score: float) -> bool:
    return finite(vol_score, 50) < 25


def reasons(modules: Dict[str, Dict[str, Any]], score: float) -> List[str]:
    order = ["trend", "breadth", "credit", "volatility", "liquidity", "cross_asset"]
    zh = {"trend": "趨勢", "breadth": "廣度", "credit": "信用", "volatility": "波動", "liquidity": "流動性", "cross_asset": "跨資產"}
    out = []
    for k in order:
        m = modules.get(k, {})
        s = finite(m.get("score"), 50) or 50
        note = m.get("note") or ""
        if s >= 65:
            out.append(f"{zh[k]}偏強：{note}".strip("："))
        elif s <= 40:
            out.append(f"{zh[k]}偏弱：{note}".strip("："))
    if not out:
        out.append("多數指標落在中性區，暫無單邊訊號。")
    return out[:5]


def build_market_compass() -> Dict[str, Any]:
    prices: Dict[str, pd.Series] = {}
    for sym in YAHOO_SYMBOLS:
        try:
            prices[sym] = fetch_yahoo_chart(sym)
            print(f"OK Yahoo {sym}: {last_value(prices[sym])}")
            time.sleep(0.1)
        except Exception as exc:
            print(f"WARN Yahoo {sym}: {exc}")

    fred: Dict[str, pd.Series] = {}
    fred_errors = []
    for key, series_id in FRED_SERIES.items():
        try:
            fred[key] = fetch_fred_series(series_id)
            print(f"OK FRED {key}/{series_id}: {last_value(fred[key])}")
            time.sleep(0.1)
        except Exception as exc:
            fred_errors.append(f"{key}:{series_id}:{exc}")
            print(f"WARN FRED {key}/{series_id}: {exc}")

    modules = {
        "trend": score_trend(prices),
        "breadth": score_breadth(prices),
        "credit": score_credit(prices, fred),
        "volatility": score_volatility(prices),
        "liquidity": score_liquidity(prices, fred),
        "cross_asset": score_cross_asset(prices, fred),
    }

    weights = {"trend": 0.25, "breadth": 0.20, "credit": 0.20, "volatility": 0.15, "liquidity": 0.15, "cross_asset": 0.05}
    score = sum((finite(modules[k].get("score"), 50) or 50) * w for k, w in weights.items())
    score = round(clamp(score), 2)

    return {
        "version": "phase3_fred_yahoo_v1",
        "updated_at": datetime.now(TAIPEI_TZ).isoformat(timespec="seconds"),
        "date": str(TODAY_TPE),
        "score": score,
        "label": label_score(score),
        "regime": regime(score, modules),
        "modules": modules,
        "weights": weights,
        "reasons": reasons(modules, score),
        "fred_enabled": bool(FRED_API_KEY),
        "fred_errors": fred_errors[:8],
        "data_sources": {
            "market_prices": "Yahoo Chart unofficial endpoint",
            "macro_credit": "FRED API" if FRED_API_KEY else "FRED API not configured",
        },
    }


def main() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    row = client.table(SUPABASE_TABLE).select("macro_meta").eq("id", PORTFOLIO_ROW_ID).single().execute().data
    macro_meta = row.get("macro_meta") if row and isinstance(row.get("macro_meta"), dict) else {}
    compass = build_market_compass()
    macro_meta["market_compass"] = compass
    client.table(SUPABASE_TABLE).update({"macro_meta": macro_meta}).eq("id", PORTFOLIO_ROW_ID).execute()
    print(f"OK market compass score={compass['score']} regime={compass['regime']} fred_enabled={compass['fred_enabled']}")


if __name__ == "__main__":
    main()
