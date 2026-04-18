import os
import io
import re
import json
import warnings
import traceback
import math
import requests
import zipfile
import numpy as np
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import scipy.optimize as sco
from supabase import create_client, Client
from google import genai

warnings.filterwarnings('ignore')
import shutil
try:
    # 針對 GitHub Actions (Linux) 或 Mac 的快取路徑
    cache_path = os.path.join(os.path.expanduser('~'), '.cache', 'yfinance')
    if os.path.exists(cache_path):
        shutil.rmtree(cache_path)
    
    # 針對 Windows 系統的快取路徑
    windows_cache = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'yfinance')
    if os.path.exists(windows_cache):
        shutil.rmtree(windows_cache)
except Exception:
    pass

# ==========================================
# 1. 讀取環境變數與初始化
# ==========================================
try:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("環境變數遺失：SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY 未設定")
    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"🔥 初始化失敗:\n{traceback.format_exc()}", flush=True)
    exit(1)

# ==========================================
# 1.5 總經規則引擎
# ==========================================
def _is_missing(x):
    if x is None: return True
    try:
        if isinstance(x, str) and not x.strip(): return True
        v = float(x)
        return math.isnan(v)
    except Exception: return True

def _num(x, default=None):
    if _is_missing(x): return default
    try: return float(x)
    except Exception: return default

def score_yield_curve(v): return 2 if _num(v)>1 else 1 if _num(v)>0 else -1 if _num(v)>-0.5 else -2
def score_hy_spread(v): return -2 if _num(v)>5 else -1 if _num(v)>=3 else 1 if _num(v)>=1.5 else 2
def score_vix(v, z=0): return -2 if _num(v)>30 or _num(z)>2.5 else -1 if _num(v)>=20 or _num(z)>1.5 else 1 if _num(v)>=12 else 2
def score_dxy(v): return -1 if _num(v)>105 else 1 if _num(v)<95 else 0
def score_btc_mom(v): return 2 if _num(v)>10 else 1 if _num(v)>=0 else -1 if _num(v)>-10 else -2
def score_oil(v): return -1 if _num(v)>90 else 1 if _num(v)<60 else 0
def score_copper_gold_ratio(v): return 1 if _num(v)>=0.25 else 0 if _num(v)>=0.15 else -1
def score_move(v, z=0): return -2 if _num(v)>120 or _num(z)>2.5 else -1 if _num(v)>=100 or _num(z)>1.5 else 1 if _num(v)>=80 else 2
def score_iwm_spy(v): return 2 if _num(v)>3 else 1 if _num(v)>=0 else -1 if _num(v)>-3 else -2
def score_xlu_xly(v): return -2 if _num(v)>3 else -1 if _num(v)>=0 else 1 if _num(v)>-3 else 2
def score_vxn(v, z=0): return -2 if _num(v)>35 or _num(z)>2.5 else -1 if _num(v)>=25 or _num(z)>1.5 else 1 if _num(v)>=15 else 2
def score_vvix(v, z=0): return -2 if _num(v)>115 or _num(z)>2.5 else -1 if _num(v)>=100 or _num(z)>1.5 else 1 if _num(v)>=80 else 2
def score_hyg_tlt(v): return -2 if _num(v)<-3 else -1 if _num(v)<0 else 1 if _num(v)<3 else 2
def score_dbc_mom(v): return -2 if _num(v)>8 else -1 if _num(v)>3 else 1 if _num(v)>-5 else 2
def score_soxx_spy(v): return 2 if _num(v)>5 else 1 if _num(v)>0 else -1 if _num(v)>-3 else -2
def score_liquidity(v): return -2 if _num(v)>0.5 else -1 if _num(v)>0.2 else 1 if _num(v)>-0.1 else 2
def score_rsp_spy(v): return 2 if _num(v)>2 else 1 if _num(v)>0 else -1 if _num(v)>-2 else -2
def score_kre_spy(v): return 1 if _num(v)>1 else -2 if _num(v)<-5 else -1 if _num(v)<-2 else 0
def score_aud_jpy(v): return 2 if _num(v)>3 else 1 if _num(v)>0 else -2 if _num(v)<-3 else -1
def score_pcr(v, z=0): return -2 if _num(v)>1.2 or _num(z)>2.0 else -1 if _num(v)>1.0 or _num(z)>1.0 else 2 if _num(v)<0.8 else 1
def score_sys_corr(v): return -3 if _num(v)>0.85 else -1 if _num(v)>0.70 else 2 if _num(v)<0.30 else 0

def choose_stage(scores):
    vals = list(scores.values())
    pos, neg, total = sum(1 for s in vals if s>0), sum(1 for s in vals if s<0), sum(vals)
    if pos>=3 and neg>=3: return "mixed"
    if scores["yield_curve"]<=-1 and scores["hy_spread"]<=-1 and scores["vix"]<=-1: return "recession_risk"
    if scores["dxy"]<=-1 and scores["hy_spread"]<=-1: return "tight_liquidity"
    if (scores.get("oil_price",0)<0 or scores.get("dbc_mom",0)<0) and (scores["yield_curve"]<=0 or scores["vix"]<=0): return "stagflation"
    if scores["yield_curve"]>0 and scores["hy_spread"]>0 and scores["vix"]>0 and scores["btc_1m_mom"]>0: return "expansion"
    if total>=10: return "expansion"
    if 3<=total<=9: return "neutral"
    if -5<=total<=2: return "tight_liquidity"
    if -12<=total<=-6: return "recession_risk"
    if total<=-13: return "stagflation"
    return "mixed"

