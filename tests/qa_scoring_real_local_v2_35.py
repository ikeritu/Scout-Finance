#!/usr/bin/env python3
"""Local-only gate over licensed phase-6 inputs; skips cleanly in CI."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/build_research_ranking_v2_35.py"
OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_35_phase6_scoring_local"
RESULTS = OUTPUT / "scoring_results_v2_35.json"
REPORT = OUTPUT / "scoring_aggregate_report_v2_35.json"
NORMALIZED = ROOT / "outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/fundamental_records_v2_34f.jsonl"


def run() -> bytes:
    completed = subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, check=True)
    return completed.stdout


def main() -> int:
    if not NORMALIZED.exists():
        print("SKIP: licensed local phase-6 inputs are not present")
        return 0
    first_stdout = run()
    first_results = RESULTS.read_bytes()
    first_report = REPORT.read_bytes()
    second_stdout = run()
    assert first_stdout == second_stdout
    assert first_results == RESULTS.read_bytes()
    assert first_report == REPORT.read_bytes()
    results = json.loads(first_results)
    report = json.loads(first_report)
    assert len(results) == 50
    assert report["ranked_assets"] == 41
    assert report["partial_comparability_assets"] == 7
    assert report["eligibility_status_counts"] == {"ELIGIBLE_PARTIAL": 41, "PARTIAL_COMPARABILITY": 7, "REVIEW_REQUIRED": 2}
    by_asset = {r["asset_id"]: r for r in results}
    assert by_asset["P020"]["eligibility_status"] == "REVIEW_REQUIRED"
    assert "absolute_margin_outside_300pct" in by_asset["P020"]["review_reasons"]
    assert by_asset["P178"]["eligibility_status"] == "REVIEW_REQUIRED"
    assert "financial_institution_requires_separate_factor_contract" in by_asset["P178"]["review_reasons"]
    ranks = [r["rank"] for r in results if "rank" in r]
    assert sorted(ranks) == list(range(1, 42))
    for row in results:
        if row["total_score"] is not None:
            assert 0 <= row["total_score"] <= 100
            assert abs(sum(row["contributions"].values()) - row["total_score"]) < 1e-6
        if row["eligibility_status"] != "ELIGIBLE_PARTIAL":
            assert "rank" not in row
    print(json.dumps({"status": "PASS", "assets": 50, "ranked": 41, "partial": 7, "review": 2, "deterministic_double_run": True}))
    print("PASS: v2.35 real-local/deterministic/traceable/states/P020/P178/no-phase7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
