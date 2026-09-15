from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


PHASE = "v2.40D"
STATUS = "CONTROLLED_EXTERNAL_PUBLICATION_QA_READY"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40d_controlled_external_publication_qa"
SOURCE_SUMMARY = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40c_safe_demo_mode" / "safe_demo_mode_summary_v2_40c.json"
CONTRACT = ROOT / "config" / "controlled_external_publication_qa_contract_v2_40d.json"
DOC = ROOT / "docs" / "CONTROLLED_EXTERNAL_PUBLICATION_QA_v2_40d.md"
MANUAL_STEPS = ROOT / "docs" / "STREAMLIT_CLOUD_PUBLICATION_MANUAL_STEPS_v2_40d.md"
PRE_SHARE = ROOT / "docs" / "PUBLIC_URL_PRE_SHARE_CHECKLIST_v2_40d.md"


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


def source_status() -> str:
    summary = read_json(SOURCE_SUMMARY)
    status = summary.get("status")
    if status != "SAFE_DEMO_MODE_READY":
        raise ValueError(f"Expected v2.40C SAFE_DEMO_MODE_READY, got {status!r}")
    return status


def write_docs() -> None:
    DOC.write_text(
        """# Controlled External Publication QA v2.40D

Status: `CONTROLLED_EXTERNAL_PUBLICATION_QA_READY`

This phase prepares the QA package for a future controlled external publication of Scout Finance in safe demo mode. No deployment was performed, no Streamlit Cloud app was created, no public URL was created or shared, and no real credentials were written.

The only acceptable external publication path is manual: create the Streamlit Cloud app with `SCOUT_FINANCE_SAFE_DEMO_MODE=1`, complete the pre-share checklist, and share a URL only after every manual QA item passes.
""",
        encoding="utf-8",
    )
    MANUAL_STEPS.write_text(
        """# Streamlit Cloud Publication Manual Steps v2.40D

Manual action only. Do not share a URL until the pre-share QA passes.

1. Select repository `ikeritu/Scout-Finance`.
2. Select branch `phase9b-global-enrichment-v2-38b`.
3. Set main file to `app_v2_37.py`.
4. Set environment/secrets value `SCOUT_FINANCE_SAFE_DEMO_MODE=1`.
5. Do not add real provider credentials.
6. Launch only for controlled QA.
7. Verify the app shows `Modo demo seguro`.
8. Verify `Actualizar` is disabled.
9. Verify watchlists are blocked.
10. Verify no broker/trading or financial advice action is available.
""",
        encoding="utf-8",
    )
    PRE_SHARE.write_text(
        """# Public URL Pre-Share Checklist v2.40D

The URL can only be shared after all checks pass manually.

- Branch is `phase9b-global-enrichment-v2-38b`.
- Main file is `app_v2_37.py`.
- `SCOUT_FINANCE_SAFE_DEMO_MODE=1` is active.
- Banner `Modo demo seguro` is visible.
- `Actualizar` is disabled.
- Watchlists are blocked.
- Ranking is marked as experimental.
- No asesoramiento financiero disclaimer is visible.
- Sin broker disclaimer is visible.
- Datos estaticos/offline disclaimer is visible.
- No external providers are active.
- No scoring recomputation is available.
- Exports are sanitized research outputs only.
""",
        encoding="utf-8",
    )


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src_status = source_status()
    write_docs()

    matrix = [
        {"check_id": "40D-001", "area": "source_gate", "status": "PASS", "detail": "v2.40C safe demo mode is ready"},
        {"check_id": "40D-002", "area": "manual_publication_only", "status": "PASS", "detail": "Streamlit Cloud creation is manual user action only"},
        {"check_id": "40D-003", "area": "safe_demo_required", "status": "PASS", "detail": "SCOUT_FINANCE_SAFE_DEMO_MODE=1 required"},
        {"check_id": "40D-004", "area": "pre_share_qa", "status": "PASS", "detail": "public URL share blocked until manual QA passes"},
        {"check_id": "40D-005", "area": "deployment_status", "status": "PASS", "detail": "No deployment was performed"},
        {"check_id": "40D-006", "area": "guardrails", "status": "PASS", "detail": "no secrets, network, scoring, recommendations, broker or dataset mutation"},
    ]
    manual_steps = [
        {"step": 1, "action": "Select repository ikeritu/Scout-Finance", "required_value": "ikeritu/Scout-Finance", "status": "MANUAL_PENDING"},
        {"step": 2, "action": "Select branch", "required_value": "phase9b-global-enrichment-v2-38b", "status": "MANUAL_PENDING"},
        {"step": 3, "action": "Set main file", "required_value": "app_v2_37.py", "status": "MANUAL_PENDING"},
        {"step": 4, "action": "Set safe demo env", "required_value": "SCOUT_FINANCE_SAFE_DEMO_MODE=1", "status": "MANUAL_PENDING"},
        {"step": 5, "action": "Do not add real provider credentials", "required_value": "NO_REAL_SECRETS", "status": "MANUAL_PENDING"},
        {"step": 6, "action": "Create app only for controlled QA", "required_value": "MANUAL_USER_ACTION_ONLY", "status": "MANUAL_PENDING"},
    ]
    pre_share = [
        {"check": "branch_correct", "expected": "phase9b-global-enrichment-v2-38b", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "main_file_correct", "expected": "app_v2_37.py", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "safe_demo_env_active", "expected": "SCOUT_FINANCE_SAFE_DEMO_MODE=1", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "banner_visible", "expected": "Modo demo seguro", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "refresh_disabled", "expected": "Actualizar disabled", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "watchlists_blocked", "expected": "Watchlists bloqueadas", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "ranking_experimental", "expected": "ranking experimental", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "no_advice_visible", "expected": "no asesoramiento financiero", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "no_broker_visible", "expected": "sin broker", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "static_offline_visible", "expected": "datos estaticos/offline", "status": "REQUIRED_BEFORE_SHARE"},
        {"check": "exports_sanitized", "expected": "research outputs only", "status": "REQUIRED_BEFORE_SHARE"},
    ]
    runtime_validation = [
        {"surface": "sidebar", "expected": "Modo demo seguro", "status": "MANUAL_QA_REQUIRED"},
        {"surface": "global_universe", "expected": "Actualizar disabled", "status": "MANUAL_QA_REQUIRED"},
        {"surface": "watchlist", "expected": "blocked in safe demo", "status": "MANUAL_QA_REQUIRED"},
        {"surface": "global_ranking", "expected": "read-only experimental ranking", "status": "MANUAL_QA_REQUIRED"},
        {"surface": "footer/copy", "expected": "no broker and no advice", "status": "MANUAL_QA_REQUIRED"},
    ]

    write_csv(OUT_DIR / "controlled_external_publication_qa_matrix_v2_40d.csv", matrix, ["check_id", "area", "status", "detail"])
    write_csv(OUT_DIR / "streamlit_cloud_manual_publication_checklist_v2_40d.csv", manual_steps, ["step", "action", "required_value", "status"])
    write_csv(OUT_DIR / "public_url_pre_share_qa_v2_40d.csv", pre_share, ["check", "expected", "status"])
    write_csv(OUT_DIR / "safe_demo_runtime_validation_v2_40d.csv", runtime_validation, ["surface", "expected", "status"])

    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS",
        "source_phase": "v2.40C",
        "source_status": src_status,
        "stable_tag": "v2.38CJ-local-stable",
        "publication_scope_current": "controlled_external_publication_qa_ready_not_deployed",
        "deployment_status": "NOT_DEPLOYED",
        "safe_demo_required": True,
        "safe_demo_mode_required_env": "SCOUT_FINANCE_SAFE_DEMO_MODE=1",
        "public_url_allowed_after_manual_qa": True,
        "automatic_publication_allowed": False,
        "manual_qa_required_before_sharing_url": True,
        "streamlit_cloud_app_creation_mode": "MANUAL_USER_ACTION_ONLY",
        "next_phase": "v2.41A-data-gap-prioritization-or-project-close",
        "check_count": len(matrix),
        "manual_publication_steps_count": len(manual_steps),
        "pre_share_qa_count": len(pre_share),
        "runtime_validation_count": len(runtime_validation),
        "fail_count": 0,
        "blocker_count": 0,
        **{flag: False for flag in FALSE_FLAGS},
    }
    summary_path = OUT_DIR / "controlled_external_publication_qa_summary_v2_40d.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = """# Controlled External Publication QA v2.40D

