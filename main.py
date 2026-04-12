import os
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import pandas_datareader as pdr
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
print("🌍 開始抓取 FRED 總經數據與比特幣避險情緒...")
try:
    start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    
    fred_data = pdr.get_data_fred(['DGS10', 'DGS2', 'BAMLH0A0HYM2'], start_date)
    latest_macro = fred_data.ffill().iloc[-1] 
    
    yield_10y = latest_macro['DGS10']
    yield_2y = latest_macro['DGS2']
    hy_spread = latest_macro['BAMLH0A0HYM2']
    yield_curve = yield_10y - yield_2y 
    
    btc = yf.download("BTC-USD", period="1mo", progress=False)["Close"]
    if isinstance(btc, pd.DataFrame): 
        btc = btc.iloc[:, 0]
    btc_1m_mom = ((btc.iloc[-1] / btc.iloc[0]) - 1) * 100

    macro_meta = {
        "yield_10y": round(yield_10y, 2),
        "yield_2y": round(yield_2y, 2),
        "yield_curve": round(yield_curve, 2),
        "hy_spread": round(hy_spread, 2),
        "btc_1m_mom": round(btc_1m_mom, 2)
    }
    
    print(f"📊 總經狀態 -> 10Y-2Y利差: {yield_curve:.2f}%, 垃圾債利差: {hy_spread:.2f}%, BTC月動能: {btc_1m_mom:.1f}%")
    supabase.table("portfolio_db").update({"macro_meta": macro_meta}).eq("id", 1).execute()
    print("✅ 總經數據已上傳至雲端大腦！")

except Exception as e:
    print(f"⚠️ 總經數據抓取失敗，錯誤訊息：{e}")


# ==========================================
# 🧠 3. 股票多因子運算與 Google Sheet 價格同步
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
    
    # 讀取你的 Google Sheet 網址並抓取最新價格
    sheet_url = settings.get("sheetUrl", "")
    sheet_prices = get_sheet_prices(sheet_url)
    
    tickers = list(stock_meta.keys())
    
    if tickers:
        benchmark = "SPY"
        yf_tickers = [f"{t}.TW" if re.match(r'^\d+[A-Za-z]?$', t) else t for t in tickers]
        download_list = yf_tickers + [benchmark]

        print(f"⏳ 正在向 Yahoo Finance 請求歷史資料...")
        prices = yf.download(download_list, period="1y")["Close"]
        
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name=download_list[0])

        returns = prices.pct_change()

        print("🧠 開始計算 多因子 風險與動能參數...")
        for i, original_ticker in enumerate(tickers):
            yf_ticker = yf_tickers[i]

            # 💡 [新增] 優先將 Google Sheet 裡的真實價格寫入 meta
            if original_ticker in sheet_prices:
                stock_meta[original_ticker]["last_price"] = float(sheet_prices[original_ticker])

            if yf_ticker not in returns.columns:
                continue

            stock_close = prices[yf_ticker].dropna()
            stock_ret = returns[yf_ticker].dropna()
            
            if len(stock_ret) < 60: 
                continue

            bench_ret = returns[benchmark]
            aligned_data = pd.concat([stock_ret, bench_ret], axis=1).dropna()
            
            if len(aligned_data) < 30:
                continue
                
            aligned_stock = aligned_data.iloc[:, 0]
            aligned_bench = aligned_data.iloc[:, 1]

            # (A) EWMA 動態標準差
            ewma_var = aligned_stock.ewm(alpha=0.06).var().iloc[-1]
            ann_std = np.sqrt(ewma_var * 252) * 100
            
            # (B) 1Y Rolling Beta
            cov = aligned_stock.cov(aligned_bench)
            bench_var = aligned_bench.var()
            beta = cov / bench_var if bench_var > 0 else 1.0

            # (C) RSI (14)
            rsi_series = ta.rsi(stock_close, length=14)
            rsi_14 = rsi_series.iloc[-1] if rsi_series is not None and not rsi_series.empty else 50.0

            # (D) MACD Histogram
            macd_df = ta.macd(stock_close, fast=12, slow=26, signal=9)
            macd_hist = macd_df.iloc[-1, 1] if macd_df is not None and not macd_df.empty else 0.0

            # (E) 6M Momentum
            mom_6m = stock_close.pct_change(periods=126).iloc[-1] * 100

            # 寫入 JSON 物件
            stock_meta[original_ticker]["std"] = round(ann_std, 2)
            stock_meta[original_ticker]["beta"] = round(beta, 2)
            stock_meta[original_ticker]["rsi"] = round(rsi_14, 2) if pd.notna(rsi_14) else 50.0
            stock_meta[original_ticker]["macd_h"] = round(macd_hist, 4) if pd.notna(macd_hist) else 0.0
            stock_meta[original_ticker]["mom_6m"] = round(mom_6m, 2) if pd.notna(mom_6m) else 0.0

            print(f"✅ [{original_ticker}] 更新 -> Beta:{beta:.2f}, Std:{ann_std:.1f}%, RSI:{rsi_14:.1f}, MACD_H:{macd_hist:.2f}")

        print("🚀 正在將多因子參數與最新估值打回 Supabase...")
        supabase.table("portfolio_db").update({"stock_meta": stock_meta}).eq("id", 1).execute()
        print("🎉 雲端自動化任務完成！總經與多因子庫已全面升級。")
