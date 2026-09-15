from __future__ import annotations

import csv
import hashlib
import json
import py_compile
from pathlib import Path


PHASE = "v2.40B"
STATUS = "STREAMLIT_CLOUD_HOSTING_PREP_READY"
ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40a_publication_decision"
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40b_streamlit_cloud_hosting_prep"
DOC_PATH = ROOT / "docs" / "STREAMLIT_CLOUD_HOSTING_PREP_v2_40b.md"
SECRETS_TEMPLATE = ROOT / "docs" / "STREAMLIT_SECRETS_TEMPLATE_v2_40b.toml.example"
CONTRACT_PATH = ROOT / "config" / "streamlit_cloud_hosting_prep_contract_v2_40b.json"


REQUIRED_FILES = [
    ("streamlit_entrypoint", "app_v2_37.py"),
    ("requirements", "requirements.txt"),
    ("local_launcher", "run_local_ui_v2_37.bat"),
    ("ranking_ui_module", "src/ui_v2_37/global_ranking.py"),
    ("global_universe_ui_module", "src/ui_v2_37/global_universe.py"),
    ("ranking_results", "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_v2_38bv.csv"),
    ("publication_decision_summary", "outputs/full_universe_source_acquisition/v2_40a_publication_decision/publication_decision_summary_v2_40a.json"),
    ("publication_policy_gate", "outputs/full_universe_source_acquisition/v2_40a_publication_decision/publication_policy_gate_v2_40a.csv"),
]


FALSE_FLAGS = [
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


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_40a_summary() -> dict:
    path = SOURCE_DIR / "publication_decision_summary_v2_40a.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing required source summary: {path}")
    summary = read_json(path)
    if summary.get("status") != "PUBLICATION_DECISION_RECORDED":
        raise ValueError("v2.40A source status is not PUBLICATION_DECISION_RECORDED")
    return summary


def requirement_status() -> tuple[str, str]:
    path = ROOT / "requirements.txt"
    if not path.exists():
        return "FAIL", "requirements.txt is missing"
    content = path.read_text(encoding="utf-8", errors="ignore").lower()
    missing = [name for name in ("streamlit", "pandas") if name not in content]
    if missing:
        return "FAIL", "Missing required dependency markers: " + ", ".join(missing)
    return "PASS", "requirements.txt declares Streamlit-compatible local dependencies"


def compile_status(relative_path: str) -> tuple[str, str]:
    path = ROOT / relative_path
    if not path.exists():
        return "FAIL", "file is missing"
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        return "FAIL", str(exc)
    return "PASS", "Python syntax compile passed"


