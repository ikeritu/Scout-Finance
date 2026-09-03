#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_macro_geopolitical_context_v2_38m.py"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run(shortlist: Path, report: Path, matrix: Path, out: Path) -> dict:
    result = subprocess.run([
        sys.executable, str(SCRIPT), "--shortlist-path", str(shortlist),
        "--shortlist-report-path", str(report), "--matrix-path", str(matrix),
        "--output-dir", str(out),
    ], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def main() -> int:
    shortlist_fields = [
        "shortlist_rank", "research_rank", "asset_id", "ticker", "company_name",
        "exchange", "experimental_score", "shortlist_bucket", "positive_drivers",
        "risk_drivers", "evidence_summary", "research_explanation", "next_research_steps",
    ]
    matrix_fields = ["asset_id", "ticker", "fundamental_signal_summary", "price_signal_summary", "risk_signal_summary"]
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        shortlist = base / "shortlist.csv"
        matrix = base / "matrix.csv"
        report = base / "report.json"
        out1 = base / "out1"
        out2 = base / "out2"
        write_csv(shortlist, shortlist_fields, [
            {"shortlist_rank": "1", "research_rank": "1", "asset_id": "U00001", "ticker": "AAA", "company_name": "Alpha Semiconductor Inc.", "exchange": "NASDAQ", "experimental_score": "82.5", "shortlist_bucket": "SHORTLIST_HIGH_PRIORITY", "positive_drivers": "positive price trend", "risk_drivers": "risk detail limited", "evidence_summary": "high evidence", "research_explanation": "semiconductor data center supplier", "next_research_steps": "manual sector review"},
            {"shortlist_rank": "2", "research_rank": "2", "asset_id": "U00002", "ticker": "BBB", "company_name": "Beta Services Inc.", "exchange": "NYSE", "experimental_score": "70.1", "shortlist_bucket": "SHORTLIST_MEDIUM_PRIORITY", "positive_drivers": "limited", "risk_drivers": "limited", "evidence_summary": "high evidence", "research_explanation": "general business", "next_research_steps": "manual sector review"},
        ])
        write_csv(matrix, matrix_fields, [
            {"asset_id": "U00001", "ticker": "AAA", "fundamental_signal_summary": "manufacturing chip growth", "price_signal_summary": "trend", "risk_signal_summary": "limited"},
            {"asset_id": "U00002", "ticker": "BBB", "fundamental_signal_summary": "general", "price_signal_summary": "trend", "risk_signal_summary": "limited"},
        ])
        report.write_text(json.dumps({"phase": "v2.38L-us-explained-shortlist"}) + "\n", encoding="utf-8")
        payload = run(shortlist, report, matrix, out1)
        assert payload == run(shortlist, report, matrix, out2)
        taxonomy = read_rows(out1 / "macro_geopolitical_taxonomy_v2_38m.csv")
        context = read_rows(out1 / "us_shortlist_macro_context_v2_38m.csv")
        notes = read_rows(out1 / "us_shortlist_macro_notes_v2_38m.csv")
        assert len(taxonomy) >= 17
        assert len(context) == 2
        assert "AI_SEMICONDUCTORS" in context[0]["applicable_themes"]
        assert context[1]["macro_context_status"] == "MACRO_CONTEXT_PARTIAL"
        assert context[0]["research_rank"] == "1"
        assert context[0]["experimental_score"] == "82.5"
        for row in context:
            opportunity = float(row["macro_opportunity_score"])
            risk = float(row["macro_risk_score"])
            balance = float(row["macro_balance"])
            assert 0 <= opportunity <= 100
            assert 0 <= risk <= 100
            assert abs(balance - (opportunity - risk)) < 0.0001
            assert row["recommendation_generated"] == "false"
        assert len(notes) >= 8
        assert payload["shortlist_assets"] == 2
        assert payload["live_news_used"] is False
    print("PASS: v2.38M/builder/offline/deterministic/static-taxonomy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
