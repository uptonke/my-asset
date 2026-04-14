import os
import io
import re
import json
import warnings
import traceback
import requests
import numpy as np
import pandas as pd
import yfinance as yf
import pandas_ta as ta
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
# 🌟 2. 第一階段：總經與市場參數自動化抓取
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
    y3m = float(y3m_clean.iloc[-1]) if not y3m_clean.empty else 0.0
    if y3m_clean.empty:
        print("⚠️ 警告：無法獲取 ^IRX 數據，已 fallback 至 0.0")
    
    # B. 抓取高收益債利差
    print("   ⏳ 正在計算信用利差...", flush=True)
    try:
        hyg_yield = yf.Ticker("HYG").info.get('yield', 0.05) * 100 
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
    print(f"📈 參數計算完成 -> Rf: {macro_payload['market_rf']}%, Rm: {macro_payload['market_rm']}%, σm: {macro_payload['market_sm']}%", flush=True)
    
    # ==========================================
    # 🧠 F. Gemini AI 雙模組備援診斷系統 (靜態超強備援管線)
    # ==========================================
    print("🤖 喚醒 Gemini AI 進行總經與風險診斷...", flush=True)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            # 🚀 捨棄容易報錯的動態抓取，直接部署「五重護城河」
            model_pipeline = [
                "gemini-3.0-pro",        # 夢幻頂規
                "gemini-3.0-flash",      # 性價比之王
                "gemini-2.5-pro",        # 高智商備援
                "gemini-2.5-flash",      # 穩定主力
                "gemini-2.0-flash"       # 絕對保底
            ]
                
            print(f"📡 系統配置 AI 備援管線: {model_pipeline}", flush=True)

            # 🚀 3. 加入強制的 JSON Schema，預防 AI 亂輸出
            prompt = f"""
            你是一位量化避險基金經理。請診斷以下數據：
            Rf: {macro_payload['market_rf']}%, Rm: {macro_payload['market_rm']}%, σm: {macro_payload['market_sm']}%
            衰退指標 (10Y-3M): {macro_payload['yield_curve']}%
            信用利差: {macro_payload['hy_spread']}%
            BTC動能: {macro_payload['btc_1m_mom']}%
            
            請嚴格依照以下 JSON 結構回傳結果，絕對不要輸出 Markdown 標籤或其他廢話：
            {{
                "summary": "一句話總結當前總經環境與操作建議",
                "details": [
                    {{
                        "icon": "🌟(填入相關emoji)", 
                        "color": "text-green-400 (或 text-red-400 / text-blue-400 等 Tailwind 顏色)", 
                        "title": "指標名稱與狀態", 
                        "desc": "詳細的量化解讀與資產配置建議"
                    }}
                ]
            }}
            """
            
            ai_success = False

            for model_name in model_pipeline:
                try:
                    response = client.models.generate_content(model=model_name, contents=prompt)
                    
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if not json_match:
                        raise ValueError("模型未回傳合法 JSON 結構")
                    
                    macro_payload['ai_analysis'] = json.loads(json_match.group(0))
                    print(f"✅ AI 診斷成功！(使用模型: {model_name})", flush=True)
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
# 📊 3. 第二階段：股票多因子管線
# ==========================================
print("\n⏳ 接著開始執行股票多因子管線...", flush=True)

def get_sheet_prices(url_str):
    if not url_str: return {}
    print("📊 正在從 Google Sheet 抓取自訂報價...", flush=True)
    try:
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', url_str)
        gid_match = re.search(r'[#&?]gid=([0-9]+)', url_str)
        if not match: return {}
        
        csv_url = f"https://docs.google.com/spreadsheets/d/{match.group(1)}/gviz/tq?tqx=out:csv&gid={gid_match.group(1) if gid_match else '0'}"
        
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

try:
    response = supabase.table("portfolio_db").select("*").limit(1).execute()
    if response.data:
        db_record = response.data[0]
        stock_meta = db_record.get("stock_meta", {})
        ledger_data = db_record.get("ledger_data", [])
        
        # 💡 從 Ledger 帳本中抽出所有標的，與舊的 stock_meta 合併防呆
        ledger_tickers = [str(tx["ticker"]).strip().upper() for tx in ledger_data if tx.get("ticker")]
        all_tickers = list(set(list(stock_meta.keys()) + ledger_tickers))
        
        for t in all_tickers:
            if t not in stock_meta: stock_meta[t] = {}

        sheet_prices = get_sheet_prices(db_record.get("settings", {}).get("sheetUrl", ""))
        
        if all_tickers:
            tw_bench, us_bench = "^TWII", "SPY"
            proxy_map = {"統一奔騰": "00981A.TW", "統一黑馬": "0050.TW", "安聯台灣科技": "0052.TW"}
            
            download_list = [tw_bench, us_bench]
            yf_tickers = []
            
            for t in all_tickers:
                if t in proxy_map: target = proxy_map[t]
                elif bool(re.search(r'[\u4e00-\u9fff]', t)): target = t
                elif re.match(r'^\d+$', t): target = f"{t}.TW"
                else: target = t
                
                yf_tickers.append(target)
                if target not in download_list: download_list.append(target)

            print(f"⏳ 正在向 Yahoo Finance 請求 {len(download_list)} 檔標的歷史資料...", flush=True)
            prices_df = yf.download(download_list, period="1y", progress=False)["Close"]
            
            if isinstance(prices_df, pd.Series):
                prices_df = prices_df.to_frame(name=download_list[0])
                
            returns = prices_df.pct_change()

            print("🧠 開始計算多因子風險與動能參數...", flush=True)
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
                    
                    stock_meta[original_ticker].update({
                        "beta": round(beta, 2), 
                        "std": round(ann_std, 2),
                        "rsi": round(rsi, 2), 
                        "macd_h": round(macd_h, 4)
                    })
                    print(f"✅ [{original_ticker}] 已更新 -> Beta: {beta:.2f}, Std: {ann_std:.1f}%, RSI: {rsi:.1f}")
                else:
                    if original_ticker not in proxy_map and not bool(re.search(r'[\u4e00-\u9fff]', original_ticker)):
                        print(f"⚠️ [{original_ticker}] 在 Yahoo 找不到對應標的 ({yf_ticker})。")

            supabase.table("portfolio_db").update({"stock_meta": stock_meta}).eq("id", target_id).execute()
            print("🎉 雲端自動化任務完成！")

except Exception as e:
    print(f"🔥 股票管線處理發生錯誤:\n{traceback.format_exc()}", flush=True)
    raise e