def build_regime_packet(macro_payload):
    raw = {k: macro_payload.get(k) for k in [
        "yield_curve", "hy_spread", "vix", "vix_z", "dxy", "btc_1m_mom", "oil_price", "copper_gold_ratio", "move_index", "move_z", 
        "iwm_spy_mom", "xlu_xly_mom", "vxn", "vxn_z", "vvix", "vvix_z", "hyg_tlt_mom", "dbc_mom", "soxx_spy_mom", "liquidity_spread", 
        "rsp_spy_mom", "kre_spy_mom", "aud_jpy_mom", "put_call_ratio", "pcr_z", "sys_corr"]}
    scores = {
        "yield_curve": score_yield_curve(raw["yield_curve"]), "hy_spread": score_hy_spread(raw["hy_spread"]),
        "vix": score_vix(raw["vix"], raw["vix_z"]), "dxy": score_dxy(raw["dxy"]), "btc_1m_mom": score_btc_mom(raw["btc_1m_mom"]),
        "oil_price": score_oil(raw["oil_price"]), "copper_gold_ratio": score_copper_gold_ratio(raw["copper_gold_ratio"]),
        "move_index": score_move(raw["move_index"], raw["move_z"]), "iwm_spy_mom": score_iwm_spy(raw["iwm_spy_mom"]),
        "xlu_xly_mom": score_xlu_xly(raw["xlu_xly_mom"]), "vxn": score_vxn(raw["vxn"], raw["vxn_z"]),
        "vvix": score_vvix(raw["vvix"], raw["vvix_z"]), "hyg_tlt_mom": score_hyg_tlt(raw["hyg_tlt_mom"]),
        "dbc_mom": score_dbc_mom(raw["dbc_mom"]), "soxx_spy_mom": score_soxx_spy(raw["soxx_spy_mom"]),
        "liquidity_spread": score_liquidity(raw["liquidity_spread"]), "rsp_spy_mom": score_rsp_spy(raw["rsp_spy_mom"]),
        "kre_spy_mom": score_kre_spy(raw["kre_spy_mom"]), "aud_jpy_mom": score_aud_jpy(raw["aud_jpy_mom"]),
        "put_call_ratio": score_pcr(raw["put_call_ratio"], raw["pcr_z"]), "sys_corr": score_sys_corr(raw["sys_corr"])
    }
    stage = choose_stage(scores)
    return {"raw": raw, "scores": scores, "stage_candidate": stage, "total_score": sum(scores.values()), "confidence_hint": 0.85}
DEFAULT_MACRO = {
    "y10": 4.2,
    "y3m": 5.0,
    "hyg_yield": 7.5,
    "btc_mom": 0.0,
    "spy_cagr": 0.10,
    "spy_vol": 0.15,
    "vix": 20.0,
    "vix_z": 0.0,
    "vxn": 22.0,
    "vxn_z": 0.0,
    "vvix": 90.0,
    "vvix_z": 0.0,
    "dxy": 100.0,
    "gold": 2000.0,
    "copper": 4.0,
    "oil": 75.0,
    "copper_gold_ratio": 0.2,
    "pcr": 1.0,
    "pcr_z": 0.0,
    "aud_jpy_mom": 0.0,
    "move_idx": 100.0,
    "move_z": 0.0,
    "iwm_spy_mom": 0.0,
    "xlu_xly_mom": 0.0,
    "hyg_tlt_mom": 0.0,
    "dbc_mom": 0.0,
    "soxx_spy_mom": 0.0,
    "liquidity_spread": 0.0,
    "rsp_spy_mom": 0.0,
    "kre_spy_mom": 0.0,
    "sys_corr": 0.3,
}

# ==========================================
# 2. 抓取總經數據與市場參數
# ==========================================
print("🌍 啟動量化大腦：開始透過 Yahoo API 抓取市場參數...", flush=True)

def calc_z_score(series):
    if series.empty or len(series) < 20: return 0.0
    std = series.std()
    return (series.iloc[-1] - series.mean()) / std if std != 0 else 0.0

def safe_download_close(symbols, period="1mo", progress=False, interval=None):
    try:
        kwargs = {
            "period": period,
            "progress": progress
        }
        if interval:
            kwargs["interval"] = interval

        raw = yf.download(symbols, **kwargs)

        if isinstance(raw, pd.DataFrame):
            if "Close" in raw.columns:
                close = raw["Close"]
            else:
                close = raw
        else:
            close = raw

        if isinstance(close, pd.Series):
            if isinstance(symbols, (list, tuple, set)):
                col_name = list(symbols)[0] if len(symbols) == 1 else (close.name or "Close")
            else:
                col_name = str(symbols)
            close = close.to_frame(name=col_name)

        return close.dropna(how="all")

    except Exception as e:
        print(f"⚠️ yfinance 下載失敗 ({symbols}): {e}", flush=True)
        return pd.DataFrame()
def safe_last(series_or_df, default=None):
    try:
        if isinstance(series_or_df, pd.DataFrame):
            if series_or_df.empty or series_or_df.shape[1] == 0:
                return default
            s = series_or_df.iloc[:, 0].dropna()
        else:
            s = pd.Series(series_or_df).dropna()
        return float(s.iloc[-1]) if len(s) > 0 else default
    except Exception:
        return default


def simple_momentum_pct(series_or_df, default=0.0):
    try:
        if isinstance(series_or_df, pd.DataFrame):
            if series_or_df.empty or series_or_df.shape[1] == 0:
                return default
            s = series_or_df.iloc[:, 0].dropna()
        else:
            s = pd.Series(series_or_df).dropna()

        if len(s) < 2:
            return default

        return float(((s.iloc[-1] / s.iloc[0]) - 1) * 100)
    except Exception:
        return default


