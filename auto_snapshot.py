import os
import requests
import pandas as pd
import io
import pytz
from datetime import datetime
from supabase import create_client, Client

# 1. 安全讀取金鑰
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

def get_sheet_prices(sheet_url):
    """將 Google Sheet 網址轉換為 CSV 下載並轉為字典"""
    try:
        # 轉換網址為 export=csv 格式
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        # 預設抓第一個分頁，gid=0
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        response = requests.get(csv_url)
        df = pd.read_csv(io.StringIO(response.text), header=None)
        # 假設 A 欄是代號，B 欄是價格
        return dict(zip(df[0].str.upper().str.strip(), df[1]))
    except Exception as e:
        print(f"⚠️ 讀取 Sheet 失敗: {e}")
        return {}

def run_daily_snapshot():
    print("📸 執行從 Google Sheet 驅動的每日快照...")
    res = supabase.table("portfolio_db").select("*").eq("id", 1).execute()
    if not res.data: return
        
    data = res.data[0]
    ledger = data.get("ledger_data", [])
    history = data.get("history_data", [])
    settings = data.get("settings", {})
    
    # 核心改變：直接從設定好的網址抓取最新價格
    sheet_url = settings.get("sheetUrl")
    if not sheet_url:
        print("❌ 設定中找不到 Google Sheet 網址")
        return
        
    price_map = get_sheet_prices(sheet_url)
    exchange_rate = float(settings.get("exchangeRate", 32.5))

    # [這裡保留你原本計算 holdings 的迴圈...]
    # (同上一版 auto_snapshot.py 的步驟 3 & 4，但價格直接使用這裡抓到的 price_map)
    
    # 寫回 Supabase
    # [這裡保留原本上傳 history_data 的邏輯...]
    print(f"✅ 快照完成！所有價格同步自 Google Sheet")

if __name__ == "__main__":
    run_daily_snapshot()
