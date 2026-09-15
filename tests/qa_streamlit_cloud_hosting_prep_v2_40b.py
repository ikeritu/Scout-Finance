from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40b_streamlit_cloud_hosting_prep"
SUMMARY_PATH = OUT_DIR / "streamlit_cloud_hosting_prep_summary_v2_40b.json"
MANIFEST_PATH = OUT_DIR / "streamlit_cloud_hosting_prep_manifest_v2_40b.json"
SECRETS_TEMPLATE = ROOT / "docs" / "STREAMLIT_SECRETS_TEMPLATE_v2_40b.toml.example"
REPORT_PATH = OUT_DIR / "STREAMLIT_CLOUD_HOSTING_PREP_v2_40b.md"


EXPECTED_FALSE_FLAGS = [
    "deployment_allowed",
    "streamlit_cloud_app_created",
    "real_secrets_written",
    "github_release_created",
    "assets_uploaded",
    "tag_created",
    "network_used",
    "credential_preparation_done",
    "dependency_install_executed",
    "datasets_mutated",
    "scoring_recomputed",
    "ranking_changed",
    "weights_changed",
    "methodology_changed",
    "ui_changed",
    "financial_advice_created",
    "broker_actions_allowed",
]


REQUIRED_FILES = [
    OUT_DIR / "streamlit_cloud_hosting_prep_matrix_v2_40b.csv",
    OUT_DIR / "streamlit_cloud_required_files_inventory_v2_40b.csv",
    OUT_DIR / "streamlit_cloud_manual_checklist_v2_40b.csv",
    OUT_DIR / "streamlit_cloud_compatibility_analysis_v2_40b.csv",
    SUMMARY_PATH,
    MANIFEST_PATH,
    REPORT_PATH,
    OUT_DIR / "README.md",
    ROOT / "docs" / "STREAMLIT_CLOUD_HOSTING_PREP_v2_40b.md",
    SECRETS_TEMPLATE,
]


FORBIDDEN_SECRET_MARKERS = [
    "AIza",
    "sk-",
    "ghp_",
    "xoxb-",
    "BEGIN PRIVATE KEY",
]


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_required_files_exist() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    assert not missing, f"Missing v2.40B files: {missing}"


def test_summary_contract_values() -> None:
    summary = read_json(SUMMARY_PATH)
    assert summary["phase"] == "v2.40B"
    assert summary["status"] == "STREAMLIT_CLOUD_HOSTING_PREP_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["source_phase"] == "v2.40A"
    assert summary["source_status"] == "PUBLICATION_DECISION_RECORDED"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["publication_scope_current"] == "local_research_tool_only"
    assert summary["hosting_prep_scope"] == "technical_preparation_only"
    assert summary["deployment_status"] == "NOT_DEPLOYED"
    assert summary["selected_publication_decision"] == "PUBLIC_DEMO_SAFE_MODE_REQUIRED_BEFORE_EXTERNAL_DEPLOYMENT"
    assert summary["required_safe_demo_phase"] == "v2.40C-safe-demo-mode"
    assert summary["blocked_deployment_phase"] == "v2.40D-controlled-external-publication-qa"
    assert summary["streamlit_entrypoint_status"] == "PASS"
    assert summary["requirements_status"] == "PASS"
    assert summary["ranking_artifact_status"] == "PASS"
    assert summary["secrets_template_status"] == "PASS"
    assert summary["safe_demo_gate_status"] == "PASS"
    assert summary["deployment_block_status"] == "PASS"
    assert summary["manual_checklist_status"] == "READY"
    assert summary["required_files_missing"] == 0
    assert summary["fail_count"] == 0
    assert summary["blocker_count"] == 0
    for flag in EXPECTED_FALSE_FLAGS:
        assert summary[flag] is False, flag


def test_secrets_template_is_placeholder_only() -> None:
    content = SECRETS_TEMPLATE.read_text(encoding="utf-8")
    for marker in FORBIDDEN_SECRET_MARKERS:
        assert marker not in content
    assert "PLACEHOLDER_ONLY" in content
    assert "REPLACE_IN_STREAMLIT_CLOUD_UI_ONLY" in content


def test_manifest_hashes_outputs_and_docs() -> None:
    manifest = read_json(MANIFEST_PATH)
    paths = {entry["path"] for entry in manifest["files"]}
    assert "docs/STREAMLIT_CLOUD_HOSTING_PREP_v2_40b.md" in paths
    assert "docs/STREAMLIT_SECRETS_TEMPLATE_v2_40b.toml.example" in paths
    assert "outputs/full_universe_source_acquisition/v2_40b_streamlit_cloud_hosting_prep/streamlit_cloud_hosting_prep_summary_v2_40b.json" in paths
    assert all(entry["sha256"] and len(entry["sha256"]) == 64 for entry in manifest["files"])


def test_report_declares_no_deployment() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "No deployment was performed" in report
    assert "NOT_DEPLOYED" in report


if __name__ == "__main__":
    test_required_files_exist()
    test_summary_contract_values()
    test_secrets_template_is_placeholder_only()
    test_manifest_hashes_outputs_and_docs()
    test_report_declares_no_deployment()
    print("v2.40B QA PASS")
