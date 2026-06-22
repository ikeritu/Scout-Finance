from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "scouting"
SRC_DIR = ROOT / "src"
RELEASES_DIR = ROOT / "releases"

SUMMARY_PATH = OUTPUT_DIR / "phase8d_candidate_source_binding_summary.json"
REPORT_PATH = OUTPUT_DIR / "phase8d_candidate_source_binding_report.md"
MEMOS_JSON_PATH = OUTPUT_DIR / "phase8d_candidate_source_bound_memos.json"
MEMOS_CSV_PATH = OUTPUT_DIR / "phase8d_candidate_source_bound_memos.csv"
CANDIDATES_CSV_PATH = OUTPUT_DIR / "phase8d_bound_top_candidates.csv"
DISCOVERY_JSON_PATH = OUTPUT_DIR / "phase8d_candidate_source_discovery.json"

REQUIRED_FILES = [
    SUMMARY_PATH,
    REPORT_PATH,
    MEMOS_JSON_PATH,
    MEMOS_CSV_PATH,
    CANDIDATES_CSV_PATH,
    DISCOVERY_JSON_PATH,
    SRC_DIR / "phase8d_candidate_source_binding.py",
    SRC_DIR / "research_memo.py",
    SRC_DIR / "fundamentals.py",
    SRC_DIR / "valuation.py",
    SRC_DIR / "risk_analysis.py",
    SRC_DIR / "moat_analysis.py",
    SRC_DIR / "growth_analysis.py",
    SRC_DIR / "institutional_view.py",
    SRC_DIR / "earnings_analysis.py",
]


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")
    raise SystemExit(1)


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    print("Scout Finance — Phase 8D Candidate Source Binding checker")
    print("=" * 92)
    for path in REQUIRED_FILES:
        if path.exists():
            ok(f"File exists: {path}")
        else:
            fail(f"Missing file: {path}")

    summary = read_json(SUMMARY_PATH)
    if summary.get("phase") == "8D":
        ok("Summary phase is 8D")
    else:
        fail(f"Unexpected phase: {summary.get('phase')}")
    if summary.get("status") == "OK":
        ok("Summary status OK")
    else:
        fail(f"Unexpected status: {summary.get('status')}")
    if summary.get("default_top_n") == 3:
        ok("Default TOP N OK: 3")
    else:
        fail(f"Unexpected default_top_n: {summary.get('default_top_n')}")

    controls = summary.get("controls") or {}
    for key in ["openai_called", "api_called", "yfinance_called", "pipeline_recalculated", "app_modified", "filters_modified", "release_modified"]:
        if controls.get(key) is False:
            ok(f"Control OK: {key}=False")
        else:
            fail(f"Control failed: {key}={controls.get(key)}")

    memos = read_json(MEMOS_JSON_PATH)
    if isinstance(memos, list):
        ok("Memos JSON is a list")
    else:
        fail("Memos JSON is not a list")
    if len(memos) <= 3:
        ok(f"Memos count <= 3: {len(memos)}")
    else:
        fail(f"Too many memos: {len(memos)}")

    discovered_sources = summary.get("discovered_sources", 0)
    if discovered_sources >= 0:
        ok(f"Discovery count present: {discovered_sources}")
    else:
        fail("Invalid discovery count")

    if summary.get("candidate_source"):
        ok("Candidate source bound")
        if len(memos) >= 1:
            ok(f"At least one memo created from bound source: {len(memos)}")
        else:
            fail("Candidate source exists but no memos were created")
        for memo in memos:
            for field in ["ticker", "company_name", "ranking_position", "quant_score", "memo_status", "sources", "estimated_cost", "model_used"]:
                if field in memo:
                    ok(f"Memo field OK: {memo.get('ticker')}::{field}")
                else:
                    fail(f"Missing memo field: {field}")
            if memo.get("estimated_cost") == 0.0:
                ok(f"Memo cost OK: {memo.get('ticker')}")
            else:
                fail(f"Memo estimated_cost not zero: {memo.get('estimated_cost')}")
            if memo.get("model_used") is None:
                ok(f"Memo model_used OK: {memo.get('ticker')}")
            else:
                fail(f"Memo model_used should be null: {memo.get('model_used')}")
    else:
        ok("No candidate source bound; no local candidate/ranking file was discoverable")

    with CANDIDATES_CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) <= 3:
        ok(f"Bound candidates CSV count <= 3: {len(rows)}")
    else:
        fail(f"Too many bound candidates: {len(rows)}")

    report = REPORT_PATH.read_text(encoding="utf-8")
    for needle in ["Phase 8D", "Candidate source", "OpenAI called", "data_insufficient", "8E"]:
        if needle in report:
            ok(f"Report contains: {needle}")
        else:
            fail(f"Report missing: {needle}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 8D Candidate Source Binding is valid")


if __name__ == "__main__":
    main()
