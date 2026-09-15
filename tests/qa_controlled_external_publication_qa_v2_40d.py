from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40d_controlled_external_publication_qa"
SUMMARY = OUT_DIR / "controlled_external_publication_qa_summary_v2_40d.json"
MANIFEST = OUT_DIR / "controlled_external_publication_qa_manifest_v2_40d.json"
REPORT = OUT_DIR / "CONTROLLED_EXTERNAL_PUBLICATION_QA_v2_40d.md"


REQUIRED_FILES = [
    ROOT / "config" / "controlled_external_publication_qa_contract_v2_40d.json",
    ROOT / "scripts" / "build_controlled_external_publication_qa_v2_40d.py",
    ROOT / "tests" / "qa_controlled_external_publication_qa_v2_40d.py",
    ROOT / "tests" / "qa_controlled_external_publication_qa_full_suite_v2_40d.py",
    ROOT / "docs" / "CONTROLLED_EXTERNAL_PUBLICATION_QA_v2_40d.md",
    ROOT / "docs" / "STREAMLIT_CLOUD_PUBLICATION_MANUAL_STEPS_v2_40d.md",
    ROOT / "docs" / "PUBLIC_URL_PRE_SHARE_CHECKLIST_v2_40d.md",
    OUT_DIR / "controlled_external_publication_qa_matrix_v2_40d.csv",
    OUT_DIR / "streamlit_cloud_manual_publication_checklist_v2_40d.csv",
    OUT_DIR / "public_url_pre_share_qa_v2_40d.csv",
    OUT_DIR / "safe_demo_runtime_validation_v2_40d.csv",
    SUMMARY,
    MANIFEST,
    REPORT,
    OUT_DIR / "README.md",
]


FALSE_FLAGS = [
    "deployment_performed",
    "streamlit_cloud_app_created",
    "public_url_created",
    "public_url_shared",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_required_files_exist() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    assert not missing, missing


def test_summary_values() -> None:
    summary = read_json(SUMMARY)
    assert summary["phase"] == "v2.40D"
    assert summary["status"] == "CONTROLLED_EXTERNAL_PUBLICATION_QA_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["source_phase"] == "v2.40C"
    assert summary["source_status"] == "SAFE_DEMO_MODE_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["publication_scope_current"] == "controlled_external_publication_qa_ready_not_deployed"
    assert summary["deployment_status"] == "NOT_DEPLOYED"
    assert summary["safe_demo_required"] is True
    assert summary["safe_demo_mode_required_env"] == "SCOUT_FINANCE_SAFE_DEMO_MODE=1"
    assert summary["public_url_allowed_after_manual_qa"] is True
    assert summary["automatic_publication_allowed"] is False
    assert summary["manual_qa_required_before_sharing_url"] is True
    assert summary["streamlit_cloud_app_creation_mode"] == "MANUAL_USER_ACTION_ONLY"
    assert summary["next_phase"] == "v2.41A-data-gap-prioritization-or-project-close"
    assert summary["check_count"] >= 6
    assert summary["manual_publication_steps_count"] >= 6
    assert summary["pre_share_qa_count"] >= 10
    assert summary["runtime_validation_count"] >= 5
    assert summary["fail_count"] == 0
    assert summary["blocker_count"] == 0
    for flag in FALSE_FLAGS:
        assert summary[flag] is False, flag


def test_manual_checklist_contains_required_items() -> None:
    rows = read_csv(OUT_DIR / "streamlit_cloud_manual_publication_checklist_v2_40d.csv")
    joined = "\n".join(f"{row['action']} {row['required_value']}" for row in rows)
    assert "phase9b-global-enrichment-v2-38b" in joined
    assert "app_v2_37.py" in joined
    assert "SCOUT_FINANCE_SAFE_DEMO_MODE=1" in joined
    assert "NO_REAL_SECRETS" in joined


def test_pre_share_checklist_contains_runtime_expectations() -> None:
    rows = read_csv(OUT_DIR / "public_url_pre_share_qa_v2_40d.csv")
    joined = "\n".join(f"{row['check']} {row['expected']}" for row in rows)
    assert "Modo demo seguro" in joined
    assert "Actualizar disabled" in joined
    assert "Watchlists bloqueadas" in joined
    assert "ranking experimental" in joined
    assert "no asesoramiento financiero" in joined
    assert "sin broker" in joined


def test_docs_declare_no_deployment() -> None:
    docs = [
        REPORT,
        ROOT / "docs" / "CONTROLLED_EXTERNAL_PUBLICATION_QA_v2_40d.md",
        ROOT / "docs" / "STREAMLIT_CLOUD_PUBLICATION_MANUAL_STEPS_v2_40d.md",
        ROOT / "docs" / "PUBLIC_URL_PRE_SHARE_CHECKLIST_v2_40d.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    assert "No deployment was performed" in combined
    assert "No Streamlit Cloud app was created" in combined
    assert "No public URL was created" in combined


def test_no_secret_markers_in_new_files() -> None:
    for path in REQUIRED_FILES:
        content = path.read_text(encoding="utf-8", errors="ignore")
        for marker in FORBIDDEN_SECRET_MARKERS:
            assert marker not in content, f"{marker} found in {path}"


def test_manifest_hashes_outputs_and_docs() -> None:
    manifest = read_json(MANIFEST)
    paths = {entry["path"] for entry in manifest["files"]}
    assert "docs/CONTROLLED_EXTERNAL_PUBLICATION_QA_v2_40d.md" in paths
    assert "docs/STREAMLIT_CLOUD_PUBLICATION_MANUAL_STEPS_v2_40d.md" in paths
    assert "docs/PUBLIC_URL_PRE_SHARE_CHECKLIST_v2_40d.md" in paths
    assert "outputs/full_universe_source_acquisition/v2_40d_controlled_external_publication_qa/controlled_external_publication_qa_summary_v2_40d.json" in paths
    assert all(len(entry["sha256"]) == 64 for entry in manifest["files"])


if __name__ == "__main__":
    test_required_files_exist()
    test_summary_values()
    test_manual_checklist_contains_required_items()
    test_pre_share_checklist_contains_runtime_expectations()
    test_docs_declare_no_deployment()
    test_no_secret_markers_in_new_files()
    test_manifest_hashes_outputs_and_docs()
    print("v2.40D QA PASS")
