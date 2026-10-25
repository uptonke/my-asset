from pathlib import Path

MAIN = Path('main.py')
SRC = Path('assets/js/src/app.bundle.source.js')
INDEX = Path('index.html')

main = MAIN.read_text(encoding='utf-8')
src = SRC.read_text(encoding='utf-8')
index = INDEX.read_text(encoding='utf-8')

# 1) Canonical Taiwan ticker aliases: support ETF codes such as 00981A / 00675L,
# and keep embedded system metadata out of the Yahoo/analytics universe.
old_norm = '''    if not t or t in {"NAN", "NONE", "NULL", "-"}:
        return ""

    # Google Finance-style Taiwan symbols are aliases, not distinct assets.
    # Keep the portfolio namespace aligned with ledger tickers such as 2317/2382.
    for prefix in ("TPE:", "TWSE:", "TPEX:"):
        if t.startswith(prefix):
            candidate = t.split(":", 1)[1].strip()
            if re.fullmatch(r"\\d{4}[A-Z]?", candidate):
                t = candidate
            break

    match = re.fullmatch(r"(\\d{4}[A-Z]?)\\.(TW|TWO)", t)
'''
new_norm = '''    if not t or t in {"NAN", "NONE", "NULL", "-"}:
        return ""
    if t.startswith("__") and t.endswith("__"):
        return ""

    # Google Finance-style Taiwan symbols are aliases, not distinct assets.
    # Support 4-6 digit Taiwan stock/ETF codes plus optional suffix letters
    # (e.g. 2317, 00981A, 00675L) and keep one canonical portfolio namespace.
    for prefix in ("TPE:", "TWSE:", "TPEX:"):
        if t.startswith(prefix):
            candidate = t.split(":", 1)[1].strip()
            if re.fullmatch(r"\\d{4,6}[A-Z]?", candidate):
                t = candidate
            break

    match = re.fullmatch(r"(\\d{4,6}[A-Z]?)\\.(TW|TWO)", t)
'''
if old_norm not in main:
    raise SystemExit('normalize_ticker_symbol block not found')
main = main.replace(old_norm, new_norm, 1)

# 2) Reusable current-market-value weighting helper for factor attribution.
anchor = '''    if is_tw_numeric_ticker(t):
        return f"{t}.TW"

    return t


def sigmoid(x):
'''
helper = '''    if is_tw_numeric_ticker(t):
        return f"{t}.TW"

    return t


def build_factor_market_value_weights(active_tickers, valid_yf_tickers, ticker_to_yf, current_shares, stock_meta, prices_df, settings):
    """Build normalized current TWD market-value weights for the factor-return proxy."""
    valid_set = set(valid_yf_tickers or [])
    settings = settings if isinstance(settings, dict) else {}
    fx = _num(settings.get("exchangeRate"), None)
    values = {}
    missing = []
    source_counts = {"stock_meta_market_value_twd": 0, "price_fx_fallback": 0}

    for original in active_tickers or []:
        yf_ticker = ticker_to_yf.get(original, "")
        if not yf_ticker or yf_ticker not in valid_set or yf_ticker not in prices_df.columns:
            continue
        shares = max(0.0, _num(current_shares.get(original), 0.0) or 0.0)
        if shares <= 0:
            continue

        meta = stock_meta.get(original, {}) if isinstance(stock_meta.get(original, {}), dict) else {}
        market_value_twd = _num(meta.get("market_value_twd"), None)
        if market_value_twd is not None and market_value_twd > 0:
            source_counts["stock_meta_market_value_twd"] += 1
        else:
            series = prices_df[yf_ticker].dropna()
            if series.empty:
                missing.append(original)
                continue
            native_price = _num(series.iloc[-1], None)
            is_twd = str(yf_ticker).upper().endswith((".TW", ".TWO"))
            if native_price is None or native_price <= 0 or (not is_twd and (fx is None or fx <= 0)):
                missing.append(original)
                continue
            price_twd = native_price if is_twd else native_price * fx
            market_value_twd = shares * price_twd
            source_counts["price_fx_fallback"] += 1

        if market_value_twd is not None and market_value_twd > 0:
            values[yf_ticker] = values.get(yf_ticker, 0.0) + float(market_value_twd)

    total = float(sum(values.values()))
    diagnostics = {
        "market_value_twd_sum": round(total, 2),
        "asset_count": len(values),
        "missing_tickers": sorted(set(missing)),
        "source_counts": source_counts,
    }
    if total <= 0:
        return pd.Series(dtype=float), diagnostics
    weights = pd.Series({ticker: value / total for ticker, value in values.items()}, dtype=float).sort_index()
    return weights, diagnostics


def sigmoid(x):
'''
if anchor not in main:
    raise SystemExit('map_to_yf_ticker helper anchor not found')
