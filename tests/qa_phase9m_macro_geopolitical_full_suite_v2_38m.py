#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9m_macro_geo_contract_v2_38m.py",
    "qa_phase9m_macro_geo_builder_v2_38m.py",
    "qa_phase9m_macro_geo_quality_v2_38m.py",
    "qa_phase9l_us_explained_shortlist_full_suite_v2_38l.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38M macro/geopolitical context/full-suite/offline/static-no-live-news/no-recommendations/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