def relative_momentum_pct(df, lhs, rhs=None, default=0.0):
    try:
        if lhs not in df.columns:
            return default
        s1 = df[lhs].dropna()
        if len(s1) < 2:
            return default

        r1 = (s1.iloc[-1] / s1.iloc[0]) - 1

        if rhs is None:
            return float(r1 * 100)

        if rhs not in df.columns:
            return default
        s2 = df[rhs].dropna()
        if len(s2) < 2:
            return default

        r2 = (s2.iloc[-1] / s2.iloc[0]) - 1
        return float((r1 - r2) * 100)
    except Exception:
        return default


PROXY_TICKER_MAP = {
    "統一奔騰": "00981A.TW",
    "安聯台灣科技": "0052.TW",
    "加密貨幣": "BTC-USD",
}


def normalize_ticker(raw):
    return str(raw).strip().upper() if raw is not None else ""


def is_tw_numeric_ticker(ticker):
    return bool(re.match(r'^\d+[A-Z]*$', ticker))


def is_chinese_label(ticker):
    return bool(re.search(r'[一-鿿]', ticker))


def map_to_yf_ticker(ticker, tw_bench="^TWII"):
    t = normalize_ticker(ticker)

    if not t:
        return ""

    if t in PROXY_TICKER_MAP:
        return PROXY_TICKER_MAP[t]

    if is_chinese_label(t):
        return tw_bench

    if is_tw_numeric_ticker(t):
        return f"{t}.TW"

    return t