main = main.replace(anchor, helper, 1)

# 3) Remove all-null failed downloads before returns are constructed; preserve mixed-market
# calendars and let each downstream model choose its own complete-case window.
old_prices = '''            prices_df = safe_download_close(download_list, period="10y", progress=False)
            returns = prices_df.pct_change().dropna()
'''
new_prices = '''            prices_df = (
                safe_download_close(download_list, period="10y", progress=False)
                .replace([np.inf, -np.inf], np.nan)
                .dropna(axis=1, how="all")
                .sort_index()
            )
            returns = (
                prices_df.pct_change(fill_method=None)
                .replace([np.inf, -np.inf], np.nan)
                .dropna(how="all")
            )
'''
if old_prices not in main:
    raise SystemExit('prices/returns block not found')
main = main.replace(old_prices, new_prices, 1)

# 4) Initialize explicit factor-model status and make optimizer use a clean complete-case panel.
old_target = '''            target_weights = {}
            if valid_investable:
                num_assets = len(valid_investable)
                dynamic_min = 0.0 if num_assets < 5 else min(0.03, 0.9 / num_assets)
                print(f"🧠 啟動機構級最佳化引擎 (限制 {dynamic_min*100:.0f}%~20%)...", flush=True)
                target_weights = get_optimal_weights(returns[valid_investable], stock_meta, min_wt=dynamic_min, max_wt=1.0 if num_assets < 5 else 0.20)
                
'''
new_target = '''            target_weights = {}
            factor_status = {
                "status": "unavailable",
                "reason_code": "not_run",
                "message": "多因子迴歸尚未執行",
                "sample_count": 0,
                "min_sample_count": 26,
                "weighting_method": "current_market_value_twd",
                "model": "FF5+Momentum+TW_Mkt+Crypto",
            }
            # Never let an old factor snapshot masquerade as a fresh successful run.
            macro_payload.pop("fama_french", None)
            macro_payload["fama_french_status"] = factor_status

            if valid_investable:
                num_assets = len(valid_investable)
                optimizer_returns = returns[valid_investable].dropna(how="any")
                if len(optimizer_returns) >= 30:
                    dynamic_min = 0.0 if num_assets < 5 else min(0.03, 0.9 / num_assets)
                    print(f"🧠 啟動機構級最佳化引擎 (限制 {dynamic_min*100:.0f}%~20%)...", flush=True)
                    target_weights = get_optimal_weights(optimizer_returns, stock_meta, min_wt=dynamic_min, max_wt=1.0 if num_assets < 5 else 0.20)
                else:
                    print(f"⚠️ 最佳化有效完整樣本不足: {len(optimizer_returns)} < 30", flush=True)
                
'''
if old_target not in main:
    raise SystemExit('target/optimizer block not found')
main = main.replace(old_target, new_target, 1)

# 5) Replace the old share-count-weighted factor engine with current TWD market-value weights,
# explicit data-quality status, and model diagnostics.
factor_start_marker = '''                # ==========================================
                # 🌟 終極升級：跨資產 8 因子模型 (FF6 + TW + Crypto)
'''
factor_end_marker = '''                except Exception as e: print(f"⚠️ 8因子迴歸失敗: {e}", flush=True)
'''
start = main.find(factor_start_marker)
if start < 0:
    raise SystemExit('factor block start not found')
end0 = main.find(factor_end_marker, start)
if end0 < 0:
    raise SystemExit('factor block end not found')
