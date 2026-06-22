"""
Run Phase 5E Stage 3 opportunity scoring.

Run from project root:

    ./.venv/Scripts/python.exe -m src.run_stage3_scoring
"""

from __future__ import annotations

from src.filter_stage3 import print_stage3_summary, run_stage3_scoring


def main() -> int:
    summary = run_stage3_scoring()
    print_stage3_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
