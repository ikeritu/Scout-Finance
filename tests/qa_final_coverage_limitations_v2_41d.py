"""QA for v2.41D final coverage limitations."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41d_final_coverage_limitations"
SOURCE_RANKING = (
    ROOT
    / "outputs"
    / "full_universe_source_acquisition"
    / "v2_38bv_global_research_ranking"
    / "global_research_ranking_results_v2_38bv.json"
)

SUMMARY = OUT_DIR / "final_coverage_limitations_summary_v2_41d.json"
MANIFEST = OUT_DIR / "final_coverage_limitations_manifest_v2_41d.json"
LIMITATIONS = OUT_DIR / "final_limitations_register_v2_41d.csv"
RECONCILIATION = OUT_DIR / "final_population_reconciliation_v2_41d.csv"
REPORT = OUT_DIR / "FINAL_COVERAGE_LIMITATIONS_v2_41d.md"

REQUIRED_FILES = [
    ROOT / "config" / "final_coverage_limitations_contract_v2_41d.json",
    ROOT / "scripts" / "build_final_coverage_limitations_v2_41d.py",
    ROOT / "tests" / "qa_final_coverage_limitations_v2_41d.py",
    ROOT / "tests" / "qa_final_coverage_limitations_full_suite_v2_41d.py",
    ROOT / "docs" / "FINAL_COVERAGE_LIMITATIONS_v2_41d.md",
    OUT_DIR / "final_coverage_by_ranking_status_v2_41d.csv",
    OUT_DIR / "final_coverage_by_country_v2_41d.csv",
    OUT_DIR / "final_coverage_by_decision_area_v2_41d.csv",
    LIMITATIONS,
    RECONCILIATION,
    SUMMARY,
    MANIFEST,
    REPORT,
    OUT_DIR / "README.md",
]

FALSE_FLAGS = [
    "network_used",
    "new_data_downloaded",
    "external_provider_enabled",
    "credentials_required",
    "datasets_mutated",
    "fundamentals_downloaded",
    "prices_downloaded",
    "scoring_recomputed",
    "ranking_changed",
    "weights_changed",
    "methodology_changed",
    "ui_changed",
    "deployment_performed",
    "public_url_created",
    "financial_advice_created",
    "recommendations_created",
    "broker_actions_allowed",
]

REQUIRED_LIMITATIONS = {
    "Luxembourg",
    "UK",
    "Cboe Europe",
    "Europe prices",
    "Manual reviews",
    "Financial institutions",
    "Extreme margin",
    "Coverage below threshold",
    "External publication risk",
    "Security / sensitive files",
    "Product/legal wording",
}

EXPECTED_COUNTS = {
    "ranking_total": 1111,
    "ranking_main_count": 318,
    "partial_comparability_count": 373,
    "review_required_count": 124,
    "blocked_count": 270,
    "no_adapter_count": 26,
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_required_files_exist() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists()]
    require(not missing, f"Missing required v2.41D files: {missing}")


def test_summary_contract() -> None:
    summary = read_json(SUMMARY)
    require(summary["phase"] == "v2.41D", "Unexpected phase")
    require(summary["status"] == "FINAL_COVERAGE_LIMITATIONS_READY", "Unexpected status")
    require(summary["qa_status"] == "PASS", "QA status must be PASS")
    require(summary["source_phase"] == "v2.41C", "Unexpected source phase")
    require(
        summary["source_status"] == "UK_CBOE_MANUAL_REVIEWS_DECISION_READY",
        "Unexpected source status",
    )
    require(summary["stable_tag"] == "v2.38CJ-local-stable", "Unexpected stable tag")
    require(summary["scope"] == "final_coverage_limitations_only", "Unexpected scope")
    require(summary["next_phase"] == "v2.42A-final-ux-hardening", "Unexpected next phase")
    require(summary["population_reconciliation_delta"] == 0, "Population delta must be zero")
    require(summary["release_blocking_limitation_count"] == 0, "No limitation may block release")
    require(summary["qa_fail_count"] == 0, "QA fail count must be zero")
    require(summary["blocker_count"] == 0, "Blocker count must be zero")
    for key, expected in EXPECTED_COUNTS.items():
        require(summary[key] == expected, f"{key} expected {expected}, got {summary[key]}")
    for flag in FALSE_FLAGS:
        require(summary[flag] is False, f"{flag} must remain false")


def test_ranking_counts_match_v2_38bv() -> None:
    summary = read_json(SUMMARY)
    source_payload = read_json(SOURCE_RANKING)
    rows = source_payload["rows"] if isinstance(source_payload, dict) else source_payload
    counts = Counter(row["eligibility_status"] for row in rows)
    require(len(rows) == summary["ranking_total"], "ranking_total does not match source rows")
    require(counts["ELIGIBLE_PARTIAL"] == summary["ranking_main_count"], "main count mismatch")
    require(
        counts["PARTIAL_COMPARABILITY"] == summary["partial_comparability_count"],
        "partial count mismatch",
    )
    require(counts["REVIEW_REQUIRED"] == summary["review_required_count"], "review count mismatch")
    require(counts["BLOCKED"] == summary["blocked_count"], "blocked count mismatch")
    require(
        counts["NOT_YET_SCORED_NO_ADAPTER"] == summary["no_adapter_count"],
        "no-adapter count mismatch",
    )


def test_limitations_register() -> None:
    rows = read_csv(LIMITATIONS)
    summary = read_json(SUMMARY)
    areas = {row["decision_area"] for row in rows}
    require(REQUIRED_LIMITATIONS.issubset(areas), "Required limitations are missing")
    require(len(rows) == summary["final_limitation_count"], "Limitation count mismatch")
    require(all(row["release_blocking"] == "False" for row in rows), "Release blocker found")


def test_population_reconciliation_is_closed() -> None:
    rows = read_csv(RECONCILIATION)
    require(rows, "Population reconciliation is empty")
    by_metric = {row["metric"]: int(row["count"]) for row in rows}
    require(
        by_metric["total_ranking_rows"]
        == by_metric["main_plus_partial_plus_review_plus_blocked_plus_no_adapter"],
        "Population components do not reconcile to the ranking total",
    )
    require(by_metric["population_reconciliation_delta"] == 0, "Population delta is not zero")


def test_report_declares_guardrails() -> None:
    report = REPORT.read_text(encoding="utf-8").lower()
    required_phrases = [
        "no network calls",
        "no data download",
        "no new scoring",
        "no ranking change",
        "no financial recommendations",
        "no broker actions",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in report]
    require(not missing, f"Report is missing guardrail wording: {missing}")


def test_manifest_hashes_outputs_and_docs() -> None:
    manifest = read_json(MANIFEST)
    artifacts = manifest["files"]
    paths = {artifact["path"] for artifact in artifacts}
    require("docs/FINAL_COVERAGE_LIMITATIONS_v2_41d.md" in paths, "Docs report missing in manifest")
    require(
        "outputs/full_universe_source_acquisition/v2_41d_final_coverage_limitations/final_coverage_limitations_summary_v2_41d.json"
        in paths,
        "Summary missing in manifest",
    )
    require(all(artifact["sha256"] for artifact in artifacts), "Manifest contains empty hashes")


def main() -> None:
    test_required_files_exist()
    test_summary_contract()
    test_ranking_counts_match_v2_38bv()
    test_limitations_register()
    test_population_reconciliation_is_closed()
    test_report_declares_guardrails()
    test_manifest_hashes_outputs_and_docs()
    print("v2.41D final coverage limitations QA passed")


if __name__ == "__main__":
    main()
