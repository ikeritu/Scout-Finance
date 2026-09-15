from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40c_safe_demo_mode"
SUMMARY = OUT_DIR / "safe_demo_mode_summary_v2_40c.json"
MANIFEST = OUT_DIR / "safe_demo_mode_manifest_v2_40c.json"
REPORT = OUT_DIR / "SAFE_DEMO_MODE_v2_40c.md"
APP = ROOT / "app_v2_37.py"
SAFE_DEMO_MODULE = ROOT / "src" / "ui_v2_37" / "safe_demo.py"


REQUIRED_FILES = [
    ROOT / "config" / "safe_demo_mode_contract_v2_40c.json",
    ROOT / "scripts" / "build_safe_demo_mode_v2_40c.py",
    ROOT / "tests" / "qa_safe_demo_mode_v2_40c.py",
    ROOT / "tests" / "qa_safe_demo_mode_full_suite_v2_40c.py",
    ROOT / "docs" / "SAFE_DEMO_MODE_v2_40c.md",
    ROOT / "docs" / "STREAMLIT_CLOUD_SAFE_DEMO_RUNBOOK_v2_40c.md",
    SAFE_DEMO_MODULE,
    OUT_DIR / "safe_demo_mode_matrix_v2_40c.csv",
    OUT_DIR / "safe_demo_controls_v2_40c.csv",
    OUT_DIR / "safe_demo_ui_inventory_v2_40c.csv",
    OUT_DIR / "safe_demo_blocked_actions_v2_40c.csv",
    SUMMARY,
    MANIFEST,
    REPORT,
    OUT_DIR / "README.md",
]


FALSE_FLAGS = [
    "deployment_performed",
    "streamlit_cloud_app_created",
    "public_url_created",
    "real_secrets_written",
    "credentials_required",
    "network_used",
    "dependency_install_executed",
    "datasets_mutated",
    "scoring_recomputed",
    "ranking_changed",
    "weights_changed",
    "methodology_changed",
    "broker_actions_allowed",
    "financial_advice_created",
    "recommendations_created",
    "external_provider_enabled",
    "github_release_created",
    "tag_created",
    "assets_uploaded",
]


FORBIDDEN_SECRET_MARKERS = [
    "AI" + "za",
    "sk" + "-",
    "gh" + "p_",
    "xo" + "xb-",
    "BEGIN " + "PRIVATE KEY",
]


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_required_files_exist() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    assert not missing, missing


def test_summary_values() -> None:
    summary = read_json(SUMMARY)
    assert summary["phase"] == "v2.40C"
    assert summary["status"] == "SAFE_DEMO_MODE_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["source_phase"] == "v2.40B"
    assert summary["source_status"] == "STREAMLIT_CLOUD_HOSTING_PREP_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["publication_scope_current"] == "safe_demo_mode_ready_not_deployed"
    assert summary["deployment_status"] == "NOT_DEPLOYED"
    assert summary["demo_mode_activation"] == "OPT_IN_ONLY"
    assert summary["demo_mode_default"] == "OFF"
    assert summary["streamlit_cloud_ready_for_demo"] is True
    assert summary["controlled_external_publication_allowed"] is False
    assert summary["next_phase"] == "v2.40D-controlled-external-publication-qa"
    assert summary["blocker_count"] == 0
    assert summary["fail_count"] == 0
    for status_key in (
        "safe_demo_banner_status",
        "no_advice_disclaimer_status",
        "offline_static_data_status",
        "broker_block_status",
        "refresh_block_status",
        "export_safety_status",
        "secrets_safety_status",
        "ranking_read_only_status",
        "methodology_lock_status",
    ):
        assert summary[status_key] == "PASS", status_key
    for flag in FALSE_FLAGS:
        assert summary[flag] is False, flag


def test_no_real_secret_markers_in_new_files() -> None:
    for path in REQUIRED_FILES:
        content = path.read_text(encoding="utf-8", errors="ignore")
        for marker in FORBIDDEN_SECRET_MARKERS:
            assert marker not in content, f"{marker} found in {path}"


def test_ui_safe_demo_text_and_blocks() -> None:
    app = APP.read_text(encoding="utf-8")
    module = SAFE_DEMO_MODULE.read_text(encoding="utf-8")
    assert "Modo demo seguro" in app
    assert "Modo demo seguro" in module
    assert "Actualización bloqueada en Modo demo seguro" in app
    assert "Watchlists bloqueadas en Modo demo seguro" in app
    assert "sin asesoramiento financiero" in module
    assert "sin broker" in module


def test_report_no_deployment_and_next_phase_blocked() -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert "No deployment was performed" in report
    assert "No public URL was created" in report
    assert "not automatically authorized" in report
    assert "v2.40D-controlled-external-publication-qa" in report


def test_manifest_hashes_outputs_and_docs() -> None:
    manifest = read_json(MANIFEST)
    paths = {entry["path"] for entry in manifest["files"]}
    assert "docs/SAFE_DEMO_MODE_v2_40c.md" in paths
    assert "docs/STREAMLIT_CLOUD_SAFE_DEMO_RUNBOOK_v2_40c.md" in paths
    assert "src/ui_v2_37/safe_demo.py" in paths
    assert all(len(entry["sha256"]) == 64 for entry in manifest["files"])


if __name__ == "__main__":
    test_required_files_exist()
    test_summary_values()
    test_no_real_secret_markers_in_new_files()
    test_ui_safe_demo_text_and_blocks()
    test_report_no_deployment_and_next_phase_blocked()
    test_manifest_hashes_outputs_and_docs()
    print("v2.40C QA PASS")
