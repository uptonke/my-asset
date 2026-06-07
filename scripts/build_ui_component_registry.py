#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "repo_architecture"
LATEST_JSON = OUT_DIR / "ui_component_registry_latest.json"
SUMMARY_MD = OUT_DIR / "ui_component_registry_summary.md"
COMPONENT_DIR = ROOT / "assets" / "js" / "src" / "components"

COMPONENTS = [
    {
        "id": "quant-risk",
        "name": "Quant Risk",
        "label_zh": "量化風控",
        "source_module": "assets/js/src/components/quant-risk.component.js",
        "runtime_anchor": "analyticsViewMode === 'risk'",
        "current_runtime": "assets/js/src/app.bundle.source.js",
        "split_status": "registry_first_not_runtime_split",
        "risk_level": "medium",
        "owns": ["risk metrics", "VaR/ES", "drawdown", "risk contribution"],
    },
    {
        "id": "optimizer-lab",
        "name": "Optimizer Lab",
        "label_zh": "最佳化",
        "source_module": "assets/js/src/components/optimizer-lab.component.js",
        "runtime_anchor": "analyticsViewMode === 'optimizer'",
        "current_runtime": "assets/js/src/app.bundle.source.js",
        "split_status": "registry_first_not_runtime_split",
        "risk_level": "high",
        "owns": ["decision center", "rebalance candidates", "approval", "audit", "governance"],
    },
    {
        "id": "macro-intelligence",
        "name": "Macro Intelligence",
        "label_zh": "市場環境",
        "source_module": "assets/js/src/components/macro-intelligence.component.js",
        "runtime_anchor": "overview/analysis anchor only",
        "current_runtime": "assets/js/quant-main-display.js",
        "split_status": "anchor_stabilized_not_runtime_split",
        "risk_level": "medium",
        "owns": ["market intelligence overview", "macro context"],
    },
    {
        "id": "holding-cards",
        "name": "Holding Cards",
        "label_zh": "持倉卡片",
        "source_module": "assets/js/src/components/holding-cards.component.js",
        "runtime_anchor": "portfolio holdings/table sections",
        "current_runtime": "assets/js/src/app.bundle.source.js",
        "split_status": "registry_first_not_runtime_split",
        "risk_level": "medium",
        "owns": ["position cards", "holding-level display"],
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    modules = []
    missing = []
    for component in COMPONENTS:
        p = ROOT / component["source_module"]
        rec = dict(component)
        rec["module_exists"] = p.exists()
        rec["bytes"] = p.stat().st_size if p.exists() else 0
        if not p.exists():
            missing.append(component["source_module"])
        modules.append(rec)

    payload = {
        "version": "v4.3",
        "generated_at": now_iso(),
        "status": "OK" if not missing else "REVIEW_REQUIRED",
        "mode": "ui_component_split_registry",
        "safe_mode": True,
        "source_of_truth": "assets/js/src/app.bundle.source.js",
        "runtime_bundle": "assets/js/app.bundle.js",
        "component_count": len(modules),
        "runtime_split_enabled": False,
        "components": modules,
        "migration_policy": {
            "step_1": "Keep app.bundle.source.js authoritative.",
            "step_2": "Register component boundaries and owners.",
            "step_3": "Only move executable code after validation gate stays green.",
            "forbidden": ["hand-edit assets/js/app.bundle.js", "split optimizer runtime without schema gate"],
        },
        "missing_modules": missing,
    }
    LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# UI Component Split Registry v4.3",
        "",
        f"- Status: **{payload['status']}**",
        f"- Component count: `{payload['component_count']}`",
        f"- Runtime split enabled: `{payload['runtime_split_enabled']}`",
        f"- Source of truth: `{payload['source_of_truth']}`",
        "",
        "## Components",
    ]
    for c in modules:
        lines.append(f"- `{c['id']}` — {c['label_zh']} — `{c['split_status']}` — module exists: `{c['module_exists']}`")
    lines += ["", "## Policy", "- This is a registry-first split. It does not change runtime behavior.", "- Actual extraction should happen only after build and validation gates remain green."]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_MD.relative_to(ROOT)}")
    print(f"Component count: {payload['component_count']}")
    return 0 if not missing else 1

if __name__ == "__main__":
    raise SystemExit(main())
