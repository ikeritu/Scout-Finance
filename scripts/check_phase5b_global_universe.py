"""
Scout Finance — Phase 5B checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase5b_global_universe.py

This script does not call OpenAI and does not modify files.
"""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

GLOBAL_UNIVERSE = PROJECT_ROOT / "data" / "universe" / "global_universe.csv"
GLOBAL_UNIVERSE_VALIDATED = PROJECT_ROOT / "data" / "universe" / "global_universe_validated.csv"
SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "universe_validation_summary.json"


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 5B global universe checker")
    print("=" * 58)

    if GLOBAL_UNIVERSE.exists():
        ok(f"Input exists: {GLOBAL_UNIVERSE}")
    else:
        fail(f"Input missing: {GLOBAL_UNIVERSE}")
        return 1

    if GLOBAL_UNIVERSE_VALIDATED.exists():
        ok(f"Validated output exists: {GLOBAL_UNIVERSE_VALIDATED}")
    else:
        warn(f"Validated output missing: {GLOBAL_UNIVERSE_VALIDATED}")

    if SUMMARY.exists():
        ok(f"Summary exists: {SUMMARY}")
    else:
        warn(f"Summary missing: {SUMMARY}")
        return 0

    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Could not read summary JSON: {exc}")
        return 1

    print()
    print("Summary")
    print("-" * 58)
    print(f"Status: {summary.get('status')}")
    print(f"Input companies: {summary.get('input_companies')}")
    print(f"Required columns OK: {summary.get('has_required_columns')}")
    print(f"Duplicated ticker rows: {summary.get('duplicated_ticker_rows')}")

    if summary.get("status") == "OK":
        ok("Phase 5B validation successful")
        return 0

    warn("Phase 5B validation completed with issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
