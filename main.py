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
import urllib.parse  # 💡 升級：引入網址解析庫，準備建立代理隧道
import json
from google import genai

warnings.filterwarnings('ignore')

# ==========================================
# 1. 讀取環境變數與初始化
# ==========================================
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# ==========================================
# 🌟 2. 總經與市場參數自動化抓取 (全面切換至 Yahoo Finance 穩定源)
# ==========================================
print("🌍 啟動量化大腦：開始透過 Yahoo API 抓取市場參數...", flush=True)

try:
    # A. 抓取美國公債殖利率 (Yahoo Finance Tickers)
    # ^TNX = 10年期公債殖利率
    # ^IRX = 13週(約3個月)國庫券殖利率 (Yahoo 沒有穩定的2年期代號，在量化實務中，以3個月來算長短利差同樣具備衰退前瞻性)
    print("   ⏳ 正在抓取公債殖利率...", flush=True)
    bonds = yf.download(["^TNX", "^IRX"], period="1mo", progress=False)["Close"]
    
    # 確保是 Series (單取代號防呆)
    y10_series = bonds["^TNX"] if isinstance(bonds, pd.DataFrame) else bonds
    y3m_series = bonds["^IRX"] if isinstance(bonds, pd.DataFrame) else bonds
    
    y10 = float(y10_series.dropna().iloc[-1])
    y3m = float(y3m_series.dropna().iloc[-1])
    
    # B. 抓取高收益債利差 (透過 HYG ETF 與 10Y 公債殖利率反推)
    # HYG (iShares iBoxx $ High Yield Corporate Bond ETF) 殖利率估算
    print("   ⏳ 正在計算信用利差...", flush=True)
    hyg = yf.Ticker("HYG")
    try:
        hyg_yield = hyg.info.get('yield', 0.05) * 100 
    except:
        hyg_yield = 7.5 # 如果 API 沒給，用長期平均 7.5% 估算
    hy_spread = max(0.1, hyg_yield - y10) # 信用利差 = 垃圾債殖利率 - 10年期無風險利率

    # C. 抓取比特幣動能 (BTC-USD)
    print("   ⏳ 正在計算加密貨幣動能...", flush=True)
    btc_data = yf.download("BTC-USD", period="1mo", progress=False)["Close"]
    if isinstance(btc_data, pd.DataFrame): btc_data = btc_data.iloc[:, 0]
    btc_mom = ((btc_data.dropna().iloc[-1] / btc_data.dropna().iloc[0]) - 1) * 100

    # D. 抓取 SPY 計算 SML/CML 市場參數
    print("   ⏳ 正在計算 SPY 長期報酬與短期波動...", flush=True)
    spy = yf.download("SPY", period="10y", progress=False)["Close"]
    if isinstance(spy, pd.DataFrame): spy = spy.iloc[:, 0]
    
    spy_cagr = ((spy.dropna().iloc[-1] / spy.dropna().iloc[0]) ** (1/10)) - 1
    spy_vol = spy.dropna().tail(252).pct_change().std() * np.sqrt(252)
    # ==========================================
    # 🧠 插入階段：Gemini AI 總經深度解析
    # ==========================================
    print("🤖 喚醒 Gemini AI 進行總經與風險診斷...", flush=True)
    ai_insights = {}
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            # 建立給 AI 的 System Prompt，要求它扮演量化經理人
            prompt = f"""
            你是一位華爾街頂級的量化避險基金經理人。請根據以下最新的市場參數，給出嚴格、客觀的市場診斷。
            切勿迎合，直接指出潛在風險或機會。
            
            【當前市場數據】
            - 10年期無風險利率 (Rf): {macro_payload['market_rf']}%
            - 標普500預期報酬 (Rm): {macro_payload['market_rm']}%
            - 標普500波動率 (σm): {macro_payload['market_sm']}%
            - 10Y-3M 利差 (衰退指標): {macro_payload['yield_curve']}%
            - 高收益債信用利差 (恐慌指標): {macro_payload['hy_spread']}%
            - 比特幣近一月動能: {macro_payload['btc_1m_mom']}%
            
            【輸出要求】
            請必須且只能回傳一個 JSON 格式，不要包含任何 Markdown 標籤 (例如 ```json)，結構如下：
            {{
                "summary": "一句話總結目前總經環境與資金流向 (30字內)",
                "details": [
                    {{"icon": "⚖️", "color": "text-blue-400", "title": "資金成本分析", "desc": "對無風險利率與期望報酬的解讀"}},
                    {{"icon": "⚠️", "color": "text-red-400", "title": "尾部風險警示", "desc": "針對利差與波動率的隱憂分析"}},
                    {{"icon": "💡", "color": "text-yellow-400", "title": "配置建議", "desc": "給予當下的資產配置戰略建議"}}
                ]
            }}
            """
            
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            
            # 清理並解析 JSON (完美融入你的錯誤處理架構)
            text = response.text.strip().strip('`')
            if text.lower().startswith('json'):
                text = text[4:].strip()
            
            ai_insights = json.loads(text)
            print("✅ AI 診斷報告生成成功！", flush=True)
            
            # 將 AI 生成的見解打包進要上傳的總經數據中
            macro_payload['ai_analysis'] = ai_insights

        except Exception as e:
            print(f"⚠️ AI 診斷生成失敗 (將略過此步驟繼續): {e}", flush=True)
    else:
        print("⚠️ 未偵測到 GEMINI_API_KEY，跳過 AI 診斷。")

    # ==========================================
    # E. 寫入 Supabase (維持你原來的動態尋標邏輯)
    # ==========================================
    print("🚀 正在同步至 Supabase...", flush=True)
    # ... 下面接著你原本的 existing = supabase.table("portfolio_db").select("id").limit(1).execute() ...

    # E. 封裝最終數據 (強制 float)
    macro_payload = {
        "yield_10y": float(round(y10, 2)),
        "yield_2y": float(round(y3m, 2)), # 名稱為 2y，實質改用 3m 確保穩定性
        "yield_curve": float(round(y10 - y3m, 2)), 
        "hy_spread": float(round(hy_spread, 2)),
        "btc_1m_mom": float(round(btc_mom, 2)),
        "market_rf": float(round(y10, 2)),
        "market_rm": float(round(spy_cagr * 100, 2)),
        "market_sm": float(round(spy_vol * 100, 2))
    }
    
    print(f"📈 計算完成 -> Rf: {macro_payload['market_rf']}%, Rm: {macro_payload['market_rm']}%, σm: {macro_payload['market_sm']}%", flush=True)

    # E. 寫入 Supabase (動態尋標防彈邏輯)
    print("🚀 正在同步至 Supabase...", flush=True)
    
    # 💡 升級：不盲目猜測 id=1，直接去資料庫找「目前唯一活著的紀錄」
    existing = supabase.table("portfolio_db").select("id").limit(1).execute()
    
    if len(existing.data) > 0:
        target_id = existing.data[0]['id']
        supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", target_id).execute()
        print(f"✅ 數據同步完成！(已精準寫入至紀錄 id={target_id})", flush=True)
    else:
        # 如果資料庫被清空了，就自動幫你建一筆最乾淨的初始資料
        print("⚠️ 偵測到空資料庫，正在建立全新量化設定檔...", flush=True)
        supabase.table("portfolio_db").insert({"id": 1, "macro_meta": macro_payload}).execute()
        print("✅ 數據初始化並同步完成！", flush=True)

