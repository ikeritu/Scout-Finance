"""QA for v2.43A final consolidated audit."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_43a_final_consolidated_audit"
SUMMARY = OUT_DIR / "final_consolidated_audit_summary_v2_43a.json"
MANIFEST = OUT_DIR / "final_consolidated_audit_manifest_v2_43a.json"
REPORT = OUT_DIR / "FINAL_CONSOLIDATED_AUDIT_v2_43a.md"

REQUIRED_FILES = [
    ROOT / "config" / "final_consolidated_audit_contract_v2_43a.json",
    ROOT / "scripts" / "build_final_consolidated_audit_v2_43a.py",
    ROOT / "tests" / "qa_final_consolidated_audit_v2_43a.py",
    ROOT / "tests" / "qa_final_consolidated_audit_full_suite_v2_43a.py",
    ROOT / "docs" / "FINAL_CONSOLIDATED_AUDIT_v2_43a.md",
    OUT_DIR / "final_consolidated_audit_matrix_v2_43a.csv",
    OUT_DIR / "final_consolidated_required_files_v2_43a.csv",
    OUT_DIR / "final_consolidated_guardrails_v2_43a.csv",
    OUT_DIR / "final_consolidated_security_checks_v2_43a.csv",
    OUT_DIR / "final_consolidated_documentation_checks_v2_43a.csv",
    OUT_DIR / "final_consolidated_ranking_integrity_v2_43a.csv",
    OUT_DIR / "final_consolidated_release_readiness_v2_43a.csv",
    SUMMARY,
    MANIFEST,
    REPORT,
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
    require(not missing, f"Missing required v2.43A files: {missing}")


def test_summary_contract() -> None:
    summary = read_json(SUMMARY)
    require(summary["phase"] == "v2.43A", "Unexpected phase")
    require(summary["status"] == "FINAL_CONSOLIDATED_AUDIT_READY", "Unexpected status")
    require(summary["qa_status"] == "PASS", "QA status must be PASS")
    require(summary["source_phase"] == "v2.42B", "Unexpected source phase")
    require(summary["source_status"] == "FINAL_IN_APP_GUIDE_READY", "Unexpected source status")
    require(summary["scope"] == "final_consolidated_audit_only", "Unexpected scope")
    require(summary["stable_tag"] == "v2.38CJ-local-stable", "Unexpected stable tag")
    require(summary["next_phase"] == "v2.44A-final-stable-release", "Unexpected next phase")
    require(summary["release_readiness"] == "READY_WITH_DOCUMENTED_LIMITATIONS", "Unexpected release readiness")
    require(summary["qa_fail_count"] == 0, "QA fail count must be zero")
    require(summary["blocker_count"] == 0, "Blocker count must be zero")
    require(summary["required_file_missing_count"] == 0, "Required files missing")
    require(summary["release_blocking_issue_count"] == 0, "Release blockers found")
    require(summary["security_blocking_finding_count"] == 0, "Security blockers found")
    for key, expected in EXPECTED_COUNTS.items():
        require(summary[key] == expected, f"{key} expected {expected}, got {summary[key]}")
    for flag in FALSE_FLAGS:
        require(summary[flag] is False, f"{flag} must remain false")


def test_matrices() -> None:
    guardrails = {row["guardrail"]: row["present"] for row in rows(OUT_DIR / "final_consolidated_guardrails_v2_43a.csv")}
    for guardrail in ["no-advice", "no-broker", "no-deployment", "no-public-url", "no-ranking-change"]:
        require(guardrails.get(guardrail) == "True", f"Guardrail missing: {guardrail}")
    require(all(row["blocking"] == "False" for row in rows(OUT_DIR / "final_consolidated_security_checks_v2_43a.csv")), "Blocking security finding found")
    docs = {row["path"] for row in rows(OUT_DIR / "final_consolidated_documentation_checks_v2_43a.csv")}
    for path in ["README.md", "VERSION.md", "CHANGELOG.md", "ROADMAP_v2_38_CURRENT.md", "docs/FINAL_COVERAGE_LIMITATIONS_v2_41d.md", "docs/FINAL_UX_HARDENING_v2_42a.md", "docs/FINAL_IN_APP_GUIDE_v2_42b.md"]:
        require(path in docs, f"Documentation check missing {path}")


def test_report_language() -> None:
    report = REPORT.read_text(encoding="utf-8").lower()
    for phrase in [
        "no network",
        "no data download",
        "no scoring recomputation",
        "no ranking change",
        "no methodology/weight change",
        "no financial advice",
        "no recommendations",
        "no broker actions",
        "ready_with_documented_limitations",
    ]:
        require(phrase in report, f"Report missing phrase {phrase}")


def test_manifest_hashes_files() -> None:
    manifest = read_json(MANIFEST)
    require(manifest["phase"] == "v2.43A", "Manifest phase mismatch")
    require(all(entry["sha256"] for entry in manifest["files"]), "Manifest contains empty hashes")


def main() -> None:
    test_required_files_exist()
    test_summary_contract()
    test_matrices()
    test_report_language()
    test_manifest_hashes_files()
    print("v2.43A final consolidated audit QA passed")


if __name__ == "__main__":
    main()
