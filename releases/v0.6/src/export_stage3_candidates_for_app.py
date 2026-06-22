"""
Export Stage 3 candidates to a bridge CSV for future app integration.

Run from project root:

    ./.venv/Scripts/python.exe -m src.export_stage3_candidates_for_app
"""

from __future__ import annotations

from src.scouting_candidates import export_candidates_for_existing_ranking


def main() -> int:
    output_path = export_candidates_for_existing_ranking()
    print(f"Stage 3 candidates bridge exported: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
