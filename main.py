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

# 關閉煩人的 pandas 警告
warnings.filterwarnings('ignore')

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
# 🌟 1.5 總經規則引擎 (Rule-based Deterministic Engine)
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

def score_yield_curve(v):
    v = _num(v)
    if v is None: return 0
    if v <= -0.5: return -2
    if v <= 0: return -1
    if v <= 1: return 1
    return 2

def score_hy_spread(v):
    v = _num(v)
    if v is None: return 0
    if v > 5: return -2
    if v >= 3: return -1
    if v >= 1.5: return 1
    return 2

def score_vix(v, z_score=0):
    v = _num(v)
    z = _num(z_score, 0)
    if v is None: return 0
    if v > 30 or z > 2.5: return -2
    if v >= 20 or z > 1.5: return -1
    if v >= 12: return 1
    return 2

def score_dxy(v):
    v = _num(v)
    if v is None: return 0
    if v > 105: return -1
    if v < 95: return 1
    return 0

def score_btc_mom(v):
    v = _num(v)
    if v is None: return 0
    if v > 10: return 2
    if v >= 0: return 1
    if v >= -10: return -1
    return -2

def score_oil(v):
    v = _num(v)
    if v is None: return 0
    if v > 90: return -1
    if v < 60: return 1
    return 0

def score_copper_gold_ratio(v):
    v = _num(v)
    if v is None: return 0
    if v >= 0.25: return 1
    if v >= 0.15: return 0
    return -1

def score_move(v, z_score=0):
    v = _num(v)
    z = _num(z_score, 0)
    if v is None: return 0
    if v > 120 or z > 2.5: return -2 
    if v >= 100 or z > 1.5: return -1 
    if v >= 80: return 1  
    return 2 

def score_iwm_spy(v):
    v = _num(v)
    if v is None: return 0
    if v > 3: return 2   
    if v >= 0: return 1  
    if v >= -3: return -1 
    return -2 

def score_xlu_xly(v):
    v = _num(v)
    if v is None: return 0
    if v > 3: return -2   
    if v >= 0: return -1  
    if v >= -3: return 1  
    return 2 

def score_vxn(v, z_score=0):
    v = _num(v)
    z = _num(z_score, 0)
    if v is None: return 0
    if v > 35 or z > 2.5: return -2 
    if v >= 25 or z > 1.5: return -1
    if v >= 15: return 1
    return 2

def score_vvix(v, z_score=0):
    v = _num(v)
    z = _num(z_score, 0)
    if v is None: return 0
    if v > 115 or z > 2.5: return -2 
    if v >= 100 or z > 1.5: return -1
    if v >= 80: return 1
    return 2

def score_hyg_tlt(v):
    v = _num(v)
    if v is None: return 0
    if v < -3: return -2 
    if v < 0: return -1
    if v < 3: return 1
    return 2 

def score_dbc_mom(v):
    v = _num(v)
    if v is None: return 0
    if v > 8: return -2 
    if v > 3: return -1
    if v > -5: return 1 
    return 2

def score_soxx_spy(v):
    v = _num(v)
    if v is None: return 0
    if v > 5: return 2 
    if v > 0: return 1
    if v > -3: return -1
    return -2 

def score_liquidity(v):
    v = _num(v)
    if v is None: return 0
    if v > 0.5: return -2 
    if v > 0.2: return -1
    if v > -0.1: return 1
    return 2 

def score_rsp_spy(v):
    v = _num(v)
    if v is None: return 0
    if v > 2: return 2  
    if v > 0: return 1
    if v > -2: return -1
    return -2 

def score_kre_spy(v):
    v = _num(v)
    if v is None: return 0
    if v > 1: return 1  
    if v < -5: return -2 
    if v < -2: return -1
    return 0

def score_aud_jpy(v):
    v = _num(v)
    if v is None: return 0
    if v > 3: return 2  
    if v > 0: return 1
    if v < -3: return -2 
    return -1

def score_pcr(v, z_score=0):
    v = _num(v)
    z = _num(z_score, 0)
    if v is None: return 0
    if v > 1.2 or z > 2.0: return -2 
    if v > 1.0 or z > 1.0: return -1
    if v < 0.8: return 2  
    return 1

def score_sys_corr(v):
    v = _num(v)
    if v is None: return 0
    if v > 0.85: return -3 
    if v > 0.70: return -1 
    if v < 0.30: return 2  
    return 0

def choose_stage(scores):
    vals = list(scores.values())
    pos = sum(1 for s in vals if s > 0)
    neg = sum(1 for s in vals if s < 0)
    total = sum(vals)

    if pos >= 3 and neg >= 3: return "mixed"
    if scores["yield_curve"] <= -1 and scores["hy_spread"] <= -1 and scores["vix"] <= -1: return "recession_risk"
    if scores["dxy"] <= -1 and scores["hy_spread"] <= -1: return "tight_liquidity"
    
    if (scores.get("oil_price", 0) < 0 or scores.get("dbc_mom", 0) < 0) and (scores["yield_curve"] <= 0 or scores["vix"] <= 0): 
        return "stagflation"
        
    if scores["yield_curve"] > 0 and scores["hy_spread"] > 0 and scores["vix"] > 0 and scores["btc_1m_mom"] > 0: return "expansion"

    if total >= 10: return "expansion"
    if 3 <= total <= 9: return "neutral"
    if -5 <= total <= 2: return "tight_liquidity"
    if -12 <= total <= -6: return "recession_risk"
    if total <= -13: return "stagflation"
    return "mixed"

