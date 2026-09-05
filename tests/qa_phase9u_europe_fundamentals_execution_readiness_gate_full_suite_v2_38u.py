#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9u_europe_fundamentals_execution_readiness_gate_contract_v2_38u.py",
    "qa_phase9u_europe_fundamentals_execution_readiness_gate_builder_v2_38u.py",
    "qa_phase9u_europe_fundamentals_execution_readiness_gate_quality_v2_38u.py",
    "qa_phase9t_europe_manual_review_pack_full_suite_v2_38t.py",
]


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_europe_fundamentals_provider_pilot_v2_38r.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/build_europe_official_filings_review_v2_38s.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/build_europe_manual_review_pack_v2_38t.py")], cwd=ROOT, check=True)
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38U Europe fundamentals execution readiness gate/full-suite/offline/no-network/no-credential-leak/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