end = end0 + len(factor_end_marker)
new_factor = '''                # ==========================================
                # Cross-asset factor model: FF5 + Momentum + TW market + Crypto
                # Current-holdings proxy is weighted by CURRENT TWD MARKET VALUE, never share count.
                # ==========================================
                print("🧠 啟動跨資產 8 因子模型 (FF5 + Momentum + TW_Mkt + Crypto) 迴歸引擎...", flush=True)
                try:
                    import statsmodels.api as sm

                    factor_weights, factor_weight_diag = build_factor_market_value_weights(
                        active_tickers=active_tickers,
                        valid_yf_tickers=valid_investable,
                        ticker_to_yf=ticker_to_yf,
                        current_shares=current_shares,
                        stock_meta=stock_meta,
                        prices_df=prices_df,
                        settings=db_record.get("settings", {}) or {},
                    )
                    factor_status["weight_diagnostics"] = factor_weight_diag

                    if factor_weights.empty:
                        factor_status.update({
                            "reason_code": "market_value_weights_unavailable",
                            "message": "無法建立目前持倉的 TWD 市值權重",
                        })
                    else:
                        domain_kf = "https://mba.tuck.dartmouth.edu"
                        ff5_url = domain_kf + "/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
                        mom_url = domain_kf + "/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip"

                        def parse_french_csv(content):
                            with zipfile.ZipFile(io.BytesIO(content)) as z:
                                name = z.namelist()[0]
                                with z.open(name) as f:
                                    lines = [line.decode('utf-8', errors='ignore') for line in f.readlines()]
                                start_idx = next(
                                    (i - 1 for i, line in enumerate(lines)
                                     if (line.strip().startswith('19') or line.strip().startswith('20')) and ',' in line),
                                    0,
                                )
                                df = pd.read_csv(z.open(name), skiprows=start_idx, index_col=0)
                                df.index = pd.to_datetime(df.index.astype(str).str.strip(), format='%Y%m%d', errors='coerce')
                                df.columns = df.columns.str.strip()
                                return df.dropna().apply(pd.to_numeric, errors='coerce').dropna() / 100.0

                        def fetch_french_zip(url):
                            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                            resp.raise_for_status()
                            if not resp.content.startswith(b"PK"):
                                raise ValueError("Ken French 回傳的不是 zip 檔")
                            return resp.content

                        ff5_data = parse_french_csv(fetch_french_zip(ff5_url))
                        mom_data = parse_french_csv(fetch_french_zip(mom_url))
                        ff_data = pd.concat([ff5_data, mom_data], axis=1).dropna()

                        custom_prices = (
                            safe_download_close(["^TWII", "BTC-USD"], period="10y", progress=False)
                            .replace([np.inf, -np.inf], np.nan)
                            .dropna(axis=1, how="all")
                            .sort_index()
                        )
                        required_custom = {"^TWII", "BTC-USD"}
                        if not required_custom.issubset(set(custom_prices.columns)):
                            raise ValueError("TW_Mkt / Crypto factor price source incomplete")
                        custom_factors = (
                            custom_prices[["^TWII", "BTC-USD"]]
                            .ffill(limit=3)
                            .pct_change(fill_method=None)
                            .replace([np.inf, -np.inf], np.nan)
                            .dropna(how="any")
                            .rename(columns={"^TWII": "TW_Mkt", "BTC-USD": "Crypto"})
                        )

                        factor_cols = [ticker for ticker in factor_weights.index if ticker in prices_df.columns]
                        factor_prices = prices_df[factor_cols].sort_index().ffill(limit=3)
                        factor_daily_returns = (
                            factor_prices.pct_change(fill_method=None)
                            .replace([np.inf, -np.inf], np.nan)
                            .dropna(how="any")
                        )

                        if len(factor_daily_returns) < 30:
                            factor_status.update({
                                "reason_code": "insufficient_daily_portfolio_samples",
                                "message": f"有效日報酬樣本不足（{len(factor_daily_returns)}/30）",
                            })
                        else:
                            usable_weights = factor_weights.reindex(factor_daily_returns.columns).fillna(0.0)
                            usable_weight_sum = float(usable_weights.sum())
                            if usable_weight_sum <= 0:
                                raise ValueError("factor market-value weights sum to zero")
                            usable_weights = usable_weights / usable_weight_sum

                            daily_port_return = factor_daily_returns.mul(usable_weights, axis=1).sum(axis=1)
                            daily_port_return.index = pd.to_datetime(daily_port_return.index).tz_localize(None)
                            daily_port_return.name = 'Port_Ret'

                            # Weekly frequency absorbs market-calendar/time-zone mismatch.
                            weekly_port = daily_port_return.resample('W-FRI').apply(lambda x: (1 + x).prod() - 1)
                            weekly_ff = ff_data.resample('W-FRI').apply(lambda x: (1 + x).prod() - 1)
                            weekly_custom = custom_factors.resample('W-FRI').apply(lambda x: (1 + x).prod() - 1)
                            aligned_data = (
                                pd.concat([weekly_port, weekly_ff, weekly_custom], axis=1)
                                .replace([np.inf, -np.inf], np.nan)
                                .dropna()
                            )

                            sample_count = int(len(aligned_data))
                            factor_status["sample_count"] = sample_count
                            if sample_count < int(factor_status["min_sample_count"]):
                                factor_status.update({
                                    "reason_code": "insufficient_aligned_weekly_samples",
                                    "message": f"有效週樣本不足（{sample_count}/{factor_status['min_sample_count']}）",
                                })
                            else:
                                aligned_data['TW_Mkt_RF'] = aligned_data['TW_Mkt'] - aligned_data['RF']
                                aligned_data['Crypto_RF'] = aligned_data['Crypto'] - aligned_data['RF']

                                Y = (aligned_data['Port_Ret'] - aligned_data['RF']).astype(float)
                                X = sm.add_constant(
                                    aligned_data[['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'Mom', 'TW_Mkt_RF', 'Crypto_RF']]
                                ).astype(float)
                                results = sm.OLS(Y, X).fit()

                                macro_payload["fama_french"] = {
                                    "alpha": float(round(results.params['const'] * 52 * 100, 2)),
                                    "mkt_beta": float(round(results.params['Mkt-RF'], 2)),
                                    "smb": float(round(results.params['SMB'], 2)),
                                    "hml": float(round(results.params['HML'], 2)),
                                    "rmw": float(round(results.params['RMW'], 2)),
                                    "cma": float(round(results.params['CMA'], 2)),
                                    "wml": float(round(results.params['Mom'], 2)),
                                    "tw_mkt": float(round(results.params.get('TW_Mkt_RF', 0), 2)),
                                    "crypto": float(round(results.params.get('Crypto_RF', 0), 2)),
                                    "r_squared": float(round(results.rsquared, 3)),
                                    "adj_r_squared": float(round(results.rsquared_adj, 3)),
                                    "sample_count": sample_count,
                                    "weighting_method": "current_market_value_twd",
                                    "model": "FF5+Momentum+TW_Mkt+Crypto",
                                }
                                factor_status.update({
                                    "status": "available",
                                    "reason_code": "ok",
                                    "message": "模型可用",
                                    "sample_count": sample_count,
                                })
                                print(
                                    f"✅ 8因子運算成功: R²={results.rsquared:.3f}, n={sample_count}, "
                                    f"TW_β={results.params.get('TW_Mkt_RF', 0):.2f}, "
                                    f"Crypto_β={results.params.get('Crypto_RF', 0):.2f}",
                                    flush=True,
                                )
                except Exception as e:
                    factor_status.update({
                        "status": "error",
                        "reason_code": "factor_engine_exception",
                        "message": f"{type(e).__name__}: {str(e)[:180]}",
                    })
                    macro_payload.pop("fama_french", None)
                    print(f"⚠️ 8因子迴歸失敗: {factor_status['message']}", flush=True)
'''
main = main[:start] + new_factor + main[end:]

