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

# ==========================================
# 2. 抓取總經數據與市場參數
# ==========================================
print("🌍 啟動量化大腦：開始透過 Yahoo API 抓取市場參數...", flush=True)

def calc_z_score(series):
    if series.empty or len(series) < 20: return 0.0
    std = series.std()
    return (series.iloc[-1] - series.mean()) / std if std != 0 else 0.0

try:
    try:
        bonds = yf.download(["^TNX", "^IRX"], period="1mo", progress=False)["Close"]
        y10 = float(bonds["^TNX"].dropna().iloc[-1])
        y3m = float(bonds["^IRX"].dropna().iloc[-1])
    except: y10, y3m = 4.2, 5.0

    try: hyg_yield = yf.Ticker("HYG").info.get('yield', 0.05) * 100 
    except: hyg_yield = 7.5
    hy_spread = max(0.1, hyg_yield - y10)

    try:
        btc_data = yf.download("BTC-USD", period="1mo", progress=False)["Close"]
        btc_clean = btc_data.iloc[:, 0].dropna() if isinstance(btc_data, pd.DataFrame) else btc_data.dropna()
        btc_mom = ((btc_clean.iloc[-1] / btc_clean.iloc[0]) - 1) * 100 if len(btc_clean) > 1 else 0.0
    except: btc_mom = 0.0

    try:
        spy = yf.download("SPY", period="10y", progress=False)["Close"]
        spy_clean = spy.iloc[:, 0].dropna() if isinstance(spy, pd.DataFrame) else spy.dropna()
        spy_cagr = ((spy_clean.iloc[-1] / spy_clean.iloc[0]) ** (1/10)) - 1 if len(spy_clean) > 10 else 0.10
        spy_vol = spy_clean.tail(252).pct_change().std() * np.sqrt(252) if len(spy_clean) > 10 else 0.15
    except: spy_cagr, spy_vol = 0.10, 0.15

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
    except:
        vix, vxn, vvix, dxy, gold, copper, oil, copper_gold_ratio = 20.0, 22.0, 90.0, 100.0, 2000.0, 4.0, 75.0, 0.2
        vix_z, vxn_z, vvix_z = 0.0, 0.0, 0.0

    try:
        pcr_data = yf.Ticker("^PCR").history(period="1y")['Close'].dropna()
        pcr, pcr_z = float(pcr_data.iloc[-1]), float(calc_z_score(pcr_data))
    except: pcr, pcr_z = 1.0, 0.0

    try:
        aud_jpy_data = yf.download("AUDJPY=X", period="1mo", progress=False)["Close"]
        aud_jpy_clean = aud_jpy_data.iloc[:, 0].dropna() if isinstance(aud_jpy_data, pd.DataFrame) else aud_jpy_data.dropna()
        aud_jpy_mom = float(((aud_jpy_clean.iloc[-1] / aud_jpy_clean.iloc[0]) - 1) * 100) if len(aud_jpy_clean) > 1 else 0.0
    except: aud_jpy_mom = 0.0

    try:
        try:
            move_data = yf.Ticker("^MOVE").history(period="1y")['Close'].dropna()
            if move_data.empty: raise ValueError
            move_idx, move_z = float(move_data.iloc[-1]), float(calc_z_score(move_data))
        except:
            tlt = yf.download("TLT", period="1y", progress=False)["Close"]
            tlt = tlt.iloc[:, 0] if isinstance(tlt, pd.DataFrame) else tlt
            move_data = (tlt.pct_change().rolling(20).std() * np.sqrt(252) * 100 * 5).dropna()
            move_idx = float(move_data.iloc[-1]) if not move_data.empty else 100.0
            move_z = float(calc_z_score(move_data))

        target_etfs = ["IWM", "SPY", "XLU", "XLY", "HYG", "TLT", "DBC", "SOXX", "BIL", "SHY", "RSP", "KRE"]
        etfs = yf.download(target_etfs, period="1mo", progress=False)["Close"]
        if isinstance(etfs, pd.Series): etfs = etfs.to_frame()
        
        def safe_mom(t1, t2=None):
            try:
                s1 = etfs[t1].dropna() if t1 in etfs.columns else pd.Series()
                if len(s1) < 2: return 0.0
                r1 = (s1.iloc[-1] / s1.iloc[0]) - 1
                if t2:
                    s2 = etfs[t2].dropna() if t2 in etfs.columns else pd.Series()
                    if len(s2) < 2: return 0.0
                    return float((r1 - ((s2.iloc[-1] / s2.iloc[0]) - 1)) * 100)
                return float(r1 * 100)
            except: return 0.0

        iwm_spy_mom = safe_mom("IWM", "SPY")
        xlu_xly_mom = safe_mom("XLU", "XLY")
        hyg_tlt_mom = safe_mom("HYG", "TLT")
        soxx_spy_mom = safe_mom("SOXX", "SPY")
        dbc_mom = safe_mom("DBC")
        liquidity_spread = safe_mom("BIL", "SHY") 
        rsp_spy_mom = safe_mom("RSP", "SPY") 
        kre_spy_mom = safe_mom("KRE", "SPY") 

    except:
        move_idx, move_z, iwm_spy_mom, xlu_xly_mom, hyg_tlt_mom = 100.0, 0.0, 0.0, 0.0, 0.0
        dbc_mom, soxx_spy_mom, liquidity_spread, rsp_spy_mom, kre_spy_mom = 0.0, 0.0, 0.0, 0.0, 0.0

    print("   ⏳ 正在計算系統相關性矩陣 (並升級為 60-Day Rolling)...", flush=True)
    sys_corr, corr_matrix, rolling_corr_series = 0.3, {}, []
    current_shares, active_tickers = {}, []
    try:
        response = supabase.table("portfolio_db").select("*").limit(1).execute()
        if response.data:
            db_record = response.data[0]
            for tx in db_record.get("ledger_data", []):
                t = str(tx.get("ticker", "")).strip().upper()
                if not t: continue
                s = float(tx.get("shares", 0))
                if str(tx.get("type", "buy")).lower() in ["sell", "賣出"]: s = -s
                current_shares[t] = current_shares.get(t, 0) + s
                
            active_tickers = [t for t, s in current_shares.items() if s > 0.0001]
            
            if len(active_tickers) > 1:
                tw_bench = "^TWII"
                proxy_map = {"統一奔騰": "00981A.TW", "安聯台灣科技": "0052.TW", "加密貨幣": "BTC-USD"}
                mapped_tickers = list(set(proxy_map.get(t, tw_bench if bool(re.search(r'[\u4e00-\u9fff]', t)) else (f"{t}.TW" if re.match(r'^\d+[a-zA-Z]*$', t) else t)) for t in active_tickers))
                
                port_df = yf.download(mapped_tickers, period="6mo", progress=False)["Close"]
                if isinstance(port_df, pd.Series): port_df = port_df.to_frame(name=mapped_tickers[0])
                port_returns = port_df.pct_change().dropna()
                
                # 🌟 升級功能：60天動態滾動相關性 (Rolling Correlation)
                if len(port_returns) >= 60:
                    for i in range(60, len(port_returns) + 1):
                        window = port_returns.iloc[i-60:i]
                        corr_df = window.corr()
                        mask = np.triu(np.ones_like(corr_df, dtype=bool), k=1)
                        mean_corr = float(corr_df.where(mask).mean().mean())
                        if not np.isnan(mean_corr):
                            rolling_corr_series.append({"date": window.index[-1].strftime("%Y-%m-%d"), "corr": round(mean_corr, 4)})
                    if rolling_corr_series: sys_corr = rolling_corr_series[-1]["corr"]
                else:
                    corr_df = port_returns.corr()
                    mask = np.triu(np.ones_like(corr_df, dtype=bool), k=1)
                    raw_sys_corr = float(corr_df.where(mask).mean().mean())
                    sys_corr = raw_sys_corr if not np.isnan(raw_sys_corr) else 0.0

                corr_matrix = port_returns.corr().replace([np.inf, -np.inf], np.nan).fillna(0.0).to_dict()
                corr_spike_alert = False
                sys_corr_change_5d = 0.0
                if len(rolling_corr_series) >= 6:
                    recent_corr = rolling_corr_series[-1]["corr"]
                    past_corr = rolling_corr_series[-6]["corr"] # 5個交易日(一週)前的相關性
                    sys_corr_change_5d = recent_corr - past_corr
                    
                    # 警報觸發條件：一週內相關性暴增超過 0.15，且目前絕對值大於 0.6 (代表開始齊漲齊跌)
                    if sys_corr_change_5d > 0.15 and recent_corr > 0.60:
                        corr_spike_alert = True
                        print(f"🚨 [警告] 系統相關性陡升警報觸發！(5日變化: +{sys_corr_change_5d:.2f}, 當前: {recent_corr:.2f})", flush=True)
    except Exception as e: print(f"⚠️ 相關性計算失敗: {e}")

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
        "sys_corr": float(round(sys_corr, 2)), "sys_corr_change_5d": float(round(sys_corr_change_5d, 4)), 
        "corr_spike_alert": corr_spike_alert, "corr_matrix": corr_matrix, "rolling_corr_series": rolling_corr_series
    }
    
    # ==========================================
    # Gemini AI 總結
    # ==========================================
    regime_packet = build_regime_packet(macro_payload)
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
               *CRITICAL_ALERT*: If `corr_spike_alert` is true in the data, you MUST declare a "流動性衝擊/無差別拋售警告" and override all bullish signals.
            3. DETAILS.TITLE: Traditional Chinese metric name.
            4. DETAILS.DESC: Max 35 chars. Explicitly cite specific numeric values (Z-Scores).
               *CRITICAL_ALERT*: If `corr_spike_alert` is true, add a dedicated detail item warning about the 5-day correlation spike.
            5. DETAILS.COLOR: "text-green-400", "text-red-400", "text-gray-400".
            6. DETAILS.ICON: Single emoji.

            [INPUT_DATA]
            {json.dumps(regime_packet, ensure_ascii=False)}
            "corr_spike_alert": {str(corr_spike_alert).lower()},
            "sys_corr_change_5d": {sys_corr_change_5d}

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
                        break
                except: continue
        except: pass

    target_id = 1
    existing = supabase.table("portfolio_db").select("id").limit(1).execute()
    if existing.data: supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", target_id).execute()
    else: supabase.table("portfolio_db").insert({"id": target_id, "macro_meta": macro_payload}).execute()

