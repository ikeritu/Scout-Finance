#!/usr/bin/env python3
"""Block I: single entry point running every offline QA module built across
phase 5 (blocks C-H), so a reviewer never has to remember which of the six
files to run individually. No network, no real credentials, no real
licensed data required -- every module below is self-contained.

This file does not duplicate any test logic: it imports each module's own
`main()` (the same function each one runs when invoked directly) and
reports which passed. A failure here means the underlying module's own
main() raised -- fix it there, not here.
"""
from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

PHASE5_QA_MODULES = [
    "qa_fundamental_schema_v2_34c",
    "qa_fundamental_acquisition_v2_34d",
    "qa_fundamentals_acquisition_report_v2_34e",
    "qa_fundamental_normalizers_v2_34f",
    "qa_fundamental_derived_metrics_v2_34g",
    "qa_fundamental_validators_v2_34h",
]


def main() -> int:
    results = []
    for name in PHASE5_QA_MODULES:
        try:
            module = importlib.import_module(name)
            code = module.main()
            results.append((name, code == 0, None))
        except Exception:  # noqa: BLE001 -- deliberately broad: we want every module's failure reported, not just the first
            results.append((name, False, traceback.format_exc()))

    print()
    print("=== v2.34I phase-5 offline QA suite ===")
    failed = [name for name, ok, _ in results if not ok]
    for name, ok, tb in results:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
        if tb:
            print(tb)

    print(f"\n{len(results) - len(failed)}/{len(results)} modules passed")
    if failed:
        print(f"FAILED modules: {failed}")
        return 1
    print("PASS: v2.34I-phase5-full-offline-qa-suite/all-blocks-c-through-h/no-network/no-real-credentials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