# Persist status even when no investable assets or regression is unavailable.
for_anchor = '''            for t in active_tickers:
                yf_t = ticker_to_yf.get(t, "")
'''
persist_block = '''            if not valid_investable:
                factor_status.update({
                    "reason_code": "no_valid_investable_assets",
                    "message": "沒有可用於多因子迴歸的有效持倉標的",
                })
            macro_payload["fama_french_status"] = factor_status
            supabase.table("portfolio_db").update({"macro_meta": macro_payload}).eq("id", target_id).execute()

            for t in active_tickers:
                yf_t = ticker_to_yf.get(t, "")
'''
if for_anchor not in main:
    raise SystemExit('factor persistence anchor not found')
main = main.replace(for_anchor, persist_block, 1)

# 6) Frontend state: carry factor-model status through cloud load and stats recomputation.
default_old = '''            ff_rmw: '-', ff_cma: '-', ff_wml: '-', ff_r_squared: '-', 
            ff_tw_mkt: '-', ff_crypto: '-'
'''
default_new = '''            ff_rmw: '-', ff_cma: '-', ff_wml: '-', ff_r_squared: '-', 
            ff_tw_mkt: '-', ff_crypto: '-',
            ff_status: 'unavailable', ff_reason: '尚未產生有效迴歸結果',
            ff_sample_count: 0, ff_weighting: '-'
'''
if default_old not in src:
    raise SystemExit('frontend stats default factor fields not found')
src = src.replace(default_old, default_new, 1)

