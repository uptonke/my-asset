#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List


def probe_module(package_name: str, import_name: Optional[str] = None) -> Dict[str, Any]:
    import_name = import_name or package_name
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        return {
            "package": package_name,
            "import_name": import_name,
            "available": False,
            "status": "MISSING",
            "version": None,
            "error": None,
        }

    try:
        mod = importlib.import_module(import_name)
        try:
            version = importlib.metadata.version(package_name)
        except Exception:
            version = getattr(mod, "__version__", None)

        return {
            "package": package_name,
            "import_name": import_name,
            "available": True,
            "status": "OK",
            "version": str(version) if version is not None else None,
            "error": None,
        }
    except Exception as exc:
        return {
            "package": package_name,
            "import_name": import_name,
            "available": False,
            "status": "IMPORT_FAILED",
            "version": None,
            "error": str(exc)[:1000],
        }


def riskfolio_smoke_test() -> Dict[str, Any]:
    try:
        import riskfolio as rp

        attrs = {
            "Portfolio": hasattr(rp, "Portfolio"),
            "HCPortfolio": hasattr(rp, "HCPortfolio"),
        }

        # Do not run optimization in v1.1. This only checks whether the expected objects exist.
        if not attrs["Portfolio"]:
            return {
                "status": "API_UNEXPECTED",
                "available": False,
                "attributes": attrs,
                "error": "riskfolio imported, but rp.Portfolio was not found.",
            }

        return {
            "status": "OK",
            "available": True,
            "attributes": attrs,
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "FAILED",
            "available": False,
            "attributes": {},
            "error": str(exc)[:1000],
        }


def main() -> None:
    packages = {
        "riskfolio": probe_module("Riskfolio-Lib", "riskfolio"),
        "cvxpy": probe_module("cvxpy", "cvxpy"),
        "scipy": probe_module("scipy", "scipy"),
        "sklearn": probe_module("scikit-learn", "sklearn"),
        "numpy": probe_module("numpy", "numpy"),
        "pandas": probe_module("pandas", "pandas"),
    }

    cvxpy_solvers: List[str] = []
    cvxpy_solver_error = None
    if packages["cvxpy"]["available"]:
        try:
            import cvxpy as cp
            cvxpy_solvers = [str(x) for x in cp.installed_solvers()]
        except Exception as exc:
            cvxpy_solver_error = str(exc)[:1000]

    smoke = riskfolio_smoke_test() if packages["riskfolio"]["available"] else {
        "status": "SKIPPED",
        "available": False,
        "attributes": {},
        "error": "riskfolio import not available.",
    }

    riskfolio_ready = bool(
        packages["riskfolio"]["available"]
        and packages["cvxpy"]["available"]
        and len(cvxpy_solvers) > 0
        and smoke.get("status") == "OK"
    )

    out = {
        "version": "v1.1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "dependency_sandbox_only",
        "status": "OK" if riskfolio_ready else "NOT_READY",
        "riskfolio_ready": riskfolio_ready,
        "packages": packages,
        "cvxpy_solvers": cvxpy_solvers,
        "cvxpy_solver_error": cvxpy_solver_error,
        "riskfolio_smoke_test": smoke,
        "next_step": (
            "v1.2 Riskfolio-Lib optimizer sandbox can be attempted."
            if riskfolio_ready
            else "Do not run v1.2 yet. Fix installation/import/solver issue first."
        ),
        "safety_boundary": [
            "No portfolio optimization is run in v1.1.",
            "No Supabase write.",
            "No official weights, no BUY/SELL.",
            "This workflow is isolated from Update Stock Quant Meta and Daily Quant Pipeline.",
        ],
    }

    print(json.dumps(out, indent=2, ensure_ascii=False))

    out_path = Path("data/optimizer/riskfolio_dependency_status.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    from pathlib import Path
    main()