def build_regime_packet(macro_payload):
    raw = {
        "yield_curve": macro_payload.get("yield_curve"),
        "hy_spread": macro_payload.get("hy_spread"),
        "vix": macro_payload.get("vix"),
        "vix_z": macro_payload.get("vix_z"), 
        "dxy": macro_payload.get("dxy"),
        "btc_1m_mom": macro_payload.get("btc_1m_mom"),
        "oil_price": macro_payload.get("oil_price"),
        "copper_gold_ratio": macro_payload.get("copper_gold_ratio"),
        "move_index": macro_payload.get("move_index"),
        "move_z": macro_payload.get("move_z"), 
        "iwm_spy_mom": macro_payload.get("iwm_spy_mom"),
        "xlu_xly_mom": macro_payload.get("xlu_xly_mom"),
        "vxn": macro_payload.get("vxn"),
        "vxn_z": macro_payload.get("vxn_z"), 
        "vvix": macro_payload.get("vvix"),
        "vvix_z": macro_payload.get("vvix_z"), 
        "hyg_tlt_mom": macro_payload.get("hyg_tlt_mom"),
        "dbc_mom": macro_payload.get("dbc_mom"),
        "soxx_spy_mom": macro_payload.get("soxx_spy_mom"),
        "liquidity_spread": macro_payload.get("liquidity_spread"),
        "rsp_spy_mom": macro_payload.get("rsp_spy_mom"),
        "kre_spy_mom": macro_payload.get("kre_spy_mom"),
        "aud_jpy_mom": macro_payload.get("aud_jpy_mom"),
        "put_call_ratio": macro_payload.get("put_call_ratio"),
        "pcr_z": macro_payload.get("pcr_z"), 
        "sys_corr": macro_payload.get("sys_corr") 
    }

    scores = {
        "yield_curve": score_yield_curve(raw["yield_curve"]),
        "hy_spread": score_hy_spread(raw["hy_spread"]),
        "vix": score_vix(raw["vix"], raw["vix_z"]),
        "dxy": score_dxy(raw["dxy"]),
        "btc_1m_mom": score_btc_mom(raw["btc_1m_mom"]),
        "oil_price": score_oil(raw["oil_price"]),
        "copper_gold_ratio": score_copper_gold_ratio(raw["copper_gold_ratio"]),
        "move_index": score_move(raw["move_index"], raw["move_z"]),
        "iwm_spy_mom": score_iwm_spy(raw["iwm_spy_mom"]),
        "xlu_xly_mom": score_xlu_xly(raw["xlu_xly_mom"]),
        "vxn": score_vxn(raw["vxn"], raw["vxn_z"]),
        "vvix": score_vvix(raw["vvix"], raw["vvix_z"]),
        "hyg_tlt_mom": score_hyg_tlt(raw["hyg_tlt_mom"]),
        "dbc_mom": score_dbc_mom(raw["dbc_mom"]),
        "soxx_spy_mom": score_soxx_spy(raw["soxx_spy_mom"]),
        "liquidity_spread": score_liquidity(raw["liquidity_spread"]),
        "rsp_spy_mom": score_rsp_spy(raw["rsp_spy_mom"]),
        "kre_spy_mom": score_kre_spy(raw["kre_spy_mom"]),
        "aud_jpy_mom": score_aud_jpy(raw["aud_jpy_mom"]),
        "put_call_ratio": score_pcr(raw["put_call_ratio"], raw["pcr_z"]),
        "sys_corr": score_sys_corr(raw["sys_corr"])
    }

    stage = choose_stage(scores)
    total_score = sum(scores.values())

    used_fields = list(scores.keys())
    valid_count = sum(1 for k in used_fields if not _is_missing(raw[k]))
    completeness = valid_count / len(used_fields)
    confidence = min(1.0, abs(total_score) / 20.0) * (0.6 + 0.4 * completeness)
    confidence = round(float(confidence), 3)

    return {
        "raw": raw,
        "scores": scores,
        "stage_candidate": stage,
        "total_score": total_score,
        "confidence_hint": confidence
    }

# ==========================================
# 🌟 2. 第一階段：總經與市場參數自動化抓取
# ==========================================
print("🌍 啟動量化大腦：開始透過 Yahoo API 抓取市場參數...", flush=True)

def calc_z_score(series):
    if series.empty or len(series) < 20: return 0.0
    mean = series.mean()
    std = series.std()
    if std == 0: return 0.0
    return (series.iloc[-1] - mean) / std

