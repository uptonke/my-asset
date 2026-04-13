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
warnings.filterwarnings('ignore')

# ==========================================
# 1. 安全地讀取 GitHub Secrets
# ==========================================
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    raise ValueError("❌ 找不到環境變數！請確認 GitHub Secrets 設定。")

supabase: Client = create_client(url, key)

# 🛠️ 輔助函數：從 Google Sheet 抓取自訂價格
def get_sheet_prices(sheet_url):
    if not sheet_url:
        return {}
    try:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        response = requests.get(csv_url)
        df = pd.read_csv(io.StringIO(response.text), header=None)
        return dict(zip(df[0].astype(str).str.upper().str.strip(), df[1]))
    except Exception as e:
        print(f"⚠️ 讀取 Sheet 失敗: {e}")
        return {}

# ==========================================
# 🌟 2. 總經與另類數據抓取 (Macro & Alternative Data)
# ==========================================
print("🌍 開始抓取 FRED 總經數據與市場參數...")
try:
    def get_fred_latest(series_id):
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        df = pd.read_csv(url, parse_dates=['DATE'], index_col='DATE', na_values='.')
        return float(df[series_id].ffill().dropna().iloc[-1])

    # 數據抓取
    y10 = get_fred_latest('DGS10')
    y2 = get_fred_latest('DGS2')
    hy = get_fred_latest('BAMLH0A0HYM2')
    
    spy = yf.download("SPY", period="10y", progress=False)["Close"]
    spy_10y_cagr = ((spy.iloc[-1] / spy.iloc[0]) ** (1/10)) - 1
    spy_1y_vol = spy.tail(252).pct_change().std() * np.sqrt(252)

    # 💡 核心升級：使用標準 Python float 徹底隔絕 Numpy 型別
    # 這是解決 NULL 欄位的終極關鍵
    macro_payload = {
        "yield_10y": float(round(y10, 2)),
        "yield_curve": float(round(y10 - y2, 2)),
        "hy_spread": float(round(hy, 2)),
        "market_rf": float(round(y10, 2)),
        "market_rm": float(round(spy_10y_cagr * 100, 2)),
        "market_sm": float(round(spy_1y_vol * 100, 2)),
        "btc_1m_mom": 0.0 # 暫時佔位
    }
    
    print(f"🚀 準備寫入 Supabase: {macro_payload}")

    # 執行更新並捕捉回傳結果
    result = supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", 1).execute()
    
    if not result.data:
        print("❌ 更新失敗：找不到 id=1 的列，或是資料庫無回應。")
    else:
        print("✅ 雲端同步成功！")

except Exception as e:
    print(f"🔥 發生致命錯誤: {str(e)}")
    raise e # 強制 Actions 報紅燈，不准裝死


# ==========================================
# 🧠 3. 股票多因子運算與 Google Sheet 價格同步 (雙基準大腦)
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
