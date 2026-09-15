from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41a_data_gap_prioritization"
SUMMARY = OUT_DIR / "data_gap_prioritization_summary_v2_41a.json"
MANIFEST = OUT_DIR / "data_gap_prioritization_manifest_v2_41a.json"
REPORT = OUT_DIR / "DATA_GAP_PRIORITIZATION_v2_41a.md"


REQUIRED_FILES = [
    ROOT / "config" / "data_gap_prioritization_contract_v2_41a.json",
    ROOT / "scripts" / "build_data_gap_prioritization_v2_41a.py",
    ROOT / "tests" / "qa_data_gap_prioritization_v2_41a.py",
    ROOT / "tests" / "qa_data_gap_prioritization_full_suite_v2_41a.py",
    ROOT / "docs" / "DATA_GAP_PRIORITIZATION_v2_41a.md",
    OUT_DIR / "data_gap_prioritization_matrix_v2_41a.csv",
    OUT_DIR / "data_gap_decision_register_v2_41a.csv",
    OUT_DIR / "data_gap_source_inventory_v2_41a.csv",
    OUT_DIR / "data_gap_impact_matrix_v2_41a.csv",
    OUT_DIR / "data_gap_next_phase_recommendation_v2_41a.csv",
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


REQUIRED_GAPS = {
    "GAP-LUX-ADAPTER",
    "GAP-UK-OFFICIAL-ACCESS",
    "GAP-CBOE-EUROPE",
    "GAP-EUROPE-PRICES",
    "GAP-MANUAL-REVIEWS",
    "GAP-FINANCIAL-INSTITUTIONS",
    "GAP-COVERAGE-BELOW-THRESHOLD",
    "GAP-EXTERNAL-PUBLICATION-RISK",
    "GAP-SECURITY-WARNINGS",
    "GAP-PRODUCT-LEGAL-WORDING",
}


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_required_files_exist() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    assert not missing, missing


def test_summary_values() -> None:
    summary = read_json(SUMMARY)
    assert summary["phase"] == "v2.41A"
    assert summary["status"] == "DATA_GAP_PRIORITIZATION_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["source_phase"] == "v2.40D"
    assert summary["source_status"] == "CONTROLLED_EXTERNAL_PUBLICATION_QA_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["publication_scope_current"] == "controlled_external_publication_qa_ready_not_deployed"
    assert summary["data_gap_scope"] == "prioritization_only"
    assert summary["evaluated_gap_count"] >= len(REQUIRED_GAPS)
    assert summary["attack_next_count"] >= 1
    assert summary["documented_limitation_count"] >= 1
    assert summary["requires_user_decision_count"] >= 1
    assert summary["blocked_structural_count"] >= 1
    assert summary["defer_post_release_count"] >= 1
    assert summary["primary_next_phase"] == "v2.41B-luxembourg-adapter-or-closure"
    assert summary["primary_next_phase_reason"]
    assert summary["qa_fail_count"] == 0
    assert summary["blocker_count"] == 0
    for flag in FALSE_FLAGS:
        assert summary[flag] is False, flag


def test_required_gaps_and_attack_next() -> None:
    rows = read_csv(OUT_DIR / "data_gap_prioritization_matrix_v2_41a.csv")
    gap_ids = {row["gap_id"] for row in rows}
    assert REQUIRED_GAPS <= gap_ids
    attack_next = [row for row in rows if row["decision"] == "ATTACK_NEXT"]
    assert attack_next
    assert attack_next[0]["recommended_next_phase"] == "v2.41B-luxembourg-adapter-or-closure"


def test_report_guardrails() -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert "does not download data" in report
    assert "does not call network" in report
    assert "does not recompute scoring" in report
    assert "does not change ranking" in report
    assert "does not provide financial recommendations" in report


def test_manifest_hashes_outputs_and_doc() -> None:
    manifest = read_json(MANIFEST)
    paths = {entry["path"] for entry in manifest["files"]}
    assert "docs/DATA_GAP_PRIORITIZATION_v2_41a.md" in paths
    assert "outputs/full_universe_source_acquisition/v2_41a_data_gap_prioritization/data_gap_prioritization_summary_v2_41a.json" in paths
    assert all(len(entry["sha256"]) == 64 for entry in manifest["files"])


if __name__ == "__main__":
    test_required_files_exist()
    test_summary_values()
    test_required_gaps_and_attack_next()
    test_report_guardrails()
    test_manifest_hashes_outputs_and_doc()
    print("v2.41A QA PASS")
