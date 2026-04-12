import os
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import pandas_datareader as pdr # 🌟 新增：聯準會數據抓取套件
import datetime
from supabase import create_client, Client
import re
import warnings
warnings.filterwarnings('ignore')

# 1. 安全地讀取 GitHub Secrets
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    raise ValueError("❌ 找不到環境變數！")

supabase: Client = create_client(url, key)

# ==========================================
# 🌟 [新增] 總經與另類數據抓取 (Macro & Alternative Data)
# ==========================================
print("🌍 開始抓取 FRED 總經數據與比特幣避險情緒...")
try:
    # 抓取近 30 天資料以防假日空缺
    start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    
    # DGS10: 美國10年期公債殖利率, DGS2: 美國2年期公債殖利率, BAMLH0A0HYM2: 美國高收益債利差
    fred_data = pdr.get_data_fred(['DGS10', 'DGS2', 'BAMLH0A0HYM2'], start_date)
    latest_macro = fred_data.ffill().iloc[-1] # 取最新一天，填補空值
    
    yield_10y = latest_macro['DGS10']
    yield_2y = latest_macro['DGS2']
    hy_spread = latest_macro['BAMLH0A0HYM2']
    yield_curve = yield_10y - yield_2y # 利差倒掛指標
    
    # 比特幣 30 天動能 (幣圈的資金流動/避險情緒指標)
    btc = yf.download("BTC-USD", period="1mo", progress=False)["Close"]
    if isinstance(btc, pd.DataFrame): # 處理 yfinance 新版結構
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
    
    # 寫入 Supabase
    supabase.table("portfolio_db").update({"macro_meta": macro_meta}).eq("id", 1).execute()
    print("✅ 總經數據已上傳至雲端大腦！")

except Exception as e:
    print(f"⚠️ 總經數據抓取失敗，錯誤訊息：{e}")


# ==========================================
# 2. 以下為原本的股票多因子運算 (維持不變)
# ==========================================
print("⏳ 接著開始執行股票多因子管線...")
# ... (下方保留你原本抓股票、算 RSI、MACD、Beta 的迴圈邏輯) ...
