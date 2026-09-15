from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41c_uk_cboe_manual_reviews_decision"
SUMMARY = OUT_DIR / "uk_cboe_manual_reviews_decision_summary_v2_41c.json"
MANIFEST = OUT_DIR / "uk_cboe_manual_reviews_decision_manifest_v2_41c.json"
REPORT = OUT_DIR / "UK_CBOE_MANUAL_REVIEWS_DECISION_v2_41c.md"
RANKING_JSON = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_38bv_global_research_ranking" / "global_research_ranking_results_v2_38bv.json"


REQUIRED_FILES = [
    ROOT / "config" / "uk_cboe_manual_reviews_decision_contract_v2_41c.json",
    ROOT / "scripts" / "build_uk_cboe_manual_reviews_decision_v2_41c.py",
    ROOT / "tests" / "qa_uk_cboe_manual_reviews_decision_v2_41c.py",
    ROOT / "tests" / "qa_uk_cboe_manual_reviews_decision_full_suite_v2_41c.py",
    ROOT / "docs" / "UK_CBOE_MANUAL_REVIEWS_DECISION_v2_41c.md",
    OUT_DIR / "uk_cboe_manual_reviews_decision_matrix_v2_41c.csv",
    OUT_DIR / "uk_scope_inventory_v2_41c.csv",
    OUT_DIR / "cboe_europe_decision_register_v2_41c.csv",
    OUT_DIR / "manual_reviews_inventory_v2_41c.csv",
    OUT_DIR / "financial_institutions_review_v2_41c.csv",
    OUT_DIR / "extreme_margin_review_v2_41c.csv",
    OUT_DIR / "uk_cboe_manual_reviews_next_phase_v2_41c.csv",
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


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_required_files_exist() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    assert not missing, missing


def test_summary_values_and_decisions() -> None:
    summary = read_json(SUMMARY)
    assert summary["phase"] == "v2.41C"
    assert summary["status"] == "UK_CBOE_MANUAL_REVIEWS_DECISION_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["source_phase"] == "v2.41B"
    assert summary["source_status"] == "LUXEMBOURG_ADAPTER_OR_CLOSURE_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["scope"] == "uk_cboe_manual_reviews_decision_only"
    assert summary["uk_decision"] == "REQUIRES_USER_DECISION_OR_DOCUMENTED_LIMITATION"
    assert summary["cboe_europe_decision"] == "BLOCKED_STRUCTURAL_KEEP_DOCUMENTED"
    assert summary["manual_reviews_decision"] == "DEFER_POST_RELEASE_WITH_EXPLICIT_SEPARATION"
    assert summary["financial_institutions_decision"] == "REQUIRES_SEPARATE_FACTOR_CONTRACT"
    assert summary["extreme_margin_decision"] == "KEEP_REVIEW_REQUIRED"
    assert summary["next_phase"] == "v2.41D-final-coverage-limitations"
    assert summary["qa_fail_count"] == 0
    assert summary["blocker_count"] == 0
    for flag in FALSE_FLAGS:
        assert summary[flag] is False, flag


def test_ranking_counts_match_v2_38bv() -> None:
    summary = read_json(SUMMARY)
    rows = read_json(RANKING_JSON)
    counts = Counter(row.get("eligibility_status", "") for row in rows)
    assert summary["ranking_total"] == len(rows)
    assert summary["ranking_main_count"] == counts["ELIGIBLE_PARTIAL"]
    assert summary["partial_comparability_count"] == counts["PARTIAL_COMPARABILITY"]
    assert summary["review_required_count"] == counts["REVIEW_REQUIRED"]
    assert summary["blocked_count"] == counts["BLOCKED"]
    assert summary["no_adapter_count"] == counts["NOT_YET_SCORED_NO_ADAPTER"]


def test_manual_reviews_stay_separated() -> None:
    rows = read_csv(OUT_DIR / "manual_reviews_inventory_v2_41c.csv")
    assert rows
    assert {row["eligibility_status"] for row in rows} == {"REVIEW_REQUIRED"}


def test_cboe_and_uk_decision_outputs() -> None:
    cboe = read_csv(OUT_DIR / "cboe_europe_decision_register_v2_41c.csv")
    uk = read_csv(OUT_DIR / "uk_scope_inventory_v2_41c.csv")
    assert cboe[0]["decision"] == "BLOCKED_STRUCTURAL_KEEP_DOCUMENTED"
    assert any(row["decision"] == "REQUIRES_USER_DECISION_OR_DOCUMENTED_LIMITATION" for row in uk)


def test_report_guardrails() -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert "no network calls" in report
    assert "no data download" in report
    assert "no new scoring" in report
    assert "no ranking change" in report
    assert "no financial recommendations" in report
    assert "no broker" in report


def test_manifest_hashes_outputs_and_doc() -> None:
    manifest = read_json(MANIFEST)
    paths = {entry["path"] for entry in manifest["files"]}
    assert "docs/UK_CBOE_MANUAL_REVIEWS_DECISION_v2_41c.md" in paths
    assert "outputs/full_universe_source_acquisition/v2_41c_uk_cboe_manual_reviews_decision/uk_cboe_manual_reviews_decision_summary_v2_41c.json" in paths
    assert all(len(entry["sha256"]) == 64 for entry in manifest["files"])


if __name__ == "__main__":
    test_required_files_exist()
    test_summary_values_and_decisions()
    test_ranking_counts_match_v2_38bv()
    test_manual_reviews_stay_separated()
    test_cboe_and_uk_decision_outputs()
    test_report_guardrails()
    test_manifest_hashes_outputs_and_doc()
    print("v2.41C QA PASS")
