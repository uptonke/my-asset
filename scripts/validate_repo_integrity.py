#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "repo_architecture"
LATEST_JSON = OUT_DIR / "validation_gate_latest.json"
SUMMARY_MD = OUT_DIR / "validation_gate_summary.md"
REGISTRY_PATH = ROOT / "schemas" / "schema_registry.json"

JSON_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}

REQUIRED_FILES = [
    "index.html",
    "assets/js/app.bundle.js",
    "assets/js/src/app.bundle.source.js",
    "assets/js/quant-main-display.js",
    "package.json",
    "split-manifest.json",
    "schemas/schema_registry.json",
    "scripts/build_frontend_bundle.py",
    "scripts/validate_repo_integrity.py",
    "scripts/build_ui_component_registry.py",
    "scripts/build_backend_module_registry.py",
    "scripts/build_dead_file_cleanup_plan.py",
    "scripts/build_consolidated_release_manifest.py",
    "scripts/build_forecast_feature_store.py",
    "scripts/build_alpha_research_sandbox.py",
    "scripts/build_rebalance_candidate_ranking.py",
    "scripts/build_alpha_validation_gate.py",
    "scripts/build_manual_rebalance_proposal.py",
    "scripts/build_execution_ready_draft.py",
    "scripts/build_formal_rebalance_draft_gate.py",
    "scripts/build_manual_trade_ticket_generator.py",
    "scripts/build_formal_draft_pass_conditions.py",
    "scripts/build_manual_approval_input_layer.py",
    "scripts/build_trading_constraints_snapshot.py",
    "scripts/build_paper_trade_tracker.py",
    "scripts/build_trade_sizing_diagnostics.py",
    "scripts/build_manual_approval_console.py",
    "scripts/build_paper_trade_performance_evaluator.py",
    "scripts/build_trade_ticket_explainability.py",
    "scripts/build_human_confirmed_trade_ticket.py",
    "scripts/build_delegated_target_weight_draft_generator.py",
    "scripts/build_daily_quant_monte_carlo_reference.py",
    "config/manual_approval_override.json",
    "docs/FRONTEND_SOURCE_OF_TRUTH.md",
    "docs/SCHEMA_REGISTRY.md",
    "docs/UI_COMPONENT_SPLIT.md",
    "docs/BACKEND_SCRIPT_SPLIT.md",
    "docs/DEAD_FILE_CLEANUP_PLAN.md",
    "docs/V4_CONSOLIDATED_RELEASE.md",
    "docs/ALPHA_RESEARCH_SANDBOX.md",
    "docs/REBALANCE_CANDIDATE_RANKING.md",
    "docs/EXECUTION_READY_DRAFT_BOUNDARY.md",
    "docs/FORMAL_REBALANCE_DRAFT_GATE.md",
    "docs/MANUAL_TRADE_TICKET_GENERATOR.md",
    "docs/FORMAL_DRAFT_PASS_CONDITIONS.md",
    "docs/MANUAL_APPROVAL_INPUT_LAYER.md",
    "docs/TRADING_CONSTRAINTS_SNAPSHOT.md",
    "docs/PAPER_TRADE_TRACKER.md",
    "docs/TRADE_SIZING_DIAGNOSTICS.md",
    "docs/MANUAL_APPROVAL_CONSOLE.md",
    "docs/PAPER_TRADE_PERFORMANCE_EVALUATOR.md",
    "docs/TRADE_TICKET_EXPLAINABILITY.md",
    "docs/HUMAN_CONFIRMED_TRADE_TICKET.md",
    "docs/DELEGATED_TARGET_WEIGHT_DRAFT_GENERATOR.md",
    "docs/DAILY_QUANT_MONTE_CARLO_REFERENCE_LAYER.md",
    ".github/workflows/optimizer-lab.yml.yml",
    ".github/workflows/repo-architecture-audit.yml.yml",
    ".github/workflows/validation-gate.yml.yml",
]

REQUIRED_WORKFLOW_DIR = ".github/workflows"
NODE_CHECK_FILES = [
    "assets/js/app.bundle.js",
    "assets/js/quant-main-display.js",
    "assets/js/terminal-ui-polish.js",
    "assets/js/terminal-ia-phase2.js",
]

