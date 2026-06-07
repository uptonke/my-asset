#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "repo_architecture"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except Exception:
        return 0


def list_files() -> List[Path]:
    ignored_parts = {".git", "node_modules", "__pycache__", ".pytest_cache"}
    files: List[Path] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.relative_to(ROOT).parts)
        if parts & ignored_parts:
            continue
        files.append(p)
    return sorted(files, key=lambda x: rel(x))


def parse_index_assets() -> Dict[str, List[str]]:
    index = ROOT / "index.html"
    html = read_text(index)
    scripts = re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", html)
    styles = re.findall(r"<link[^>]+href=[\"']([^\"']+)[\"']", html)
    local_scripts = [s.split("?")[0] for s in scripts if not re.match(r"^https?://", s)]
    local_styles = [s.split("?")[0] for s in styles if not re.match(r"^https?://", s) and s != "data:,"]
    return {
        "script_src": scripts,
        "style_href": styles,
        "local_script_files": local_scripts,
        "local_style_files": local_styles,
    }


def load_manifest() -> Dict[str, Any]:
    p = ROOT / "split-manifest.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_error": str(exc)}


def classify_files(files: List[Path], html_assets: Dict[str, List[str]], manifest: Dict[str, Any]) -> Dict[str, Any]:
    local_runtime = set(html_assets.get("local_script_files", []) + html_assets.get("local_style_files", []))
    referenced_runtime_files = []
    missing_references = []
    for asset in sorted(local_runtime):
        p = ROOT / asset
        item = {"path": asset, "exists": p.exists(), "size_bytes": file_size(p) if p.exists() else None, "sha256": sha256(p) if p.exists() else None}
        if p.exists():
            referenced_runtime_files.append(item)
        else:
            missing_references.append(item)

    root_js = [p for p in files if p.parent == ROOT and p.suffix == ".js"]
    src_js = [p for p in files if rel(p).startswith("assets/js/src/") and p.suffix == ".js"]
    asset_js = [p for p in files if rel(p).startswith("assets/js/") and p.suffix == ".js"]
    css_files = [p for p in files if p.suffix == ".css"]
    workflow_files = [p for p in files if rel(p).startswith(".github/workflows/") and p.suffix in {".yml", ".yaml"}]
    root_workflow_like = [p for p in files if p.parent == ROOT and p.name.endswith((".yml", ".yaml"))]
    data_optimizer = [p for p in files if rel(p).startswith("data/optimizer/")]
    data_repo_arch = [p for p in files if rel(p).startswith("data/repo_architecture/")]

    root_duplicate_candidates = []
    src_names = {p.name for p in src_js}
    asset_js_names = {p.name for p in asset_js}
    for p in root_js:
        reason = []
        if p.name in src_names:
            reason.append("same filename exists under assets/js/src")
        if p.name in asset_js_names:
            reason.append("same filename exists under assets/js")
        if p.name == "app.bundle.js":
            reason.append("root bundle conflicts with runtime bundle assets/js/app.bundle.js")
        if p.name == "quant-main-display.js":
            reason.append("index.html references assets/js/quant-main-display.js, not root quant-main-display.js")
        root_duplicate_candidates.append({
            "path": rel(p),
            "size_bytes": file_size(p),
            "sha256": sha256(p),
            "reason": reason or ["root-level JS should be reviewed before deletion"],
        })

    canonical_source = manifest.get("frontend_source_of_truth", {}).get("canonical_source")
    runtime_bundle = manifest.get("js_runtime", "assets/js/app.bundle.js")
    canonical = ROOT / canonical_source if canonical_source else None
    runtime = ROOT / runtime_bundle
    source_truth = {
        "policy": manifest.get("frontend_source_of_truth", {}).get("policy", "not_declared"),
        "canonical_source": canonical_source,
        "canonical_source_exists": canonical.exists() if canonical else False,
        "runtime_bundle": runtime_bundle,
        "runtime_bundle_exists": runtime.exists(),
        "canonical_source_sha256": sha256(canonical) if canonical and canonical.exists() else None,
        "runtime_bundle_sha256": sha256(runtime) if runtime.exists() else None,
        "runtime_matches_canonical_source": bool(canonical and canonical.exists() and runtime.exists() and sha256(canonical) == sha256(runtime)),
        "legacy_fragments": manifest.get("js_source_fragments", []),
    }

    safe_delete_candidates = []
    review_before_delete = []
    for item in root_duplicate_candidates:
        review_before_delete.append(item)
    if root_workflow_like:
        for p in root_workflow_like:
            review_before_delete.append({
                "path": rel(p),
                "size_bytes": file_size(p),
                "sha256": sha256(p),
                "reason": ["workflow-like YAML outside .github/workflows; GitHub Actions will not execute it from root"],
            })

    return {
        "referenced_runtime_files": referenced_runtime_files,
        "missing_references": missing_references,
        "workflow_files": [{"path": rel(p), "size_bytes": file_size(p)} for p in workflow_files],
        "root_workflow_like_files": [{"path": rel(p), "size_bytes": file_size(p)} for p in root_workflow_like],
        "root_js_duplicate_candidates": root_duplicate_candidates,
        "frontend_source_of_truth": source_truth,
        "counts": {
            "total_files": len(files),
            "root_js_files": len(root_js),
            "assets_js_files": len(asset_js),
            "assets_js_src_files": len(src_js),
            "css_files": len(css_files),
            "workflow_files": len(workflow_files),
            "optimizer_output_files": len(data_optimizer),
            "repo_architecture_output_files": len(data_repo_arch),
        },
        "data_outputs": {
            "optimizer": [{"path": rel(p), "size_bytes": file_size(p)} for p in data_optimizer],
            "repo_architecture": [{"path": rel(p), "size_bytes": file_size(p)} for p in data_repo_arch],
        },
        "cleanup_review": {
            "safe_delete_candidates": safe_delete_candidates,
            "review_before_delete": review_before_delete,
            "do_not_delete_without_tests": [
                "index.html",
                "assets/js/app.bundle.js",
                "assets/js/src/app.bundle.source.js",
                "assets/js/quant-main-display.js",
                "assets/css/tailwind-built.css",
                ".github/workflows/*.yml",
                "scripts/*.py used by workflows",
                "data/optimizer/*.json read by frontend",
            ],
        },
    }