try:
    print("   ⏳ 正在抓取公債殖利率...", flush=True)
    try:
        bonds = yf.download(["^TNX", "^IRX"], period="1mo", progress=False)["Close"]
        y10_series = bonds["^TNX"] if isinstance(bonds, pd.DataFrame) else bonds
        y3m_series = bonds["^IRX"] if isinstance(bonds, pd.DataFrame) else bonds
        
        y10_clean = y10_series.dropna()
        y10 = float(y10_clean.iloc[-1]) if not y10_clean.empty else 4.2 
        
        y3m_clean = y3m_series.dropna()
        y3m = float(y3m_clean.iloc[-1]) if not y3m_clean.empty else 5.0 
    except Exception as e:
        print(f"⚠️ 公債殖利率抓取失敗，使用預設值: {e}")
        y10, y3m = 4.2, 5.0

    print("   ⏳ 正在計算信用利差...", flush=True)
    try: hyg_yield = yf.Ticker("HYG").info.get('yield', 0.05) * 100 
    except: hyg_yield = 7.5
    hy_spread = max(0.1, hyg_yield - y10)

    print("   ⏳ 正在計算加密貨幣動能...", flush=True)
    try:
        btc_data = yf.download("BTC-USD", period="1mo", progress=False)["Close"]
        if isinstance(btc_data, pd.DataFrame): btc_data = btc_data.iloc[:, 0]
        btc_clean = btc_data.dropna()
        btc_mom = ((btc_clean.iloc[-1] / btc_clean.iloc[0]) - 1) * 100 if len(btc_clean) > 1 else 0.0
    except: btc_mom = 0.0

    print("   ⏳ 正在計算 SPY 長期報酬與短期波動...", flush=True)
    try:
        spy = yf.download("SPY", period="10y", progress=False)["Close"]
        if isinstance(spy, pd.DataFrame): spy = spy.iloc[:, 0]
        spy_clean = spy.dropna()
        spy_cagr = ((spy_clean.iloc[-1] / spy_clean.iloc[0]) ** (1/10)) - 1 if len(spy_clean) > 10 else 0.10
        spy_vol = spy_clean.tail(252).pct_change().std() * np.sqrt(252) if len(spy_clean) > 10 else 0.15
    except: spy_cagr, spy_vol = 0.10, 0.15

    print("   ⏳ 正在抓取跨資產期貨、情緒指標、PCR與AUD/JPY (1年期歷史計算Z-Score)...", flush=True)
    try:
        vix_family = yf.download(["^VIX", "^VXN", "^VVIX"], period="1y", progress=False)["Close"]
        if isinstance(vix_family, pd.Series): vix_family = vix_family.to_frame()
        
        vix_s = vix_family["^VIX"].dropna() if "^VIX" in vix_family.columns else pd.Series([20.0])
        vxn_s = vix_family["^VXN"].dropna() if "^VXN" in vix_family.columns else pd.Series([22.0])
        vvix_s = vix_family["^VVIX"].dropna() if "^VVIX" in vix_family.columns else pd.Series([90.0])
        
        vix, vix_z = float(vix_s.iloc[-1]), float(calc_z_score(vix_s))
        vxn, vxn_z = float(vxn_s.iloc[-1]), float(calc_z_score(vxn_s))
        vvix, vvix_z = float(vvix_s.iloc[-1]), float(calc_z_score(vvix_s))
        
        dxy = float(yf.Ticker("DX-Y.NYB").history(period="5d")['Close'].dropna().iloc[-1])
        gold = float(yf.Ticker("GC=F").history(period="5d")['Close'].dropna().iloc[-1])
        copper = float(yf.Ticker("HG=F").history(period="5d")['Close'].dropna().iloc[-1]) 
        oil = float(yf.Ticker("CL=F").history(period="5d")['Close'].dropna().iloc[-1])    
        copper_gold_ratio = (copper / gold) * 100 
    except Exception as e:
        print(f"⚠️ 情緒指標抓取失敗，使用預設值: {e}")
        vix, vxn, vvix, dxy, gold, copper, oil, copper_gold_ratio = 20.0, 22.0, 90.0, 100.0, 2000.0, 4.0, 75.0, 0.2
        vix_z, vxn_z, vvix_z = 0.0, 0.0, 0.0

    try:
        pcr_data = yf.Ticker("^PCR").history(period="1y")['Close'].dropna()
        pcr = float(pcr_data.iloc[-1]) if not pcr_data.empty else 1.0
        pcr_z = float(calc_z_score(pcr_data))
    except:
        print("⚠️ Put/Call Ratio (^PCR) 讀取失敗或無資料，預設為中性值 1.0")
        pcr, pcr_z = 1.0, 0.0

    try:
        aud_jpy_data = yf.download("AUDJPY=X", period="1mo", progress=False)["Close"]
        if isinstance(aud_jpy_data, pd.DataFrame): aud_jpy_data = aud_jpy_data.iloc[:, 0]
        aud_jpy_clean = aud_jpy_data.dropna()
        aud_jpy_mom = float(((aud_jpy_clean.iloc[-1] / aud_jpy_clean.iloc[0]) - 1) * 100) if len(aud_jpy_clean) > 1 else 0.0
    except:
        print("⚠️ AUD/JPY 抓取失敗，預設動能為 0.0")
        aud_jpy_mom = 0.0

    print("   ⏳ 正在抓取 MOVE 指數與板塊輪動指標...", flush=True)
    try:
        try:
            move_data = yf.Ticker("^MOVE").history(period="1y")['Close'].dropna()
            if move_data.empty: raise ValueError
            move_idx = float(move_data.iloc[-1])
            move_z = float(calc_z_score(move_data))
        except:
            tlt = yf.download("TLT", period="1y", progress=False)["Close"]
            if isinstance(tlt, pd.DataFrame): tlt = tlt.iloc[:, 0]
            tlt_vol = tlt.pct_change().rolling(20).std() * np.sqrt(252) * 100 * 5
            move_data = tlt_vol.dropna()
            move_idx = float(move_data.iloc[-1]) if not move_data.empty else 100.0
            move_z = float(calc_z_score(move_data))

        target_etfs = ["IWM", "SPY", "XLU", "XLY", "HYG", "TLT", "DBC", "SOXX", "BIL", "SHY", "RSP", "KRE"]
        etfs = yf.download(target_etfs, period="1mo", progress=False)["Close"]
        if isinstance(etfs, pd.Series): etfs = etfs.to_frame()
        
        def safe_mom(ticker1, ticker2=None):
            try:
                if ticker1 not in etfs.columns or etfs[ticker1].dropna().empty: 
                    return 0.0
                s1 = etfs[ticker1].dropna()
                if len(s1) < 2: return 0.0
                ret1 = (s1.iloc[-1] / s1.iloc[0]) - 1
                
                if ticker2:
                    if ticker2 not in etfs.columns or etfs[ticker2].dropna().empty: 
                        return 0.0
                    s2 = etfs[ticker2].dropna()
                    if len(s2) < 2: return 0.0
                    ret2 = (s2.iloc[-1] / s2.iloc[0]) - 1
                    return float((ret1 - ret2) * 100)
                else:
                    return float(ret1 * 100)
            except Exception as e:
                print(f"⚠️ {ticker1} 或 {ticker2} 動能計算錯誤: {e}")
                return 0.0

        iwm_spy_mom = safe_mom("IWM", "SPY")
        xlu_xly_mom = safe_mom("XLU", "XLY")
        hyg_tlt_mom = safe_mom("HYG", "TLT")
        soxx_spy_mom = safe_mom("SOXX", "SPY")
        dbc_mom = safe_mom("DBC")
        liquidity_spread = safe_mom("BIL", "SHY") 
        rsp_spy_mom = safe_mom("RSP", "SPY") 
        kre_spy_mom = safe_mom("KRE", "SPY") 

    except Exception as e:
        print(f"⚠️ 進階輪動指標抓取發生意外: {e}")
        move_idx, move_z, iwm_spy_mom, xlu_xly_mom, hyg_tlt_mom = 100.0, 0.0, 0.0, 0.0, 0.0
        dbc_mom, soxx_spy_mom, liquidity_spread, rsp_spy_mom, kre_spy_mom = 0.0, 0.0, 0.0, 0.0, 0.0

    print("   ⏳ 正在計算投資組合平均相關係數 (系統性風險)...", flush=True)
    try:
        response = supabase.table("portfolio_db").select("*").limit(1).execute()
        sys_corr = 0.3 
        corr_matrix = {}
        current_shares = {}
        
        if response.data:
            db_record = response.data[0]
            ledger_data = db_record.get("ledger_data", [])
            for tx in ledger_data:
                t = str(tx.get("ticker", "")).strip().upper()
                if not t: continue
                s = float(tx.get("shares", 0))
                if str(tx.get("type", "buy")).lower() in ["sell", "賣出"]: s = -s
                current_shares[t] = current_shares.get(t, 0) + s
                
            active_tickers = [t for t, s in current_shares.items() if s > 0.0001]
            
            if len(active_tickers) > 1:
                tw_bench = "^TWII"
                proxy_map = {"統一奔騰": "00981A.TW", "安聯台灣科技": "0052.TW", "加密貨幣": "BTC-USD"}
                mapped_tickers = []
                for t in active_tickers:
                    t_clean = t.strip().upper()
                    if t_clean in proxy_map: mapped_tickers.append(proxy_map[t_clean])
                    elif bool(re.search(r'[\u4e00-\u9fff]', t_clean)): mapped_tickers.append(tw_bench)
                    elif re.match(r'^\d+[a-zA-Z]*$', t_clean): mapped_tickers.append(f"{t_clean}.TW")
                    else: mapped_tickers.append(t_clean)
                
                mapped_tickers = list(set(mapped_tickers))
                
                port_df = yf.download(mapped_tickers, period="3mo", progress=False)["Close"]
                if isinstance(port_df, pd.Series): port_df = port_df.to_frame(name=mapped_tickers[0])
                
                port_returns = port_df.pct_change().dropna()
                corr_df = port_returns.corr()
                
                mask = np.triu(np.ones_like(corr_df, dtype=bool), k=1)
                raw_sys_corr = float(corr_df.where(mask).mean().mean())
                if np.isnan(raw_sys_corr) or np.isinf(raw_sys_corr):
                    sys_corr = 0.0
                else:
                    sys_corr = raw_sys_corr
                
                corr_matrix = corr_df.replace([np.inf, -np.inf], np.nan).fillna(0.0).to_dict()
    except Exception as e:
        print(f"⚠️ 相關係數計算失敗: {e}")
        sys_corr = 0.3
        corr_matrix = {}

    macro_payload = {
        "yield_10y": float(round(y10, 2)), "yield_2y": float(round(y3m, 2)), "yield_curve": float(round(y10 - y3m, 2)), 
        "hy_spread": float(round(hy_spread, 2)), "btc_1m_mom": float(round(btc_mom, 2)), "market_rf": float(round(y10, 2)),
        "market_rm": float(round(spy_cagr * 100, 2)), "market_sm": float(round(spy_vol * 100, 2)),
        "vix": float(round(vix, 2)), "vix_z": float(round(vix_z, 2)),
        "vxn": float(round(vxn, 2)), "vxn_z": float(round(vxn_z, 2)),
        "vvix": float(round(vvix, 2)), "vvix_z": float(round(vvix_z, 2)),
        "dxy": float(round(dxy, 2)), "gold_price": float(round(gold, 2)), "oil_price": float(round(oil, 2)), 
        "copper_gold_ratio": float(round(copper_gold_ratio, 4)), 
        "move_index": float(round(move_idx, 2)), "move_z": float(round(move_z, 2)),
        "iwm_spy_mom": float(round(iwm_spy_mom, 2)), "xlu_xly_mom": float(round(xlu_xly_mom, 2)),
        "hyg_tlt_mom": float(round(hyg_tlt_mom, 2)), "dbc_mom": float(round(dbc_mom, 2)),
        "soxx_spy_mom": float(round(soxx_spy_mom, 2)), "liquidity_spread": float(round(liquidity_spread, 2)),
        "rsp_spy_mom": float(round(rsp_spy_mom, 2)), "kre_spy_mom": float(round(kre_spy_mom, 2)),
        "aud_jpy_mom": float(round(aud_jpy_mom, 2)), 
        "put_call_ratio": float(round(pcr, 2)), "pcr_z": float(round(pcr_z, 2)),
        "sys_corr": float(round(sys_corr, 2)),
        "corr_matrix": corr_matrix 
    }
    
    # ==========================================
    # 🧠 Gemini AI 總結與前端格式化轉換
    # ==========================================
    regime_packet = build_regime_packet(macro_payload)
    print(f"🤖 喚醒 Gemini AI 進行格式化 (內部判定階段: {regime_packet['stage_candidate']})...", flush=True)
    
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            model_pipeline = ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-3.1-pro-preview", "gemini-2.5-pro", "gemini-2.0-flash"]
                
            prompt = f"""
            [SYSTEM_DIRECTIVE]
            Task: Transform deterministic macro signals into aggressive tactical trading metadata.
            Tone: High-Alpha Quant, Contrarian, Extreme Aggressive (Risk = Opportunity). Focus deeply on Z-Scores (statistical extremes) and `sys_corr` (systemic liquidation risk).
            Language: MUST strictly output all text values in TRADITIONAL CHINESE (繁體中文).
            Constraints: 
            - ZERO conversational text.
            - ZERO Markdown formatting (no ```json). 
            - Output RAW JSON strictly matching [OUTPUT_SCHEMA].
            - ZERO external data hallucination. MUST strictly ground logic in [INPUT_DATA].

            [TRANSFORMATION_RULES]
            1. STAGE: Translate `stage_candidate` to Traditional Chinese. 
               expansion -> "擴張期"
               recession_risk -> "衰退風險"
               stagflation -> "滯脹期"
               tight_liquidity -> "流動性緊縮"
               mixed -> "混合/震盪期"
            2. SUMMARY: 1 sentence. **MUST START WITH "[目前總經形勢: 翻譯後的STAGE]"**. Map the stage and extreme Z-scores to a max-alpha allocation strategy.
               *CRITICAL*: If `sys_corr` > 0.8, you MUST declare a systemic liquidation event (e.g., 雷曼時刻降臨，分散投資失效).
            3. DETAILS.TITLE: Translate the metric name to Traditional Chinese (e.g., "科技恐慌 (VXN Z-Score)", "系統性風險 (平均相關性)").
            4. DETAILS.DESC: Max 35 chars in Traditional Chinese. 
               *** CRITICAL DATA RULE ***: You MUST explicitly cite specific numeric values (especially Z-Scores if > 2.0 or < -2.0) from `raw` in every description. Combine the number with an actionable contrarian trigger. 
               (e.g., MUST output "VIX Z-Score={macro_payload.get('vix_z')} 極端異常，準備暴力反彈買點🔪").
            5. DETAILS.COLOR: "text-green-400" (momentum/buy/opportunity), "text-red-400" (tail-risk/hedge/sell/high correlation), "text-gray-400" (neutral).
            6. DETAILS.ICON: Single emoji (🔥, ⚡, 🚀, 🔪, 🛡️, 🩸, 🦅, 🐻).

            [INPUT_DATA]
            stage_candidate: {regime_packet["stage_candidate"]}
            total_score: {regime_packet["total_score"]}
            confidence: {regime_packet["confidence_hint"]}
            scores: {json.dumps(regime_packet["scores"], ensure_ascii=False)}
            raw: {json.dumps(regime_packet["raw"], ensure_ascii=False)}

            [OUTPUT_SCHEMA]
            {{
              "summary": "<string_in_traditional_chinese>",
              "details": [
                {{
                  "icon": "<emoji>",
                  "color": "<string_tailwind_class>",
                  "title": "<string_metric_name_in_traditional_chinese>",
                  "desc": "<string_data_driven_insight_in_traditional_chinese>"
                }}
              ]
            }}
            """
            
            ai_success = False
            for model_name in model_pipeline:
                try:
                    response = client.models.generate_content(model=model_name, contents=prompt)
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if not json_match: raise ValueError("模型未回傳合法 JSON 結構")
                    
                    macro_payload['ai_analysis'] = json.loads(json_match.group(0))
                    macro_payload['ai_analysis']['calculated_stage'] = regime_packet["stage_candidate"]
                    print(f"✅ AI 格式轉換成功！(使用模型: {model_name})", flush=True)
                    ai_success = True
                    break
                except Exception as ai_e:
                    print(f"⚠️ {model_name} 執行失敗: {ai_e}，準備切換備援...", flush=True)
                    continue
            
            if not ai_success:
                print("❌ 所有 AI 模型皆無回應或解析失敗，跳過 AI 診斷。", flush=True)

        except Exception as e:
            print(f"🔥 AI 初始化發生錯誤: {e}", flush=True)

    # ==========================================
    # 💾 G. 寫入 Supabase (屬於第一階段總經管線)
    # ==========================================
    print("🚀 正在同步總經數據至 Supabase...", flush=True)
    existing = supabase.table("portfolio_db").select("id").limit(1).execute()
    target_id = existing.data[0]['id'] if existing.data else 1
    
    if existing.data:
        supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", target_id).execute()
    else:
        supabase.table("portfolio_db").insert({"id": target_id, "macro_meta": macro_payload}).execute()

