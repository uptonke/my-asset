from pathlib import Path

path = Path('scripts/update_stock_meta.py')
text = path.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    text = text.replace(old, new, 1)


def replace_in_function(function_name: str, old: str, new: str, label: str) -> None:
    global text
    marker = f'def {function_name}('
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f'{label}: function {function_name} not found')
    end = text.find('\ndef ', start + len(marker))
    if end < 0:
        end = len(text)
    block = text[start:end]
    count = block.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match in {function_name}, found {count}')
    block = block.replace(old, new, 1)
    text = text[:start] + block + text[end:]


replace_once(
'''def compute_beta_and_corr(asset: pd.DataFrame, bench: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    if asset.empty or bench.empty:
        return None, None
    a = asset[["date", "close"]].copy()
    b = bench[["date", "close"]].copy()
    a["date"] = pd.to_datetime(a["date"]).dt.date
    b["date"] = pd.to_datetime(b["date"]).dt.date
    merged = pd.merge(a, b, on="date", suffixes=("_asset", "_bench")).sort_values("date")
    if len(merged) < 80:
        return None, None
    aligned = pd.concat([merged["close_asset"].pct_change(), merged["close_bench"].pct_change()], axis=1).dropna()
    aligned.columns = ["asset", "bench"]
    if len(aligned) < 60:
        return None, None
    var = float(np.var(aligned["bench"], ddof=1))
    if var == 0 or not math.isfinite(var):
        return None, None
    beta = float(np.cov(aligned["asset"], aligned["bench"], ddof=1)[0, 1] / var)
    corr = float(aligned["asset"].corr(aligned["bench"]))
    return beta, corr
''',
'''def compute_beta_and_corr(asset: pd.DataFrame, bench: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    if asset.empty or bench.empty:
        return None, None
    a = asset[["date", "close"]].copy()
    b = bench[["date", "close"]].copy()
    a["date"] = pd.to_datetime(a["date"]).dt.date
    b["date"] = pd.to_datetime(b["date"]).dt.date
    a["close"] = pd.to_numeric(a["close"], errors="coerce").replace([np.inf, -np.inf], np.nan)
    b["close"] = pd.to_numeric(b["close"], errors="coerce").replace([np.inf, -np.inf], np.nan)
    a = a.dropna(subset=["close"])
    b = b.dropna(subset=["close"])
    a = a[a["close"] > 0]
    b = b[b["close"] > 0]
    merged = pd.merge(a, b, on="date", suffixes=("_asset", "_bench")).sort_values("date")
    if len(merged) < 80:
        return None, None
    aligned = pd.concat([
        merged["close_asset"].pct_change(fill_method=None),
        merged["close_bench"].pct_change(fill_method=None),
    ], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    aligned.columns = ["asset", "bench"]
    if len(aligned) < 60:
        return None, None
    var = float(np.var(aligned["bench"], ddof=1))
    if var == 0 or not math.isfinite(var):
        return None, None
    beta = float(np.cov(aligned["asset"], aligned["bench"], ddof=1)[0, 1] / var)
    corr = float(aligned["asset"].corr(aligned["bench"]))
    if not math.isfinite(beta):
        beta = None
    if not math.isfinite(corr):
        corr = None
    return beta, corr
''',
'compute_beta_and_corr')

replace_once(
'''def compute_meta(ticker: str, category: str, df: pd.DataFrame, source: str, extras: Dict[str, Any]) -> Dict[str, Any]:
    df = df.dropna(subset=["close"]).sort_values("date").copy()
    close = pd.to_numeric(df["close"], errors="coerce").dropna()
    returns = close.pct_change().dropna()
''',
'''def compute_meta(ticker: str, category: str, df: pd.DataFrame, source: str, extras: Dict[str, Any]) -> Dict[str, Any]:
    df = df.dropna(subset=["close"]).sort_values("date").copy()
    close = pd.to_numeric(df["close"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    close = close[close > 0]
    returns = close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).dropna()
''',
'compute_meta returns cleanup')

replace_once(
'''def clean_price_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty or "date" not in df.columns or "close" not in df.columns:
        return pd.Series(dtype=float)
    out = df[["date", "close"]].copy()
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None).dt.normalize()
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna(subset=["date", "close"]).drop_duplicates(subset=["date"]).sort_values("date")
    if out.empty:
        return pd.Series(dtype=float)
    return pd.Series(out["close"].values, index=out["date"], dtype=float)
''',
'''def clean_price_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty or "date" not in df.columns or "close" not in df.columns:
        return pd.Series(dtype=float)
    out = df[["date", "close"]].copy()
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None).dt.normalize()
    out["close"] = pd.to_numeric(out["close"], errors="coerce").replace([np.inf, -np.inf], np.nan)
    out = out.dropna(subset=["date", "close"]).drop_duplicates(subset=["date"]).sort_values("date")
    out = out[out["close"] > 0]
    if out.empty:
        return pd.Series(dtype=float)
    return pd.Series(out["close"].values, index=out["date"], dtype=float)
''',
'clean_price_series')

replace_in_function(
    'ewma_annual_vol',
    '        r = pd.to_numeric(returns, errors="coerce").dropna()\n',
    '        r = pd.to_numeric(returns, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()\n',
    'ewma annual vol finite cleanup',
)

replace_in_function(
    'ewma_covariance_matrix',
    '        df = returns.apply(pd.to_numeric, errors="coerce").dropna(how="any")\n',
    '        df = returns.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna(how="any")\n',
    'ewma covariance finite cleanup',
)

replace_once(
'''def merge_stock_meta(existing: Dict[str, Any], new_meta: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    merged = dict(existing or {})
    for ticker, meta in new_meta.items():
        old = merged.get(ticker, {})
        if not isinstance(old, dict):
            old = {}
        merged[ticker] = {**old, **meta}
    return merged

def write_supabase_stock_meta(client, merged_stock_meta: Dict[str, Any]) -> None:
    if DRY_RUN:
        print("DRY_RUN=true, not writing to Supabase.")
        return
    try:
        client.table(SUPABASE_TABLE).upsert({"id": int(PORTFOLIO_ROW_ID), "stock_meta": merged_stock_meta}, on_conflict="id").execute()
    except Exception as exc:
        fail(f"Failed to write Supabase stock_meta: {exc}")
''',
'''def merge_stock_meta(existing: Dict[str, Any], new_meta: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    merged = dict(existing or {})
    for ticker, meta in new_meta.items():
        old = merged.get(ticker, {})
        if not isinstance(old, dict):
            old = {}
        merged[ticker] = {**old, **meta}
    return merged


def sanitize_json_value(value: Any) -> Any:
    """Recursively convert numpy scalars and non-finite floats into strict JSON values."""
    if isinstance(value, dict):
        return {str(k): sanitize_json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_json_value(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def write_supabase_stock_meta(client, merged_stock_meta: Dict[str, Any]) -> None:
    if DRY_RUN:
        print("DRY_RUN=true, not writing to Supabase.")
        return
    try:
        safe_stock_meta = sanitize_json_value(merged_stock_meta)
        client.table(SUPABASE_TABLE).upsert({"id": int(PORTFOLIO_ROW_ID), "stock_meta": safe_stock_meta}, on_conflict="id").execute()
    except Exception as exc:
        fail(f"Failed to write Supabase stock_meta: {exc}")
''',
'strict JSON Supabase write')

path.write_text(text, encoding='utf-8')
print('patched scripts/update_stock_meta.py')
