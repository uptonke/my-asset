#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "repo_architecture"
LATEST_JSON = OUT_DIR / "dead_file_cleanup_execution_latest.json"
SUMMARY_MD = OUT_DIR / "dead_file_cleanup_execution_summary.md"

SAFE_DELETE_PATHS = [
    "README_FRONTEND_MIGRATION.md",
    "README_TERMINAL_DESIGN_SYSTEM.md",
    "README_V05_V06_OVERLAY.md",
    "daily_update.yml",
    "weekly_macro_update.yml",
    "frontend_tailwind_migration.yml",
]

CONFIRMED_DUPLICATE_PATHS = [
    "00-bootstrap-and-cro.js",
    "00-tailwind-config.js",
    "10-state-auth-cloud.js",
    "30-risk-xray-tail.js",
    "40-actions-history-buffer.js",
    "60-ui-and-charts.js",
    "app.bundle.js",
    "quant-main-display.js",
]

PROTECTED_PATHS = [
    "index.html",
    "assets/js/app.bundle.js",
    "assets/js/src/app.bundle.source.js",
    "assets/js/quant-main-display.js",
    "assets/css/tailwind-built.css",
    "backup.py",
    "main.py",
    "update_stock_meta.py",
    ".github/workflows/optimizer-lab.yml.yml",
    ".github/workflows/validation-gate.yml.yml",
    ".github/workflows/repo-architecture-audit.yml.yml",
]

# Root-level files intentionally NOT deleted in this pass.
EXPLICITLY_RETAINED = [
    "backup.py",  # .github/workflows/weekly_backup.yml.yml still calls python backup.py
    "UPLOAD_TO_GITHUB_PAGES.txt",  # non-runtime doc; keep until a docs policy pass
    "README.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def root_script_is_referenced(index_text: str, basename: str) -> bool:
    """Return True only if index.html references the root-level file, not assets/ counterpart."""
    patterns = [
        rf"src=[\"']{re.escape(basename)}(?:[?#][^\"']*)?[\"']",
        rf"href=[\"']{re.escape(basename)}(?:[?#][^\"']*)?[\"']",
        rf"src=[\"']\./{re.escape(basename)}(?:[?#][^\"']*)?[\"']",
        rf"href=[\"']\./{re.escape(basename)}(?:[?#][^\"']*)?[\"']",
    ]
    return any(re.search(p, index_text) for p in patterns)


def build_guardrails() -> Dict[str, Any]:
    index_text = read_text(ROOT / "index.html")
    required_runtime = []
    missing_runtime = []
    for rel in PROTECTED_PATHS:
        p = ROOT / rel
        row = {"path": rel, "exists": p.exists()}
        required_runtime.append(row)
        if not p.exists():
            missing_runtime.append(rel)

    root_ref_errors = []
    for rel in CONFIRMED_DUPLICATE_PATHS:
        if root_script_is_referenced(index_text, Path(rel).name):
            root_ref_errors.append(rel)

    return {
        "protected_paths": required_runtime,
        "missing_protected_paths": missing_runtime,
        "root_duplicate_reference_errors": root_ref_errors,
        "backup_py_retained_because_weekly_backup_uses_it": (ROOT / "backup.py").exists(),
        "explicitly_retained": EXPLICITLY_RETAINED,
    }


def cleanup_paths(paths: List[str], category: str, execute: bool) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for rel in paths:
        p = ROOT / rel
        exists_before = p.exists()
        size = p.stat().st_size if exists_before and p.is_file() else None
        action = "delete" if execute else "would_delete"
        status = "deleted" if execute else "dry_run"
        error = None
        if not exists_before:
            action = "skip"
            status = "missing"
        elif p.is_dir():
            action = "skip"
            status = "directory_not_supported"
            error = "This cleanup pass only removes files, not directories."
        elif execute:
            try:
                p.unlink()
            except Exception as exc:  # pragma: no cover - defensive workflow reporting
                status = "error"
                error = str(exc)
        rows.append({
            "path": rel,
            "category": category,
            "exists_before": exists_before,
            "bytes_before": size,
            "action": action,
            "status": status,
            "error": error,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply v4.7 dead file cleanup with guardrails.")
    parser.add_argument("--execute", action="store_true", help="Actually delete safe dead files. Default is dry-run.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    guardrails = build_guardrails()
    blocked = bool(guardrails["missing_protected_paths"] or guardrails["root_duplicate_reference_errors"])

    results: List[Dict[str, Any]] = []
    if blocked:
        mode = "blocked"
        status = "BLOCKED"
    else:
        mode = "execute" if args.execute else "dry_run"
        status = "OK"
        results.extend(cleanup_paths(SAFE_DELETE_PATHS, "safe_delete", args.execute))
        results.extend(cleanup_paths(CONFIRMED_DUPLICATE_PATHS, "confirmed_duplicate_root_file", args.execute))

    deleted = [r for r in results if r["status"] == "deleted"]
    dry_run = [r for r in results if r["status"] == "dry_run"]
    missing = [r for r in results if r["status"] == "missing"]
    errors = [r for r in results if r.get("error")]

    payload: Dict[str, Any] = {
        "version": "v4.7",
        "generated_at": utc_now(),
        "status": "FAIL" if blocked or errors else status,
        "mode": mode,
        "safe_mode": True,
        "auto_delete_enabled": False,
        "manual_workflow_execution_required": True,
        "summary": {
            "target_count": len(SAFE_DELETE_PATHS) + len(CONFIRMED_DUPLICATE_PATHS),
            "deleted_count": len(deleted),
            "dry_run_count": len(dry_run),
            "missing_count": len(missing),
            "error_count": len(errors),
        },
        "guardrails": guardrails,
        "deleted_paths": [r["path"] for r in deleted],
        "results": results,
        "retained_paths": EXPLICITLY_RETAINED,
        "safety_boundary": [
            "This cleanup removes only non-runtime root-level duplicates and stale migration notes.",
            "It does not remove runtime assets, schemas, optimizer outputs, workflows, or backup.py.",
            "It does not change portfolio data, does not write Supabase, and does not enable execution.",
        ],
    }

    LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Dead File Cleanup Execution v4.7",
        "",
        f"- Status: **{payload['status']}**",
        f"- Mode: `{mode}`",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Target count: `{payload['summary']['target_count']}`",
        f"- Deleted count: `{payload['summary']['deleted_count']}`",
        f"- Missing count: `{payload['summary']['missing_count']}`",
        f"- Error count: `{payload['summary']['error_count']}`",
        "",
        "## Deleted paths",
    ]
    if deleted:
        lines.extend([f"- `{p}`" for p in payload["deleted_paths"]])
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Retained paths",
        "",
    ])
    lines.extend([f"- `{p}`" for p in EXPLICITLY_RETAINED])
    if guardrails["missing_protected_paths"]:
        lines.extend(["", "## Blocking missing protected paths", ""])
        lines.extend([f"- `{p}`" for p in guardrails["missing_protected_paths"]])
    if guardrails["root_duplicate_reference_errors"]:
        lines.extend(["", "## Blocking root duplicate references", ""])
        lines.extend([f"- `{p}`" for p in guardrails["root_duplicate_reference_errors"]])
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {LATEST_JSON.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_MD.relative_to(ROOT)}")
    print(f"Status: {payload['status']}")
    print(f"Deleted count: {payload['summary']['deleted_count']}")
    if payload["status"] == "FAIL":
        print("Dead file cleanup failed or was blocked by guardrails.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