def write_summary(report: Dict[str, Any]) -> None:
    audit = report["audit"]
    ft = audit["frontend_source_of_truth"]
    lines = [
        "# v4.0 Repo Architecture Audit",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Total files scanned: `{audit['counts']['total_files']}`",
        f"- GitHub workflow files: `{audit['counts']['workflow_files']}`",
        f"- Optimizer output files: `{audit['counts']['optimizer_output_files']}`",
        "",
        "## v4.1 Frontend Source of Truth",
        "",
        f"- Policy: `{ft['policy']}`",
        f"- Canonical source: `{ft['canonical_source']}`",
        f"- Runtime bundle: `{ft['runtime_bundle']}`",
        f"- Runtime matches canonical source: `{ft['runtime_matches_canonical_source']}`",
        "",
        "## Runtime files referenced by index.html",
        "",
    ]
    for item in audit["referenced_runtime_files"]:
        lines.append(f"- `{item['path']}` — {item['size_bytes']} bytes")
    if audit["missing_references"]:
        lines += ["", "## Missing runtime references", ""]
        for item in audit["missing_references"]:
            lines.append(f"- `{item['path']}`")
    lines += ["", "## Review-before-delete candidates", ""]
    candidates = audit["cleanup_review"]["review_before_delete"]
    if candidates:
        for item in candidates:
            reason = "; ".join(item.get("reason", []))
            lines.append(f"- `{item['path']}` — {reason}")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Do-not-delete without tests",
        "",
    ]
    for item in audit["cleanup_review"]["do_not_delete_without_tests"]:
        lines.append(f"- `{item}`")
    (OUT_DIR / "repo_architecture_audit_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    files = list_files()
    html_assets = parse_index_assets()
    manifest = load_manifest()
    audit = classify_files(files, html_assets, manifest)
    report = {
        "version": "v4.0",
        "generated_at": utc_now(),
        "scope": "repo_architecture_audit",
        "audit": audit,
        "safety_boundary": [
            "This audit is read-only.",
            "No files are deleted by this script.",
            "Deletion candidates require separate review before removal.",
        ],
    }
    (OUT_DIR / "repo_architecture_audit_latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(report)

    frontend_report = {
        "version": "v4.1",
        "generated_at": report["generated_at"],
        "scope": "frontend_source_of_truth",
        "frontend_source_of_truth": audit["frontend_source_of_truth"],
        "decision": {
            "canonical_source": audit["frontend_source_of_truth"]["canonical_source"],
            "runtime_bundle": audit["frontend_source_of_truth"]["runtime_bundle"],
            "legacy_fragments_status": "preserved_for_reference_not_authoritative",
            "do_not_edit_runtime_bundle_directly": True,
            "build_command": "python scripts/build_frontend_bundle.py",
            "check_command": "python scripts/build_frontend_bundle.py --check",
        },
    }
    (OUT_DIR / "frontend_source_of_truth_latest.json").write_text(json.dumps(frontend_report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "frontend_source_of_truth_summary.md").write_text(
        "# v4.1 Frontend Source of Truth\n\n"
        f"- Canonical source: `{frontend_report['decision']['canonical_source']}`\n"
        f"- Runtime bundle: `{frontend_report['decision']['runtime_bundle']}`\n"
        "- Legacy fragments: `assets/js/src/00-*.js` to `60-*.js` are retained for reference but are not authoritative in v4.1.\n"
        "- Rule: edit canonical source, then run `python scripts/build_frontend_bundle.py`.\n"
        "- Rule: do not hand-edit `assets/js/app.bundle.js`.\n",
        encoding="utf-8",
    )
    print("Wrote data/repo_architecture/repo_architecture_audit_latest.json")
    print("Wrote data/repo_architecture/repo_architecture_audit_summary.md")
    print("Wrote data/repo_architecture/frontend_source_of_truth_latest.json")
    print("Wrote data/repo_architecture/frontend_source_of_truth_summary.md")
    print(f"Runtime matches canonical source: {audit['frontend_source_of_truth']['runtime_matches_canonical_source']}")


if __name__ == "__main__":
    main()