except Exception as e:
    print(f"🔥 總經數據處理致命錯誤:\n{traceback.format_exc()}", flush=True)
    raise e

# ==========================================
# 3. 股票多因子管線與最佳化
# ==========================================
print("\n⏳ 接著開始執行股票多因子管線與最佳化...", flush=True)

def get_sheet_prices(url_str):
    if not url_str: return {}
    try:
        clean_url = re.sub(r'\[.*?\]\((.*?)\)', r'\1', url_str)
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', clean_url)
        gid_match = re.search(r'[#&?]gid=([0-9]+)', clean_url)
        if not match: return {}
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
                    if ':' in ticker: price_map[ticker.split(':')[1].strip()] = price
                except: pass
        return price_map
    except: return {}

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
    if response.data:
        db_record = response.data[0]
        stock_meta, ledger_data = db_record.get("stock_meta", {}), db_record.get("ledger_data", [])
        ledger_tickers = [str(tx["ticker"]).strip().upper() for tx in ledger_data if tx.get("ticker")]
        all_tickers = list(set(list(stock_meta.keys()) + ledger_tickers))
        for t in all_tickers:
            if t not in stock_meta: stock_meta[t] = {}

        sheet_prices = get_sheet_prices(db_record.get("settings", {}).get("sheetUrl", ""))
        
        if all_tickers:
            tw_bench, us_bench = "^TWII", "SPY"
            proxy_map = {"統一奔騰": "00981A.TW", "安聯台灣科技": "0052.TW", "加密貨幣": "BTC-USD"}
            download_list, yf_tickers = [tw_bench, us_bench], []
            
            for t in all_tickers:
                t_clean = str(t).strip().upper()
                target = proxy_map.get(t_clean, tw_bench if bool(re.search(r'[\u4e00-\u9fff]', t_clean)) else (f"{t_clean}.TW" if re.match(r'^\d+[a-zA-Z]*$', t_clean) else t_clean))
                yf_tickers.append(target)
                if target not in download_list: download_list.append(target)
                    
            prices_df = yf.download(download_list, period="1y", progress=False)["Close"]
            if isinstance(prices_df, pd.Series): prices_df = prices_df.to_frame(name=download_list[0])
            returns = prices_df.pct_change().dropna()

            current_shares = {}
            for tx in ledger_data:
                t = str(tx.get("ticker", "")).strip().upper()
                if not t: continue
                current_shares[t] = current_shares.get(t, 0) + (float(tx.get("shares", 0)) * (-1 if str(tx.get("type", "buy")).lower() in ["sell", "賣出"] else 1))

            active_tickers = [t for t, s in current_shares.items() if s > 0.0001]
            ticker_to_yf = dict(zip(all_tickers, yf_tickers))
            valid_investable = [yf_t for t in active_tickers if (yf_t := ticker_to_yf.get(t)) and yf_t in returns.columns and yf_t not in [tw_bench, us_bench]]

            target_weights = {}
            if valid_investable:
                num_assets = len(valid_investable)
                dynamic_min = 0.0 if num_assets < 5 else min(0.03, 0.9 / num_assets)
                target_weights = get_optimal_weights(returns[valid_investable], stock_meta, min_wt=dynamic_min, max_wt=1.0 if num_assets < 5 else 0.20)
                
                # ==========================================
                # 🌟 升級：Fama-French 6 因子模型 (FF5 + Momentum)
                # ==========================================
                print("🧠 啟動 Fama-French 6 因子模型 (FF5 + Momentum) 迴歸引擎...", flush=True)
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

                            aligned_data = pd.concat([daily_port_return, ff_data], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
                            
                            if len(aligned_data) > 30:
                                Y = (aligned_data['Port_Ret'] - aligned_data['RF']).astype(float)
                                X = sm.add_constant(aligned_data[['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'Mom']]).astype(float)
                                
                                results = sm.OLS(Y, X).fit()
                                macro_payload["fama_french"] = {
                                    "alpha": float(round(results.params['const'] * 252 * 100, 2)),
                                    "mkt_beta": float(round(results.params['Mkt-RF'], 2)),
                                    "smb": float(round(results.params['SMB'], 2)),
                                    "hml": float(round(results.params['HML'], 2)),
                                    "rmw": float(round(results.params['RMW'], 2)),
                                    "cma": float(round(results.params['CMA'], 2)),
                                    "wml": float(round(results.params['Mom'], 2)),
                                    "r_squared": float(round(results.rsquared, 2))
                                }
                                print(f"✅ FF6 運算成功: R²={results.rsquared:.2f}, RMW={results.params['RMW']:.2f}, WML={results.params['Mom']:.2f}")
                                supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", target_id).execute()
                except Exception as e: print(f"⚠️ FF6 迴歸失敗: {e}", flush=True)

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
                    stock_meta[original_ticker].update({
                        "beta": round(aligned.iloc[:,0].cov(aligned.iloc[:,1]) / bench_var if bench_var > 0 else 1.0, 2),
                        "std": round(np.sqrt(aligned.iloc[:,0].var() * 252) * 100, 2),
                        "rsi": round(ta.rsi(stock_close).iloc[-1] if ta.rsi(stock_close) is not None else 50.0, 2), 
                        "macd_h": round(ta.macd(stock_close).iloc[-1, 1] if ta.macd(stock_close) is not None else 0.0, 4),
                        "target_weight": float(target_weights.get(yf_ticker, 0.0))
                    })

            supabase.table("portfolio_db").update({"stock_meta": stock_meta}).eq("id", target_id).execute()

            print("\n⚖️ 啟動自動再平衡引擎...", flush=True)
            portfolio_value, asset_values, rebalance_signals = 0.0, {}, []
            for t in all_tickers:
                shares = current_shares.get(t, 0)
                lp = stock_meta.get(t, {}).get("last_price", 0.0)
                if lp == 0.0 and yf_tickers and yf_tickers[all_tickers.index(t)] in prices_df.columns:
                    lp = float(prices_df[yf_tickers[all_tickers.index(t)]].dropna().iloc[-1])
                val = max(0, shares * lp)
                asset_values[t], portfolio_value = val, portfolio_value + val

            if portfolio_value > 0:
                for t in all_tickers:
                    tw = stock_meta.get(t, {}).get("target_weight", 0.0)
                    cw = asset_values.get(t, 0.0) / portfolio_value
                    if abs(tw - cw) > 0.01:
                        rebalance_signals.append({"ticker": t, "action": "BUY (加碼)" if tw > cw else "SELL (減碼)", "current_weight": f"{cw*100:.2f}%", "target_weight": f"{tw*100:.2f}%", "delta_weight": f"{(tw-cw)*100:.2f}%", "trade_amount": round((portfolio_value * tw) - asset_values.get(t, 0.0), 2)})

            if rebalance_signals and GEMINI_API_KEY:
                try:
                    rebalance_prompt = f"""
                    [SYSTEM_DIRECTIVE]
                    Task: Generate a high-conviction, logically flawless rebalance execution plan.
                    Tone: Institutional Risk Manager & Quant Trader. Coldly rational, strictly data-driven.
                    Language: STRICTLY Traditional Chinese (繁體中文). ONLY JSON output.

                    [LOGICAL_GUARDRAILS]
                    - CRITICAL: DO NOT confuse "Sector Rotation" with "Hedging".
                    - TRUE HEDGING means moving to cash, bonds, or negative-beta assets.
                    - If the trades involve moving capital to high-beta assets, explicitly frame it as "Risk-On Rotation", NEVER as "Hedging".
                    - 🚨 BLACK SWAN OVERRIDE: If the Macro Summary mentions "流動性衝擊", "相關性陡升", or "無差別拋售", you MUST frame the entire rebalance execution as extreme defensive De-Risking (selling high-beta, fleeing to safety).

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
                except Exception as e: print(f"⚠️ AI 執行報告生成失敗: {e}")

except Exception as e:
    print(f"🔥 股票管線致命錯誤:\n{traceback.format_exc()}", flush=True)
    raise e
