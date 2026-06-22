
"""
Scout Finance — Phase 6E clean global runner checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase6e_clean_global_runner.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "global_funnel_run_summary.json"
STAGE1_PASSED = PROJECT_ROOT / "data" / "stages" / "stage1_passed.csv"
STAGE1_PASSED_ENRICHED = PROJECT_ROOT / "data" / "stages" / "stage1_passed_enriched.csv"
STAGE2_SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "stage2_summary.json"
TOP100 = PROJECT_ROOT / "outputs" / "scouting" / "top_100_candidates.csv"
BRIDGE = PROJECT_ROOT / "outputs" / "scouting" / "stage3_candidates_for_ranking.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 6E clean global runner checker")
    print("=" * 68)

    if not SUMMARY.exists():
        fail(f"Missing global funnel summary: {SUMMARY}")
        print("Run first: .\\.venv\\Scripts\\python.exe -m src.run_global_funnel_demo")
        return 1

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    if summary.get("phase") != "6E":
        fail(f"Summary phase is not 6E: {summary.get('phase')}")
        return 1

    ok("Summary phase is 6E")

    if summary.get("status") != "OK":
        fail(f"Runner status is not OK: {summary.get('status')}")
        return 1

    ok("Runner status OK")

    if summary.get("clean_enriched_flow") is True:
        ok("Clean enriched flow enabled")
    else:
        fail("Clean enriched flow flag is not True")
        return 1

    if summary.get("stage1_passed_overwritten") is False:
        ok("stage1_passed.csv was not overwritten by runner")
    else:
        fail("Summary indicates stage1_passed.csv was overwritten")
        return 1

    if summary.get("openai_called") is False:
        ok("OpenAI was not called")
    else:
        fail("Summary indicates OpenAI was called")
        return 1

    if summary.get("api_called") is False:
        ok("External API was not called")
    else:
        fail("Summary indicates external API was called")
        return 1

    if not STAGE1_PASSED.exists():
        fail(f"Missing clean Stage 1 file: {STAGE1_PASSED}")
        return 1

    if not STAGE1_PASSED_ENRICHED.exists():
        fail(f"Missing enriched Stage 1 file: {STAGE1_PASSED_ENRICHED}")
        return 1

    ok("Stage 1 clean and enriched files exist")

    stage1_df = pd.read_csv(STAGE1_PASSED)
    enriched_df = pd.read_csv(STAGE1_PASSED_ENRICHED)

    if len(stage1_df) != len(enriched_df):
        fail("Clean and enriched Stage 1 files have different row counts")
        return 1

    ok("Clean and enriched Stage 1 row counts match")

    if "revenue_ttm" not in enriched_df.columns:
        fail("Enriched Stage 1 file has no revenue_ttm column")
        return 1

    ok("Enriched Stage 1 contains fundamentals")

    if not STAGE2_SUMMARY.exists():
        fail(f"Missing Stage 2 summary: {STAGE2_SUMMARY}")
        return 1

    stage2_summary = json.loads(STAGE2_SUMMARY.read_text(encoding="utf-8"))

    if stage2_summary.get("input_companies") != len(enriched_df):
        fail("Stage 2 input count does not match enriched Stage 1 rows")
        return 1

    ok("Stage 2 input count matches enriched Stage 1")

    expected_steps = [
        "Stage 0 — Validate global universe",
        "Stage 1 — Investable universe filter",
        "Phase 6C — Enrich Stage 1 fundamentals cleanly",
        "Phase 6D — Stage 2 from enriched Stage 1",
        "Demo enrichment — Stage 2 scoring inputs",
        "Stage 3 — Opportunity scoring",
        "Export — Stage 3 candidates bridge",
    ]

    step_names = [step.get("name") for step in summary.get("steps", [])]
    missing_steps = [step for step in expected_steps if step not in step_names]

    if missing_steps:
        fail("Missing expected steps:")
        for step in missing_steps:
            print(f"   - {step}")
        return 1

    ok("All expected clean-runner steps present")

    for path in [TOP100, BRIDGE]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    print()
    print("Funnel counts")
    print("-" * 68)
    counts = summary.get("funnel_counts", {})
    print(f"Stage 0 input: {counts.get('stage0_input_companies')}")
    print(f"Stage 1 passed/watchlist/rejected: {counts.get('stage1_passed')} / {counts.get('stage1_watchlist')} / {counts.get('stage1_rejected')}")
    print(f"Fundamentals matched: {counts.get('fundamentals_matched_companies')}")
    print(f"Stage 2 passed/watchlist/rejected: {counts.get('stage2_passed')} / {counts.get('stage2_watchlist')} / {counts.get('stage2_rejected')}")
    print(f"Stage 3 passed/watchlist/rejected: {counts.get('stage3_passed')} / {counts.get('stage3_watchlist')} / {counts.get('stage3_rejected')}")

    print()
    print("Result")
    print("-" * 68)
    ok("Phase 6E clean global runner is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
