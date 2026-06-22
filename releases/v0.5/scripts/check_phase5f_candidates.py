"""
Scout Finance — Phase 5F.1 candidates integration checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase5f_candidates.py

This script does not call OpenAI and does not modify app.py.
It also works without manually setting PYTHONPATH.
"""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.scouting_candidates import (  # noqa: E402
    SCOUTING_CANDIDATE_FILES,
    build_scouting_candidates_summary,
    export_candidates_for_existing_ranking,
    load_scouting_candidates,
)


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 5F.1 candidates integration checker")
    print("=" * 66)

    for label, path in SCOUTING_CANDIDATE_FILES.items():
        if path.exists():
            ok(f"{label} exists: {path}")
        else:
            warn(f"{label} missing: {path}")

    top100 = load_scouting_candidates()

    if top100.empty:
        fail("Top 100 candidates is empty or missing. Run Phase 5E first.")
        return 1

    ok(f"Top 100 candidates loaded: {len(top100)} rows")

    required_columns = [
        "ticker",
        "name",
        "final_stage3_score",
        "stage3_category",
    ]

    missing_columns = [column for column in required_columns if column not in top100.columns]

    if missing_columns:
        fail("Top 100 candidates missing required columns:")
        for column in missing_columns:
            print(f"   - {column}")
        return 1

    ok("Required candidate columns present")

    summary = build_scouting_candidates_summary()

    print()
    print("Summary")
    print("-" * 66)
    print(f"Available: {summary.get('available')}")
    print(f"Top company: {summary.get('top_company')}")
    print(f"Category distribution: {summary.get('category_distribution')}")

    bridge_path = export_candidates_for_existing_ranking()

    if bridge_path.exists():
        ok(f"Bridge CSV exported: {bridge_path}")
    else:
        fail("Bridge CSV was not created.")
        return 1

    print()
    print("Result")
    print("-" * 66)
    ok("Phase 5F.1 candidate bridge is ready")
    print("No OpenAI call. app.py not modified.")
    print("PYTHONPATH was not required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
