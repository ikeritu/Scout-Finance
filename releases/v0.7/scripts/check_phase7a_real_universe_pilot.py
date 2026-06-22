
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PILOT_SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "real_universe_pilot_summary.json"
PILOT_INPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_pilot.csv"
GLOBAL_UNIVERSE = PROJECT_ROOT / "data" / "universe" / "global_universe.csv"
STAGE1_PASSED = PROJECT_ROOT / "data" / "stages" / "stage1_passed.csv"
STAGE1_REJECTED = PROJECT_ROOT / "data" / "stages" / "stage1_rejected.csv"
STAGE1_REJECTION_LOG = PROJECT_ROOT / "data" / "stages" / "stage1_rejection_log.csv"
COVERAGE_REPORT = PROJECT_ROOT / "outputs" / "scouting" / "fundamental_coverage_report.json"


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def _rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return 0


def main() -> int:
    print("Scout Finance — Phase 7A real universe pilot checker")
    print("=" * 68)

    required_outputs = [
        PILOT_SUMMARY, PILOT_INPUT, GLOBAL_UNIVERSE, STAGE1_PASSED,
        STAGE1_REJECTED, STAGE1_REJECTION_LOG, COVERAGE_REPORT,
    ]

    for path in required_outputs:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    try:
        summary = json.loads(PILOT_SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read pilot summary: {exc}")
        return 1

    if summary.get("phase") != "7A":
        fail(f"Summary phase is not 7A: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7A")

    if summary.get("status") != "OK":
        fail(f"Pilot status is not OK: {summary.get('status')}")
        return 1
    ok("Pilot status OK")

    for flag, label in [
        ("openai_called", "OpenAI was not called"),
        ("api_called", "External API was not called"),
        ("app_modified", "app.py was not modified"),
        ("release_v0_6_modified", "release v0.6 was not modified"),
    ]:
        if summary.get(flag) is False:
            ok(label)
        else:
            fail(f"Summary flag invalid: {flag}")
            return 1

    counts = summary.get("counts", {})
    stage1_total = (
        (counts.get("stage1_passed") or 0)
        + (counts.get("stage1_watchlist") or 0)
        + (counts.get("stage1_rejected") or 0)
    )
    stage0_input = counts.get("stage0_input_companies")

    if stage0_input is not None and stage1_total != stage0_input:
        fail("Stage 1 passed/watchlist/rejected does not sum to Stage 0 input")
        return 1
    ok("Stage 1 counts are consistent")

    if _rows(PILOT_INPUT) == summary.get("raw_rows_loaded"):
        ok("Pilot input row count matches summary")
    else:
        warn("Pilot input rows differ from summary raw_rows_loaded")

    if _rows(GLOBAL_UNIVERSE) == stage0_input:
        ok("global_universe row count matches Stage 0 input")
    else:
        warn("global_universe rows differ from Stage 0 input")

    print()
    print("Summary")
    print("-" * 68)
    print(f"Pilot rows loaded: {summary.get('raw_rows_loaded')}")
    print(f"Limit: {summary.get('limit')}")
    print(f"Stage 0 input: {stage0_input}")
    print(f"Stage 1 passed/watchlist/rejected: {counts.get('stage1_passed')} / {counts.get('stage1_watchlist')} / {counts.get('stage1_rejected')}")
    print(f"Companies ready for Stage 2: {counts.get('companies_ready_for_stage2')}")
    print(f"Companies not ready for Stage 2: {counts.get('companies_not_ready_for_stage2')}")
    print(f"Average core Stage 2 coverage: {counts.get('average_core_stage2_coverage_percent')}%")

    print()
    print("Result")
    print("-" * 68)
    ok("Phase 7A real universe pilot is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
