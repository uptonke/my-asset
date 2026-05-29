#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from supabase import create_client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

TAIPEI_TZ = timezone(timedelta(hours=8))
TODAY_TPE = datetime.now(TAIPEI_TZ).date()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_SECRET_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "portfolio_db")
PORTFOLIO_ROW_ID = int(os.getenv("PORTFOLIO_ROW_ID", "1"))
CONFIG_PATH = os.getenv("OFFICIAL_DATA_CONFIG_PATH", "config/official_data_sources.json")

TWSE_ENDPOINTS = {
    "institutional_investors": "https://openapi.twse.com.tw/v1/exchangeReport/T86",
    "margin_trading": "https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN",
    "market_value_volume": "https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK",
}

# 公開資料 URL：優先讀 GitHub Variables；沒有 Variables 時讀 config/official_data_sources.json。
# 這些不是 Secret，建議放 repo config，必要時再用 Variables 覆蓋。
DATA_GOV_TW_URL_ENV = {
    "business_signal": "TAIWAN_BUSINESS_SIGNAL_URL",
    "export_orders": "TAIWAN_EXPORT_ORDERS_URL",
    "cpi": "TAIWAN_CPI_URL",
    "gdp": "TAIWAN_GDP_URL",
    "money_supply": "TAIWAN_MONEY_SUPPLY_URL",
    "fx_reserves": "TAIWAN_FX_RESERVES_URL",
}

TREASURY_ENDPOINTS = {
    "daily_treasury_statement": "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/dts_table_1",
    "debt_to_penny": "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny",
}

DEFAULT_WORLD_BANK_INDICATORS = {
    "usa_real_gdp_growth": {"countries": "USA", "indicator": "NY.GDP.MKTP.KD.ZG"},
    "usa_cpi_inflation": {"countries": "USA", "indicator": "FP.CPI.TOTL.ZG"},
    "usa_broad_money_growth": {"countries": "USA", "indicator": "FM.LBL.BMNY.ZG"},
}

OPTIONAL_URL_MAP_ENVS = {
    "bis": "BIS_API_URLS",
    "oecd": "OECD_API_URLS",
    "imf": "IMF_API_URLS",
}


