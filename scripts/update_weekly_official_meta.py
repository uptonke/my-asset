#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from supabase import create_client
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

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

TREASURY_ENDPOINTS = {
    "daily_treasury_statement": "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/dts_table_1",
    "debt_to_penny": "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny",
}

DEFAULT_WORLD_BANK_INDICATORS = {
    "usa_real_gdp_growth": {"countries": "USA", "indicator": "NY.GDP.MKTP.KD.ZG"},
    "usa_cpi_inflation": {"countries": "USA", "indicator": "FP.CPI.TOTL.ZG"},
    "usa_broad_money_growth": {"countries": "USA", "indicator": "FM.LBL.BMNY.ZG"},
}

OPTIONAL_URL_MAP_ENVS = {"bis": "BIS_API_URLS", "oecd": "OECD_API_URLS", "imf": "IMF_API_URLS"}


def parse_num(x: Any) -> Optional[float]:
    try:
        if isinstance(x, str):
            x = x.replace(",", "").replace("%", "").strip()
        return float(x)
    except Exception:
        return None


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1.2, min=1, max=12),
    retry=retry_if_exception_type((requests.RequestException, RuntimeError)),
)
def http_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    resp = requests.get(
        url,
        params=params or {},
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/csv,*/*"},
        timeout=30,
    )
    if resp.status_code in {429, 500, 502, 503, 504}:
        raise RuntimeError(f"retryable HTTP {resp.status_code}")
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"raw_text_preview": resp.text[:3000]}


def load_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def latest_row(rows: Any) -> Optional[Dict[str, Any]]:
    if isinstance(rows, dict):
        rows = rows.get("data") or rows.get("result") or rows.get("records") or rows.get("items")
    if not isinstance(rows, list) or not rows:
        return None
    return rows[-1] if isinstance(rows[-1], dict) else {"value": rows[-1]}


def numeric_sum(rows: List[Dict[str, Any]], include: List[str], exclude: Optional[List[str]] = None) -> Optional[float]:
    exclude = exclude or []
    total = 0.0
    used = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        for k, v in row.items():
            name = str(k)
            if all(w in name for w in include) and not any(w in name for w in exclude):
                n = parse_num(v)
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
                out["summary"]["margin_balance"] = numeric_sum(rows, ["融資", "今日餘額"])
                out["summary"]["short_balance"] = numeric_sum(rows, ["融券", "今日餘額"])
            elif key == "market_value_volume":
                out["summary"]["market_latest"] = latest_row(rows) or {}
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


def world_bank_indicators(config: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    indicators = DEFAULT_WORLD_BANK_INDICATORS.copy()
    raw = os.getenv("WORLD_BANK_INDICATORS", "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                indicators.update(parsed)
                return indicators, "env"
        except Exception:
            return indicators, "env_parse_error"
    cfg = config.get("world_bank") if isinstance(config, dict) else None
    if isinstance(cfg, dict):
        indicators.update({k: v for k, v in cfg.items() if isinstance(v, dict)})
        return indicators, "config"
    return indicators, "default"


def summarize_world_bank(config: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"updated_at": str(TODAY_TPE), "indicators": {}, "errors": []}
    indicators, mode = world_bank_indicators(config)
    out["source_mode"] = mode
    for key, spec in indicators.items():
        try:
            countries = spec["countries"]
            indicator = spec["indicator"]
            url = f"https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}"
            data = http_json(url, {"format": "json", "per_page": 100, "MRV": 5})
            rows = data[1] if isinstance(data, list) and len(data) > 1 else []
            latest = next((r for r in rows if r.get("value") is not None), None)
            out["indicators"][key] = {"countries": countries, "indicator": indicator, "latest": latest}
        except Exception as exc:
            out["errors"].append(f"{key}:{exc}")
    return out


def optional_url_map(config: Dict[str, Any], group: str, env_name: str) -> Tuple[Dict[str, Any], str]:
    raw = os.getenv(env_name, "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            return (parsed if isinstance(parsed, dict) else {}), "env"
        except Exception:
            return {}, "env_parse_error"
    value = ((config.get("global") or {}).get(group) or {}) if isinstance(config, dict) else {}
    return (value if isinstance(value, dict) else {}), "config" if value else "none"


def summarize_optional_url_maps(config: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for group, env_name in OPTIONAL_URL_MAP_ENVS.items():
        items, mode = optional_url_map(config, group, env_name)
        group_out = {"updated_at": str(TODAY_TPE), "configured": bool(items), "source_mode": mode, "items": {}, "errors": []}
        for key, url in items.items():
            try:
                data = http_json(str(url))
                sample = latest_row(data) if isinstance(data, (list, dict)) else None
                group_out["items"][key] = {"url": url, "sample": sample}
            except Exception as exc:
                group_out["errors"].append(f"{key}:{exc}")
        out[group] = group_out
    return out


def build_official_weekly_meta() -> Dict[str, Any]:
    config = load_config()
    twse = summarize_twse()
    treasury = summarize_treasury()
    world_bank = summarize_world_bank(config)
    optional = summarize_optional_url_maps(config)
    errors: List[str] = []
    for block in [twse, treasury, world_bank, *optional.values()]:
        errors.extend(block.get("errors", []) if isinstance(block, dict) else [])
    return {
        "version": "weekly_official_macro_v3_no_taiwan_open_data",
        "config_path": CONFIG_PATH,
        "config_loaded": bool(config),
        "updated_at": datetime.now(TAIPEI_TZ).isoformat(timespec="seconds"),
        "date": str(TODAY_TPE),
        "twse": twse,
        "us_treasury": treasury,
        "world_bank": world_bank,
        "bis": optional.get("bis", {}),
        "oecd": optional.get("oecd", {}),
        "imf": optional.get("imf", {}),
        "data_quality": {"error_count": len(errors), "errors": errors[:12]},
        "notes": [
            "本層只保留 TWSE、U.S. Treasury、World Bank，以及可選的 BIS/OECD/IMF URL map。",
            "已移除台灣景氣燈號、外銷訂單、CPI、GDP、M1B/M2、外匯存底等 data.gov.tw URL 監控。",
            "BIS/OECD/IMF 未設定時不視為缺失或錯誤。",
        ],
    }


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
        f"treasury_errors={len(official['us_treasury'].get('errors', []))} "
        f"world_bank_errors={len(official['world_bank'].get('errors', []))} "
        f"errors={official['data_quality']['error_count']}"
    )


if __name__ == "__main__":
    main()
