from __future__ import annotations

import csv
import json
from pathlib import Path

from conftest import project_path


def _load_json(path: Path) -> dict:
    assert path.exists(), f"Missing JSON file: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    assert path.exists(), f"Missing CSV file: {path}"
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_combined_scoring_summary_ok() -> None:
    summary = _load_json(project_path("outputs", "scoring", "combined_score_v1_summary.json"))

    assert summary.get("phase") == "v1.6C"
    assert summary.get("status") == "OK"
    assert int(summary.get("rows_input", 0)) >= 1
    assert int(summary.get("rows_scored", 0)) >= 1
    assert int(summary.get("fundamentals_matched", 0)) >= 1

    # Safety controls: this phase must stay local/offline.
    assert summary.get("openai_called") is False
    assert summary.get("broker_called") is False
    assert summary.get("pipeline_recalculated") is False
    assert summary.get("yfinance_called") is False
    assert summary.get("fundamentals_api_called") is False


def test_active_ranking_is_combined_score_v1() -> None:
    rows = _load_csv(project_path("outputs", "scouting", "active_real_universe_top_candidates.csv"))

    assert rows, "Active ranking is empty"

    first = rows[0]
    assert "ticker" in first
    assert "score" in first
    assert "combined_score_v1" in first
    assert "stage3_status" in first

    assert first["stage3_status"] == "COMBINED_SCORE_V1"

    score = float(first["score"])
    combined = float(first["combined_score_v1"])

    assert abs(score - combined) < 0.0001


def test_combined_breakdown_has_components() -> None:
    rows = _load_csv(project_path("outputs", "scoring", "combined_score_v1_breakdown.csv"))

    assert rows, "Combined scoring breakdown is empty"

    first = rows[0]
    required_columns = {
        "ticker",
        "metadata_score_component",
        "market_data_score_component",
        "fundamentals_score_component",
        "combined_score_v1",
    }

    missing = required_columns.difference(first.keys())
    assert not missing, f"Missing columns: {sorted(missing)}"

    assert float(first["metadata_score_component"]) >= 0
    assert float(first["market_data_score_component"]) >= 0
    assert float(first["fundamentals_score_component"]) >= 0
    assert float(first["combined_score_v1"]) >= 0
