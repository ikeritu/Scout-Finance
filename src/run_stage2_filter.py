"""
Run Phase 5D Stage 2 financial sanity check.

Run from project root:

    ./.venv/Scripts/python.exe -m src.run_stage2_filter
"""

from __future__ import annotations

from src.filter_stage2 import print_stage2_summary, run_stage2_filter


def main() -> int:
    summary = run_stage2_filter()
    print_stage2_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
