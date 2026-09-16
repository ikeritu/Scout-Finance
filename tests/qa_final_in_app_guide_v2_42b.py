"""QA for v2.42B final in-app responsible-use guide."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_42b_final_in_app_guide"
SUMMARY = OUT_DIR / "final_in_app_guide_summary_v2_42b.json"
MANIFEST = OUT_DIR / "final_in_app_guide_manifest_v2_42b.json"
REPORT = OUT_DIR / "FINAL_IN_APP_GUIDE_v2_42b.md"

REQUIRED_FILES = [
    ROOT / "config" / "final_in_app_guide_contract_v2_42b.json",
    ROOT / "scripts" / "build_final_in_app_guide_v2_42b.py",
    ROOT / "tests" / "qa_final_in_app_guide_v2_42b.py",
    ROOT / "tests" / "qa_final_in_app_guide_full_suite_v2_42b.py",
    ROOT / "docs" / "FINAL_IN_APP_GUIDE_v2_42b.md",
    OUT_DIR / "final_in_app_guide_sections_v2_42b.csv",
    OUT_DIR / "final_in_app_guide_guardrails_v2_42b.csv",
    OUT_DIR / "final_in_app_guide_document_links_v2_42b.csv",
    OUT_DIR / "final_in_app_guide_ui_checks_v2_42b.csv",
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
    require(not missing, f"Missing required v2.42B files: {missing}")


def test_summary_contract() -> None:
    summary = read_json(SUMMARY)
    require(summary["phase"] == "v2.42B", "Unexpected phase")
    require(summary["status"] == "FINAL_IN_APP_GUIDE_READY", "Unexpected status")
    require(summary["qa_status"] == "PASS", "QA status must be PASS")
    require(summary["source_phase"] == "v2.42A", "Unexpected source phase")
    require(summary["source_status"] == "FINAL_UX_HARDENING_READY", "Unexpected source status")
    require(summary["scope"] == "final_in_app_guide_only", "Unexpected scope")
    require(summary["stable_tag"] == "v2.38CJ-local-stable", "Unexpected stable tag")
    require(summary["next_phase"] == "v2.43A-final-consolidated-audit", "Unexpected next phase")
    require(summary["qa_fail_count"] == 0, "QA fail count must be zero")
    require(summary["blocker_count"] == 0, "Blocker count must be zero")
    for key, expected in EXPECTED_COUNTS.items():
        require(summary[key] == expected, f"{key} expected {expected}, got {summary[key]}")
    for flag in FALSE_FLAGS:
        require(summary[flag] is False, f"{flag} must remain false")


def test_in_app_page_and_navigation() -> None:
    app = (ROOT / "app_v2_37.py").read_text(encoding="utf-8")
    require('"final_guide"' in app, "final_guide screen key missing")
    require("Guía final y uso responsable" in app, "Final guide navigation label missing")
    require("def render_final_guide" in app, "render_final_guide missing")
    require('"final_guide": render_final_guide' in app, "Final guide is not wired into router")
    require("render_safe_demo_banner(st, SAFE_DEMO_MODE)" in app[app.find("def render_final_guide"):], "Safe demo banner missing from final guide")


def test_required_copy_present() -> None:
    app = (ROOT / "app_v2_37.py").read_text(encoding="utf-8")
    required = [
        "No constituye asesoramiento financiero",
        "No recomienda comprar, vender ni mantener",
        "No predice rentabilidad",
        "No ejecuta órdenes",
        "No se conecta a broker",
        "datos locales/offline",
        "ranking experimental",
        "priorizar investigación",
        "limitaciones documentadas",
        "modo demo seguro",
    ]
    missing = [phrase for phrase in required if phrase not in app]
    require(not missing, f"Missing required copy: {missing}")


def test_matrices_are_complete() -> None:
    require(all(row["present"] == "true" for row in rows(OUT_DIR / "final_in_app_guide_sections_v2_42b.csv")), "Missing guide sections")
    require(all(row["present"] == "true" for row in rows(OUT_DIR / "final_in_app_guide_guardrails_v2_42b.csv")), "Missing guide guardrails")
    doc_rows = rows(OUT_DIR / "final_in_app_guide_document_links_v2_42b.csv")
    require(all(row["referenced_in_app"] == "true" for row in doc_rows), "Missing document references in app")
    require(all(row["exists_in_repo"] == "true" for row in doc_rows), "Referenced docs must exist")
    require(all(row["status"] == "true" for row in rows(OUT_DIR / "final_in_app_guide_ui_checks_v2_42b.csv")), "UI checks failed")


def test_report_guardrails() -> None:
    report = REPORT.read_text(encoding="utf-8").lower()
    for phrase in [
        "no network",
        "no data download",
        "no scoring recomputation",
        "no ranking change",
        "no financial advice",
        "no recommendations",
        "no broker actions",
    ]:
        require(phrase in report, f"Report missing phrase {phrase}")


def test_manifest_hashes_files() -> None:
    manifest = read_json(MANIFEST)
    paths = {entry["path"] for entry in manifest["files"]}
    require("app_v2_37.py" in paths, "app_v2_37.py missing from manifest")
    require("src/ui_v2_37/safe_demo.py" in paths, "safe_demo.py missing from manifest")
    require("src/ui_v2_37/global_ranking.py" in paths, "global_ranking.py missing from manifest")
    require(all(entry["sha256"] for entry in manifest["files"]), "Manifest contains empty hashes")


def main() -> None:
    test_required_files_exist()
    test_summary_contract()
    test_in_app_page_and_navigation()
    test_required_copy_present()
    test_matrices_are_complete()
    test_report_guardrails()
    test_manifest_hashes_files()
    print("v2.42B final in-app guide QA passed")


if __name__ == "__main__":
    main()
