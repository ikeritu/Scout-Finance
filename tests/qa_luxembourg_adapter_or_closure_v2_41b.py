from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_41b_luxembourg_adapter_or_closure"
SUMMARY = OUT_DIR / "luxembourg_adapter_or_closure_summary_v2_41b.json"
MANIFEST = OUT_DIR / "luxembourg_adapter_or_closure_manifest_v2_41b.json"
REPORT = OUT_DIR / "LUXEMBOURG_ADAPTER_OR_CLOSURE_v2_41b.md"


REQUIRED_FILES = [
    ROOT / "config" / "luxembourg_adapter_or_closure_contract_v2_41b.json",
    ROOT / "scripts" / "build_luxembourg_adapter_or_closure_v2_41b.py",
    ROOT / "tests" / "qa_luxembourg_adapter_or_closure_v2_41b.py",
    ROOT / "tests" / "qa_luxembourg_adapter_or_closure_full_suite_v2_41b.py",
    ROOT / "docs" / "LUXEMBOURG_ADAPTER_OR_CLOSURE_v2_41b.md",
    OUT_DIR / "luxembourg_adapter_or_closure_matrix_v2_41b.csv",
    OUT_DIR / "luxembourg_candidate_inventory_v2_41b.csv",
    OUT_DIR / "luxembourg_evidence_review_v2_41b.csv",
    OUT_DIR / "luxembourg_decision_register_v2_41b.csv",
    OUT_DIR / "luxembourg_next_phase_recommendation_v2_41b.csv",
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


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_required_files_exist() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    assert not missing, missing


def test_summary_values_and_decision() -> None:
    summary = read_json(SUMMARY)
    assert summary["phase"] == "v2.41B"
    assert summary["status"] == "LUXEMBOURG_ADAPTER_OR_CLOSURE_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["source_phase"] == "v2.41A"
    assert summary["source_status"] == "DATA_GAP_PRIORITIZATION_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["scope"] == "luxembourg_adapter_or_documented_closure"
    assert summary["luxembourg_candidate_count"] == 26
    assert summary["decision"] in {"DOCUMENTED_CLOSURE_READY", "ADAPTER_READY_READ_ONLY"}
    assert summary["decision"] == "DOCUMENTED_CLOSURE_READY"
    assert summary["adapter_built"] is False
    assert summary["closure_documented"] is True
    assert summary["primary_reason"]
    assert summary["next_phase"] == "v2.41C-uk-cboe-manual-review-decision"
    assert summary["qa_fail_count"] == 0
    assert summary["blocker_count"] == 0
    for flag in FALSE_FLAGS:
        assert summary[flag] is False, flag


def test_luxembourg_inventory_is_unscored_no_adapter() -> None:
    rows = read_csv(OUT_DIR / "luxembourg_candidate_inventory_v2_41b.csv")
    assert len(rows) == 26
    assert {row["country"] for row in rows} == {"LU"}
    assert {row["eligibility_status"] for row in rows} == {"NOT_YET_SCORED_NO_ADAPTER"}
    assert all(row["raw_factor_count"] == "0" for row in rows)
    assert all(row["normalized_factor_count"] == "0" for row in rows)


def test_report_guardrails() -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert "no network" in report
    assert "no data download" in report
    assert "no new scoring" in report
    assert "no ranking change" in report
    assert "no financial recommendations" in report
    assert "no broker" in report


def test_manifest_hashes_outputs_and_doc() -> None:
    manifest = read_json(MANIFEST)
    paths = {entry["path"] for entry in manifest["files"]}
    assert "docs/LUXEMBOURG_ADAPTER_OR_CLOSURE_v2_41b.md" in paths
    assert "outputs/full_universe_source_acquisition/v2_41b_luxembourg_adapter_or_closure/luxembourg_adapter_or_closure_summary_v2_41b.json" in paths
    assert all(len(entry["sha256"]) == 64 for entry in manifest["files"])


if __name__ == "__main__":
    test_required_files_exist()
    test_summary_values_and_decision()
    test_luxembourg_inventory_is_unscored_no_adapter()
    test_report_guardrails()
    test_manifest_hashes_outputs_and_doc()
    print("v2.41B QA PASS")