except Exception as e:
    print(f"🔥 發生錯誤: {str(e)}", flush=True)
    raise e

# ==========================================
# 🧠 3. 股票多因子管線 (往下維持原邏輯不變)
# ==========================================
def get_sheet_prices(url_str):
    print("📊 正在從 Google Sheet 抓取自訂報價...", flush=True)
    if not url_str:
        return {}
    try:
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', url_str)
        gid_match = re.search(r'[#&?]gid=([0-9]+)', url_str)
        if not match:
            return {}
        sheet_id = match.group(1)
        gid = gid_match.group(1) if gid_match else '0'
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
        
        df = pd.read_csv(csv_url, header=None)
        price_map = {}
        for _, row in df.iterrows():
            if len(row) >= 2 and pd.notna(row[0]) and pd.notna(row[1]):
                ticker = str(row[0]).strip().upper()
                try:
                    price = float(row[1])
                    price_map[ticker] = price
                    if ':' in ticker:
                        price_map[ticker.split(':')[1].strip()] = price
                except:
                    pass
        print(f"✅ 成功抓取 {len(price_map)} 筆自訂報價！", flush=True)
        return price_map
    except Exception as e:
        print(f"⚠️ Sheet 報價讀取失敗，將使用預設報價: {e}", flush=True)
        return {}
