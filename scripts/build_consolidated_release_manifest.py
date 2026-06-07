#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "repo_architecture"
LATEST_JSON = OUT_DIR / "consolidated_release_manifest_latest.json"
SUMMARY_MD = OUT_DIR / "consolidated_release_manifest_summary.md"

CORE_RUNTIME = [
    "index.html",
    "assets/css/tailwind-built.css",
    "assets/js/app.bundle.js",
    "assets/js/quant-main-display.js",
    "assets/js/terminal-ui-polish.js",
    "assets/js/terminal-ia-phase2.js",
    "data/optimizer/decision_center_latest.json",
    "data/optimizer/model_governance_dashboard_latest.json",
    "data/repo_architecture/validation_gate_latest.json",
]
SOURCE_OF_TRUTH = [
    "assets/js/src/app.bundle.source.js",
    "scripts/build_frontend_bundle.py",
    "schemas/schema_registry.json",
    "scripts/validate_repo_integrity.py",
]
WORKFLOWS = [
    ".github/workflows/optimizer-lab.yml.yml",
    ".github/workflows/validation-gate.yml.yml",
    ".github/workflows/repo-architecture-audit.yml.yml",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def manifest_entries(paths):
    return [{"path": p, "exists": exists(p), "bytes": (ROOT / p).stat().st_size if exists(p) and (ROOT / p).is_file() else 0} for p in paths]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    runtime = manifest_entries(CORE_RUNTIME)
    source = manifest_entries(SOURCE_OF_TRUTH)
    workflows = manifest_entries(WORKFLOWS)
    missing = [x["path"] for x in runtime + source + workflows if not x["exists"]]
    payload = {
        "version": "v4.8",
        "generated_at": now_iso(),
        "status": "READY_FOR_REVIEW" if not missing else "REVIEW_REQUIRED",
        "mode": "full_consolidated_release_manifest",
        "safe_mode": True,
        "release_overlay_generated": True,
        "auto_delete_enabled": False,
        "core_runtime": runtime,
        "source_of_truth": source,
        "workflow_contract": workflows,
        "missing_required_for_release_review": missing,
        "release_policy": {
            "runtime_bundle": "assets/js/app.bundle.js",
            "frontend_source": "assets/js/src/app.bundle.source.js",
            "backend_split_mode": "registry_first",
            "component_split_mode": "registry_first",
            "validation_required_before_merge": True,
            "trade_execution_enabled": False,
        },
        "next_allowed_steps": [
            "Review v4.7 cleanup plan manually.",
            "Delete only safe candidates after a green validation gate.",
            "Defer actual UI/backend runtime split until after consolidated release is stable.",
        ],
    }
    LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Full Consolidated Release Manifest v4.8",
        "",
        f"- Status: **{payload['status']}**",
        f"- Release overlay generated: `{payload['release_overlay_generated']}`",
        f"- Auto delete enabled: `{payload['auto_delete_enabled']}`",
        f"- Missing required files: `{len(missing)}`",
        "",
        "## Core runtime",
    ]
    for x in runtime:
        lines.append(f"- `{x['path']}` — exists: `{x['exists']}`")
    lines.append("\n## Source of truth")
    for x in source:
        lines.append(f"- `{x['path']}` — exists: `{x['exists']}`")
    lines.append("\n## Workflows")
    for x in workflows:
        lines.append(f"- `{x['path']}` — exists: `{x['exists']}`")
    lines += ["", "## Policy", "- This release is a consolidated overlay and governance baseline.", "- It does not enable automatic trading or official alpha execution."]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_MD.relative_to(ROOT)}")
    print(f"Release status: {payload['status']}")
    return 0 if not missing else 1

if __name__ == "__main__":
    raise SystemExit(main())
