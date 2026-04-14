import os
import json
import datetime
from supabase import create_client, Client

def main():
    print("🌍 啟動異地備援程序...")

    # 1. 讀取 GitHub Secrets 裡的環境變數
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("❌ 找不到 Supabase 憑證，請檢查 GitHub Secrets 設定！")
        exit(1)

    # 2. 連線至 Supabase
    try:
        supabase: Client = create_client(url, key)
        print("✅ 成功連線至 Supabase 資料庫")
    except Exception as e:
        print(f"❌ Supabase 連線失敗: {e}")
        exit(1)

    # 3. 抓取 portfolio_db 的所有資料
    try:
        print("⏳ 正在下載量化系統資料庫...")
        response = supabase.table("portfolio_db").select("*").execute()
        data = response.data

        if not data:
            print("⚠️ 資料庫為空，無資料可備份。")
            return
            
    except Exception as e:
        print(f"❌ 資料下載失敗: {e}")
        exit(1)

    # 4. 建立備份資料夾並存檔
    try:
        # 確保 backups 資料夾存在
        os.makedirs("backups", exist_ok=True)
        
        # 產生帶有時間戳記的檔名 (例如: portfolio_2026-04-14.json)
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"backups/portfolio_backup_{today_str}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 備份成功！資料已寫入: {filename}")
        
    except Exception as e:
        print(f"❌ 檔案寫入失敗: {e}")
        exit(1)

if __name__ == "__main__":
    main()
