import os
import io
import warnings
from datetime import datetime
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse, parse_qs

import pandas as pd
import pytz
import requests
import yfinance as yf
from supabase import create_client, Client

warnings.filterwarnings("ignore")

# ==========================================
# 基本設定
# ==========================================
TABLE_NAME = "portfolio_db"
ROW_ID = 1
TIMEZONE = "Asia/Taipei"
DEFAULT_EXCHANGE_RATE = 32.5
REQUEST_TIMEOUT = 20

# 你可能在 Google Sheet 使用的欄位名稱
TICKER_CANDIDATES = ["TICKER", "SYMBOL", "代號", "股票代號"]
PRICE_CANDIDATES = ["PRICE", "CURRENT PRICE", "價格", "報價", "目前報價"]

# 判斷哪些 category 視為美元計價
USD_CATEGORIES = {"美股", "US", "US STOCK", "美國股票"}

# ==========================================
# 安全讀取金鑰
# ==========================================
def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("❌ 找不到 Supabase 金鑰，請確認 GitHub Secrets 設定。")

    return create_client(url, key)


# ==========================================
# HTTP Session
# ==========================================
def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "portfolio-daily-snapshot/1.0"
    })
    return session


# ==========================================
# 匯率：抓 USD/TWD
# ==========================================
def get_usd_twd_rate(default_rate: float = DEFAULT_EXCHANGE_RATE) -> float:
    try:
        print("💱 正在透過 Yahoo Finance 獲取即時 USD/TWD 匯率...")
        # TWD=X 通常代表 1 USD = 幾 TWD
        ticker = yf.Ticker("TWD=X")
        hist = ticker.history(period="5d")

        if hist.empty or "Close" not in hist.columns:
            raise ValueError("Yahoo Finance 未回傳有效匯率資料。")

        current_rate = float(hist["Close"].dropna().iloc[-1])
        print(f"✅ 成功獲取即時匯率: {current_rate:.4f}")
        return current_rate

    except Exception as e:
        print(f"⚠️ 匯率抓取失敗（{e}），改用 fallback 匯率: {default_rate}")
        return float(default_rate)


# ==========================================
# Google Sheet URL -> CSV URL
# ==========================================
def build_google_sheet_csv_url(sheet_url: str) -> str:
    """
    支援常見的 Google Sheet 分享網址：
    - https://docs.google.com/spreadsheets/d/<sheet_id>/edit?gid=0#gid=0
    - 其他帶 gid 的形式
    """
    if "/d/" not in sheet_url:
        raise ValueError("不是有效的 Google Sheet 網址。")

    sheet_id = sheet_url.split("/d/")[1].split("/")[0]

    parsed = urlparse(sheet_url)
    query = parse_qs(parsed.query)
    gid = query.get("gid", [None])[0]

    # 有 gid 就帶 gid；沒有也能抓第一個工作表
    if gid:
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"


# ==========================================
# 從 Google Sheet 抓自訂價格
# ==========================================
def get_sheet_prices(sheet_url):
    if not sheet_url:
        return {}

    try:
        # 從網址抓 sheet_id
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]

        # 嘗試抓 gid；沒有就預設 0
        gid = "0"
        if "gid=" in sheet_url:
            gid = sheet_url.split("gid=")[1].split("&")[0].split("#")[0]

        # 正確的 CSV 匯出網址
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"

        print(f"📥 正在讀取 Google Sheet: {csv_url}")

        response = requests.get(csv_url, timeout=20)
        response.raise_for_status()

        # 你的 sheet 沒有 header，所以 header=None
        df = pd.read_csv(io.StringIO(response.text), header=None)

        if df.shape[1] < 2:
            print("⚠️ Sheet 格式錯誤：至少需要 A 欄代號、B 欄價格。", flush=True)
            return {}

        # 只取前兩欄：A=ticker, B=price
        df = df.iloc[:, :2].copy()
        df.columns = ["ticker", "price"]

        # 清理資料
        df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
        df["price"] = pd.to_numeric(df["price"], errors="coerce")

        # 去掉空白列 / 無效價格
        df = df.dropna(subset=["ticker", "price"])
        df = df[df["ticker"] != ""]

        price_dict = dict(zip(df["ticker"], df["price"]))

        print(f"✅ 成功抓取 {len(price_dict)} 筆 Sheet 報價。")
        return {k: float(v) for k, v in price_dict.items()}

    except Exception as e:
        print(f"⚠️ Google Sheet 報價抓取失敗: {e}", flush=True)
        return {}

# ==========================================
# 抓 Supabase 單筆資料
# ==========================================
def fetch_portfolio_row(supabase: Client) -> Dict[str, Any]:
    res = supabase.table(TABLE_NAME).select("*").eq("id", ROW_ID).execute()
    if not res.data:
        raise ValueError(f"❌ 找不到 {TABLE_NAME} 中 id={ROW_ID} 的紀錄。")
    return res.data[0]


