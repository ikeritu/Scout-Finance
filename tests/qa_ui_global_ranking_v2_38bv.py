#!/usr/bin/env python3
"""Offline QA for src/ui_v2_37/global_ranking.py -- the read-only loader
behind the "🏆 Ranking global (experimental)" screen. No real ranking
file, no Streamlit runtime: load_global_ranking() is pointed at synthetic
fixtures under a temporary root."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_v2_37.global_ranking import RESULTS_REL, load_global_ranking  # noqa: E402


def write_results(root: Path, rows: list[dict]) -> None:
    path = root / RESULTS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows), encoding="utf-8")


def test_missing_results_reports_unavailable_never_crashes():
    with tempfile.TemporaryDirectory() as tmp:
        data = load_global_ranking(Path(tmp))
    assert data.available is False
    assert data.rows == ()
    assert "v2_38bv" in data.error


def test_existing_results_load_all_rows_and_a_real_mtime():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_results(root, [{"asset_id": "U1", "eligibility_status": "ELIGIBLE_PARTIAL", "rank": 1, "total_score": 82.5}])
        data = load_global_ranking(root)
    assert data.available is True
    assert len(data.rows) == 1
    assert data.generated_at
    assert data.rows[0]["asset_id"] == "U1"


def test_corrupted_results_file_reports_error_never_crashes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = root / RESULTS_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"not real json")
        data = load_global_ranking(root)
    assert data.available is False
    assert data.error


def test_path_traversal_is_rejected():
    """Same discipline as global_universe.py's own _rooted() -- must
    never resolve outside the project root, even though RESULTS_REL is a
    hardcoded constant, not user input."""
    import src.ui_v2_37.global_ranking as gr
    with tempfile.TemporaryDirectory() as tmp:
        try:
            gr._rooted(Path(tmp), "../../etc/passwd")
            raised = False
        except ValueError:
            raised = True
    assert raised


CASES = [
    test_missing_results_reports_unavailable_never_crashes,
    test_existing_results_load_all_rows_and_a_real_mtime,
    test_corrupted_results_file_reports_error_never_crashes,
    test_path_traversal_is_rejected,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: ui-global-ranking/read-only/fail-closed/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