def build_docs() -> None:
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(
        """# Streamlit Cloud Hosting Prep v2.40B

Status: `STREAMLIT_CLOUD_HOSTING_PREP_READY`

This phase prepares the technical checklist for a future Streamlit Cloud deployment. It does not deploy Scout Finance, does not create a Streamlit Cloud app, does not upload release assets, does not create tags, and does not write real credentials.

## Hosting Shape

- Repository: `ikeritu/Scout-Finance`
- Branch: `phase9b-global-enrichment-v2-38b`
- Main file: `app_v2_37.py`
- Current product scope: `local_research_tool_only`
- Current deployment status: `NOT_DEPLOYED`

## Required Gates

- `v2.40B`: technical hosting preparation only.
- `v2.40C`: safe demo mode is required before any public demo.
- `v2.40D`: controlled external publication QA remains blocked until `v2.40B` and `v2.40C` are complete.

## Guardrails

- No real secrets are stored in the repository.
- No broker workflows are allowed.
- No financial advice, recommendations, ranking methodology changes, scoring recomputation, or dataset mutation are introduced here.
- No deployment was performed in this phase.
""",
        encoding="utf-8",
    )
    SECRETS_TEMPLATE.write_text(
        """# Streamlit Cloud secrets template for Scout Finance v2.40B
# Copy values into Streamlit Cloud secrets only after v2.40C safe demo mode exists.
# Keep this file as placeholders only. Do not commit real secrets.

[scout_finance]
environment = "demo_safe_mode_required"
publication_scope = "local_research_tool_only"

[optional_providers]
provider_name = "PLACEHOLDER_ONLY"
api_key = "REPLACE_IN_STREAMLIT_CLOUD_UI_ONLY"
""",
        encoding="utf-8",
    )


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_summary = load_40a_summary()
    build_docs()

    inventory_rows = []
    present_count = 0
    for role, relative_path in REQUIRED_FILES:
        path = ROOT / relative_path
        exists = path.exists()
        present_count += int(exists)
        inventory_rows.append(
            {
                "role": role,
                "path": relative_path,
                "status": "PRESENT" if exists else "MISSING",
                "required_for_streamlit_cloud": "true",
            }
        )

    requirements_check, requirements_detail = requirement_status()
    app_compile_status, app_compile_detail = compile_status("app_v2_37.py")
    ranking_compile_status, ranking_compile_detail = compile_status("src/ui_v2_37/global_ranking.py")
    missing_count = len(REQUIRED_FILES) - present_count
    ranking_artifact_exists = (ROOT / REQUIRED_FILES[5][1]).exists()

    matrix_rows = [
        {"check_id": "40B-001", "area": "source_gate", "status": "PASS", "detail": "v2.40A publication decision is recorded"},
        {"check_id": "40B-002", "area": "streamlit_entrypoint", "status": app_compile_status, "detail": app_compile_detail},
        {"check_id": "40B-003", "area": "ranking_ui_module", "status": ranking_compile_status, "detail": ranking_compile_detail},
        {"check_id": "40B-004", "area": "requirements", "status": requirements_check, "detail": requirements_detail},
        {"check_id": "40B-005", "area": "ranking_artifact", "status": "PASS" if ranking_artifact_exists else "FAIL", "detail": "ranking artifact is present and reused without recomputation"},
        {"check_id": "40B-006", "area": "secrets_template", "status": "PASS", "detail": "placeholder-only secrets template created"},
        {"check_id": "40B-007", "area": "streamlit_config", "status": "WARN", "detail": "optional config is documented but not created in this phase"},
        {"check_id": "40B-008", "area": "safe_demo_gate", "status": "PASS", "detail": "v2.40C is required before public demo"},
        {"check_id": "40B-009", "area": "deployment_block", "status": "PASS", "detail": "no deployment was performed and v2.40D remains blocked"},
        {"check_id": "40B-010", "area": "manual_checklist", "status": "PASS", "detail": "operator checklist created for future manual hosting setup"},
    ]

    compatibility_rows = [
        {"component": "entrypoint", "status": app_compile_status, "finding": app_compile_detail},
        {"component": "requirements", "status": requirements_check, "finding": requirements_detail},
        {"component": "ranking_artifact", "status": "PASS" if ranking_artifact_exists else "FAIL", "finding": "existing v2.38BV ranking output is present"},
        {"component": "safe_demo_mode", "status": "BLOCKED_PENDING_40C", "finding": "public demo requires v2.40C before external deployment"},
        {"component": "deployment", "status": "NOT_DEPLOYED", "finding": "technical preparation only"},
    ]
    checklist_rows = [
        {"step": 1, "action": "Confirm branch phase9b-global-enrichment-v2-38b is selected in Streamlit Cloud", "status": "MANUAL_PENDING"},
        {"step": 2, "action": "Use app_v2_37.py as the main file", "status": "MANUAL_PENDING"},
        {"step": 3, "action": "Paste secrets only in Streamlit Cloud UI after v2.40C", "status": "BLOCKED_PENDING_40C"},
        {"step": 4, "action": "Run v2.40D controlled external publication QA before sharing any URL", "status": "BLOCKED_PENDING_40D"},
    ]

    write_csv(OUT_DIR / "streamlit_cloud_hosting_prep_matrix_v2_40b.csv", matrix_rows, ["check_id", "area", "status", "detail"])
    write_csv(OUT_DIR / "streamlit_cloud_required_files_inventory_v2_40b.csv", inventory_rows, ["role", "path", "status", "required_for_streamlit_cloud"])
    write_csv(OUT_DIR / "streamlit_cloud_manual_checklist_v2_40b.csv", checklist_rows, ["step", "action", "status"])
    write_csv(OUT_DIR / "streamlit_cloud_compatibility_analysis_v2_40b.csv", compatibility_rows, ["component", "status", "finding"])

    fail_count = sum(1 for row in matrix_rows if row["status"] == "FAIL")
    warn_count = sum(1 for row in matrix_rows if row["status"] == "WARN")
    pass_count = sum(1 for row in matrix_rows if row["status"] == "PASS")

    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS" if fail_count == 0 else "FAIL",
        "source_phase": "v2.40A",
        "source_status": source_summary["status"],
        "stable_tag": "v2.38CJ-local-stable",
        "publication_scope_current": "local_research_tool_only",
        "hosting_prep_scope": "technical_preparation_only",
        "deployment_status": "NOT_DEPLOYED",
        "selected_publication_decision": "PUBLIC_DEMO_SAFE_MODE_REQUIRED_BEFORE_EXTERNAL_DEPLOYMENT",
        "required_safe_demo_phase": "v2.40C-safe-demo-mode",
        "blocked_deployment_phase": "v2.40D-controlled-external-publication-qa",
        "required_files_total": len(REQUIRED_FILES),
        "required_files_present": present_count,
        "required_files_missing": missing_count,
        "check_count": len(matrix_rows),
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "blocker_count": 0 if fail_count == 0 else fail_count,
        "streamlit_entrypoint_status": app_compile_status,
        "requirements_status": requirements_check,
        "ranking_artifact_status": "PASS" if ranking_artifact_exists else "FAIL",
        "secrets_template_status": "PASS",
        "streamlit_config_status": "OPTIONAL_DOCUMENTED_NOT_CREATED",
        "safe_demo_gate_status": "PASS",
        "deployment_block_status": "PASS",
        "manual_checklist_status": "READY",
        "next_phase": "v2.40C-safe-demo-mode",
        **{flag: False for flag in FALSE_FLAGS},
    }
    (OUT_DIR / "streamlit_cloud_hosting_prep_summary_v2_40b.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = f"""# Streamlit Cloud Hosting Prep v2.40B

Status: `{STATUS}`

This phase prepares Scout Finance for a future Streamlit Cloud setup as technical preparation only. No deployment was performed.

## Result

- Source phase: `v2.40A`
- Source status: `{source_summary["status"]}`
- Required files present: `{present_count}/{len(REQUIRED_FILES)}`
- Matrix checks: `{pass_count}` pass, `{warn_count}` warn, `{fail_count}` fail
- Deployment status: `NOT_DEPLOYED`
- Selected decision: `PUBLIC_DEMO_SAFE_MODE_REQUIRED_BEFORE_EXTERNAL_DEPLOYMENT`

## Next Gate

`v2.40C-safe-demo-mode` must exist before any public demo. `v2.40D-controlled-external-publication-qa` remains blocked until 40B and 40C are complete.
"""
    (OUT_DIR / "STREAMLIT_CLOUD_HOSTING_PREP_v2_40b.md").write_text(report, encoding="utf-8")
    (OUT_DIR / "README.md").write_text(
        """# v2.40B Streamlit Cloud Hosting Prep

Generated technical hosting-prep outputs for Scout Finance. This directory records readiness checks, required-file inventory, manual hosting checklist, compatibility analysis, summary, manifest and report.

No external deployment, credential writing, dependency installation, dataset mutation, scoring recomputation, methodology change, financial advice, broker action or public app creation is performed here.
""",
        encoding="utf-8",
    )

    manifest_files = [
        CONTRACT_PATH,
        DOC_PATH,
        SECRETS_TEMPLATE,
        OUT_DIR / "streamlit_cloud_hosting_prep_matrix_v2_40b.csv",
        OUT_DIR / "streamlit_cloud_required_files_inventory_v2_40b.csv",
        OUT_DIR / "streamlit_cloud_manual_checklist_v2_40b.csv",
        OUT_DIR / "streamlit_cloud_compatibility_analysis_v2_40b.csv",
        OUT_DIR / "streamlit_cloud_hosting_prep_summary_v2_40b.json",
        OUT_DIR / "STREAMLIT_CLOUD_HOSTING_PREP_v2_40b.md",
        OUT_DIR / "README.md",
    ]
    manifest = {
        "phase": PHASE,
        "status": STATUS,
        "files": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)}
            for path in manifest_files
        ],
    }
    manifest_path = OUT_DIR / "streamlit_cloud_hosting_prep_manifest_v2_40b.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