except Exception as e:
    print(f"🔥 總經數據處理發生致命錯誤:\n{traceback.format_exc()}", flush=True)
    raise e

# ==========================================
# 📊 3. 第二階段：股票多因子管線與最佳化
# ==========================================
print("\n⏳ 接著開始執行股票多因子管線與最佳化...", flush=True)

def get_sheet_prices(url_str):
    if not url_str: return {}
    print("📊 正在從 Google Sheet 抓取自訂報價...", flush=True)
    try:
        # 🌟 修正 1：純字串處理，徹底拔除 Markdown 殘留
        clean_url = re.sub(r'\[.*?\]\((.*?)\)', r'\1', url_str)
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', clean_url)
        gid_match = re.search(r'[#&?]gid=([0-9]+)', clean_url)
        if not match: return {}
        
        sheet_id = match.group(1)
        gid = gid_match.group(1) if gid_match else '0'
        domain = "https://docs.google.com"
        path = "/spreadsheets/d/" + sheet_id + "/gviz/tq?tqx=out:csv&gid=" + gid
        csv_url = domain + path

        
        response = requests.get(csv_url, timeout=10)
        response.raise_for_status() 
        df = pd.read_csv(io.StringIO(response.text), header=None)
        
        price_map = {}
        for _, row in df.iterrows():
            if len(row) >= 2 and pd.notna(row[0]) and pd.notna(row[1]):
                ticker = str(row[0]).strip().upper()
                try:
                    price = float(str(row[1]).replace(',', ''))
                    price_map[ticker] = price
                    if ':' in ticker: price_map[ticker.split(':')[1].strip()] = price
                except: pass
        return price_map
    except Exception as e:
        print(f"⚠️ Sheet 報價讀取失敗:\n{traceback.format_exc()}", flush=True)
        return {}

