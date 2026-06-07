#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "repo_architecture"
LATEST_JSON = OUT_DIR / "dead_file_cleanup_plan_latest.json"
SUMMARY_MD = OUT_DIR / "dead_file_cleanup_plan_summary.md"

SAFE_DELETE_PATTERNS = [
    "README_FRONTEND_MIGRATION.md",
    "README_TERMINAL_DESIGN_SYSTEM.md",
    "README_V05_V06_OVERLAY.md",
    "daily_update.yml",
    "weekly_macro_update.yml",
    "frontend_tailwind_migration.yml",
]
REVIEW_BEFORE_DELETE = [
    "00-bootstrap-and-cro.js",
    "00-tailwind-config.js",
    "10-state-auth-cloud.js",
    "30-risk-xray-tail.js",
    "40-actions-history-buffer.js",
    "60-ui-and-charts.js",
    "app.bundle.js",
    "quant-main-display.js",
    "backup.py",
]
DO_NOT_DELETE = [
    "index.html",
    "assets/js/app.bundle.js",
    "assets/js/src/app.bundle.source.js",
    "assets/js/quant-main-display.js",
    "assets/css/tailwind-built.css",
    ".github/workflows/optimizer-lab.yml.yml",
    ".github/workflows/validation-gate.yml.yml",
    ".github/workflows/repo-architecture-audit.yml.yml",
    "scripts/validate_repo_integrity.py",
    "scripts/build_frontend_bundle.py",
    "schemas/schema_registry.json",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_info(path: str):
    p = ROOT / path
    return {
        "path": path,
        "exists": p.exists(),
        "bytes": p.stat().st_size if p.exists() and p.is_file() else 0,
        "reason": None,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    safe = []
    for item in SAFE_DELETE_PATTERNS:
        rec = file_info(item)
        rec["reason"] = "root-level stale workflow/readme duplicate or migration note; not a runtime path"
        safe.append(rec)
    review = []
    for item in REVIEW_BEFORE_DELETE:
        rec = file_info(item)
        rec["reason"] = "root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference"
        review.append(rec)
    keep = []
    for item in DO_NOT_DELETE:
        rec = file_info(item)
        rec["reason"] = "runtime, source-of-truth, validation, schema, or workflow-critical file"
        keep.append(rec)
    payload = {
        "version": "v4.7",
        "generated_at": now_iso(),
        "status": "PLAN_ONLY",
        "mode": "dead_file_cleanup_plan",
        "safe_mode": True,
        "auto_delete_enabled": False,
        "delete_command_generated": False,
        "safe_delete_candidates": safe,
        "review_before_delete": review,
        "do_not_delete": keep,
        "policy": {
            "rule": "This plan never deletes files automatically.",
            "required_before_delete": ["Validation Gate OK", "GitHub Pages manual smoke test", "No unresolved audit warnings"],
        },
    }
    LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Dead File Cleanup Plan v4.7",
        "",
        "- Status: **PLAN_ONLY**",
        f"- Auto delete enabled: `{payload['auto_delete_enabled']}`",
        f"- Safe-delete candidates existing: `{sum(1 for x in safe if x['exists'])}`",
        f"- Review-before-delete existing: `{sum(1 for x in review if x['exists'])}`",
        "",
        "## Safe delete candidates",
    ]
    for x in safe:
        lines.append(f"- `{x['path']}` — exists: `{x['exists']}` — {x['reason']}")
    lines.append("\n## Review before delete")
    for x in review:
        lines.append(f"- `{x['path']}` — exists: `{x['exists']}` — {x['reason']}")
    lines.append("\n## Do not delete")
    for x in keep:
        lines.append(f"- `{x['path']}` — exists: `{x['exists']}`")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_MD.relative_to(ROOT)}")
    print(f"Safe-delete candidates: {sum(1 for x in safe if x['exists'])}")
    print(f"Review-before-delete candidates: {sum(1 for x in review if x['exists'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
