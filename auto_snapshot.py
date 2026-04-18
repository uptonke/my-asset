import os
import pytz
import requests
import pandas as pd
import io
from datetime import datetime
from supabase import create_client, Client
import warnings
import yfinance as yf

warnings.filterwarnings('ignore')

# ==========================================
# 1. 安全讀取金鑰 (GitHub Secrets)
# ==========================================
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    raise ValueError("❌ 找不到 Supabase 金鑰！請確認 GitHub Secrets 設定。")

supabase: Client = create_client(url, key)

# ==========================================
# 💱 輔助函數：獲取即時 USD/TWD 匯率
# ==========================================
def get_usd_twd_rate(default_rate=32.5):
    try:
        print("💱 正在透過 Yahoo Finance 獲取即時 USD/TWD 匯率...")
        # 抓取 TWD=X (美金對台幣)
        ticker = yf.Ticker("TWD=X")
        # 拿最近一天的收盤價
        current_rate = ticker.history(period="1d")['Close'].iloc[-1]
        print(f"✅ 成功獲取即時匯率: {current_rate:.4f}")
        return float(current_rate)
    except Exception as e:
        print(f"⚠️ 獲取即時匯率失敗 ({e})，啟動 Fallback 機制使用預設匯率: {default_rate}", flush=True)
        return float(default_rate)

# ==========================================
# 🛠️ 輔助函數：從 Google Sheet 抓取自訂價格 (Header 綁定版)
# ==========================================
def get_sheet_prices(sheet_url):
    if not sheet_url:
        return {}
    try:
        # 從網址萃取 sheet_id
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/1cVoE67-mR9lQQLn4FE_GYftAOAR2RjvaL3MgqIUQ880/edit?gid=0#gid=0"
        
        response = requests.get(csv_url)
        response.raise_for_status() # 確認連線成功
        
        # header=0 代表第一列是標題列
        df = pd.read_csv(io.StringIO(response.text), header=0)
        
        # 將所有欄位名稱轉成大寫並去頭尾，增加容錯率
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
        # 定義你可能在 Sheet 使用的欄位名稱 (可自行擴充)
        ticker_candidates = ['TICKER', 'SYMBOL', '代號', '股票代號']
        price_candidates = ['PRICE', 'CURRENT PRICE', '價格', '報價', '目前報價']
        
        # 動態尋找存在的欄位
        ticker_col = next((col for col in df.columns if col in ticker_candidates), None)
        price_col = next((col for col in df.columns if col in price_candidates), None)
        
        if not ticker_col or not price_col:
            print(f"⚠️ Sheet 解析失敗：找不到對應的標題列。請確保有 {ticker_candidates[0]} 與 {price_candidates[0]}。", flush=True)
            return {}
            
        # 清理資料：只留下欄位有值的 row，並轉成 Dictionary
        df = df.dropna(subset=[ticker_col, price_col])
        price_dict = dict(zip(
            df[ticker_col].astype(str).str.upper().str.strip(), 
            pd.to_numeric(df[price_col], errors='coerce')
        ))
        
        # 過濾掉無法轉換為數字的無效價格 (NaN)
        return {k: v for k, v in price_dict.items() if pd.notna(v)}
        
    except Exception as e:
        print(f"⚠️ Google Sheet 報價抓取失敗: {e}", flush=True)
        return {}

