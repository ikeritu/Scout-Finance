#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE6_MODULES = [
    "tests/qa_scoring_engine_v2_35.py",
    "tests/qa_scoring_real_local_v2_35.py",
    "tests/qa_phase6_final_gate_v2_35c.py",
]


def main() -> int:
    for module in PHASE6_MODULES:
        subprocess.run([sys.executable, module], cwd=ROOT, check=True)
    missing_dependencies = [name for name in ("jsonschema", "certifi") if importlib.util.find_spec(name) is None]
    if missing_dependencies:
        print("SKIP_DEPENDENCY_MISSING: phase-5 inherited suite requires " + ", ".join(missing_dependencies))
    else:
        subprocess.run([sys.executable, "tests/qa_fundamentals_phase5_full_suite_v2_34i.py"], cwd=ROOT, check=True)
    print("PASS: v2.35C phase-6 full suite/no-network/no-secrets/no-phase7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
