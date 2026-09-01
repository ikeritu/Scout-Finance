#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "tests/qa_product_contract_v2_37b.py",
    "tests/qa_ui_data_readiness_v2_37c.py",
    "tests/qa_watchlists_reports_v2_37.py",
    "tests/qa_phase7_full_suite_v2_36.py",
]


def main() -> int:
    for test in TESTS:
        completed = subprocess.run([sys.executable, test], cwd=ROOT)
        if completed.returncode:
            raise SystemExit(f"FAIL: {test}")
    for path in [ROOT / "app_v2_37.py", *sorted((ROOT / "src/ui_v2_37").glob("*.py"))]:
        text = path.read_text(encoding="utf-8").lower()
        assert "api_token" not in text and "password" not in text
    print("PASS: v2.37 phase-8 full suite/offline/no-secrets/no-broker/phase7-limit-visible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
