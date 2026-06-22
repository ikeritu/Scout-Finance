"""
Scout Finance — Phase 5I global funnel runner checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase5i_global_funnel_runner.py

This checker does not call OpenAI and does not modify app.py.
"""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "global_funnel_run_summary.json"
TOP100 = PROJECT_ROOT / "outputs" / "scouting" / "top_100_candidates.csv"
BRIDGE = PROJECT_ROOT / "outputs" / "scouting" / "stage3_candidates_for_ranking.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 5I global funnel runner checker")
    print("=" * 66)

    if not SUMMARY.exists():
        fail(f"Run summary missing: {SUMMARY}")
        print("Run first: .\\.venv\\Scripts\\python.exe -m src.run_global_funnel_demo")
        return 1

    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read summary JSON: {exc}")
        return 1

    if summary.get("status") != "OK":
        fail(f"Runner status is not OK: {summary.get('status')}")
        return 1

    ok("Runner summary status OK")

    if summary.get("openai_called") is False:
        ok("OpenAI was not called")
    else:
        fail("Summary indicates OpenAI was called")
        return 1

    if summary.get("app_modified") is False:
        ok("app.py was not modified by runner")
    else:
        fail("Summary indicates app.py was modified")
        return 1

    steps = summary.get("steps", [])

    expected_steps = [
        "Stage 0 — Validate global universe",
        "Stage 1 — Investable universe filter",
        "Demo enrichment — Stage 1 financials",
        "Stage 2 — Financial sanity check",
        "Demo enrichment — Stage 2 scoring inputs",
        "Stage 3 — Opportunity scoring",
        "Export — Stage 3 candidates bridge",
    ]

    step_names = [step.get("name") for step in steps]
    missing_steps = [step for step in expected_steps if step not in step_names]

    if missing_steps:
        fail("Missing expected steps:")
        for step in missing_steps:
            print(f"   - {step}")
        return 1

    ok("All expected steps present")

    failed_steps = [step for step in steps if step.get("status") != "OK"]

    if failed_steps:
        fail("Some steps failed:")
        for step in failed_steps:
            print(f"   - {step.get('name')}: {step.get('error')}")
        return 1

    ok("All steps finished OK")

    for path in [TOP100, BRIDGE]:
        if path.exists():
            ok(f"Output exists: {path}")
        else:
            fail(f"Output missing: {path}")
            return 1

    counts = summary.get("funnel_counts", {})

    print()
    print("Funnel counts")
    print("-" * 66)
    print(f"Stage 0 input: {counts.get('stage0_input_companies')}")
    print(f"Stage 1 passed/watchlist/rejected: {counts.get('stage1_passed')} / {counts.get('stage1_watchlist')} / {counts.get('stage1_rejected')}")
    print(f"Stage 2 passed/watchlist/rejected: {counts.get('stage2_passed')} / {counts.get('stage2_watchlist')} / {counts.get('stage2_rejected')}")
    print(f"Stage 3 passed/watchlist/rejected: {counts.get('stage3_passed')} / {counts.get('stage3_watchlist')} / {counts.get('stage3_rejected')}")

    print()
    print("Result")
    print("-" * 66)
    ok("Phase 5I global funnel runner is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
