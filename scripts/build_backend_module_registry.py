#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "repo_architecture"
LATEST_JSON = OUT_DIR / "backend_module_registry_latest.json"
SUMMARY_MD = OUT_DIR / "backend_module_registry_summary.md"
MODULE_DIR = ROOT / "scripts" / "modules"

MODULES = [
    {"id": "data_fetch", "path": "scripts/modules/data_fetch.py", "target_source": "update_stock_meta.py", "split_status": "boundary_registered"},
    {"id": "beta", "path": "scripts/modules/beta.py", "target_source": "update_stock_meta.py", "split_status": "boundary_registered"},
    {"id": "synthetic_risk", "path": "scripts/modules/synthetic_risk.py", "target_source": "update_stock_meta.py", "split_status": "boundary_registered"},
    {"id": "optimizer_outputs", "path": "scripts/modules/optimizer_outputs.py", "target_source": "scripts/build_*optimizer*.py", "split_status": "boundary_registered"},
    {"id": "stock_meta_schema", "path": "scripts/modules/stock_meta_schema.py", "target_source": "update_stock_meta.py", "split_status": "boundary_registered"},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_module_meta(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        return {}, "spec_load_failed"
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:
        return {}, str(exc)
    return {
        "module_id": getattr(module, "MODULE_ID", path.stem),
        "owned_concerns": getattr(module, "OWNED_CONCERNS", []),
        "side_effects_allowed": getattr(module, "SIDE_EFFECTS_ALLOWED", None),
    }, None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    errors = []
    for item in MODULES:
        p = ROOT / item["path"]
        rec = dict(item)
        rec["exists"] = p.exists()
        rec["bytes"] = p.stat().st_size if p.exists() else 0
        if p.exists():
            meta, err = load_module_meta(p)
            rec.update(meta)
            if err:
                rec["import_error"] = err
                errors.append({"path": item["path"], "error": err})
        else:
            errors.append({"path": item["path"], "error": "missing module"})
        records.append(rec)
    payload = {
        "version": "v4.4",
        "generated_at": now_iso(),
        "status": "OK" if not errors else "REVIEW_REQUIRED",
        "mode": "backend_script_split_registry",
        "safe_mode": True,
        "runtime_refactor_enabled": False,
        "module_count": len(records),
        "modules": records,
        "split_policy": {
            "current_runtime": ["update_stock_meta.py", "main.py", "scripts/build_*"],
            "rule": "Registry-first split only; do not move side-effecting code until tests and schemas pass.",
            "forbidden": ["change Supabase writes during split", "change optimizer output semantics during split"],
        },
        "errors": errors,
    }
    LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Backend Module Registry v4.4",
        "",
        f"- Status: **{payload['status']}**",
        f"- Module count: `{payload['module_count']}`",
        f"- Runtime refactor enabled: `{payload['runtime_refactor_enabled']}`",
        "",
        "## Modules",
    ]
    for m in records:
        concerns = ", ".join(m.get("owned_concerns") or [])
        lines.append(f"- `{m['id']}` — exists: `{m['exists']}` — concerns: {concerns}")
    lines += ["", "## Policy", "- This version registers backend boundaries only.", "- update_stock_meta.py remains authoritative until module tests are added."]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LATEST_JSON.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_MD.relative_to(ROOT)}")
    print(f"Module count: {payload['module_count']}")
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
