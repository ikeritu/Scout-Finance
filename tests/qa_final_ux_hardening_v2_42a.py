"""QA for v2.42A final UX hardening."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_42a_final_ux_hardening"
SUMMARY = OUT_DIR / "final_ux_hardening_summary_v2_42a.json"
MANIFEST = OUT_DIR / "final_ux_hardening_manifest_v2_42a.json"
REPORT = OUT_DIR / "FINAL_UX_HARDENING_v2_42a.md"

REQUIRED_FILES = [
    ROOT / "config" / "final_ux_hardening_contract_v2_42a.json",
    ROOT / "scripts" / "build_final_ux_hardening_v2_42a.py",
    ROOT / "tests" / "qa_final_ux_hardening_v2_42a.py",
    ROOT / "tests" / "qa_final_ux_hardening_full_suite_v2_42a.py",
    ROOT / "docs" / "FINAL_UX_HARDENING_v2_42a.md",
    OUT_DIR / "final_ux_hardening_matrix_v2_42a.csv",
    OUT_DIR / "final_ux_empty_states_v2_42a.csv",
    OUT_DIR / "final_ux_error_messages_v2_42a.csv",
    OUT_DIR / "final_ux_export_contract_v2_42a.csv",
    OUT_DIR / "final_ux_guardrails_v2_42a.csv",
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
    "deployment_performed",
    "public_url_created",
    "financial_advice_created",
    "recommendations_created",
    "broker_actions_allowed",
]

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


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_required_files_exist() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists()]
    require(not missing, f"Missing required v2.42A files: {missing}")


def test_summary_contract() -> None:
    summary = read_json(SUMMARY)
    require(summary["phase"] == "v2.42A", "Unexpected phase")
    require(summary["status"] == "FINAL_UX_HARDENING_READY", "Unexpected status")
    require(summary["qa_status"] == "PASS", "QA status must be PASS")
    require(summary["source_phase"] == "v2.41D", "Unexpected source phase")
    require(summary["source_status"] == "FINAL_COVERAGE_LIMITATIONS_READY", "Unexpected source status")
    require(summary["scope"] == "final_ux_hardening_only", "Unexpected scope")
    require(summary["stable_tag"] == "v2.38CJ-local-stable", "Unexpected stable tag")
    require(summary["next_phase"] == "v2.42B-final-in-app-guide", "Unexpected next phase")
    require(summary["qa_fail_count"] == 0, "QA fail count must be zero")
    require(summary["blocker_count"] == 0, "Blocker count must be zero")
    for key, expected in EXPECTED_COUNTS.items():
        require(summary[key] == expected, f"{key} expected {expected}, got {summary[key]}")
    for flag in FALSE_FLAGS:
        require(summary[flag] is False, f"{flag} must remain false")


def test_ux_matrices_cover_required_items() -> None:
    empty_states = {row["state"] for row in rows(OUT_DIR / "final_ux_empty_states_v2_42a.csv")}
    for state in {
        "ranking_principal_empty",
        "comparabilidad_parcial_empty",
        "review_required_empty",
        "blocked_empty",
        "no_adapter_empty",
        "filter_no_results",
        "dataset_not_found",
        "dataset_corrupt",
    }:
        require(state in empty_states, f"Missing empty state {state}")
    guardrails = {row["guardrail"] for row in rows(OUT_DIR / "final_ux_guardrails_v2_42a.csv")}
    for guardrail in {
        "ranking experimental",
        "no financial advice",
        "no broker",
        "local/offline data",
        "limitations documented v2.41D",
    }:
        require(guardrail in guardrails, f"Missing guardrail {guardrail}")


def test_source_contains_ux_hardening_copy() -> None:
    app = (ROOT / "app_v2_37.py").read_text(encoding="utf-8")
    ranking = (ROOT / "src" / "ui_v2_37" / "global_ranking.py").read_text(encoding="utf-8")
    require("GLOBAL_RANKING_EMPTY_MESSAGES" in app, "Empty state helper missing")
    require("scout_finance_ranking_experimental_filtered_v2_42a.csv" in app, "v2.42A export filename missing")
    require("No se encuentra el ranking global experimental" in ranking, "Missing dataset error copy missing")
    require("JSON valido" in ranking, "Corrupt dataset error copy missing")
    require("v2.41D" in app or "v2.41D" in ranking, "v2.41D reference missing")


def test_report_guardrails() -> None:
    report = REPORT.read_text(encoding="utf-8").lower()
    for phrase in [
        "no network",
        "no data download",
        "no scoring recomputation",
        "no ranking change",
        "no recommendations",
        "no broker actions",
    ]:
        require(phrase in report, f"Report missing phrase {phrase}")


def test_manifest_hashes_files() -> None:
    manifest = read_json(MANIFEST)
    paths = {entry["path"] for entry in manifest["files"]}
    require("app_v2_37.py" in paths, "app_v2_37.py missing from manifest")
    require("src/ui_v2_37/global_ranking.py" in paths, "global_ranking.py missing from manifest")
    require("src/ui_v2_37/safe_demo.py" in paths, "safe_demo.py missing from manifest")
    require(all(entry["sha256"] for entry in manifest["files"]), "Manifest contains empty hashes")


def main() -> None:
    test_required_files_exist()
    test_summary_contract()
    test_ux_matrices_cover_required_items()
    test_source_contains_ux_hardening_copy()
    test_report_guardrails()
    test_manifest_hashes_files()
    print("v2.42A final UX hardening QA passed")


if __name__ == "__main__":
    main()
