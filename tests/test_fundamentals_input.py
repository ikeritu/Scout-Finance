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


def test_fundamentals_summary_exists_and_is_ok() -> None:
    summary = _load_json(project_path("outputs", "fundamentals", "fundamentals_input_summary.json"))

    assert summary, "Fundamentals summary is empty"

    status = str(summary.get("status", summary.get("estado", "OK"))).upper()
    assert status in {"OK", "VALID", "VALIDATED", "SUCCESS"}

    coverage_candidates = [
        summary.get("coverage"),
        summary.get("coverage_ratio"),
        summary.get("fundamentals_coverage"),
        summary.get("valid_coverage"),
    ]

    numeric_coverages = []
    for value in coverage_candidates:
        if value is None:
            continue
        try:
            numeric_coverages.append(float(value))
        except (TypeError, ValueError):
            pass

    if numeric_coverages:
        assert max(numeric_coverages) >= 1.0 or max(numeric_coverages) >= 100.0


def test_fundamentals_valid_rows_exist() -> None:
    rows = _load_csv(project_path("outputs", "fundamentals", "manual_fundamentals_valid_rows.csv"))

    assert rows, "No valid fundamentals rows found"

    first = rows[0]
    assert "ticker" in first

    tickers = {row.get("ticker", "").strip().upper() for row in rows}
    assert {"MSFT", "ASML", "AAPL"}.intersection(tickers)


def test_fundamentals_issues_file_exists() -> None:
    issues_path = project_path("outputs", "fundamentals", "manual_fundamentals_issues.csv")
    assert issues_path.exists(), f"Missing issues file: {issues_path}"