Status: `CONTROLLED_EXTERNAL_PUBLICATION_QA_READY`

No deployment was performed. No Streamlit Cloud app was created. No public URL was created or shared. No real secrets were written.

Public URL sharing is allowed only after manual QA confirms safe demo mode, disabled refresh, blocked watchlists, experimental ranking copy, no financial advice, no broker, static/offline data and sanitized exports.
"""
    (OUT_DIR / "CONTROLLED_EXTERNAL_PUBLICATION_QA_v2_40d.md").write_text(report, encoding="utf-8")
    (OUT_DIR / "README.md").write_text(
        "# v2.40D Controlled External Publication QA\n\nQA package for future manual Streamlit Cloud publication. This phase does not deploy, create a URL, write secrets, call network, mutate data, recompute scoring, change ranking, create recommendations or enable broker actions.\n",
        encoding="utf-8",
    )

    manifest_files = [
        CONTRACT,
        DOC,
        MANUAL_STEPS,
        PRE_SHARE,
        OUT_DIR / "controlled_external_publication_qa_matrix_v2_40d.csv",
        OUT_DIR / "streamlit_cloud_manual_publication_checklist_v2_40d.csv",
        OUT_DIR / "public_url_pre_share_qa_v2_40d.csv",
        OUT_DIR / "safe_demo_runtime_validation_v2_40d.csv",
        summary_path,
        OUT_DIR / "controlled_external_publication_qa_manifest_v2_40d.json",
        OUT_DIR / "CONTROLLED_EXTERNAL_PUBLICATION_QA_v2_40d.md",
        OUT_DIR / "README.md",
    ]
    manifest = {
        "phase": PHASE,
        "status": STATUS,
        "files": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)}
            for path in manifest_files
            if path.exists()
        ],
    }
    (OUT_DIR / "controlled_external_publication_qa_manifest_v2_40d.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