print("\n⏳ 接著開始執行股票多因子管線...")
response = supabase.table("portfolio_db").select("*").eq("id", 1).execute()
data = response.data

if not data:
    print("❌ 資料庫沒東西或連線失敗！")
else:
    db_record = data[0]
    stock_meta = db_record.get("stock_meta", {})
    settings = db_record.get("settings", {})
    
    sheet_url = settings.get("sheetUrl", "")
    sheet_prices = get_sheet_prices(sheet_url)
    
    tickers = list(stock_meta.keys())
    
    if tickers:
        tw_bench = "^TWII"  
        us_bench = "SPY"    
        
        yf_tickers = [f"{t}.TW" if re.match(r'^\d+[A-Za-z]?$', t) else t for t in tickers]
        download_list = yf_tickers + [tw_bench, us_bench]

        print(f"⏳ 正在向 Yahoo Finance 請求歷史資料...")
        prices = yf.download(download_list, period="1y")["Close"]
        
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name=download_list[0])

        returns = prices.pct_change()

        print("🧠 開始計算 多因子 風險與動能參數...")
        for i, original_ticker in enumerate(tickers):
            yf_ticker = yf_tickers[i]

            if original_ticker in sheet_prices:
                stock_meta[original_ticker]["last_price"] = float(sheet_prices[original_ticker])

            if yf_ticker not in returns.columns:
                continue

            stock_close = prices[yf_ticker].dropna()
            stock_ret = returns[yf_ticker].dropna()
            
            if len(stock_ret) < 60: 
                continue

            is_tw_stock = yf_ticker.endswith(".TW")
            bench_ticker = tw_bench if is_tw_stock else us_bench
            bench_ret = returns[bench_ticker].dropna()
            
            aligned_data = pd.concat([stock_ret, bench_ret], axis=1).dropna()
            
            if len(aligned_data) < 30:
                continue
                
            aligned_stock = aligned_data.iloc[:, 0]
            aligned_bench = aligned_data.iloc[:, 1]

            ewma_var = aligned_stock.ewm(alpha=0.06).var().iloc[-1]
            ann_std = np.sqrt(ewma_var * 252) * 100

            cov = aligned_stock.cov(aligned_bench)
            bench_var = aligned_bench.var()
            beta = cov / bench_var if bench_var > 0 else 1.0

            rsi_series = ta.rsi(stock_close, length=14)
            rsi_14 = rsi_series.iloc[-1] if rsi_series is not None and not rsi_series.empty else 50.0

            macd_df = ta.macd(stock_close, fast=12, slow=26, signal=9)
            macd_hist = macd_df.iloc[-1, 1] if macd_df is not None and not macd_df.empty else 0.0

            mom_6m = stock_close.pct_change(periods=126).iloc[-1] * 100 if len(stock_close) > 126 else 0.0

            stock_meta[original_ticker]["std"] = round(ann_std, 2)
            stock_meta[original_ticker]["beta"] = round(beta, 2)
            stock_meta[original_ticker]["rsi"] = round(rsi_14, 2) if pd.notna(rsi_14) else 50.0
            stock_meta[original_ticker]["macd_h"] = round(macd_hist, 4) if pd.notna(macd_hist) else 0.0
            stock_meta[original_ticker]["mom_6m"] = round(mom_6m, 2) if pd.notna(mom_6m) else 0.0

            print(f"✅ [{original_ticker}] 更新 -> 基準:{bench_ticker}, Beta:{beta:.2f}, Std:{ann_std:.1f}%, RSI:{rsi_14:.1f}")

        print("🚀 正在將多因子參數與最新估值打回 Supabase...")
        supabase.table("portfolio_db").update({"stock_meta": stock_meta}).eq("id", 1).execute()
        print("🎉 雲端自動化任務完成！")
