#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from supabase import create_client


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restore one portfolio_db row from a committed JSON backup."
    )
    parser.add_argument("--backup-date", required=True, help="Backup date in YYYY-MM-DD format.")
    parser.add_argument("--row-id", type=int, default=1, help="portfolio_db row id to restore.")
    parser.add_argument(
        "--table",
        default=os.getenv("SUPABASE_TABLE", "portfolio_db"),
        help="Supabase table name.",
    )
    parser.add_argument(
        "--confirm",
        required=True,
        help='Safety acknowledgement. Must be exactly "RESTORE".',
    )
    return parser.parse_args()


def load_backup_row(backup_date: str, row_id: int) -> tuple[Dict[str, Any], Path]:
    path = ROOT / "backups" / f"portfolio_backup_{backup_date}.json"
    if not path.exists():
        raise FileNotFoundError(f"Backup not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    rows: List[Dict[str, Any]]

    if isinstance(raw, list):
        rows = [row for row in raw if isinstance(row, dict)]
    elif isinstance(raw, dict):
        if isinstance(raw.get("data"), list):
            rows = [row for row in raw["data"] if isinstance(row, dict)]
        else:
            rows = [raw]
    else:
        raise ValueError("Backup JSON must be an object or array of objects.")

    row = next((item for item in rows if int(item.get("id", -1)) == row_id), None)
    if row is None:
        raise ValueError(f"Row id={row_id} not found in {path.name}")

    return row, path


def portfolio_counts(row: Dict[str, Any]) -> Dict[str, int]:
    ledger = row.get("ledger_data")
    history = row.get("history_data")
    stock_meta = row.get("stock_meta")

    return {
        "ledger_data": len(ledger) if isinstance(ledger, list) else 0,
        "history_data": len(history) if isinstance(history, list) else 0,
        "stock_meta": len(stock_meta) if isinstance(stock_meta, dict) else 0,
    }


def require_nonempty_portfolio(row: Dict[str, Any], source: str) -> Dict[str, int]:
    counts = portfolio_counts(row)
    if any(counts[key] <= 0 for key in ("ledger_data", "history_data", "stock_meta")):
        raise ValueError(
            f"Refusing restore: {source} is not a valid non-empty portfolio backup. Counts={counts}"
        )
    return counts


def main() -> None:
    args = parse_args()

    if args.confirm != "RESTORE":
        raise SystemExit('Refusing restore: --confirm must be exactly "RESTORE".')

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SECRET_KEY) are required."
        )

    backup_row, backup_path = load_backup_row(args.backup_date, args.row_id)
    expected = require_nonempty_portfolio(backup_row, backup_path.name)

    print(f"Backup: {backup_path.relative_to(ROOT)}")
    print(f"Target: {args.table} id={args.row_id}")
    print(f"Backup counts: {expected}")

    client = create_client(url, key)

    current_response = (
        client.table(args.table)
        .select("id,ledger_data,history_data,stock_meta")
        .eq("id", args.row_id)
        .single()
        .execute()
    )
    current = current_response.data or {}
    print(f"Current counts before restore: {portfolio_counts(current)}")

    payload = {key: value for key, value in backup_row.items() if key != "id"}
    if not payload:
        raise ValueError("Backup row has no restorable fields.")

    (
        client.table(args.table)
        .update(payload)
        .eq("id", args.row_id)
        .execute()
    )

    verify_response = (
        client.table(args.table)
        .select("*")
        .eq("id", args.row_id)
        .single()
        .execute()
    )
    restored = verify_response.data or {}
    actual = require_nonempty_portfolio(restored, "restored Supabase row")

    if actual != expected:
        raise RuntimeError(
            f"Restore verification failed: expected counts={expected}, actual counts={actual}"
        )

    print(f"Restore verified successfully: {actual}")
    print("RESTORE_OK")


if __name__ == "__main__":
    main()
