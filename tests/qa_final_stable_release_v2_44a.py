"""QA for v2.44A final stable release closure."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_44a_final_stable_release"
SUMMARY = OUT_DIR / "final_stable_release_summary_v2_44a.json"
MANIFEST = OUT_DIR / "final_stable_release_manifest_v2_44a.json"
REPORT = OUT_DIR / "final_project_closure_report_v2_44a.md"

REQUIRED_FILES = [
    ROOT / "config" / "final_stable_release_contract_v2_44a.json",
    ROOT / "scripts" / "build_final_stable_release_v2_44a.py",
    ROOT / "tests" / "qa_final_stable_release_v2_44a.py",
    ROOT / "tests" / "qa_final_stable_release_full_suite_v2_44a.py",
    ROOT / "docs" / "FINAL_STABLE_RELEASE_v2_44a.md",
    SUMMARY,
    MANIFEST,
    REPORT,
    OUT_DIR / "final_release_checklist_v2_44a.csv",
    OUT_DIR / "final_release_traceability_v2_44a.csv",
    OUT_DIR / "final_maintenance_recommendations_v2_44a.csv",
    OUT_DIR / "final_publication_readiness_v2_44a.csv",
    OUT_DIR / "final_guardrails_v2_44a.csv",
    OUT_DIR / "README.md",
]

EXPECTED_COUNTS = {
    "ranking_total": 1111,
    "ranking_main_count": 318,
    "partial_comparability_count": 373,
    "review_required_count": 124,
    "blocked_count": 270,
    "no_adapter_count": 26,
}

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
    "deployment_performed",
    "public_url_created",
    "financial_advice_created",
    "recommendations_created",
    "broker_actions_allowed",
]

PROHIBITED_LANGUAGE = [
    "deberias comprar",
    "deberías comprar",
    "compra ahora",
    "vende ahora",
    "recomendacion de compra",
    "recomendación de compra",
    "garantiza rentabilidad",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_required_files_exist() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists()]
    require(not missing, f"Missing required v2.44A files: {missing}")


def test_summary_contract() -> None:
    summary = read_json(SUMMARY)
    require(summary["phase"] == "v2.44A", "Unexpected phase")
    require(summary["status"] == "FINAL_STABLE_RELEASE_READY", "Unexpected status")
    require(summary["qa_status"] == "PASS", "QA status must be PASS")
    require(summary["source_phase"] == "v2.43A", "Unexpected source phase")
    require(summary["source_status"] == "FINAL_CONSOLIDATED_AUDIT_READY", "Unexpected source status")
    require(summary["scope"] == "final_release_closure_only", "Unexpected scope")
    require(summary["stable_release_name"] == "Scout Finance v2.44A Final Stable", "Unexpected stable release name")
    require(summary["previous_stable_tag"] == "v2.38CJ-local-stable", "Unexpected previous tag")
    require(summary["recommended_final_tag"] == "v2.44A-final-stable", "Unexpected final tag")
    require(summary["release_readiness"] == "READY_WITH_DOCUMENTED_LIMITATIONS", "Unexpected readiness")
    require(summary["project_state"] == "CLOSED_FOR_STABLE_LOCAL_RELEASE", "Unexpected project state")
    require(summary["next_state"] == "maintenance_or_controlled_publication", "Unexpected next state")
    require(summary["required_file_missing_count"] == 0, "Required files missing")
    require(summary["release_blocking_issue_count"] == 0, "Release blockers found")
    require(summary["security_blocking_finding_count"] == 0, "Security blockers found")
    require(summary["qa_fail_count"] == 0, "QA fail count must be zero")
    require(summary["blocker_count"] == 0, "Blocker count must be zero")
    for key, expected in EXPECTED_COUNTS.items():
        require(summary[key] == expected, f"{key} expected {expected}, got {summary[key]}")
    for flag in FALSE_FLAGS:
        require(summary[flag] is False, f"{flag} must remain false")


def test_outputs() -> None:
    checklist = rows(OUT_DIR / "final_release_checklist_v2_44a.csv")
    require(all(row["status"] == "PASS" for row in checklist), "Release checklist must be PASS")
    require(all(row["blocking"] == "False" for row in checklist), "Release checklist contains blockers")
    guardrails = rows(OUT_DIR / "final_guardrails_v2_44a.csv")
    require(all(row["status"] == "True" for row in guardrails), "A final guardrail is not true")
    publication = {row["check"]: row for row in rows(OUT_DIR / "final_publication_readiness_v2_44a.csv")}
    require(publication["public_url_created"]["value"] == "False", "Public URL must not be created")
    require(publication["deployment_performed"]["value"] == "False", "Deployment must not be performed")


def test_report_language() -> None:
    report = REPORT.read_text(encoding="utf-8")
    lowered = report.lower()
    require("No constituye asesoramiento financiero" in report, "Missing no-advice disclaimer")
    require("no public url" in lowered or "public url" in lowered, "Missing public URL language")
    require("does not use network" in lowered, "Missing no-network language")
    require("does not" in lowered and "change ranking" in lowered, "Missing no-ranking-change language")
    for phrase in PROHIBITED_LANGUAGE:
        require(phrase not in lowered, f"Prohibited advice language found: {phrase}")


def test_manifest_hashes_files() -> None:
    manifest = read_json(MANIFEST)
    require(manifest["phase"] == "v2.44A", "Manifest phase mismatch")
    require(manifest["status"] == "FINAL_STABLE_RELEASE_READY", "Manifest status mismatch")
    require(all(entry["sha256"] for entry in manifest["files"]), "Manifest contains empty hashes")


def main() -> None:
    test_required_files_exist()
    test_summary_contract()
    test_outputs()
    test_report_language()
    test_manifest_hashes_files()
    print("v2.44A final stable release QA passed")


if __name__ == "__main__":
    main()