try:
    print("   ⏳ 正在抓取公債殖利率...", flush=True)
    try:
        bonds = safe_download_close(["^TNX", "^IRX"], period="1mo", progress=False)
        y10 = float(bonds["^TNX"].dropna().iloc[-1])
        y3m = float(bonds["^IRX"].dropna().iloc[-1])
    except Exception as e:
        print(f"⚠️ 抓取公債殖利率失敗，改用預設值: {e}", flush=True)
        y10, y3m = DEFAULT_MACRO["y10"], DEFAULT_MACRO["y3m"]

    print("   ⏳ 正在計算信用利差...", flush=True)
    try:
        hyg_yield = yf.Ticker("HYG").info.get('yield', 0.05) * 100
    except Exception as e:
        print(f"⚠️ 抓取 HYG 殖利率失敗，改用預設值: {e}", flush=True)
        hyg_yield = DEFAULT_MACRO["hyg_yield"]
    hy_spread = max(0.1, hyg_yield - y10)

    print("   ⏳ 正在計算加密貨幣動能...", flush=True)
    try:
        btc_data = safe_download_close("BTC-USD", period="1mo", progress=False)
        btc_mom = simple_momentum_pct(btc_data, default=0.0)
    except Exception as e:
        print(f"⚠️ 抓取 BTC 動能失敗，改用預設值: {e}", flush=True)
        btc_mom = DEFAULT_MACRO["btc_mom"]

    print("   ⏳ 正在計算 SPY 長期報酬與短期波動...", flush=True)
    try:
        spy = safe_download_close("SPY", period="10y", progress=False)
        spy_clean = spy.iloc[:, 0].dropna()
        if len(spy_clean) > 10:
            years = max(1, (spy_clean.index[-1] - spy_clean.index[0]).days / 365.25)
            spy_cagr = (spy_clean.iloc[-1] / spy_clean.iloc[0]) ** (1 / years) - 1
            spy_vol = spy_clean.tail(252).pct_change().std() * np.sqrt(252)
        else:
            spy_cagr, spy_vol = DEFAULT_MACRO["spy_cagr"], DEFAULT_MACRO["spy_vol"]
    except Exception as e:
        print(f"⚠️ 抓取 SPY 長期資料失敗，改用預設值: {e}", flush=True)
        spy_cagr, spy_vol = DEFAULT_MACRO["spy_cagr"], DEFAULT_MACRO["spy_vol"]

    print("   ⏳ 正在抓取跨資產期貨、情緒指標、PCR與AUD/JPY...", flush=True)
    try:
        vix_family = safe_download_close(["^VIX", "^VXN", "^VVIX"], period="1y", progress=False)
        vix_s = vix_family["^VIX"].dropna() if "^VIX" in vix_family.columns else pd.Series([DEFAULT_MACRO["vix"]])
        vxn_s = vix_family["^VXN"].dropna() if "^VXN" in vix_family.columns else pd.Series([DEFAULT_MACRO["vxn"]])
        vvix_s = vix_family["^VVIX"].dropna() if "^VVIX" in vix_family.columns else pd.Series([DEFAULT_MACRO["vvix"]])

        vix, vix_z = float(vix_s.iloc[-1]), float(calc_z_score(vix_s))
        vxn, vxn_z = float(vxn_s.iloc[-1]), float(calc_z_score(vxn_s))
        vvix, vvix_z = float(vvix_s.iloc[-1]), float(calc_z_score(vvix_s))

        dxy = safe_last(safe_download_close("DX-Y.NYB", period="5d", progress=False), default=DEFAULT_MACRO["dxy"])
        gold = safe_last(safe_download_close("GC=F", period="5d", progress=False), default=DEFAULT_MACRO["gold"])
        copper = safe_last(safe_download_close("HG=F", period="5d", progress=False), default=DEFAULT_MACRO["copper"])
        oil = safe_last(safe_download_close("CL=F", period="5d", progress=False), default=DEFAULT_MACRO["oil"])
        copper_gold_ratio = (copper / gold) * 100 if gold else DEFAULT_MACRO["copper_gold_ratio"]
    except Exception as e:
        print(f"⚠️ 抓取跨資產價格失敗，改用預設值: {e}", flush=True)
        vix = DEFAULT_MACRO["vix"]
        vxn = DEFAULT_MACRO["vxn"]
        vvix = DEFAULT_MACRO["vvix"]
        dxy = DEFAULT_MACRO["dxy"]
        gold = DEFAULT_MACRO["gold"]
        copper = DEFAULT_MACRO["copper"]
        oil = DEFAULT_MACRO["oil"]
        copper_gold_ratio = DEFAULT_MACRO["copper_gold_ratio"]
        vix_z = DEFAULT_MACRO["vix_z"]
        vxn_z = DEFAULT_MACRO["vxn_z"]
        vvix_z = DEFAULT_MACRO["vvix_z"]

    try:
        pcr_data = yf.Ticker("^PCR").history(period="1y")['Close'].dropna()
        pcr, pcr_z = float(pcr_data.iloc[-1]), float(calc_z_score(pcr_data))
    except Exception as e:
        print(f"   ⚠️ ^PCR 可能已下市或抓取失敗: {e}", flush=True)
        pcr, pcr_z = DEFAULT_MACRO["pcr"], DEFAULT_MACRO["pcr_z"]

    try:
        aud_jpy_data = safe_download_close("AUDJPY=X", period="1mo", progress=False)
        aud_jpy_mom = simple_momentum_pct(aud_jpy_data, default=0.0)
    except Exception as e:
        print(f"⚠️ 抓取 AUD/JPY 動能失敗，改用預設值: {e}", flush=True)
        aud_jpy_mom = DEFAULT_MACRO["aud_jpy_mom"]

    print("   ⏳ 正在抓取 MOVE 指數與板塊輪動指標...", flush=True)
    try:
        try:
            move_data = yf.Ticker("^MOVE").history(period="1y")['Close'].dropna()
            if move_data.empty:
                raise ValueError("MOVE 資料為空")
            move_idx, move_z = float(move_data.iloc[-1]), float(calc_z_score(move_data))
        except Exception:
            tlt = safe_download_close("TLT", period="1y", progress=False)
            tlt_series = tlt.iloc[:, 0].dropna() if not tlt.empty else pd.Series(dtype=float)
            move_data = (tlt_series.pct_change().rolling(20).std() * np.sqrt(252) * 100 * 5).dropna()
            move_idx = float(move_data.iloc[-1]) if not move_data.empty else DEFAULT_MACRO["move_idx"]
            move_z = float(calc_z_score(move_data)) if not move_data.empty else DEFAULT_MACRO["move_z"]

        target_etfs = ["IWM", "SPY", "XLU", "XLY", "HYG", "TLT", "DBC", "SOXX", "BIL", "SHY", "RSP", "KRE"]
        etfs = safe_download_close(target_etfs, period="1mo", progress=False)

        iwm_spy_mom = relative_momentum_pct(etfs, "IWM", "SPY")
        xlu_xly_mom = relative_momentum_pct(etfs, "XLU", "XLY")
        hyg_tlt_mom = relative_momentum_pct(etfs, "HYG", "TLT")
        soxx_spy_mom = relative_momentum_pct(etfs, "SOXX", "SPY")
        dbc_mom = relative_momentum_pct(etfs, "DBC")
        liquidity_spread = relative_momentum_pct(etfs, "BIL", "SHY")
        rsp_spy_mom = relative_momentum_pct(etfs, "RSP", "SPY")
        kre_spy_mom = relative_momentum_pct(etfs, "KRE", "SPY")
    except Exception as e:
        print(f"⚠️ 抓取 MOVE / 板塊輪動指標失敗，改用預設值: {e}", flush=True)
        move_idx = DEFAULT_MACRO["move_idx"]
        move_z = DEFAULT_MACRO["move_z"]
        iwm_spy_mom = DEFAULT_MACRO["iwm_spy_mom"]
        xlu_xly_mom = DEFAULT_MACRO["xlu_xly_mom"]
        hyg_tlt_mom = DEFAULT_MACRO["hyg_tlt_mom"]
        dbc_mom = DEFAULT_MACRO["dbc_mom"]
        soxx_spy_mom = DEFAULT_MACRO["soxx_spy_mom"]
        liquidity_spread = DEFAULT_MACRO["liquidity_spread"]
        rsp_spy_mom = DEFAULT_MACRO["rsp_spy_mom"]
        kre_spy_mom = DEFAULT_MACRO["kre_spy_mom"]

    print("   ⏳ 正在計算系統靜態相關性矩陣 (系統性風險)...", flush=True)
    sys_corr, corr_matrix = DEFAULT_MACRO["sys_corr"], {}
    current_shares, active_tickers = {}, []
    try:
        response = supabase.table("portfolio_db").select("*").limit(1).execute()
        if response.data:
            db_record = response.data[0]
            for tx in db_record.get("ledger_data", []):
                t = str(tx.get("ticker", "")).strip().upper()
                if not t:
                    continue
                s = float(tx.get("shares", 0))
                if str(tx.get("type", "buy")).lower() in ["sell", "賣出"]:
                    s = -s
                current_shares[t] = current_shares.get(t, 0) + s

            active_tickers = [t for t, s in current_shares.items() if s > 0.0001]

            if len(active_tickers) > 1:
                tw_bench = "^TWII"
                mapped_tickers = list(set(map_to_yf_ticker(t, tw_bench=tw_bench) for t in active_tickers))
                port_df = safe_download_close(mapped_tickers, period="6mo", progress=False)
                port_returns = port_df.pct_change().dropna()

                corr_df = port_returns.corr()
                mask = np.triu(np.ones_like(corr_df, dtype=bool), k=1)
                raw_sys_corr = float(corr_df.where(mask).mean().mean())
                sys_corr = raw_sys_corr if not np.isnan(raw_sys_corr) else 0.0
                corr_matrix = corr_df.replace([np.inf, -np.inf], np.nan).fillna(0.0).to_dict()
    except Exception as e:
        print(f"⚠️ 相關性計算失敗: {e}")

    macro_payload = {
        "yield_10y": float(round(y10, 2)), "yield_2y": float(round(y3m, 2)), "yield_curve": float(round(y10 - y3m, 2)),
        "hy_spread": float(round(hy_spread, 2)), "btc_1m_mom": float(round(btc_mom, 2)), "market_rf": float(round(y10, 2)),
        "market_rm": float(round(spy_cagr * 100, 2)), "market_sm": float(round(spy_vol * 100, 2)),
        "vix": float(round(vix, 2)), "vix_z": float(round(vix_z, 2)), "vxn": float(round(vxn, 2)), "vxn_z": float(round(vxn_z, 2)),
        "vvix": float(round(vvix, 2)), "vvix_z": float(round(vvix_z, 2)),
        "dxy": float(round(dxy, 2)), "gold_price": float(round(gold, 2)), "oil_price": float(round(oil, 2)), "copper_gold_ratio": float(round(copper_gold_ratio, 4)),
        "move_index": float(round(move_idx, 2)), "move_z": float(round(move_z, 2)),
        "iwm_spy_mom": float(round(iwm_spy_mom, 2)), "xlu_xly_mom": float(round(xlu_xly_mom, 2)),
        "hyg_tlt_mom": float(round(hyg_tlt_mom, 2)), "dbc_mom": float(round(dbc_mom, 2)),
        "soxx_spy_mom": float(round(soxx_spy_mom, 2)), "liquidity_spread": float(round(liquidity_spread, 2)),
        "rsp_spy_mom": float(round(rsp_spy_mom, 2)), "kre_spy_mom": float(round(kre_spy_mom, 2)), "aud_jpy_mom": float(round(aud_jpy_mom, 2)),
        "put_call_ratio": float(round(pcr, 2)), "pcr_z": float(round(pcr_z, 2)),
        "sys_corr": float(round(sys_corr, 2)), "corr_matrix": corr_matrix
    }

    regime_packet = build_regime_packet(macro_payload)
    print(f"🤖 喚醒 Gemini AI 進行格式化 (內部判定階段: {regime_packet['stage_candidate']})...", flush=True)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""
            [SYSTEM_DIRECTIVE]
            Task: Transform deterministic macro signals into aggressive tactical trading metadata.
            Tone: High-Alpha Quant, Contrarian, Extreme Aggressive (Risk = Opportunity). Focus deeply on Z-Scores and `sys_corr`.
            Language: STRICTLY Traditional Chinese. ONLY output RAW JSON.

            [TRANSFORMATION_RULES]
            1. STAGE: Translate `stage_candidate` to Traditional Chinese.
            2. SUMMARY: 1 sentence. MUST START WITH "[目前總經形勢: 翻譯後的STAGE]". Map stage to a max-alpha strategy.
            3. DETAILS.TITLE: Traditional Chinese metric name.
            4. DETAILS.DESC: Max 35 chars. Explicitly cite specific numeric values (Z-Scores).
            5. DETAILS.COLOR: "text-green-400", "text-red-400", "text-gray-400".
            6. DETAILS.ICON: Single emoji.

            [INPUT_DATA]
            {json.dumps(regime_packet, ensure_ascii=False)}

            [OUTPUT_SCHEMA]
            {{"summary": "<string>", "details": [{{"icon": "<emoji>", "color": "<string_class>", "title": "<string>", "desc": "<string>"}}]}}
            """
            for model_name in ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.0-flash"]:
                try:
                    res = client.models.generate_content(model=model_name, contents=prompt)
                    match = re.search(r'\{.*\}', res.text, re.DOTALL)
                    if match:
                        macro_payload['ai_analysis'] = json.loads(match.group(0))
                        macro_payload['ai_analysis']['calculated_stage'] = regime_packet["stage_candidate"]
                        print(f"✅ AI 格式轉換成功！(使用模型: {model_name})")
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠️ Gemini AI 格式轉換失敗: {e}", flush=True)

    print("🚀 正在同步總經數據至 Supabase...", flush=True)
    target_id = 1
    existing = supabase.table("portfolio_db").select("id").limit(1).execute()
    if existing.data:
        supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", target_id).execute()
    else:
        supabase.table("portfolio_db").insert({"id": target_id, "macro_meta": macro_payload}).execute()

except Exception as e:
    print(f"🔥 總經數據處理致命錯誤:\n{traceback.format_exc()}", flush=True)
    raise e

# ==========================================
# 3. 股票多因子管線與最佳化
# ==========================================
print("\n⏳ 接著開始執行股票多因子管線與最佳化...", flush=True)

def get_sheet_prices(url_str):
    if not url_str:
        return {}
    try:
        clean_url = re.sub(r'\[.*?\]\((.*?)\)', r'', url_str)
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', clean_url)
        gid_match = re.search(r'[#&?]gid=([0-9]+)', clean_url)
        if not match:
            return {}
        csv_url = "https://docs.google.com/spreadsheets/d/" + match.group(1) + "/gviz/tq?tqx=out:csv&gid=" + (gid_match.group(1) if gid_match else '0')

        response = requests.get(csv_url, timeout=10)
        df = pd.read_csv(io.StringIO(response.text), header=None)
        price_map = {}
        for _, row in df.iterrows():
            if len(row) >= 2 and pd.notna(row[0]) and pd.notna(row[1]):
                ticker = str(row[0]).strip().upper()
                try:
                    price = float(str(row[1]).replace(',', ''))
                    price_map[ticker] = price
                    if ':' in ticker:
                        price_map[ticker.split(':')[1].strip()] = price
                except Exception as e:
                    print(f"⚠️ Google Sheet 報價解析失敗 ({ticker}): {e}", flush=True)
        return price_map
    except Exception as e:
        print(f"⚠️ Google Sheet 報價抓取失敗: {e}", flush=True)
        return {}

def get_optimal_weights(returns_df, stock_meta, min_wt=0.03, max_wt=0.20):
    num_assets = len(returns_df.columns)
    if num_assets == 0: return {}
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252 + np.eye(num_assets) * 1e-6 
    
    if min_wt * num_assets > 1.0: return {col: 1.0/num_assets for col in returns_df.columns}

    crypto_indices, low_risk_indices, tw_and_fund_indices = [], [], []
    for i, ticker in enumerate(returns_df.columns):
        meta = stock_meta.get(ticker, {})
        cat, risk = str(meta.get("category", "")).lower(), str(meta.get("risk", "")).lower()
        if "加密" in cat or "btc" in ticker.lower() or "eth" in ticker.lower(): crypto_indices.append(i)
        if risk == "low" or "低風險" in risk: low_risk_indices.append(i)
        if "台股" in cat or "基金" in cat: tw_and_fund_indices.append(i)

    def neg_sharpe(w): return -(np.sum(mean_returns * w) - 0.02) / np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))) + 1e-4 * np.sum(w**2)

    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    if crypto_indices and (num_assets - len(crypto_indices)) * max_wt >= 0.80: constraints.append({'type': 'ineq', 'fun': lambda x: 0.20 - np.sum(x[crypto_indices])})
    if low_risk_indices and (num_assets - len(low_risk_indices)) * max_wt >= 0.85: constraints.append({'type': 'ineq', 'fun': lambda x: 0.15 - np.sum(x[low_risk_indices])})
    if tw_and_fund_indices and (num_assets - len(tw_and_fund_indices)) * max_wt >= 0.85: constraints.append({'type': 'ineq', 'fun': lambda x: 0.15 - np.sum(x[tw_and_fund_indices])})

    bounds = tuple((min_wt, max_wt) for _ in range(num_assets))
    res = sco.minimize(neg_sharpe, np.array(num_assets * [1./num_assets]), method='SLSQP', bounds=bounds, constraints=constraints, options={'maxiter': 1000})
    return dict(zip(returns_df.columns, np.round(res.x, 4))) if res.success else dict(zip(returns_df.columns, np.round(np.array(num_assets * [1./num_assets]), 4)))

try:
    portfolio_resp = supabase.table("portfolio_db").select("*").limit(1).execute()
    if portfolio_resp.data:
        db_record = portfolio_resp.data[0]
        stock_meta, ledger_data = db_record.get("stock_meta", {}), db_record.get("ledger_data", [])
        ledger_tickers = [str(tx["ticker"]).strip().upper() for tx in ledger_data if tx.get("ticker")]
        all_tickers = list(set(list(stock_meta.keys()) + ledger_tickers))
        for t in all_tickers:
            if t not in stock_meta: stock_meta[t] = {}

        print("📊 正在從 Google Sheet 抓取自訂報價...", flush=True)
        sheet_prices = get_sheet_prices(db_record.get("settings", {}).get("sheetUrl", ""))
        
        if all_tickers:
            tw_bench, us_bench = "^TWII", "SPY"
            download_list, yf_tickers = [tw_bench, us_bench], []

            for t in all_tickers:
                target = map_to_yf_ticker(t, tw_bench=tw_bench)
                yf_tickers.append(target)
                if target and target not in download_list:
                    download_list.append(target)

            print(f"⏳ 正在向 Yahoo Finance 請求 {len(download_list)} 檔標的歷史資料...", flush=True)
            prices_df = safe_download_close(download_list, period="1y", progress=False)
            returns = prices_df.pct_change().dropna()

            print("⚖️ 正在過濾真實庫存標的...", flush=True)
            current_shares = {}
            for tx in ledger_data:
                t = str(tx.get("ticker", "")).strip().upper()
                if not t: continue
                current_shares[t] = current_shares.get(t, 0) + (float(tx.get("shares", 0)) * (-1 if str(tx.get("type", "buy")).lower() in ["sell", "賣出"] else 1))

            active_tickers = [t for t, s in current_shares.items() if s > 0.0001]
            ticker_to_yf = dict(zip(all_tickers, yf_tickers))
            valid_investable = [yf_t for t in active_tickers if (yf_t := ticker_to_yf.get(t)) and yf_t in returns.columns and yf_t not in [tw_bench, us_bench]]
            
            print(f"✅ 篩選完成：庫存共有 {len(valid_investable)} 檔標的進入最佳化引擎。")

            target_weights = {}
            if valid_investable:
                num_assets = len(valid_investable)
                dynamic_min = 0.0 if num_assets < 5 else min(0.03, 0.9 / num_assets)
                print(f"🧠 啟動機構級最佳化引擎 (限制 {dynamic_min*100:.0f}%~20%)...", flush=True)
                target_weights = get_optimal_weights(returns[valid_investable], stock_meta, min_wt=dynamic_min, max_wt=1.0 if num_assets < 5 else 0.20)
                
                # ==========================================
                # 🌟 終極升級：跨資產 8 因子模型 (FF6 + TW + Crypto)
                # ==========================================
                print("🧠 啟動跨資產 8 因子模型 (FF6 + TW_Mkt + Crypto) 迴歸引擎...", flush=True)
                try:
                    import statsmodels.api as sm
                    domain_kf = "https://mba.tuck.dartmouth.edu"
                    ff5_url = domain_kf + "/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
                    mom_url = domain_kf + "/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip"
                    
                    def parse_french_csv(content):
                        with zipfile.ZipFile(io.BytesIO(content)) as z:
                            with z.open(z.namelist()[0]) as f:
                                lines = [line.decode('utf-8', errors='ignore') for line in f.readlines()]
                                start_idx = next((i - 1 for i, line in enumerate(lines) if (line.strip().startswith('19') or line.strip().startswith('20')) and ',' in line), 0)
                                z.open(z.namelist()[0]).seek(0)
                                df = pd.read_csv(z.open(z.namelist()[0]), skiprows=start_idx, index_col=0)
                                df.index = pd.to_datetime(df.index.astype(str).str.strip(), format='%Y%m%d', errors='coerce')
                                df.columns = df.columns.str.strip()
                                return df.dropna().apply(pd.to_numeric, errors='coerce').dropna() / 100.0

                    ff5_data = parse_french_csv(requests.get(ff5_url, timeout=15).content)
                    mom_data = parse_french_csv(requests.get(mom_url, timeout=15).content)
                    ff_data = pd.concat([ff5_data, mom_data], axis=1).dropna()
                    
                    # 🌟 新增：獨立抓取台股大盤與比特幣資料作為客製化因子
                    custom_factors_df = safe_download_close(["^TWII", "BTC-USD"], period="2y", progress=False).pct_change().dropna()
                    # 確保欄位名稱正確
                    if "^TWII" in custom_factors_df.columns and "BTC-USD" in custom_factors_df.columns:
                        custom_factors = custom_factors_df[["^TWII", "BTC-USD"]].rename(columns={"^TWII": "TW_Mkt", "BTC-USD": "Crypto"})
                    else:
                        custom_factors = pd.DataFrame(0, index=ff_data.index, columns=["TW_Mkt", "Crypto"])

                    if len(returns) > 30:
                        port_weights = []
                        total_shares = sum([current_shares.get(t, 0) for t in active_tickers])
                        if total_shares > 0:
                            for yt in valid_investable:
                                orig_t = list(ticker_to_yf.keys())[list(ticker_to_yf.values()).index(yt)]
                                port_weights.append(current_shares.get(orig_t, 0) / total_shares)
                                
                            daily_port_return = returns[valid_investable].dot(np.array(port_weights))
                            daily_port_return.index = pd.to_datetime(daily_port_return.index).tz_localize(None)
                            daily_port_return.name = 'Port_Ret'

                            # 🌟 將所有資料降頻為「週報酬 (Weekly)」吸收時差與假日錯位
                            weekly_port = daily_port_return.resample('W-FRI').apply(lambda x: (1 + x).prod() - 1)
                            weekly_ff = ff_data.resample('W-FRI').apply(lambda x: (1 + x).prod() - 1)
                            weekly_custom = custom_factors.resample('W-FRI').apply(lambda x: (1 + x).prod() - 1)
                            
                            aligned_data = pd.concat([weekly_port, weekly_ff, weekly_custom], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
                            
                            if len(aligned_data) > 10:
                                # 計算客製化因子的超額報酬 (扣除無風險利率 RF)
                                aligned_data['TW_Mkt_RF'] = aligned_data['TW_Mkt'] - aligned_data['RF']
                                aligned_data['Crypto_RF'] = aligned_data['Crypto'] - aligned_data['RF']
                                
                                Y = (aligned_data['Port_Ret'] - aligned_data['RF']).astype(float)
                                X = sm.add_constant(aligned_data[['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'Mom', 'TW_Mkt_RF', 'Crypto_RF']]).astype(float)
                                
                                results = sm.OLS(Y, X).fit()
                                macro_payload["fama_french"] = {
                                    "alpha": float(round(results.params['const'] * 52 * 100, 2)),
                                    "mkt_beta": float(round(results.params['Mkt-RF'], 2)),
                                    "smb": float(round(results.params['SMB'], 2)),
                                    "hml": float(round(results.params['HML'], 2)),
                                    "rmw": float(round(results.params['RMW'], 2)),
                                    "cma": float(round(results.params['CMA'], 2)),
                                    "wml": float(round(results.params['Mom'], 2)),
                                    "tw_mkt": float(round(results.params.get('TW_Mkt_RF', 0), 2)), # 🌟 台股因子
                                    "crypto": float(round(results.params.get('Crypto_RF', 0), 2)), # 🌟 加密貨幣因子
                                    "r_squared": float(round(results.rsquared, 2))
                                }
                                print(f"✅ 8因子運算成功: R²={results.rsquared:.2f}, TW_β={results.params.get('TW_Mkt_RF', 0):.2f}, Crypto_β={results.params.get('Crypto_RF', 0):.2f}")
                                supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", target_id).execute()
                except Exception as e: print(f"⚠️ 8因子迴歸失敗: {e}", flush=True)

            print("🧠 開始計算各別標的風險參數並寫入資料庫...", flush=True)
            for i, original_ticker in enumerate(all_tickers):
                yf_ticker = yf_tickers[i]
                if original_ticker in sheet_prices: stock_meta[original_ticker]["last_price"] = sheet_prices[original_ticker]
                
                if yf_ticker in returns.columns:
                    stock_close = prices_df[yf_ticker].dropna()
                    if len(stock_close) < 60: continue
                    
                    bench = tw_bench if yf_ticker.endswith(".TW") else us_bench
                    aligned = pd.concat([returns[yf_ticker], returns[bench]], axis=1).dropna()
                    if len(aligned) < 30: continue
                    
                    bench_var = aligned.iloc[:,1].var()
                    beta_val = round(aligned.iloc[:,0].cov(aligned.iloc[:,1]) / bench_var if bench_var > 0 else 1.0, 2)
                    std_val = round(np.sqrt(aligned.iloc[:,0].var() * 252) * 100, 2)
                    tw_val = float(target_weights.get(yf_ticker, 0.0))
                    
                    stock_meta[original_ticker].update({
                        "beta": beta_val,
                        "std": std_val,
                        "rsi": round(ta.rsi(stock_close).iloc[-1] if ta.rsi(stock_close) is not None else 50.0, 2), 
                        "macd_h": round(ta.macd(stock_close).iloc[-1, 1] if ta.macd(stock_close) is not None else 0.0, 4),
                        "target_weight": tw_val
                    })
                    print(f"✅ [{original_ticker}] 更新 -> Beta: {beta_val:.2f}, Std: {std_val:.1f}%, 目標權重: {tw_val*100:.2f}%")

            supabase.table("portfolio_db").update({"stock_meta": stock_meta}).eq("id", target_id).execute()

            print("\n⚖️ 啟動自動再平衡引擎：計算目標權重落差與交易訊號...", flush=True)
            portfolio_value, asset_values, rebalance_signals = 0.0, {}, []
            for t in all_tickers:
                shares = current_shares.get(t, 0)
                lp = stock_meta.get(t, {}).get("last_price", 0.0)
                if lp == 0.0 and yf_tickers and yf_tickers[all_tickers.index(t)] in prices_df.columns:
                    lp = float(prices_df[yf_tickers[all_tickers.index(t)]].dropna().iloc[-1])
                val = max(0, shares * lp)
                asset_values[t], portfolio_value = val, portfolio_value + val

            print(f"💰 當前投資組合總淨值估算: {portfolio_value:,.2f}")
            if portfolio_value > 0:
                for t in all_tickers:
                    tw = stock_meta.get(t, {}).get("target_weight", 0.0)
                    cw = asset_values.get(t, 0.0) / portfolio_value
                    if abs(tw - cw) > 0.01:
                        action_str = "BUY (加碼)" if tw > cw else "SELL (減碼)"
                        print(f"   [{t}] {action_str} -> 目標: {tw*100:.1f}%, 當前: {cw*100:.1f}%")
                        rebalance_signals.append({"ticker": t, "action": action_str, "current_weight": f"{cw*100:.2f}%", "target_weight": f"{tw*100:.2f}%", "delta_weight": f"{(tw-cw)*100:.2f}%", "trade_amount": round((portfolio_value * tw) - asset_values.get(t, 0.0), 2)})

            if rebalance_signals and GEMINI_API_KEY:
                print("🤖 喚醒 AI 撰寫再平衡交易執行報告...", flush=True)
                try:
                    rebalance_prompt = f"""
                    [SYSTEM_DIRECTIVE]
                    Task: Generate a high-conviction, logically flawless rebalance execution plan.
                    Tone: Institutional Risk Manager & Quant Trader. Coldly rational, strictly data-driven.
                    Language: STRICTLY Traditional Chinese (繁體中文). ONLY JSON output.

                    [LOGICAL_GUARDRAILS]
                    - CRITICAL: DO NOT confuse "Sector Rotation / Capital Efficiency" with "Hedging".
                    - TRUE HEDGING means moving to cash, bonds, or negative-beta assets.
                    - DO NOT suggest buying high-beta, risk-on assets (like Crypto or Tech stocks) as a "hedge" against market risks.
                    - If the trades involve moving capital to high-beta assets, explicitly frame it as "Risk-On Rotation", "Pursuing Alpha", or "Capitalizing on Momentum", NEVER as "Hedging".

                    [INPUT_DATA]
                    Macro Summary: {macro_payload.get('ai_analysis', {}).get('summary', '無')}
                    Execution List: {json.dumps(rebalance_signals, ensure_ascii=False)}

                    [OUTPUT_SCHEMA]
                    {{
                        "execution_summary": "<string_1_sentence_rationale_linking_macro_to_trades_in_traditional_chinese_with_strict_financial_logic>",
                        "priority_trades": [ {{"ticker": "<string>", "reason": "<string_short_rationale>"}} ]
                    }}
                    """
                    rb_match = re.search(r'\{.*\}', client.models.generate_content(model="gemini-3-flash-preview", contents=rebalance_prompt).text, re.DOTALL)
                    if rb_match:
                        supabase.table("portfolio_db").update({"rebalance_meta": {"signals": rebalance_signals, "ai_execution_plan": json.loads(rb_match.group(0))}}).eq("id", target_id).execute()
                        print("✅ 再平衡交易清單與 AI 執行報告已成功同步至 Supabase！")
                except Exception as e: print(f"⚠️ AI 執行報告生成失敗: {e}")

except Exception as e:
    print(f"🔥 股票管線致命錯誤:\n{traceback.format_exc()}", flush=True)
    raise e
