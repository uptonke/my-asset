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
import scipy.optimize as sco
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

    # 🌟 NEW: E. 抓取機構級情緒、通膨與實體經濟指標 (VIX, DXY, Gold, Copper, Oil)
    print("   ⏳ 正在抓取跨資產期貨與情緒指標...", flush=True)
    try:
        vix = float(yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1])
        dxy = float(yf.Ticker("DX-Y.NYB").history(period="5d")['Close'].iloc[-1])
        gold = float(yf.Ticker("GC=F").history(period="5d")['Close'].iloc[-1])
        copper = float(yf.Ticker("HG=F").history(period="5d")['Close'].iloc[-1]) # 銅博士
        oil = float(yf.Ticker("CL=F").history(period="5d")['Close'].iloc[-1])    # WTI原油
        
        # 計算銅金比 (實體經濟擴張指標)
        copper_gold_ratio = (copper / gold) * 100 
    except Exception as e:
        print(f"⚠️ 額外期貨指標抓取失敗，使用預設值: {e}")
        vix, dxy, gold, copper, oil, copper_gold_ratio = 20.0, 100.0, 2000.0, 4.0, 75.0, 0.2

    # F. 🌟 封裝數據 (終極全天候矩陣)
    macro_payload = {
        "yield_10y": float(round(y10, 2)),
        "yield_2y": float(round(y3m, 2)),
        "yield_curve": float(round(y10 - y3m, 2)), 
        "hy_spread": float(round(hy_spread, 2)),
        "btc_1m_mom": float(round(btc_mom, 2)),
        "market_rf": float(round(y10, 2)),
        "market_rm": float(round(spy_cagr * 100, 2)),
        "market_sm": float(round(spy_vol * 100, 2)),
        "vix": float(round(vix, 2)),
        "dxy": float(round(dxy, 2)),
        "gold_price": float(round(gold, 2)),
        "oil_price": float(round(oil, 2)),
        "copper_gold_ratio": float(round(copper_gold_ratio, 4))
    }
    print(f"📈 參數計算完成 -> VIX: {macro_payload['vix']}, 銅金比: {macro_payload['copper_gold_ratio']}, 油價: {macro_payload['oil_price']}", flush=True)
    
    # ==========================================
    # 🧠 Gemini AI 雙模組備援診斷系統
    # ==========================================
    print("🤖 喚醒 Gemini AI 進行總經與風險診斷...", flush=True)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            # 使用 2026 最新的 API 命名
            model_pipeline = [
                "gemini-3.1-pro-preview", 
                "gemini-3-flash-preview", 
                "gemini-2.5-pro", 
                "gemini-2.5-flash", 
                "gemini-2.0-flash"
            ]
                
            # 🌟 NEW: 更新 Prompt，強迫 AI 進行跨資產邏輯推演
            prompt = f"""
            你是一位頂尖的量化避險基金經理。請基於以下總經、情緒與大宗商品指標，進行交叉診斷：
            
            【資金面與流動性 (Financial Conditions)】
            - Rf (無風險利率): {macro_payload['market_rf']}%
            - 衰退指標 (10Y-3M利差): {macro_payload['yield_curve']}% (負值為倒掛)
            - 美元指數 (DXY): {macro_payload['dxy']} (全球流動性)
            - 信用利差 (HY-10Y): {macro_payload['hy_spread']}% (企業融資壓力)
            
            【實體經濟與通膨 (Growth & Inflation)】
            - 銅金比 (Copper/Gold Ratio): {macro_payload['copper_gold_ratio']} (衡量景氣復甦動能)
            - WTI 原油價格: {macro_payload['oil_price']} (通膨預期)
            
            【風險與情緒指標 (Sentiment)】
            - 恐慌指數 (VIX): {macro_payload['vix']}
            - BTC 近一月動能: {macro_payload['btc_1m_mom']}% (高風險偏好)
            - 黃金期貨價格: {macro_payload['gold_price']} (避險需求)
            
            請嚴格依照以下 JSON 結構回傳結果，絕對不要輸出 Markdown 標籤或其他廢話：
            {{
                "summary": "結合 VIX、銅金比與利差，用一句話判斷目前處於經濟週期的哪個階段 (如：擴張、滯脹、衰退)，並給出資產配置方向",
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
# 📊 3. 第二階段：股票多因子管線與最佳化
# ==========================================
print("\n⏳ 接著開始執行股票多因子管線與最佳化...", flush=True)

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

def get_optimal_weights(returns_df, stock_meta, min_wt=0.03, max_wt=0.20):
    num_assets = len(returns_df.columns)
    if num_assets == 0: return {}
    
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252
    risk_free_rate = 0.02 
    
    # 1. 找出哪些資產屬於加密貨幣，哪些屬於低風險資產
    crypto_indices = []
    low_risk_indices = []
    
    for i, ticker in enumerate(returns_df.columns):
        # 這裡從你之前傳入的 stock_meta 或 ticker 名稱判斷
        # 假設 stock_meta[ticker] 裡有 'category' 和 'risk'
        meta = stock_meta.get(ticker, {})
        category = str(meta.get("category", "")).lower()
        risk = str(meta.get("risk", "")).lower() # 你手動定義的 'low'
        
        if "加密" in category or "btc" in ticker.lower() or "eth" in ticker.lower():
            crypto_indices.append(i)
        if risk == "low" or "低風險" in risk:
            low_risk_indices.append(i)

    def neg_sharpe_ratio(weights):
        p_ret = np.sum(mean_returns * weights)
        p_var = np.dot(weights.T, np.dot(cov_matrix, weights))
        p_vol = np.sqrt(p_var)
        return -(p_ret - risk_free_rate) / p_vol

    # 2. 定義約束條件
    constraints = [
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}, # 總和 = 100%
        # 🌟 群組約束 1：加密貨幣總和 <= 20% (即 0.20 - sum >= 0)
        {'type': 'ineq', 'fun': lambda x: 0.20 - np.sum(x[crypto_indices]) if crypto_indices else 1},
        # 🌟 群組約束 2：低風險資產總和 <= 15% (即 0.15 - sum >= 0)
        {'type': 'ineq', 'fun': lambda x: 0.15 - np.sum(x[low_risk_indices]) if low_risk_indices else 1}
    ]
    
    bounds = tuple((min_wt, max_wt) for _ in range(num_assets))
    init_guess = num_assets * [1. / num_assets]

    optimized_result = sco.minimize(
        neg_sharpe_ratio, 
        init_guess, 
        method='SLSQP', 
        bounds=bounds, 
        constraints=constraints
    )

    if optimized_result.success:
        return dict(zip(returns_df.columns, np.round(optimized_result.x, 4)))
    else:
        print(f"⚠️ 最佳化失敗: {optimized_result.message}")
        return {col: 1.0/num_assets for col in returns_df.columns}

try:
    response = supabase.table("portfolio_db").select("*").limit(1).execute()
    if response.data:
        db_record = response.data[0]
        stock_meta = db_record.get("stock_meta", {})
        ledger_data = db_record.get("ledger_data", [])
        
        # 從 Ledger 帳本中抽出所有標的
        ledger_tickers = [str(tx["ticker"]).strip().upper() for tx in ledger_data if tx.get("ticker")]
        all_tickers = list(set(list(stock_meta.keys()) + ledger_tickers))
        
        for t in all_tickers:
            if t not in stock_meta: stock_meta[t] = {}

        sheet_prices = get_sheet_prices(db_record.get("settings", {}).get("sheetUrl", ""))
        
        if all_tickers:
            tw_bench, us_bench = "^TWII", "SPY"
            # 建立代號映射表 (處理自訂基金和特殊標的)
            proxy_map = {
                "統一奔騰": "00981A.TW", 
                "安聯台灣科技": "0052.TW",
                "加密貨幣": "BTC-USD"
            }
            
            download_list = [tw_bench, us_bench]
            yf_tickers = []
            
            for t in all_tickers:
                t_clean = str(t).strip().upper()
                target = t_clean 
                
                if t_clean in proxy_map: 
                    target = proxy_map[t_clean]
                elif bool(re.search(r'[\u4e00-\u9fff]', t_clean)): 
                    target = tw_bench 
                elif re.match(r'^\d+[a-zA-Z]*$', t_clean): 
                    target = f"{t_clean}.TW"
                
                yf_tickers.append(target)
                if target not in download_list: 
                    download_list.append(target)
                    
            print(f"⏳ 正在向 Yahoo Finance 請求 {len(download_list)} 檔標的歷史資料...", flush=True)
            prices_df = yf.download(download_list, period="1y", progress=False)["Close"]
            
            if isinstance(prices_df, pd.Series):
                prices_df = prices_df.to_frame(name=download_list[0])
                
            returns = prices_df.pct_change().dropna()

            print("🧠 啟動機構級最佳化引擎 (限制 3%~20%)...", flush=True)
            # 準備計算最佳權重 (排除大盤指標)
            investable_tickers = [t for t in yf_tickers if t not in [tw_bench, us_bench]]
            # 確保欄位存在
            valid_investable = [t for t in investable_tickers if t in returns.columns]
            
            target_weights = {}
            if valid_investable:
                investable_returns = returns[valid_investable]
                
                # 🌟 動態放寬權重邊界防呆機制
                num_assets = len(valid_investable)
                if num_assets < 5:
                    # 如果庫存標的少於 5 檔，強迫每檔最高 20% 會導致總和永遠達不到 100%
                    # 因此放寬為：不限制最高權重 (1.0)，最低 0%
                    dynamic_min = 0.0
                    dynamic_max = 1.0
                else:
                    # 標的數量充足時，嚴格執行機構級紀律
                    dynamic_min = 0.03
                    dynamic_max = 0.20
                    
                target_weights = get_optimal_weights(
                    investable_returns, 
                    stock_meta, 
                    min_wt=dynamic_min, 
                    max_wt=dynamic_max
                )

            print("🧠 開始計算多因子風險參數並寫入資料庫...", flush=True)
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
                    
                    # 抓取剛算好的目標權重
                    target_w = target_weights.get(yf_ticker, 0.0)
                    
                    stock_meta[original_ticker].update({
                        "beta": round(beta, 2), 
                        "std": round(ann_std, 2),
                        "rsi": round(rsi, 2), 
                        "macd_h": round(macd_h, 4),
                        "target_weight": float(target_w)
                    })
                    print(f"✅ [{original_ticker}] 更新 -> Beta: {beta:.2f}, Std: {ann_std:.1f}%, RSI: {rsi:.1f}, 目標權重: {target_w*100:.2f}%")
                else:
                    if original_ticker not in proxy_map and not bool(re.search(r'[\u4e00-\u9fff]', original_ticker)):
                        print(f"⚠️ [{original_ticker}] 在 Yahoo 找不到對應標的 ({yf_ticker})。")

            supabase.table("portfolio_db").update({"stock_meta": stock_meta}).eq("id", target_id).execute()
            print("🎉 股票元資料與權重任務完成！")

            # ==========================================
            # ⚖️ 4. 第三階段：自動化再平衡與交易訊號生成
            # ==========================================
            print("\n⚖️ 啟動再平衡引擎：計算目標權重落差與交易訊號...", flush=True)
            
            current_holdings = {}
            for tx in ledger_data:
                t = str(tx.get("ticker", "")).strip().upper()
                if not t: continue
                shares = float(tx.get("shares", 0))
                tx_type = str(tx.get("type", "buy")).lower()
                if tx_type in ["sell", "賣出"]:
                    shares = -shares
                current_holdings[t] = current_holdings.get(t, 0) + shares

            portfolio_value = 0.0
            asset_values = {}
            
            for t in all_tickers:
                shares = current_holdings.get(t, 0)
                last_price = stock_meta.get(t, {}).get("last_price", 0.0)
                
                # 如果庫存沒紀錄最新價格，從 yfinance 的 dataframe 抓
                if last_price == 0.0 and yf_tickers:
                    idx = all_tickers.index(t)
                    yt = yf_tickers[idx]
                    if yt in prices_df.columns:
                        last_price = float(prices_df[yt].dropna().iloc[-1])
                
                value = max(0, shares * last_price)
                asset_values[t] = value
                portfolio_value += value

            rebalance_signals = []
            
            if portfolio_value > 0:
                print(f"💰 當前投資組合總淨值估算: {portfolio_value:,.2f}", flush=True)
                for t in all_tickers:
                    target_w = stock_meta.get(t, {}).get("target_weight", 0.0)
                    current_w = asset_values.get(t, 0.0) / portfolio_value
                    delta_w = target_w - current_w
                    
                    target_value = portfolio_value * target_w
                    delta_value = target_value - asset_values.get(t, 0.0)
                    
                    # 變動超過 1% NAV 才發出交易訊號
                    if abs(delta_w) > 0.01:
                        action = "BUY (加碼)" if delta_w > 0 else "SELL (減碼)"
                        rebalance_signals.append({
                            "ticker": t,
                            "action": action,
                            "current_weight": f"{current_w*100:.2f}%",
                            "target_weight": f"{target_w*100:.2f}%",
                            "delta_weight": f"{delta_w*100:.2f}%",
                            "trade_amount": round(delta_value, 2)
                        })
                        print(f"   [{t}] {action} -> 目標: {target_w*100:.1f}%, 當前: {current_w*100:.1f}%, 需調整金額: {delta_value:,.2f}")

            if rebalance_signals and GEMINI_API_KEY:
                print("🤖 喚醒 AI 撰寫再平衡交易執行報告...", flush=True)
                rebalance_prompt = f"""
                你是一位機構級交易員。基金經理已經透過約束最佳化演算法計算出了最新的目標權重。
                
                以下是需要執行的再平衡清單：
                {json.dumps(rebalance_signals, ensure_ascii=False, indent=2)}
                
                當前總經環境診斷摘要：{macro_payload.get('ai_analysis', {}).get('summary', '無')}
                
                請嚴格依照以下 JSON 格式回傳一份給交易台的執行摘要，絕對不要輸出 Markdown 標籤：
                {{
                    "execution_summary": "一句話總結本次再平衡的核心邏輯（例如：因應VIX攀升，減碼高Beta股，加碼防禦資產）",
                    "priority_trades": [
                        {{
                            "ticker": "標的代號",
                            "reason": "為什麼演算法要求加/減碼這檔？(結合總經環境簡短分析)"
                        }}
                    ]
                }}
                """
                
                # 直接用主力引擎產生報告
                rebalance_res = client.models.generate_content(model="gemini-3.1-pro-preview", contents=rebalance_prompt)
                
                try:
                    rb_match = re.search(r'\{.*\}', rebalance_res.text, re.DOTALL)
                    if rb_match:
                        rb_analysis = json.loads(rb_match.group(0))
                        supabase.table("portfolio_db").update({
                            "rebalance_meta": {
                                "signals": rebalance_signals,
                                "ai_execution_plan": rb_analysis
                            }
                        }).eq("id", target_id).execute()
                        print("✅ 再平衡交易清單與 AI 執行報告已成功同步至 Supabase！")
                except Exception as e:
                    print(f"⚠️ AI 執行報告解析失敗: {e}")

except Exception as e:
    print(f"🔥 股票管線處理發生錯誤:\n{traceback.format_exc()}", flush=True)
    raise e