def get_optimal_weights(returns_df, stock_meta, min_wt=0.03, max_wt=0.20):
    num_assets = len(returns_df.columns)
    if num_assets == 0: return {}
    
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252
    cov_matrix = cov_matrix + np.eye(num_assets) * 1e-6 
    risk_free_rate = 0.02 
    
    if min_wt * num_assets > 1.0:
        print("⚠️ 警告：最低權重總和超過 100%，將自動等權重分配")
        return {col: 1.0/num_assets for col in returns_df.columns}

    crypto_indices = []
    low_risk_indices = []
    tw_and_fund_indices = []

    for i, ticker in enumerate(returns_df.columns):
        meta = stock_meta.get(ticker, {})
        category = str(meta.get("category", "")).lower()
        risk = str(meta.get("risk", "")).lower()
        
        if "加密" in category or "btc" in ticker.lower() or "eth" in ticker.lower():
            crypto_indices.append(i)
        if risk == "low" or "低風險" in risk:
            low_risk_indices.append(i)
        
        if "台股" in category or "基金" in category:
            tw_and_fund_indices.append(i)

    def neg_sharpe_ratio(weights):
        p_ret = np.sum(mean_returns * weights)
        p_var = np.dot(weights.T, np.dot(cov_matrix, weights))
        p_vol = np.sqrt(p_var)
        l2_penalty = 1e-4 * np.sum(weights**2)
        return -(p_ret - risk_free_rate) / p_vol + l2_penalty

    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    
    if crypto_indices and (num_assets - len(crypto_indices)) * max_wt >= 0.80:
        constraints.append({'type': 'ineq', 'fun': lambda x: 0.20 - np.sum(x[crypto_indices])})
        
    if low_risk_indices and (num_assets - len(low_risk_indices)) * max_wt >= 0.85:
        constraints.append({'type': 'ineq', 'fun': lambda x: 0.15 - np.sum(x[low_risk_indices])})
        
    if tw_and_fund_indices and (num_assets - len(tw_and_fund_indices)) * max_wt >= 0.85:
        constraints.append({'type': 'ineq', 'fun': lambda x: 0.15 - np.sum(x[tw_and_fund_indices])})

    bounds = tuple((min_wt, max_wt) for _ in range(num_assets))
    init_guess = np.array(num_assets * [1. / num_assets])
    opts = {'ftol': 1e-6, 'disp': False, 'maxiter': 1000}

    optimized_result = sco.minimize(
        neg_sharpe_ratio, init_guess, method='SLSQP', bounds=bounds, constraints=constraints, options=opts
    )

    if not optimized_result.success:
        print(f"⚠️ SLSQP 最佳化失敗 ({optimized_result.message})，自動降級至 trust-constr 演算法...")
        from scipy.optimize import LinearConstraint
        A_eq = np.ones((1, num_assets))
        tc_constraints = [LinearConstraint(A_eq, [1], [1])] 
        
        if crypto_indices and (num_assets - len(crypto_indices)) * max_wt >= 0.80:
            A_crypto = np.zeros((1, num_assets))
            for idx in crypto_indices: A_crypto[0, idx] = 1
            tc_constraints.append(LinearConstraint(A_crypto, [-np.inf], [0.20]))
            
        if low_risk_indices and (num_assets - len(low_risk_indices)) * max_wt >= 0.85:
            A_low = np.zeros((1, num_assets))
            for idx in low_risk_indices: A_low[0, idx] = 1
            tc_constraints.append(LinearConstraint(A_low, [-np.inf], [0.15]))

        if tw_and_fund_indices and (num_assets - len(tw_and_fund_indices)) * max_wt >= 0.85:
            A_tw_fund = np.zeros((1, num_assets))
            for idx in tw_and_fund_indices: A_tw_fund[0, idx] = 1
            tc_constraints.append(LinearConstraint(A_tw_fund, [-np.inf], [0.15]))

        optimized_result = sco.minimize(
            neg_sharpe_ratio, init_guess, method='trust-constr', bounds=bounds, constraints=tc_constraints
        )

    if optimized_result.success:
        return dict(zip(returns_df.columns, np.round(optimized_result.x, 4)))
    else:
        print(f"❌ 雙重最佳化皆失敗: {optimized_result.message}。套用等權重備援方案。")
        fallback_w = np.round(init_guess, 4)
        return dict(zip(returns_df.columns, fallback_w))

