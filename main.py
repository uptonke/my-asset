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
print("🌍 啟動量化大腦：開始抓取 FRED 與市場參數...", flush=True)

try:
    def get_fred_latest(series_id):
        print(f"   ⏳ 正在呼叫 FRED API ({series_id})...", flush=True)
        target_url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            # 策略 A：嘗試直連 (只給 3 秒，既然常被封鎖就不浪費時間)
            res = requests.get(target_url, headers=headers, timeout=3)
            res.raise_for_status()
        except requests.exceptions.RequestException:
            # 💡 核心戰略 B：直連失敗，立刻啟動反向代理路由 (Reverse Proxy Bypass)
            print(f"   ⚠️ 偵測到 IP 封鎖，啟動反向代理路由繞道抓取 ({series_id})...", flush=True)
            encoded_url = urllib.parse.quote(target_url, safe='')
            proxy_url = f"https://api.allorigins.win/raw?url={encoded_url}"
            res = requests.get(proxy_url, headers=headers, timeout=15)
            res.raise_for_status()

        df = pd.read_csv(io.StringIO(res.text), parse_dates=['DATE'], index_col='DATE', na_values='.')
        return float(df[series_id].ffill().dropna().iloc[-1])

    # A. 抓取 FRED 數據
    y10 = get_fred_latest('DGS10')
    y2 = get_fred_latest('DGS2')
    hy = get_fred_latest('BAMLH0A0HYM2')

    # B. 抓取比特幣動能 (BTC-USD)
    print("   ⏳ 正在呼叫 Yahoo Finance (BTC-USD)...", flush=True)
    btc_data = yf.download("BTC-USD", period="1mo", progress=False)["Close"]
    if isinstance(btc_data, pd.DataFrame): btc_data = btc_data.iloc[:, 0]
    btc_mom = ((btc_data.iloc[-1] / btc_data.iloc[0]) - 1) * 100

    # C. 抓取 SPY 計算 SML/CML 市場參數
    print("   ⏳ 正在呼叫 Yahoo Finance (SPY 10年數據)...", flush=True)
    spy = yf.download("SPY", period="10y", progress=False)["Close"]
    if isinstance(spy, pd.DataFrame): spy = spy.iloc[:, 0]
    
    spy_cagr = ((spy.iloc[-1] / spy.iloc[0]) ** (1/10)) - 1
    spy_vol = spy.tail(252).pct_change().std() * np.sqrt(252)

    # D. 封裝數據
    macro_payload = {
        "yield_10y": float(round(y10, 2)),
        "yield_2y": float(round(y2, 2)),
        "yield_curve": float(round(y10 - y2, 2)),
        "hy_spread": float(round(hy, 2)),
        "btc_1m_mom": float(round(btc_mom, 2)),
        "market_rf": float(round(y10, 2)),
        "market_rm": float(round(spy_cagr * 100, 2)),
        "market_sm": float(round(spy_vol * 100, 2))
    }
    
    print(f"📈 計算完成 -> Rf: {macro_payload['market_rf']}%, Rm: {macro_payload['market_rm']}%, σm: {macro_payload['market_sm']}%", flush=True)

    # E. 寫入 Supabase
    print("🚀 正在同步至 Supabase...", flush=True)
    res = supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", 1).execute()
    
    if len(res.data) > 0:
        print("✅ 數據同步完成！", flush=True)
    else:
        raise Exception("❌ 資料庫更新失敗：找不到對應的 id=1 紀錄。")

except Exception as e:
    print(f"🔥 發生錯誤: {str(e)}", flush=True)
    raise e

# ==========================================
# 🧠 3. 股票多因子管線 (往下維持原邏輯不變)
# ==========================================
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