FORBIDDEN_TRUE_KEYS = {
    "execution_permission",
    "official_alpha_enabled",
    "alpha_model_enabled",
    "maximum_sharpe_optimization_enabled",
    "auto_trade_enabled",
    "supabase_write_enabled",
    "trade_signal_enabled",
    "official_rebalance_enabled",
}
FORBIDDEN_FALSE_KEYS = {"not_trade_order"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace(os.sep, "/")
    except ValueError:
        return str(path)


def add_error(errors: List[Dict[str, Any]], category: str, message: str, path: str | None = None) -> None:
    errors.append({"category": category, "message": message, "path": path})


def add_warning(warnings: List[Dict[str, Any]], category: str, message: str, path: str | None = None) -> None:
    warnings.append({"category": category, "message": message, "path": path})


def load_json(path: Path) -> Tuple[Any, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, str(exc)


def validate_schema_subset(data: Any, schema: Dict[str, Any], path: str) -> List[str]:
    problems: List[str] = []
    expected_type = schema.get("type")
    if expected_type:
        py_type = JSON_TYPE_MAP.get(expected_type)
        if py_type and not isinstance(data, py_type):
            # bool is a subclass of int in Python; keep integers strict.
            if not (expected_type == "number" and isinstance(data, (int, float)) and not isinstance(data, bool)):
                problems.append(f"{path}: expected {expected_type}, got {type(data).__name__}")
                return problems
    if isinstance(data, dict):
        for key in schema.get("required", []):
            if key not in data:
                problems.append(f"{path}: missing required key '{key}'")
        props = schema.get("properties", {})
        for key, child_schema in props.items():
            if key in data:
                problems.extend(validate_schema_subset(data[key], child_schema, f"{path}.{key}"))
    elif isinstance(data, list):
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(data):
                problems.extend(validate_schema_subset(item, item_schema, f"{path}[{idx}]"))
    return problems


def walk_values(obj: Any, path: str = "$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path, k, v
            yield from walk_values(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_values(v, f"{path}[{i}]")


def check_safety_flags(data: Any, path: str, errors: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> None:
    if not isinstance(data, dict):
        return
    if path.startswith("data/optimizer/"):
        if data.get("safe_mode") is not True:
            add_error(errors, "safety", "optimizer output must keep safe_mode=true", path)
    for parent, key, value in walk_values(data):
        if key in FORBIDDEN_TRUE_KEYS and value is True:
            add_error(errors, "safety", f"{key}=true is forbidden at {parent}.{key}", path)
        if key in FORBIDDEN_FALSE_KEYS and value is False:
            add_error(errors, "safety", f"{key}=false is forbidden at {parent}.{key}", path)
        if key == "mode" and isinstance(value, str) and "trade" in value.lower() and path.startswith("data/optimizer/"):
            add_warning(warnings, "safety", f"mode contains trade-like wording at {parent}.{key}: {value}", path)


def check_required_files(errors, warnings) -> Dict[str, Any]:
    present = []
    missing = []
    for item in REQUIRED_FILES:
        if (ROOT / item).exists():
            present.append(item)
        else:
            missing.append(item)
            add_error(errors, "required_files", "required file missing", item)
    workflow_dir = ROOT / REQUIRED_WORKFLOW_DIR
    workflows = sorted(rel(p) for p in workflow_dir.glob("*.yml")) if workflow_dir.exists() else []
    if not workflow_dir.exists():
        add_error(errors, "required_files", "workflow directory missing", REQUIRED_WORKFLOW_DIR)
    if not workflows:
        add_error(errors, "required_files", "no workflow YAML files found", REQUIRED_WORKFLOW_DIR)
    return {"present": present, "missing": missing, "workflow_files": workflows}


def check_json_parse(errors, warnings) -> Dict[str, Any]:
    parsed = []
    failed = []
    skip_parts = {"node_modules", ".git"}
    for p in ROOT.rglob("*.json"):
        if any(part in skip_parts for part in p.parts):
            continue
        data, err = load_json(p)
        if err:
            failed.append({"path": rel(p), "error": err})
            add_error(errors, "json_parse", err, rel(p))
        else:
            parsed.append(rel(p))
    return {"parsed_count": len(parsed), "failed": failed}


def check_schema_registry(errors, warnings) -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        add_error(errors, "schema", "schema registry missing", rel(REGISTRY_PATH))
        return {"status": "ERROR", "validated": [], "skipped": [], "errors": ["registry missing"]}
    registry, err = load_json(REGISTRY_PATH)
    if err:
        add_error(errors, "schema", f"schema registry parse error: {err}", rel(REGISTRY_PATH))
        return {"status": "ERROR", "validated": [], "skipped": [], "errors": [err]}
    validated = []
    skipped = []
    schema_errors = []
    for entry in registry.get("files", []):
        file_path = ROOT / entry.get("path", "")
        schema_path = ROOT / entry.get("schema", "")
        required = bool(entry.get("required", False))
        entry_id = {"path": entry.get("path"), "schema": entry.get("schema"), "required": required}
        if not file_path.exists():
            if required:
                msg = "registered required data file missing"
                schema_errors.append({**entry_id, "error": msg})
                add_error(errors, "schema", msg, entry.get("path"))
            else:
                skipped.append({**entry_id, "reason": "optional file missing"})
            continue
        if not schema_path.exists():
            msg = "registered schema file missing"
            schema_errors.append({**entry_id, "error": msg})
            add_error(errors, "schema", msg, entry.get("schema"))
            continue
        data, data_err = load_json(file_path)
        schema, schema_err = load_json(schema_path)
        if data_err:
            msg = f"data parse error: {data_err}"
            schema_errors.append({**entry_id, "error": msg})
            add_error(errors, "schema", msg, entry.get("path"))
            continue
        if schema_err:
            msg = f"schema parse error: {schema_err}"
            schema_errors.append({**entry_id, "error": msg})
            add_error(errors, "schema", msg, entry.get("schema"))
            continue
        problems = validate_schema_subset(data, schema, "$")
        check_safety_flags(data, entry.get("path", ""), errors, warnings)
        if problems:
            for problem in problems:
                add_error(errors, "schema", problem, entry.get("path"))
            schema_errors.extend({**entry_id, "error": problem} for problem in problems)
        else:
            validated.append(entry_id)
    return {
        "status": "OK" if not schema_errors else "ERROR",
        "registry_version": registry.get("version"),
        "validated_count": len(validated),
        "validated": validated,
        "skipped": skipped,
        "errors": schema_errors,
    }


def check_python_compile(errors, warnings) -> Dict[str, Any]:
    compiled = []
    failed = []
    for p in sorted((ROOT / "scripts").rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        try:
            py_compile.compile(str(p), doraise=True)
            compiled.append(rel(p))
        except Exception as exc:
            failed.append({"path": rel(p), "error": str(exc)})
            add_error(errors, "python_compile", str(exc), rel(p))
    return {"compiled_count": len(compiled), "failed": failed}


def run_command(cmd: List[str]) -> Tuple[int, str]:
    try:
        res = subprocess.run(cmd, cwd=ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return res.returncode, res.stdout.strip()
    except FileNotFoundError as exc:
        return 127, str(exc)


def check_node(errors, warnings) -> Dict[str, Any]:
    if not shutil.which("node"):
        add_warning(warnings, "node_check", "node executable not found; JS syntax check skipped")
        return {"status": "SKIPPED", "reason": "node not found", "checked": []}
    checked = []
    failed = []
    for item in NODE_CHECK_FILES:
        p = ROOT / item
        if not p.exists():
            continue
        code, output = run_command(["node", "--check", item])
        if code == 0:
            checked.append(item)
        else:
            failed.append({"path": item, "output": output})
            add_error(errors, "node_check", output, item)
    return {"status": "OK" if not failed else "ERROR", "checked": checked, "failed": failed}


def check_frontend_source(errors, warnings) -> Dict[str, Any]:
    script = ROOT / "scripts" / "build_frontend_bundle.py"
    if not script.exists():
        add_error(errors, "frontend", "frontend build/check script missing", rel(script))
        return {"status": "ERROR", "runtime_matches_source": None}
    code, output = run_command([sys.executable, "scripts/build_frontend_bundle.py", "--check"])
    ok = code == 0
    if not ok:
        add_error(errors, "frontend", output or "frontend source/runtime check failed", "assets/js/app.bundle.js")
    return {"status": "OK" if ok else "ERROR", "command_output": output}


def check_workflows(errors, warnings) -> Dict[str, Any]:
    workflow_dir = ROOT / REQUIRED_WORKFLOW_DIR
    files = sorted(workflow_dir.glob("*.yml")) if workflow_dir.exists() else []
    results = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        has_name = "name:" in text
        has_on = "on:" in text or "on :" in text
        has_jobs = "jobs:" in text
        item = {"path": rel(p), "has_name": has_name, "has_on": has_on, "has_jobs": has_jobs}
        results.append(item)
        if not (has_name and has_on and has_jobs):
            add_warning(warnings, "workflow", "workflow may be missing name/on/jobs", rel(p))
    return {"workflow_count": len(results), "workflows": results}


def write_outputs(result: Dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Validation Gate v4.6",
        "",
        f"- Status: **{result['status']}**",
        f"- Generated at: `{result['generated_at']}`",
        f"- Error count: `{result['summary']['error_count']}`",
        f"- Warning count: `{result['summary']['warning_count']}`",
        f"- Schema validated: `{result['checks']['schema_registry'].get('validated_count', 0)}` files",
        f"- JSON parsed: `{result['checks']['json_parse'].get('parsed_count', 0)}` files",
        f"- Python compiled: `{result['checks']['python_compile'].get('compiled_count', 0)}` scripts",
        "",
        "## Errors",
    ]
    if result["errors"]:
        for e in result["errors"][:50]:
            lines.append(f"- `{e.get('category')}` `{e.get('path')}` — {e.get('message')}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Warnings")
    if result["warnings"]:
        for w in result["warnings"][:50]:
            lines.append(f"- `{w.get('category')}` `{w.get('path')}` — {w.get('message')}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Policy")
    lines.append("- Validation failure must block workflow commit/output promotion.")
    lines.append("- This gate does not approve trades and does not enable execution.")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Repo validation gate v4.6")
    parser.add_argument("--no-node", action="store_true", help="Skip node --check")
    args = parser.parse_args()

    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    checks: Dict[str, Any] = {}

    checks["required_files"] = check_required_files(errors, warnings)
    checks["json_parse"] = check_json_parse(errors, warnings)
    checks["schema_registry"] = check_schema_registry(errors, warnings)
    checks["python_compile"] = check_python_compile(errors, warnings)
    checks["frontend_source_runtime"] = check_frontend_source(errors, warnings)
    checks["workflows"] = check_workflows(errors, warnings)
    checks["node_check"] = {"status": "SKIPPED", "reason": "--no-node"} if args.no_node else check_node(errors, warnings)

    result = {
        "version": "v4.6",
        "status": "OK" if not errors else "FAIL",
        "generated_at": now_iso(),
        "mode": "validation_gate",
        "safe_mode": True,
        "summary": {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "schema_validated_count": checks["schema_registry"].get("validated_count", 0),
            "python_compiled_count": checks["python_compile"].get("compiled_count", 0),
        },
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "safety_boundary": [
            "Validation gate only checks repository integrity and schema contracts.",
            "It does not approve trades, does not write Supabase, and does not enable execution.",
            "If status is FAIL, downstream workflow commit should be blocked."
        ],
    }
    write_outputs(result)
    print(f"Wrote {rel(LATEST_JSON)}")
    print(f"Wrote {rel(SUMMARY_MD)}")
    print(f"Status: {result['status']}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    if errors:
        print("VALIDATION_ERRORS_BEGIN")
        for idx, e in enumerate(errors[:50], start=1):
            print(f"{idx}. [{e.get('category')}] {e.get('path')}: {e.get('message')}")
        print("VALIDATION_ERRORS_END")
    if warnings:
        print("VALIDATION_WARNINGS_BEGIN")
        for idx, w in enumerate(warnings[:50], start=1):
            print(f"{idx}. [{w.get('category')}] {w.get('path')}: {w.get('message')}")
        print("VALIDATION_WARNINGS_END")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
