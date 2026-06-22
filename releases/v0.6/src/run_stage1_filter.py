"""
Run Phase 5C Stage 1 filter.

Run from project root:

    ./.venv/Scripts/python.exe -m src.run_stage1_filter
"""

from __future__ import annotations

from src.filter_stage1 import print_stage1_summary, run_stage1_filter


def main() -> int:
    summary = run_stage1_filter()
    print_stage1_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