def finite(x: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if isinstance(x, str):
            x = x.replace(",", "").replace("%", "").strip()
        v = float(x)
        return v if math.isfinite(v) else default
    except Exception:
        return default


def parse_number(x: Any) -> Optional[float]:
    return finite(x)


def standard_date(value: Any) -> Optional[str]:
    if value in {None, ""}:
        return None
    text = str(value).strip()
    # TWSE often uses ROC dates: 114/05/29 or 114年05月29日
    m = re.match(r"^(\d{2,3})[/-](\d{1,2})[/-](\d{1,2})$", text)
    if m:
        y, mo, d = map(int, m.groups())
        if y < 1911:
            y += 1911
        return f"{y:04d}-{mo:02d}-{d:02d}"
    text = text.replace("年", "-").replace("月", "-").replace("日", "")
    try:
        return pd.to_datetime(text).date().isoformat()
    except Exception:
        return None


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1.2, min=1, max=12), retry=retry_if_exception_type((requests.RequestException, RuntimeError)))
def http_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    resp = requests.get(url, params=params or {}, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/csv,*/*"}, timeout=30)
    if resp.status_code in {429, 500, 502, 503, 504}:
        raise RuntimeError(f"retryable HTTP {resp.status_code}")
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        # data.gov.tw 有時直接給 CSV/TXT；保留前幾行，避免 pipeline 中斷。
        return {"raw_text_preview": resp.text[:3000]}




def load_official_data_config() -> Dict[str, Any]:
    path = Path(CONFIG_PATH) if "Path" in globals() else None
    # Avoid a hard dependency on pathlib import at top in older patch merges.
    try:
        from pathlib import Path as _Path
        cfg_path = _Path(CONFIG_PATH)
        if cfg_path.exists():
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}


def env_or_config_url(config: Dict[str, Any], section: str, key: str, env_name: str) -> str:
    env_value = os.getenv(env_name, "").strip()
    if env_value:
        return env_value
    value = ((config.get(section) or {}).get(key) or "") if isinstance(config, dict) else ""
    return str(value).strip()


def env_or_config_map(config: Dict[str, Any], group: str, env_name: str) -> Tuple[Dict[str, Any], Optional[str]]:
    raw = os.getenv(env_name, "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed, "env"
            return {}, f"{env_name} must be JSON object"
        except Exception as exc:
            return {}, f"{env_name} parse:{exc}"
    value = (((config.get("global") or {}).get(group)) or {}) if isinstance(config, dict) else {}
    if isinstance(value, dict):
        return value, "config" if value else None
    return {}, f"config.global.{group} must be JSON object"


def env_or_config_world_bank(config: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    indicators = DEFAULT_WORLD_BANK_INDICATORS.copy()
    raw = os.getenv("WORLD_BANK_INDICATORS", "").strip()
    if raw:
        try:
            override = json.loads(raw)
            if isinstance(override, dict):
                indicators.update(override)
                return indicators, "env"
            return indicators, "WORLD_BANK_INDICATORS must be JSON object"
        except Exception as exc:
            return indicators, f"WORLD_BANK_INDICATORS parse:{exc}"
    cfg = (config.get("world_bank") or {}) if isinstance(config, dict) else {}
    if isinstance(cfg, dict):
        indicators.update({k: v for k, v in cfg.items() if isinstance(v, dict)})
        return indicators, "config" if cfg else None
    return indicators, "config.world_bank must be JSON object"

def latest_row(rows: Any) -> Optional[Dict[str, Any]]:
    if isinstance(rows, dict):
        data = rows.get("data") or rows.get("result") or rows.get("records") or rows.get("items")
        if isinstance(data, list):
            rows = data
    if not isinstance(rows, list) or not rows:
        return None
    return rows[-1] if isinstance(rows[-1], dict) else {"value": rows[-1]}


def numeric_sum(rows: List[Dict[str, Any]], include_keywords: List[str], exclude_keywords: Optional[List[str]] = None) -> Optional[float]:
    exclude_keywords = exclude_keywords or []
    total = 0.0
    used = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        for k, v in row.items():
            name = str(k)
            if all(word in name for word in include_keywords) and not any(word in name for word in exclude_keywords):
                n = parse_number(v)
                if n is not None:
                    total += n
                    used += 1
    return total if used else None


def summarize_twse() -> Dict[str, Any]:
    out: Dict[str, Any] = {"updated_at": str(TODAY_TPE), "sources": {}, "summary": {}, "errors": []}
    for key, url in TWSE_ENDPOINTS.items():
        try:
            data = http_json(url)
            rows = data if isinstance(data, list) else data.get("data") if isinstance(data, dict) else []
            if not isinstance(rows, list):
                rows = []
            out["sources"][key] = {"url": url, "rows": len(rows), "latest_sample": latest_row(rows)}
            if key == "institutional_investors":
                out["summary"]["foreign_net_buy_sell"] = numeric_sum(rows, ["外資", "買賣超"], ["自營商"])
                out["summary"]["dealer_net_buy_sell"] = numeric_sum(rows, ["自營商", "買賣超"])
                out["summary"]["investment_trust_net_buy_sell"] = numeric_sum(rows, ["投信", "買賣超"])
            elif key == "margin_trading":
                out["summary"]["margin_balance_change"] = numeric_sum(rows, ["融資", "今日餘額"])
                out["summary"]["short_balance_change"] = numeric_sum(rows, ["融券", "今日餘額"])
            elif key == "market_value_volume":
                row = latest_row(rows) or {}
                out["summary"]["market_latest"] = row
        except Exception as exc:
            out["errors"].append(f"{key}:{exc}")
    return out


def fetch_configured_open_data(config: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"updated_at": str(TODAY_TPE), "datasets": {}, "missing_config": [], "errors": [], "config_path": CONFIG_PATH}
    for key, env_name in DATA_GOV_TW_URL_ENV.items():
        url = env_or_config_url(config, "taiwan", key, env_name)
        if not url:
            out["missing_config"].append(f"taiwan.{key} / {env_name}")
            continue
        source_mode = "env" if os.getenv(env_name, "").strip() else "config"
        try:
            data = http_json(url)
            rows = data if isinstance(data, list) else data.get("data") if isinstance(data, dict) else None
            sample = latest_row(rows) if isinstance(rows, list) else None
            out["datasets"][key] = {"source_mode": source_mode, "env": env_name, "url": url, "sample": sample, "rows": len(rows) if isinstance(rows, list) else None}
        except Exception as exc:
            out["errors"].append(f"{key}:{exc}")
    return out


def summarize_treasury() -> Dict[str, Any]:
    out: Dict[str, Any] = {"updated_at": str(TODAY_TPE), "sources": {}, "summary": {}, "errors": []}
    for key, url in TREASURY_ENDPOINTS.items():
        try:
            data = http_json(url, {"sort": "-record_date", "page[size]": 5})
            rows = data.get("data") if isinstance(data, dict) else []
            sample = rows[0] if rows else None
            out["sources"][key] = {"url": url, "rows": len(rows), "latest_sample": sample}
            if key == "daily_treasury_statement" and sample:
                out["summary"]["dts_latest_date"] = sample.get("record_date")
                out["summary"]["dts_latest"] = sample
            if key == "debt_to_penny" and sample:
                out["summary"]["debt_latest_date"] = sample.get("record_date")
                out["summary"]["debt_latest"] = sample
        except Exception as exc:
            out["errors"].append(f"{key}:{exc}")
    return out


def summarize_world_bank(config: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"updated_at": str(TODAY_TPE), "indicators": {}, "errors": []}
    indicators, source_note = env_or_config_world_bank(config)
    if source_note and "parse" in source_note or source_note and "must" in source_note:
        out["errors"].append(source_note)
    out["source_mode"] = source_note or "default"
    for key, spec in indicators.items():
        try:
            countries = spec["countries"]
            indicator = spec["indicator"]
            url = f"https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}"
            data = http_json(url, {"format": "json", "per_page": 100, "MRV": 5})
            rows = data[1] if isinstance(data, list) and len(data) > 1 else []
            latest = None
            for row in rows or []:
                if row.get("value") is not None:
                    latest = row
                    break
            out["indicators"][key] = {"countries": countries, "indicator": indicator, "latest": latest}
        except Exception as exc:
            out["errors"].append(f"{key}:{exc}")
    return out


def summarize_optional_url_maps(config: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for group, env_name in OPTIONAL_URL_MAP_ENVS.items():
        group_out = {"updated_at": str(TODAY_TPE), "configured": False, "items": {}, "errors": []}
        url_map, source_note = env_or_config_map(config, group, env_name)
        if source_note and ("parse" in source_note or "must" in source_note):
            group_out["errors"].append(source_note)
            out[group] = group_out
            continue
        if not url_map:
            group_out["missing_config"] = f"global.{group} / {env_name}"
            out[group] = group_out
            continue
        group_out["configured"] = True
        group_out["source_mode"] = source_note or "config"
        for key, url in url_map.items():
            try:
                data = http_json(str(url))
                if isinstance(data, list):
                    sample = latest_row(data)
                    rows = len(data)
                elif isinstance(data, dict):
                    sample = latest_row(data) or data.get("raw_text_preview")
                    rows = len(data.get("data") or []) if isinstance(data.get("data"), list) else None
                else:
                    sample, rows = None, None
                group_out["items"][key] = {"url": url, "rows": rows, "sample": sample}
            except Exception as exc:
                group_out["errors"].append(f"{key}:{exc}")
        out[group] = group_out
    return out


def build_official_weekly_meta() -> Dict[str, Any]:
    config = load_official_data_config()
    twse = summarize_twse()
    taiwan_open_data = fetch_configured_open_data(config)
    treasury = summarize_treasury()
    world_bank = summarize_world_bank(config)
    optional = summarize_optional_url_maps(config)

    missing = []
    errors = []
    for block in [twse, taiwan_open_data, treasury, world_bank, *optional.values()]:
        missing.extend(block.get("missing_config", []) if isinstance(block, dict) else [])
        errors.extend(block.get("errors", []) if isinstance(block, dict) else [])

    official = {
        "version": "weekly_official_macro_v2_config_first",
        "config_path": CONFIG_PATH,
        "config_loaded": bool(config),
        "updated_at": datetime.now(TAIPEI_TZ).isoformat(timespec="seconds"),
        "date": str(TODAY_TPE),
        "twse": twse,
        "taiwan_open_data": taiwan_open_data,
        "us_treasury": treasury,
        "world_bank": world_bank,
        "bis": optional.get("bis", {}),
        "oecd": optional.get("oecd", {}),
        "imf": optional.get("imf", {}),
        "data_quality": {
            "missing_optional_config": missing,
            "error_count": len(errors),
            "errors": errors[:12],
        },
        "notes": [
            "TWSE 與 U.S. Treasury / World Bank 預設不需要 API key。",
            "data.gov.tw 多數資料集不需要 key；實際資料 URL 建議放 config/official_data_sources.json。",
            "GitHub Variables 仍可覆蓋 config，適合臨時改 URL。",
            "BIS / OECD / IMF 已保留 URL map 入口；建議先放精選資料 URL，不要一次抓全庫。",
        ],
    }
    return official


def main() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    row = client.table(SUPABASE_TABLE).select("macro_meta").eq("id", PORTFOLIO_ROW_ID).single().execute().data
    macro_meta = row.get("macro_meta") if row and isinstance(row.get("macro_meta"), dict) else {}
    official = build_official_weekly_meta()
    macro_meta["official_weekly"] = official
    client.table(SUPABASE_TABLE).update({"macro_meta": macro_meta}).eq("id", PORTFOLIO_ROW_ID).execute()
    print(
        "OK official weekly meta "
        f"twse_errors={len(official['twse'].get('errors', []))} "
        f"open_data_missing={len(official['taiwan_open_data'].get('missing_config', []))} "
        f"errors={official['data_quality']['error_count']}"
    )


if __name__ == "__main__":
    main()