# ==========================================
# 📸 核心邏輯：執行每日資產快照
# ==========================================
def run_daily_snapshot():
    print("📸 開始執行每日資產快照 (Google Sheet 驅動版)...")
    
    # 2. 抓取目前資料庫狀態
    res = supabase.table("portfolio_db").select("*").eq("id", 1).execute()
    if not res.data:
        print("❌ 找不到資料庫 id=1 的紀錄。")
        return
        
    data = res.data[0]
    ledger = data.get("ledger_data", [])
    history = data.get("history_data", [])
    settings = data.get("settings", {})
    
    if not ledger:
        print("⚠️ 帳本為空，沒有部位可供快照，任務結束。")
        return

    # 3. 獲取即時匯率與 Google Sheet 網址
    fallback_rate = float(settings.get("exchangeRate", 32.5))
    exchange_rate = get_usd_twd_rate(fallback_rate) # 自動抓取或降級
    sheet_url = settings.get("sheetUrl", "")
    
    if not sheet_url:
        print("⚠️ 警告：找不到 Google Sheet 網址，將無法獲取最新報價，快照可能會失真。")
        
    # 🌟 4. 下載最高優先級的 Sheet 報價
    print("📥 正在從 Google Sheet 同步最新報價...")
    sheet_prices = get_sheet_prices(sheet_url)
    print(f"📊 成功抓取 {len(sheet_prices)} 筆標的報價。")

    # 5. 結算每一檔股票的「目前剩餘股數」與「總成本」
    holdings = {}
    for tx in ledger:
        t = tx.get("ticker")
        if not t: continue
        
        t = str(t).upper().strip()
        
        if t not in holdings:
            holdings[t] = {"shares": 0, "total_cost": 0, "category": tx.get("category", "台股")}
            
        if tx["type"] == "Buy":
            holdings[t]["shares"] += float(tx.get("shares", 0))
            holdings[t]["total_cost"] += abs(float(tx.get("totalCashFlow", 0)))
        elif tx["type"] == "Sell":
            avg_cost = holdings[t]["total_cost"] / holdings[t]["shares"] if holdings[t]["shares"] > 0 else 0
            holdings[t]["shares"] -= float(tx.get("shares", 0))
            holdings[t]["total_cost"] -= avg_cost * float(tx.get("shares", 0))

    # 過濾掉已經賣光的標的 (股數趨近於0)
    active_holdings = {k: v for k, v in holdings.items() if v["shares"] > 0.0001}

    # 6. 計算今日總市值與總成本
    total_assets_twd = 0
    total_cost_twd = 0
    missing_price_tickers = []
    
    print("\n🧮 開始計算各部位市值...")
    for ticker, h_data in active_holdings.items():
        # 優先使用 Google Sheet 的價格
        raw_price = sheet_prices.get(ticker)
        
        # 如果 Sheet 裡找不到這檔股票的價格，發出警告，並暫時使用持倉均價代替
        if raw_price is None:
            missing_price_tickers.append(ticker)
            raw_price = h_data["total_cost"] / h_data["shares"] if h_data["shares"] > 0 else 0
            
        # 判斷是否為美股，決定是否需要乘上匯率
        is_usd = h_data.get("category") == "美股"
        current_price_twd = float(raw_price) * exchange_rate if is_usd else float(raw_price)
        
        asset_value = h_data["shares"] * current_price_twd
        total_assets_twd += asset_value
        total_cost_twd += h_data["total_cost"]
        
        # 印出單檔明細方便 Debug
        currency_label = "USD" if is_usd else "TWD"
        print(f"  - [{ticker}] 股數: {h_data['shares']:.2f} | 單價: {raw_price:.2f} {currency_label} | 市值: {asset_value:,.0f} TWD")

    if missing_price_tickers:
        print(f"\n⚠️ 警告：以下標的在 Google Sheet 中找不到報價，已使用持倉均價暫代計算市值：")
        print(f"   {', '.join(missing_price_tickers)}")
        print("   建議您將這些代號補上您的 Google Sheet。")

    # 7. 準備寫入 History (強制使用台北時間，避免 GitHub 伺服器時差)
    tw_tz = pytz.timezone('Asia/Taipei')
    today_str = datetime.now(tw_tz).strftime('%Y-%m-%d')
    
    new_record = {
        "date": today_str,
        "assets": round(total_assets_twd),
        "cost": round(total_cost_twd)
    }
    
    # 移除當天可能已經存在的手動紀錄，避免重複，然後加入新紀錄
    updated_history = [h for h in history if h.get("date") != today_str]
    updated_history.append(new_record)
    
    # 確保歷史紀錄按日期排序
    updated_history.sort(key=lambda x: x["date"])

    # 8. 上傳更新回 Supabase
    supabase.table("portfolio_db").update({"history_data": updated_history}).eq("id", 1).execute()
    
    print(f"\n🎉 快照任務圓滿完成！")
    print(f"📅 紀錄日期: {today_str}")
    print(f"💰 總淨值: NT$ {round(total_assets_twd):,}")
    print(f"💵 總成本: NT$ {round(total_cost_twd):,}")

if __name__ == "__main__":
    run_daily_snapshot()
