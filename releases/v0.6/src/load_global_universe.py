"""
Run Phase 5B global universe validation.

Run from project root:

    ./.venv/Scripts/python.exe -m src.load_global_universe
"""

from __future__ import annotations

from src.global_universe import (
    print_summary,
    validate_and_prepare_global_universe,
)


def main() -> int:
    summary = validate_and_prepare_global_universe()
    print_summary(summary)

    if summary.get("status") != "OK":
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
