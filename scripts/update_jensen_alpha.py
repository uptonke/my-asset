#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import Any, Dict

from supabase import create_client

from jensen_alpha import compute_jensen_alpha_regression

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_SECRET_KEY", "")
TABLE = os.getenv("SUPABASE_TABLE", "portfolio_db")
ROW_ID = int(os.getenv("PORTFOLIO_ROW_ID", "1"))


def main() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    row = client.table(TABLE).select("history_data,ledger_data,chaos_meta").eq("id", ROW_ID).single().execute().data
    if not row:
        raise SystemExit("ERROR: portfolio row not found")

    alpha_regression = compute_jensen_alpha_regression(
        history_data=row.get("history_data") or [],
        ledger_data=row.get("ledger_data") or [],
    )
    chaos_meta: Dict[str, Any] = row.get("chaos_meta") if isinstance(row.get("chaos_meta"), dict) else {}
    previous = chaos_meta.get("alpha_regression") if isinstance(chaos_meta.get("alpha_regression"), dict) else None
    if (
        alpha_regression.get("status") not in {"available", "partial"}
        and previous
        and previous.get("status") in {"available", "partial", "stale_cache"}
    ):
        cached = dict(previous)
        cached["status"] = "stale_cache"
        cached["refresh_status"] = "FAILED_USING_LAST_VALID"
        cached["refresh_error"] = alpha_regression.get("error") or alpha_regression.get("status")
        alpha_regression = cached

    chaos_meta["alpha_regression"] = alpha_regression
    client.table(TABLE).update({"chaos_meta": chaos_meta}).eq("id", ROW_ID).execute()

    print(f"OK Jensen alpha regression status={alpha_regression.get('status')}")
    for benchmark, result in (alpha_regression.get("benchmarks") or {}).items():
        if result.get("status") == "available":
            print(
                f"{benchmark}: alpha={result.get('alpha_annualized_pct')}% "
                f"t={result.get('alpha_t_stat_hac')} p={result.get('alpha_p_value_hac')} "
                f"CI=[{result.get('alpha_ci95_low_annualized_pct')}, {result.get('alpha_ci95_high_annualized_pct')}] "
                f"beta={result.get('beta')} R2={result.get('r_squared')} n={result.get('n')}"
            )
        else:
            print(f"{benchmark}: status={result.get('status')} error={result.get('error', '')}")


if __name__ == "__main__":
    main()
