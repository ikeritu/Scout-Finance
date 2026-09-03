#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9o_europe_price_history_contract_v2_38o.py",
    "qa_phase9o_europe_price_history_plan_v2_38o.py",
    "qa_phase9o_europe_price_history_runner_v2_38o.py",
    "qa_phase9o_europe_price_history_quality_v2_38o.py",
    "qa_phase9n_europe_home_exchange_full_suite_v2_38n.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38O Europe price history acquisition/full-suite/offline/no-secrets/no-scoring/no-ranking/no-recommendations/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
