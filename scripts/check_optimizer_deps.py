#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List


def probe_python_module(module_name: str, package_name: Optional[str] = None, import_name: Optional[str] = None) -> Dict[str, Any]:
    package_name = package_name or module_name
    import_name = import_name or module_name
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        return {"package": package_name, "import_name": import_name, "available": False, "status": "MISSING", "version": None, "error": None}
    try:
        mod = importlib.import_module(import_name)
        try:
            version = importlib.metadata.version(package_name)
        except Exception:
            version = getattr(mod, "__version__", None)
        return {"package": package_name, "import_name": import_name, "available": True, "status": "OK", "version": str(version) if version is not None else None, "error": None}
    except Exception as exc:
        return {"package": package_name, "import_name": import_name, "available": False, "status": "IMPORT_FAILED", "version": None, "error": str(exc)[:500]}


def main() -> None:
    packages = {
        "skfolio": probe_python_module("skfolio", "skfolio", "skfolio"),
        "riskfolio": probe_python_module("riskfolio", "Riskfolio-Lib", "riskfolio"),
        "cvxpy": probe_python_module("cvxpy", "cvxpy", "cvxpy"),
        "scipy": probe_python_module("scipy", "scipy", "scipy"),
        "sklearn": probe_python_module("sklearn", "scikit-learn", "sklearn"),
        "numpy": probe_python_module("numpy", "numpy", "numpy"),
        "pandas": probe_python_module("pandas", "pandas", "pandas"),
    }

    solvers: List[str] = []
    if packages["cvxpy"]["available"]:
        try:
            import cvxpy as cp
            solvers = [str(x) for x in cp.installed_solvers()]
        except Exception:
            solvers = []

    out = {
        "version": "v0.7",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "packages": packages,
        "cvxpy_solvers": solvers,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
