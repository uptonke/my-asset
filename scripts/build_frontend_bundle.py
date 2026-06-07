#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "repo_architecture"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> Dict[str, Any]:
    path = ROOT / "split-manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_from_legacy_fragments(manifest: Dict[str, Any]) -> str:
    fragments: List[str] = manifest.get("js_source_fragments", [])
    if not fragments:
        raise FileNotFoundError("No canonical source and no js_source_fragments in split-manifest.json")
    parts = []
    for frag in fragments:
        p = ROOT / frag
        if not p.exists():
            raise FileNotFoundError(f"Missing JS fragment: {frag}")
        parts.append(p.read_text(encoding="utf-8"))
    return "\n\n".join(parts) + "\n"


def node_check(path: Path) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["node", "--check", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "available": True,
            "returncode": result.returncode,
            "ok": result.returncode == 0,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
        }
    except FileNotFoundError:
        return {
            "available": False,
            "returncode": None,
            "ok": None,
            "stdout": "",
            "stderr": "node executable not found",
        }


def write_status(status: Dict[str, Any]) -> None:
    (OUT_DIR / "frontend_build_status_latest.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# v4.2 Frontend Build Pipeline",
        "",
        f"- Generated: `{status['generated_at']}`",
        f"- Mode: `{status['mode']}`",
        f"- Source: `{status['source_path']}`",
        f"- Runtime bundle: `{status['runtime_path']}`",
        f"- Status: `{status['status']}`",
        f"- Runtime matches source: `{status['runtime_matches_source']}`",
        f"- Node syntax check: `{status['node_check']['ok']}`",
        "",
    ]
    if status.get("warnings"):
        lines += ["## Warnings", ""]
        for w in status["warnings"]:
            lines.append(f"- {w}")
    if status.get("error"):
        lines += ["", "## Error", "", f"```txt\n{status['error']}\n```"]
    (OUT_DIR / "frontend_build_status_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="v4.2 frontend bundle build/check pipeline")
    parser.add_argument("--check", action="store_true", help="Validate that runtime bundle matches canonical source without writing.")
    parser.add_argument("--skip-node-check", action="store_true", help="Skip node --check syntax validation.")
    args = parser.parse_args()

    manifest = load_manifest()
    source_rel = manifest.get("frontend_source_of_truth", {}).get("canonical_source", "assets/js/src/app.bundle.source.js")
    runtime_rel = manifest.get("js_runtime", "assets/js/app.bundle.js")
    source = ROOT / source_rel
    runtime = ROOT / runtime_rel
    warnings: List[str] = []
    error = None

    if source.exists():
        source_text = source.read_text(encoding="utf-8")
        source_mode = "canonical_single_source"
    else:
        warnings.append(f"Canonical source not found: {source_rel}; falling back to legacy js_source_fragments.")
        source_text = build_from_legacy_fragments(manifest)
        source_mode = "legacy_fragments_fallback"

    runtime_exists_before = runtime.exists()
    runtime_before_hash = sha256(runtime)

    if args.check:
        if not runtime.exists():
            error = f"Runtime bundle missing: {runtime_rel}"
            status_value = "FAIL"
        else:
            runtime_matches = runtime.read_text(encoding="utf-8") == source_text
            status_value = "OK" if runtime_matches else "DRIFT"
            if not runtime_matches:
                error = "Runtime bundle differs from canonical source. Run: python scripts/build_frontend_bundle.py"
    else:
        runtime.parent.mkdir(parents=True, exist_ok=True)
        if (not runtime.exists()) or runtime.read_text(encoding="utf-8") != source_text:
            runtime.write_text(source_text, encoding="utf-8")
        runtime_matches = runtime.read_text(encoding="utf-8") == source_text
        status_value = "OK" if runtime_matches else "FAIL"
        if not runtime_matches:
            error = "Runtime bundle still differs from source after write."

    node = {"available": None, "returncode": None, "ok": None, "stdout": "", "stderr": "skipped"}
    if not args.skip_node_check and runtime.exists():
        node = node_check(runtime)
        if node.get("ok") is False:
            status_value = "FAIL"
            error = "node --check failed for runtime bundle."

    status = {
        "version": "v4.2",
        "generated_at": utc_now(),
        "scope": "frontend_build_pipeline",
        "mode": "check" if args.check else "write",
        "source_mode": source_mode,
        "source_path": source_rel,
        "runtime_path": runtime_rel,
        "runtime_exists_before": runtime_exists_before,
        "runtime_hash_before": runtime_before_hash,
        "source_hash": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        "runtime_hash_after": sha256(runtime),
        "runtime_matches_source": runtime.exists() and runtime.read_text(encoding="utf-8") == source_text,
        "status": status_value,
        "warnings": warnings,
        "error": error,
        "node_check": node,
        "safety_boundary": [
            "The runtime bundle is generated from the canonical source.",
            "Do not hand-edit assets/js/app.bundle.js.",
            "Legacy fragments are not authoritative in v4.1/v4.2 unless explicitly selected later.",
        ],
    }
    write_status(status)
    print("Wrote data/repo_architecture/frontend_build_status_latest.json")
    print("Wrote data/repo_architecture/frontend_build_status_summary.md")
    print(f"Status: {status_value}")
    print(f"Runtime matches source: {status['runtime_matches_source']}")

    if args.check and status_value != "OK":
        raise SystemExit(1)
    if status_value == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
