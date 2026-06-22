
"""
Scout Finance — Phase 6D Stage 2 using enriched Stage 1 input.

Purpose:
- Run Stage 2 directly from data/stages/stage1_passed_enriched.csv
- Avoid overwriting data/stages/stage1_passed.csv
- Keep Stage 1 output clean and auditable

This module does not call external APIs.
It does not call OpenAI.
It does not modify app.py.

Run from project root:

    ./.venv/Scripts/python.exe -m src.run_stage2_filter_enriched
"""

from __future__ import annotations

from pathlib import Path

from src.filter_stage2 import print_stage2_summary, run_stage2_filter
from src.funnel_paths import STAGES_DIR


STAGE1_PASSED_ENRICHED_PATH = STAGES_DIR / "stage1_passed_enriched.csv"


def main() -> int:
    if not STAGE1_PASSED_ENRICHED_PATH.exists():
        raise FileNotFoundError(
            f"Enriched Stage 1 file not found: {STAGE1_PASSED_ENRICHED_PATH}. "
            "Run first: python -m src.prepare_fundamentals_csv"
        )

    summary = run_stage2_filter(input_path=STAGE1_PASSED_ENRICHED_PATH)
    print_stage2_summary(summary)

    print()
    print("Phase 6D note")
    print("-" * 64)
    print(f"Stage 2 input: {STAGE1_PASSED_ENRICHED_PATH}")
    print("stage1_passed.csv was not overwritten by this command.")
    print("No API call. No OpenAI call. app.py not modified.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
