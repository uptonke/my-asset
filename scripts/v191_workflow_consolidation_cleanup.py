#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF_DIR = ROOT / ".github" / "workflows"

KEEP = {
    "optimizer-lab.yml",
    "daily_update.yml",
    "update_stock_meta.yml",
    "weekly_backup.yml",
    "weekly_macro_update.yml",
}

LEGACY_BASES = [
    "apply_terminal_ia_phase2",
    "optimizer-install-sandbox",
    "optimizer-robustness",
    "optimizer-stress-tests",
    "riskfolio-dependency-sandbox",
    "riskfolio-sandbox",
    "skfolio-sandbox",
    "v19-technical-debt-cleanup",
]

def main() -> None:
    WF_DIR.mkdir(parents=True, exist_ok=True)

    deleted = []
    kept = []
    unknown = []

    legacy_names = set()
    for base in LEGACY_BASES:
        legacy_names.add(f"{base}.yml")
        legacy_names.add(f"{base}.yaml")
        legacy_names.add(f"{base}.yml.yml")
        legacy_names.add(f"{base}.yaml.yml")

    for path in sorted(WF_DIR.glob("*")):
        if not path.is_file():
            continue

        if path.name in KEEP:
            kept.append(path.name)
            continue

        if path.name in legacy_names:
            path.unlink()
            deleted.append(path.name)
            continue

        # Do not delete unrecognized production workflows automatically.
        unknown.append(path.name)

    inventory = {
        "version": "v1.9.1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_dir": str(WF_DIR.relative_to(ROOT)),
        "kept": kept,
        "deleted_legacy_optimizer_workflows": deleted,
        "unknown_not_deleted": unknown,
        "consolidated_workflow": ".github/workflows/optimizer-lab.yml",
        "notes": [
            "Optimizer / Riskfolio / skfolio / stress / robustness / terminal IA / cleanup tasks are consolidated into Optimizer Lab.",
            "Daily, weekly, backup, and Update Stock Quant Meta workflows are intentionally kept separate.",
            "Unknown workflows are not deleted automatically to avoid accidental production breakage.",
        ],
    }

    out_dir = ROOT / "data" / "repo_health"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "workflow_consolidation_inventory.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    docs = ROOT / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    lines = [
        "# v1.9.1 Workflow Consolidation Map",
        "",
        f"- Timestamp UTC: `{inventory['timestamp_utc']}`",
        f"- Consolidated workflow: `{inventory['consolidated_workflow']}`",
        "",
        "## Kept production workflows",
        "",
    ]
    lines += [f"- `{x}`" for x in kept] or ["- None"]
    lines += ["", "## Deleted legacy optimizer workflows", ""]
    lines += [f"- `{x}`" for x in deleted] or ["- None"]
    lines += ["", "## Unknown workflows not deleted", ""]
    lines += [f"- `{x}`" for x in unknown] or ["- None"]
    lines += [
        "",
        "## Optimizer Lab task mapping",
        "",
        "| Old workflow | New task |",
        "|---|---|",
        "| `optimizer-install-sandbox.yml` | `optimizer_install_probe` |",
        "| `skfolio-sandbox.yml` | `skfolio_sandbox` |",
        "| `riskfolio-dependency-sandbox.yml` | `riskfolio_dependency_probe` |",
        "| `riskfolio-sandbox.yml` | `riskfolio_sandbox` |",
        "| `optimizer-robustness.yml` | `optimizer_robustness` |",
        "| `optimizer-stress-tests.yml` | `optimizer_stress_tests` |",
        "| `apply_terminal_ia_phase2.yml` | `apply_terminal_ia_phase2` |",
        "| `v19-technical-debt-cleanup.yml` | `technical_debt_cleanup` |",
        "| multiple optimizer refresh workflows | `all_optimizer_outputs` |",
    ]
    (docs / "TECHNICAL_DEBT_MAP.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(inventory, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
