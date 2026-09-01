#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9a_dataset_resolution_v2_38a.py",
    "qa_phase9a_universe_audit_v2_38a.py",
    "qa_phase9a_exclusions_readiness_v2_38a.py",
    "qa_phase9a_provider_route_matrix_v2_38a.py",
    "qa_market_universe_inventory_v2_33l.py",
]


def main() -> int:
    for name in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / name)], cwd=ROOT)
        if result.returncode:
            print(f"FAIL: {name}")
            return result.returncode
    print("PASS: v2.38A full suite/offline/43089/no-scoring/no-ranking/no-recommendations/no-phase9b")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