try:
    response = supabase.table("portfolio_db").select("*").limit(1).execute()
    if response.data:
        db_record = response.data[0]
        stock_meta = db_record.get("stock_meta", {})
        ledger_data = db_record.get("ledger_data", [])
        
        ledger_tickers = [str(tx["ticker"]).strip().upper() for tx in ledger_data if tx.get("ticker")]
        all_tickers = list(set(list(stock_meta.keys()) + ledger_tickers))
        
        for t in all_tickers:
            if t not in stock_meta: stock_meta[t] = {}

        sheet_prices = get_sheet_prices(db_record.get("settings", {}).get("sheetUrl", ""))
        
        if all_tickers:
            tw_bench, us_bench = "^TWII", "SPY"
            proxy_map = {"統一奔騰": "00981A.TW", "安聯台灣科技": "0052.TW", "加密貨幣": "BTC-USD"}
            
            download_list = [tw_bench, us_bench]
            yf_tickers = []
            
            for t in all_tickers:
                t_clean = str(t).strip().upper()
                target = t_clean 
                if t_clean in proxy_map: target = proxy_map[t_clean]
                elif bool(re.search(r'[\u4e00-\u9fff]', t_clean)): target = tw_bench 
                elif re.match(r'^\d+[a-zA-Z]*$', t_clean): target = f"{t_clean}.TW"
                
                yf_tickers.append(target)
                if target not in download_list: download_list.append(target)
                    
            print(f"⏳ 正在向 Yahoo Finance 請求 {len(download_list)} 檔標的歷史資料...", flush=True)
            prices_df = yf.download(download_list, period="1y", progress=False)["Close"]
            
            if isinstance(prices_df, pd.Series): prices_df = prices_df.to_frame(name=download_list[0])
            returns = prices_df.pct_change().dropna()

            print("🧠 啟動機構級最佳化引擎 (限制 3%~20%)...", flush=True)
            print("⚖️ 正在過濾真實庫存標的...", flush=True)
            
            current_shares = {}
            for tx in ledger_data:
                t = str(tx.get("ticker", "")).strip().upper()
                if not t: continue
                s = float(tx.get("shares", 0))
                if str(tx.get("type", "buy")).lower() in ["sell", "賣出"]: s = -s
                current_shares[t] = current_shares.get(t, 0) + s

            active_tickers = [t for t, s in current_shares.items() if s > 0.0001]
            ticker_to_yf = dict(zip(all_tickers, yf_tickers))
            
            valid_investable = []
            for t in active_tickers:
                yf_t = ticker_to_yf.get(t)
                if yf_t and yf_t in returns.columns and yf_t not in [tw_bench, us_bench]:
                    valid_investable.append(yf_t)

            print(f"✅ 篩選完成：庫存共有 {len(valid_investable)} 檔標的進入最佳化引擎。", flush=True)

            target_weights = {}
            if valid_investable:
                investable_returns = returns[valid_investable]
                num_assets = len(valid_investable)
                if num_assets < 5:
                    dynamic_min = 0.0
                    dynamic_max = 1.0
                else:
                    dynamic_min = min(0.03, 0.9 / num_assets) if num_assets > 0 else 0.0
                    dynamic_max = 0.20
                    
                target_weights = get_optimal_weights(investable_returns, stock_meta, min_wt=dynamic_min, max_wt=dynamic_max)
                
                                # ==========================================
                # 🔬 NEW: 啟動 Fama-French 3 因子模型迴歸引擎
                # ==========================================
                print("🧠 啟動 Fama-French 3 因子模型迴歸引擎...", flush=True)
                try:
                    import statsmodels.api as sm
                    
                    # 🌟 修正 3：字串拼接大法！徹底防止編輯器自動加上 Markdown 超連結中括號
                    domain = "https://mba.tuck.dartmouth.edu"
                    path = "/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"
                    ff_url = domain + path
                    
                    r = requests.get(ff_url, timeout=15)
                    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                        with z.open(z.namelist()[0]) as f:
                            # Kenneth French 的檔案前三行是說明文字，要跳過
                            ff_data = pd.read_csv(f, skiprows=3, index_col=0)
                    
                    # 整理資料：去除無效欄位，將日期轉為 datetime，數值轉為小數
                    ff_data.index = pd.to_datetime(ff_data.index.astype(str).str.strip(), format='%Y%m%d', errors='coerce')
                    ff_data = ff_data.dropna()
                    ff_data = ff_data.apply(pd.to_numeric, errors='coerce').dropna()
                    ff_data = ff_data / 100.0 

                    if len(returns) > 30:
                        port_weights = []
                        total_shares = sum([current_shares.get(t, 0) for t in active_tickers])
                        
                        if total_shares > 0:
                            for yt in valid_investable:
                                original_ticker = list(ticker_to_yf.keys())[list(ticker_to_yf.values()).index(yt)]
                                weight = current_shares.get(original_ticker, 0) / total_shares
                                port_weights.append(weight)
                                
                            port_weights = np.array(port_weights)
                            daily_port_return = investable_returns.dot(port_weights)
                            daily_port_return.index = pd.to_datetime(daily_port_return.index).tz_localize(None)
                            daily_port_return.name = 'Port_Ret'

                            aligned_data = pd.concat([daily_port_return, ff_data], axis=1).dropna()
                            
                            if len(aligned_data) > 30:
                                # 🚨 終極清洗：確保 aligned_data 裡面絕對沒有 NaN 或 Infinity
                                aligned_data = aligned_data.replace([np.inf, -np.inf], np.nan).dropna()
                                
                                if len(aligned_data) > 30:
                                    # 準備 Y (應變數：投組超額報酬 = 投組報酬 - 無風險利率)
                                    Y = aligned_data['Port_Ret'] - aligned_data['RF']
                                    
                                    # 準備 X (自變數：Mkt-RF, SMB, HML)
                                    X = aligned_data[['Mkt-RF', 'SMB', 'HML']]
                                    X = sm.add_constant(X) # 加入 Alpha (截距項)
                                    
                                    # 🚨 再加上一層保險，確保轉換為 float 類型
                                    Y = Y.astype(float)
                                    X = X.astype(float)
                                    
                                    # 執行 OLS 多元線性迴歸
                                    model = sm.OLS(Y, X)
                                    results = model.fit()
                                
                                ff_alpha = results.params['const'] * 252 * 100 
                                ff_mkt_beta = results.params['Mkt-RF']
                                ff_smb = results.params['SMB']
                                ff_hml = results.params['HML']
                                ff_r_squared = results.rsquared
                                
                                fama_french_stats = {
                                    "alpha": float(round(ff_alpha, 2)),
                                    "mkt_beta": float(round(ff_mkt_beta, 2)),
                                    "smb": float(round(ff_smb, 2)),
                                    "hml": float(round(ff_hml, 2)),
                                    "r_squared": float(round(ff_r_squared, 2))
                                }
                                
                                print(f"✅ FF3 運算成功: Mkt β={ff_mkt_beta:.2f}, SMB={ff_smb:.2f}, HML={ff_hml:.2f}, R²={ff_r_squared:.2f}")
                                
                                macro_payload["fama_french"] = fama_french_stats
                                supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", target_id).execute()
                            else:
                                print("⚠️ 日期對齊後資料點不足，跳過 FF3 運算。")
                except Exception as e:
                    print(f"⚠️ Fama-French 迴歸運算失敗: {e}", flush=True)
                # ==========================================


            print("🧠 開始計算多因子風險參數並寫入資料庫...", flush=True)
            for i, original_ticker in enumerate(all_tickers):
                yf_ticker = yf_tickers[i]
                
                if original_ticker in sheet_prices:
                    stock_meta[original_ticker]["last_price"] = sheet_prices[original_ticker]
                
                if yf_ticker in returns.columns:
                    stock_close = prices_df[yf_ticker].dropna()
                    if len(stock_close) < 60: continue
                    
                    bench = tw_bench if yf_ticker.endswith(".TW") else us_bench
                    aligned = pd.concat([returns[yf_ticker], returns[bench]], axis=1).dropna()
                    if len(aligned) < 30: continue
                    
                    bench_var = aligned.iloc[:,1].var()
                    beta = aligned.iloc[:,0].cov(aligned.iloc[:,1]) / bench_var if bench_var > 0 else 1.0
                    ann_std = np.sqrt(aligned.iloc[:,0].var() * 252) * 100
                    
                    rsi_series = ta.rsi(stock_close)
                    rsi = rsi_series.iloc[-1] if rsi_series is not None and not rsi_series.empty else 50.0
                    
                    macd_df = ta.macd(stock_close)
                    macd_h = macd_df.iloc[-1, 1] if macd_df is not None and not macd_df.empty else 0.0
                    
                    target_w = target_weights.get(yf_ticker, 0.0)
                    
                    stock_meta[original_ticker].update({
                        "beta": round(beta, 2), "std": round(ann_std, 2), "rsi": round(rsi, 2), 
                        "macd_h": round(macd_h, 4), "target_weight": float(target_w)
                    })
                    print(f"✅ [{original_ticker}] 更新 -> Beta: {beta:.2f}, Std: {ann_std:.1f}%, 目標權重: {target_w*100:.2f}%")
                else:
                    if original_ticker not in proxy_map and not bool(re.search(r'[\u4e00-\u9fff]', original_ticker)):
                        print(f"⚠️ [{original_ticker}] 在 Yahoo 找不到對應標的 ({yf_ticker})。")

            supabase.table("portfolio_db").update({"stock_meta": stock_meta}).eq("id", target_id).execute()

            # ==========================================
            # ⚖️ 4. 第三階段：自動化再平衡與交易訊號生成
            # ==========================================
            print("\n⚖️ 啟動再平衡引擎：計算目標權重落差與交易訊號...", flush=True)
            
            portfolio_value = 0.0
            asset_values = {}
            
            for t in all_tickers:
                shares = current_shares.get(t, 0)
                last_price = stock_meta.get(t, {}).get("last_price", 0.0)
                if last_price == 0.0 and yf_tickers:
                    idx = all_tickers.index(t)
                    yt = yf_tickers[idx]
                    if yt in prices_df.columns: last_price = float(prices_df[yt].dropna().iloc[-1])
                
                value = max(0, shares * last_price)
                asset_values[t] = value
                portfolio_value += value

            rebalance_signals = []
            
            if portfolio_value > 0:
                print(f"💰 當前投資組合總淨值估算: {portfolio_value:,.2f}", flush=True)
                for t in all_tickers:
                    target_w = stock_meta.get(t, {}).get("target_weight", 0.0)
                    current_w = asset_values.get(t, 0.0) / portfolio_value
                    delta_w = target_w - current_w
                    
                    target_value = portfolio_value * target_w
                    delta_value = target_value - asset_values.get(t, 0.0)
                    
                    if abs(delta_w) > 0.01:
                        action = "BUY (加碼)" if delta_w > 0 else "SELL (減碼)"
                        rebalance_signals.append({
                            "ticker": t, "action": action, "current_weight": f"{current_w*100:.2f}%",
                            "target_weight": f"{target_w*100:.2f}%", "delta_weight": f"{delta_w*100:.2f}%",
                            "trade_amount": round(delta_value, 2)
                        })
                        print(f"   [{t}] {action} -> 目標: {target_w*100:.1f}%, 當前: {current_w*100:.1f}%")

            if rebalance_signals and GEMINI_API_KEY:
                print("🤖 喚醒 AI 撰寫再平衡交易執行報告...", flush=True)
                rebalance_prompt = f"""
                [SYSTEM_DIRECTIVE]
                Task: Generate a high-conviction, logically flawless rebalance execution plan.
                Tone: Institutional Risk Manager & Quant Trader. Coldly rational, strictly data-driven.
                Language: MUST strictly output all text values in TRADITIONAL CHINESE (繁體中文).
                Constraints: Output ONLY JSON. No conversational filler.

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
                    "priority_trades": [
                        {{
                            "ticker": "<string>",
                            "reason": "<string_short_rationale_combining_macro_and_target_weight_in_traditional_chinese>"
                        }}
                    ]
                }}
                """
                
                rebalance_res = client.models.generate_content(model="gemini-3-flash-preview", contents=rebalance_prompt)
                
                try:
                    rb_match = re.search(r'\{.*\}', rebalance_res.text, re.DOTALL)
                    if rb_match:
                        rb_analysis = json.loads(rb_match.group(0))
                        supabase.table("portfolio_db").update({
                            "rebalance_meta": {
                                "signals": rebalance_signals,
                                "ai_execution_plan": rb_analysis
                            }
                        }).eq("id", target_id).execute()
                        print("✅ 再平衡交易清單與 AI 執行報告已成功同步至 Supabase！")
                except Exception as e:
                    print(f"⚠️ AI 執行報告解析失敗: {e}")

except Exception as e:
    print(f"🔥 股票管線處理發生錯誤:\n{traceback.format_exc()}", flush=True)
    raise e
