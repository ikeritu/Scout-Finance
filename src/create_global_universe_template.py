"""
Create data/universe/global_universe.csv template.

Run from project root:

    ./.venv/Scripts/python.exe -m src.create_global_universe_template
"""

from __future__ import annotations

import csv

from src.funnel_paths import GLOBAL_UNIVERSE_PATH, ensure_funnel_directories
from src.global_universe import REQUIRED_COLUMNS, OPTIONAL_COLUMNS


def main() -> int:
    ensure_funnel_directories()

    columns = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

    if GLOBAL_UNIVERSE_PATH.exists():
        print(f"Template already exists: {GLOBAL_UNIVERSE_PATH}")
        return 0

    with GLOBAL_UNIVERSE_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(columns)

    print(f"Template created: {GLOBAL_UNIVERSE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