load_old = '''                        if (macroData.fama_french) {
                            stats.value.ff_alpha = macroData.fama_french.alpha;
                            stats.value.ff_mkt_beta = macroData.fama_french.mkt_beta;
                            stats.value.ff_smb = macroData.fama_french.smb;
                            stats.value.ff_hml = macroData.fama_french.hml;
                            stats.value.ff_rmw = macroData.fama_french.rmw;
                            stats.value.ff_cma = macroData.fama_french.cma;
                            stats.value.ff_wml = macroData.fama_french.wml;
                            stats.value.ff_r_squared = macroData.fama_french.r_squared;
                            stats.value.ff_tw_mkt = macroData.fama_french.tw_mkt;
                            stats.value.ff_crypto = macroData.fama_french.crypto;
                        }
'''
load_new = '''                        const ffStatus = macroData.fama_french_status || {};
                        stats.value.ff_status = ffStatus.status || (macroData.fama_french ? 'available' : 'unavailable');
                        stats.value.ff_reason = ffStatus.message || ffStatus.reason_code || '尚未產生有效迴歸結果';
                        stats.value.ff_sample_count = Number(ffStatus.sample_count ?? macroData.fama_french?.sample_count ?? 0);
                        stats.value.ff_weighting = ffStatus.weighting_method || macroData.fama_french?.weighting_method || '-';

                        if (macroData.fama_french) {
                            stats.value.ff_alpha = macroData.fama_french.alpha;
                            stats.value.ff_mkt_beta = macroData.fama_french.mkt_beta;
                            stats.value.ff_smb = macroData.fama_french.smb;
                            stats.value.ff_hml = macroData.fama_french.hml;
                            stats.value.ff_rmw = macroData.fama_french.rmw;
                            stats.value.ff_cma = macroData.fama_french.cma;
                            stats.value.ff_wml = macroData.fama_french.wml;
                            stats.value.ff_r_squared = macroData.fama_french.r_squared;
                            stats.value.ff_tw_mkt = macroData.fama_french.tw_mkt;
                            stats.value.ff_crypto = macroData.fama_french.crypto;
                        }
'''
if load_old not in src:
    raise SystemExit('frontend factor cloud-load block not found')
src = src.replace(load_old, load_new, 1)

factor_fields = ['ff_alpha', 'ff_mkt_beta', 'ff_smb', 'ff_hml', 'ff_rmw', 'ff_cma', 'ff_wml', 'ff_tw_mkt', 'ff_crypto', 'ff_r_squared']
for field in factor_fields:
    src = src.replace(f"stats.value.{field} || '-'", f"stats.value.{field} ?? '-'")

recompute_old = '''                 ff_crypto: stats.value.ff_crypto ?? '-', 
                 ff_r_squared: stats.value.ff_r_squared ?? '-'
             }; 
'''
recompute_new = '''                 ff_crypto: stats.value.ff_crypto ?? '-', 
                 ff_r_squared: stats.value.ff_r_squared ?? '-',
                 ff_status: stats.value.ff_status || 'unavailable',
                 ff_reason: stats.value.ff_reason || '尚未產生有效迴歸結果',
                 ff_sample_count: Number(stats.value.ff_sample_count || 0),
                 ff_weighting: stats.value.ff_weighting || '-'
             }; 
'''
if recompute_old not in src:
    raise SystemExit('frontend stats recompute factor tail not found')
src = src.replace(recompute_old, recompute_new, 1)

# 7) UI: identify the actual model/proxy and show explicit status/reason rather than a silent dash wall.
old_title = '多因子迴歸解構 (FF5 + Momentum)'
new_title = '多因子迴歸解構 (FF5 + Momentum + TW + Crypto)'
if old_title not in index:
    raise SystemExit('factor panel title not found')
index = index.replace(old_title, new_title, 1)

old_desc = '''<p class="text-xs text-gray-400 mb-5">透過 Carhart 4-Factor 與 FF5 擴充模型，解構投資組合的真實超額報酬來源。($R^2 = {{ stats?.ff_r_squared || '-' }})</p>'''
new_desc = '''<p class="text-xs text-gray-400 mb-5">
                            <span v-if="stats?.ff_status === 'available'">目前持倉以 TWD 市值加權重建報酬 proxy；週頻 OLS。R² = {{ stats?.ff_r_squared ?? '-' }}，n = {{ stats?.ff_sample_count || 0 }}。</span>
                            <span v-else class="text-amber-300">模型暫不可用：{{ stats?.ff_reason || '尚未產生有效迴歸結果' }}</span>
                        </p>'''
if old_desc not in index:
    raise SystemExit('factor panel description not found')
index = index.replace(old_desc, new_desc, 1)

for field in factor_fields:
    index = index.replace(f"stats?.{field} || '-'", f"stats?.{field} ?? '-'")

MAIN.write_text(main, encoding='utf-8')
SRC.write_text(src, encoding='utf-8')
INDEX.write_text(index, encoding='utf-8')
print('Applied multifactor regression repair patch')
