import os
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import datetime
import requests
import io
from supabase import create_client, Client
import re
import warnings
import urllib.parse
import json
from google import genai
import time

warnings.filterwarnings('ignore')

# ==========================================
# 1. 讀取環境變數與初始化
# ==========================================
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# ==========================================
# 🌟 2. 總經與市場參數自動化抓取
# ==========================================
print("🌍 啟動量化大腦：開始透過 Yahoo API 抓取市場參數...", flush=True)

try:
    # A. 抓取公債殖利率
    print("   ⏳ 正在抓取公債殖利率...", flush=True)
    bonds = yf.download(["^TNX", "^IRX"], period="1mo", progress=False)["Close"]
    
    y10_series = bonds["^TNX"] if isinstance(bonds, pd.DataFrame) else bonds
    y3m_series = bonds["^IRX"] if isinstance(bonds, pd.DataFrame) else bonds
    
    y10 = float(y10_series.dropna().iloc[-1])
    
    y3m_clean = y3m_series.dropna()
    if not y3m_clean.empty:
        y3m = float(y3m_clean.iloc[-1])
    else:
        print("⚠️ 警告：無法獲取 ^IRX 數據，使用備用數值")
        y3m = 0.0
    
    # B. 抓取高收益債利差
    print("   ⏳ 正在計算信用利差...", flush=True)
    hyg = yf.Ticker("HYG")
    try:
        hyg_yield = hyg.info.get('yield', 0.05) * 100 
    except:
        hyg_yield = 7.5
    hy_spread = max(0.1, hyg_yield - y10)

    # C. 抓取比特幣動能
    print("   ⏳ 正在計算加密貨幣動能...", flush=True)
    btc_data = yf.download("BTC-USD", period="1mo", progress=False)["Close"]
    if isinstance(btc_data, pd.DataFrame): btc_data = btc_data.iloc[:, 0]
    btc_mom = ((btc_data.dropna().iloc[-1] / btc_data.dropna().iloc[0]) - 1) * 100

    # D. 抓取 SPY 長期報酬與波動
    print("   ⏳ 正在計算 SPY 長期報酬與短期波動...", flush=True)
    spy = yf.download("SPY", period="10y", progress=False)["Close"]
    if isinstance(spy, pd.DataFrame): spy = spy.iloc[:, 0]
    
    spy_cagr = ((spy.dropna().iloc[-1] / spy.dropna().iloc[0]) ** (1/10)) - 1
    spy_vol = spy.dropna().tail(252).pct_change().std() * np.sqrt(252)

    # E. 🌟 封裝數據
    macro_payload = {
        "yield_10y": float(round(y10, 2)),
        "yield_2y": float(round(y3m, 2)),
        "yield_curve": float(round(y10 - y3m, 2)), 
        "hy_spread": float(round(hy_spread, 2)),
        "btc_1m_mom": float(round(btc_mom, 2)),
        "market_rf": float(round(y10, 2)),
        "market_rm": float(round(spy_cagr * 100, 2)),
        "market_sm": float(round(spy_vol * 100, 2))
    }
    print(f"📈 計算完成 -> Rf: {macro_payload['market_rf']}%, Rm: {macro_payload['market_rm']}%, σm: {macro_payload['market_sm']}%", flush=True)
    
    # ==========================================
    # 🧠 F. Gemini AI 雙模組備援診斷系統
    # ==========================================
    print("🤖 喚醒 Gemini AI 進行總經與風險診斷...", flush=True)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""
            你是一位量化避險基金經理。請診斷以下數據：
            Rf: {macro_payload['market_rf']}%, Rm: {macro_payload['market_rm']}%, σm: {macro_payload['market_sm']}%
            衰退指標 (10Y-3M): {macro_payload['yield_curve']}%
            信用利差: {macro_payload['hy_spread']}%
            BTC動能: {macro_payload['btc_1m_mom']}%
            請回傳一個 JSON 格式（不要 Markdown），包含 summary 和 details 陣列。
            """
            model_pipeline = ["gemini-2.0-flash", "gemini-1.5-flash"]
            ai_success = False

            for model_name in model_pipeline:
                try:
                    response = client.models.generate_content(model=model_name, contents=prompt)
                    text = response.text.strip().strip('`')
                    if text.lower().startswith('json'): text = text[4:].strip()
                    macro_payload['ai_analysis'] = json.loads(text)
                    print(f"✅ AI 診斷成功！({model_name})", flush=True)
                    ai_success = True
                    break
                except:
                    continue
            
            if not ai_success: print("⚠️ AI 診斷暫時不可用。", flush=True)
        except Exception as e:
            print(f"⚠️ AI 初始化失敗: {e}", flush=True)

    # G. 寫入 Supabase 
    print("🚀 正在同步至 Supabase...", flush=True)
    existing = supabase.table("portfolio_db").select("id").limit(1).execute()
    if len(existing.data) > 0:
        target_id = existing.data[0]['id']
        supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", target_id).execute()
    else:
        target_id = 1
        supabase.table("portfolio_db").insert({"id": target_id, "macro_meta": macro_payload}).execute()

except Exception as e:
    print(f"🔥 總經數據處理發生錯誤: {str(e)}", flush=True)
    raise e

# ==========================================
# 🧠 3. 股票多因子管線
# ==========================================
print("\n⏳ 接著開始執行股票多因子管線...", flush=True)

def get_sheet_prices(url_str):
    print("📊 正在從 Google Sheet 抓取自訂報價...", flush=True)
    if not url_str: return {}
    try:
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', url_str)
        gid_match = re.search(r'[#&?]gid=([0-9]+)', url_str)
        if not match: return {}
        sheet_id = match.group(1)
        gid = gid_match.group(1) if gid_match else '0'
        
        # 🌟 這裡修正了網址格式，移除了所有括號
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
        
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
        print(f"⚠️ Sheet 報價讀取失敗: {e}", flush=True)
        return {}

response = supabase.table("portfolio_db").select("*").limit(1).execute()
if response.data:
    db_record = response.data[0]
    stock_meta = db_record.get("stock_meta", {})
    sheet_prices = get_sheet_prices(db_record.get("settings", {}).get("sheetUrl", ""))
    
    tickers = list(stock_meta.keys())
    if tickers:
        tw_bench, us_bench = "^TWII", "SPY"
        proxy_map = {"統一奔騰": "00981A.TW", "統一黑馬": "0050.TW", "安聯台灣科技": "0052.TW"}
        
        download_list = [tw_bench, us_bench]
        yf_tickers = []
        for t in tickers:
            if t in proxy_map: target = proxy_map[t]
            elif bool(re.search(r'[\u4e00-\u9fff]', t)): target = t
            elif re.match(r'^\d+$', t): target = f"{t}.TW"
            else: target = t
            yf_tickers.append(target)
            if target not in download_list: download_list.append(target)

        print(f"⏳ 正在向 Yahoo Finance 請求資料...", flush=True)
        prices_df = yf.download(download_list, period="1y")["Close"]
        returns = prices_df.pct_change()

        for i, original_ticker in enumerate(tickers):
            yf_ticker = yf_tickers[i]
            if original_ticker in sheet_prices:
                stock_meta[original_ticker]["last_price"] = sheet_prices[original_ticker]
            
            if yf_ticker in returns.columns:
                stock_close = prices_df[yf_ticker].dropna()
                if len(stock_close) < 60: continue
                
                bench = tw_bench if yf_ticker.endswith(".TW") else us_bench
                aligned = pd.concat([returns[yf_ticker], returns[bench]], axis=1).dropna()
                
                beta = aligned.iloc[:,0].cov(aligned.iloc[:,1]) / aligned.iloc[:,1].var()
                ann_std = np.sqrt(aligned.iloc[:,0].var() * 252) * 100
                rsi = ta.rsi(stock_close).iloc[-1]
                macd = ta.macd(stock_close).iloc[-1, 1]
                
                stock_meta[original_ticker].update({
                    "beta": round(beta, 2), "std": round(ann_std, 2),
                    "rsi": round(rsi, 2), "macd_h": round(macd, 4)
                })
                print(f"✅ [{original_ticker}] 已更新。")

        supabase.table("portfolio_db").update({"stock_meta": stock_meta}).eq("id", target_id).execute()
        print("🎉 雲端自動化任務完成！")