# ==========================================
# Ledger -> Active Holdings
# ==========================================
def aggregate_holdings(ledger: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    以移動平均成本法整理剩餘持倉。
    回傳格式：
    {
        "AAPL": {
            "shares": 10.0,
            "total_cost": 50000.0,
            "category": "美股"
        }
    }
    """
    holdings: Dict[str, Dict[str, Any]] = {}

    for tx in ledger:
        ticker = str(tx.get("ticker", "")).upper().strip()
        if not ticker:
            continue

        tx_type = str(tx.get("type", "")).strip()
        shares = float(tx.get("shares", 0) or 0)
        total_cash_flow = float(tx.get("totalCashFlow", 0) or 0)
        category = tx.get("category", "台股")

        if ticker not in holdings:
            holdings[ticker] = {
                "shares": 0.0,
                "total_cost": 0.0,
                "category": category,
            }

        h = holdings[ticker]

        if tx_type == "Buy":
            h["shares"] += shares
            h["total_cost"] += abs(total_cash_flow)

        elif tx_type == "Sell":
            if h["shares"] <= 0:
                print(f"⚠️ [{ticker}] 偵測到賣出，但目前持股為 0，已略過此筆賣出。")
                continue

            sell_shares = min(shares, h["shares"])
            avg_cost = h["total_cost"] / h["shares"] if h["shares"] > 0 else 0.0

            h["shares"] -= sell_shares
            h["total_cost"] -= avg_cost * sell_shares

            # 防止浮點數殘值
            if h["shares"] < 1e-8:
                h["shares"] = 0.0
                h["total_cost"] = 0.0

    active_holdings = {
        ticker: h for ticker, h in holdings.items()
        if h["shares"] > 0.0001
    }

    return active_holdings


# ==========================================
# 判斷是否美元計價
# ==========================================
def is_usd_category(category: Any) -> bool:
    if category is None:
        return False
    return str(category).strip().upper() in {c.upper() for c in USD_CATEGORIES}


# ==========================================
# 估值
# ==========================================
def value_holdings(
    holdings: Dict[str, Dict[str, Any]],
    sheet_prices: Dict[str, float],
    exchange_rate: float
) -> Tuple[float, float, List[str]]:
    total_assets_twd = 0.0
    total_cost_twd = 0.0
    missing_price_tickers: List[str] = []

    print("\n🧮 開始計算各部位市值...")

    for ticker, h in holdings.items():
        shares = float(h["shares"])
        total_cost = float(h["total_cost"])
        category = h.get("category", "台股")

        raw_price = sheet_prices.get(ticker)

        # Sheet 沒價格 -> 用持倉均價先代替
        if raw_price is None:
            missing_price_tickers.append(ticker)
            raw_price = total_cost / shares if shares > 0 else 0.0

        usd_flag = is_usd_category(category)
        price_twd = float(raw_price) * exchange_rate if usd_flag else float(raw_price)

        asset_value = shares * price_twd
        total_assets_twd += asset_value
        total_cost_twd += total_cost

        currency_label = "USD" if usd_flag else "TWD"
        print(
            f"  - [{ticker}] 股數: {shares:.4f} | "
            f"單價: {raw_price:.4f} {currency_label} | "
            f"市值: {asset_value:,.0f} TWD"
        )

    return total_assets_twd, total_cost_twd, missing_price_tickers


# ==========================================
# 更新 history_data
# ==========================================
def upsert_history(
    history: List[Dict[str, Any]],
    assets_twd: float,
    cost_twd: float
) -> List[Dict[str, Any]]:
    tw_tz = pytz.timezone(TIMEZONE)
    today_str = datetime.now(tw_tz).strftime("%Y-%m-%d")

    new_record = {
        "date": today_str,
        "assets": round(assets_twd),
        "cost": round(cost_twd),
    }

    updated_history = [h for h in history if h.get("date") != today_str]
    updated_history.append(new_record)
    updated_history.sort(key=lambda x: x["date"])

    return updated_history


# ==========================================
# 主流程
# ==========================================
def run_daily_snapshot() -> None:
    print("📸 開始執行每日資產快照（重寫穩定版）...")

    supabase = get_supabase_client()
    session = build_session()

    # 1) 抓資料庫資料
    row = fetch_portfolio_row(supabase)
    ledger = row.get("ledger_data", []) or []
    history = row.get("history_data", []) or []
    settings = row.get("settings", {}) or {}

    if not ledger:
        print("⚠️ 帳本為空，沒有部位可供快照，任務結束。")
        return

    # 2) 匯率與報價
    fallback_rate = float(settings.get("exchangeRate", DEFAULT_EXCHANGE_RATE) or DEFAULT_EXCHANGE_RATE)
    exchange_rate = get_usd_twd_rate(fallback_rate)

    sheet_url = str(settings.get("sheetUrl", "") or "").strip()
    if not sheet_url:
        print("⚠️ 找不到 Google Sheet 網址，將無法同步最新報價，會改用持倉均價 fallback。")

    print("📥 正在從 Google Sheet 同步最新報價...")
    sheet_prices = get_sheet_prices(sheet_url, session)

    # 3) 聚合持倉
    active_holdings = aggregate_holdings(ledger)
    if not active_holdings:
        print("⚠️ 沒有剩餘持倉，任務結束。")
        return

    # 4) 估值
    total_assets_twd, total_cost_twd, missing_price_tickers = value_holdings(
        holdings=active_holdings,
        sheet_prices=sheet_prices,
        exchange_rate=exchange_rate,
    )

    if missing_price_tickers:
        print("\n⚠️ 以下標的在 Google Sheet 找不到報價，已改用持倉均價暫代：")
        print("   " + ", ".join(missing_price_tickers))

    # 5) 更新 history
    updated_history = upsert_history(history, total_assets_twd, total_cost_twd)

    supabase.table(TABLE_NAME).update({
        "history_data": updated_history
    }).eq("id", ROW_ID).execute()

    tw_tz = pytz.timezone(TIMEZONE)
    today_str = datetime.now(tw_tz).strftime("%Y-%m-%d")

    print("\n🎉 快照任務完成")
    print(f"📅 日期: {today_str}")
    print(f"💰 總淨值: NT$ {round(total_assets_twd):,}")
    print(f"💵 總成本: NT$ {round(total_cost_twd):,}")


if __name__ == "__main__":
    run_daily_snapshot()
