#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_us_explained_shortlist_v2_38l.py"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run(scores: Path, report: Path, matrix: Path, out: Path, limit: int) -> dict:
    result = subprocess.run([
        sys.executable, str(SCRIPT), "--scores-path", str(scores),
        "--score-report-path", str(report), "--matrix-path", str(matrix),
        "--output-dir", str(out), "--limit", str(limit)
    ], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def main() -> int:
    fields = [
        "research_rank", "asset_id", "ticker", "company_name", "exchange", "cik",
        "candidate_matrix_status", "evidence_level", "experimental_score", "score_bucket",
        "top_positive_drivers", "top_risk_drivers", "recommendation_generated",
    ]
    rows = [
        {"research_rank": "2", "asset_id": "U00002", "ticker": "BBB", "company_name": "Beta Builders Inc.", "exchange": "NYSE", "cik": "0000000002", "candidate_matrix_status": "CANDIDATE_MATRIX_READY", "evidence_level": "high", "experimental_score": "70.1", "score_bucket": "INVESTIGATE_MEDIUM", "top_positive_drivers": "positive price trend", "top_risk_drivers": "risk detail limited", "recommendation_generated": "false"},
        {"research_rank": "1", "asset_id": "U00001", "ticker": "AAA", "company_name": "Alpha Analytics Inc.", "exchange": "NASDAQ", "cik": "0000000001", "candidate_matrix_status": "CANDIDATE_MATRIX_READY", "evidence_level": "high", "experimental_score": "82.5", "score_bucket": "INVESTIGATE_HIGH", "top_positive_drivers": "positive revenue growth; positive price trend", "top_risk_drivers": "no dominant risk flag", "recommendation_generated": "false"},
        {"research_rank": "", "asset_id": "U00003", "ticker": "CCC", "company_name": "Core Cloud Inc.", "exchange": "NASDAQ", "cik": "0000000003", "candidate_matrix_status": "CANDIDATE_MATRIX_PARTIAL_PRICE", "evidence_level": "medium", "experimental_score": "", "score_bucket": "REVIEW_REQUIRED", "top_positive_drivers": "", "top_risk_drivers": "", "recommendation_generated": "false"},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        scores = base / "scores.csv"
        matrix = base / "matrix.csv"
        report = base / "report.json"
        out1 = base / "out1"
        out2 = base / "out2"
        write_csv(scores, fields, rows)
        write_csv(matrix, ["asset_id", "ticker"], [{"asset_id": r["asset_id"], "ticker": r["ticker"]} for r in rows])
        report.write_text(json.dumps({"phase": "v2.38K-us-experimental-scoring"}) + "\n", encoding="utf-8")
        payload = run(scores, report, matrix, out1, 2)
        assert payload == run(scores, report, matrix, out2, 2)
        shortlist = read_rows(out1 / "us_explained_shortlist_v2_38l.csv")
        notes = read_rows(out1 / "us_explained_shortlist_research_notes_v2_38l.csv")
        assert [r["asset_id"] for r in shortlist] == ["U00001", "U00002"]
        assert [r["shortlist_rank"] for r in shortlist] == ["1", "2"]
        assert shortlist[0]["shortlist_bucket"] == "SHORTLIST_HIGH_PRIORITY"
        assert shortlist[1]["shortlist_bucket"] == "SHORTLIST_MEDIUM_PRIORITY"
        assert all(r["recommendation_generated"] == "false" for r in shortlist)
        assert all(r["research_explanation"] for r in shortlist)
        assert len(notes) >= 8
        assert payload["shortlist_size"] == 2
    print("PASS: v2.38L/builder/offline/deterministic/limit-ready-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
