#!/usr/bin/env python3
from __future__ import annotations

import math
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from supabase import create_client

TAIPEI_TZ = timezone(timedelta(hours=8))
TODAY_TPE = datetime.now(TAIPEI_TZ).date()


def env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    return default if value is None or value == "" else value


SUPABASE_URL = env("SUPABASE_URL")
SUPABASE_SECRET_KEY = env("SUPABASE_SECRET_KEY")
SUPABASE_TABLE = env("SUPABASE_TABLE", "portfolio_db")
PORTFOLIO_ROW_ID = env("PORTFOLIO_ROW_ID", "1")
DRY_RUN = str(env("DRY_RUN", "false")).lower() in {"1", "true", "yes", "y"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def finite_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        x = float(value)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def clamp(x: Any, low: float = 0.0, high: float = 10.0) -> float:
    n = finite_float(x, 0.0) or 0.0
    return round(max(low, min(high, n)), 3)


def recompute_health(meta: Dict[str, Any]) -> float:
    trend = finite_float(meta.get("trend_score"), 5.0) or 5.0
    tech = finite_float(meta.get("technical_score"), 5.0) or 5.0
    valuation = finite_float(meta.get("valuation_score"), 5.0) or 5.0
    risk = finite_float(meta.get("risk_score"), 5.0) or 5.0
    return clamp(
        0.35 * trend
        + 0.25 * tech
        + 0.15 * valuation
        + 0.25 * (10.0 - risk)
    )


def main() -> None:
    if not SUPABASE_URL:
        fail("SUPABASE_URL missing.")
    if not SUPABASE_SECRET_KEY:
        fail("SUPABASE_SECRET_KEY missing.")

    client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    response = client.table(SUPABASE_TABLE).select("stock_meta").eq("id", int(PORTFOLIO_ROW_ID)).single().execute()
    stock_meta = response.data.get("stock_meta") if response.data else None
    if not isinstance(stock_meta, dict):
        fail("stock_meta is missing or not a dict.")

    changed = 0
    for ticker, meta in stock_meta.items():
        if not isinstance(meta, dict):
            continue
        if "chip_score" in meta:
            meta.pop("chip_score", None)
            changed += 1
        old_health = meta.get("quant_health_score")
        new_health = recompute_health(meta)
        if old_health != new_health:
            meta["quant_health_score"] = new_health
            changed += 1
        meta["quant_health_formula"] = "no_chip_v1: 35% trend + 25% technical + 15% valuation + 25% inverse risk"
        meta["chip_factor_policy"] = "excluded_from_core_factor; institutional flow fields remain as Taiwan-only supplemental data"
        meta["updated_at"] = str(TODAY_TPE)

    if DRY_RUN:
        print(f"DRY_RUN=true, normalized stock_meta without writing; changed_items={changed}")
        return

    client.table(SUPABASE_TABLE).upsert({
        "id": int(PORTFOLIO_ROW_ID),
        "stock_meta": stock_meta,
    }, on_conflict="id").execute()
    print(f"OK removed chip_score from core factor layer; changed_items={changed}")


if __name__ == "__main__":
    main()
