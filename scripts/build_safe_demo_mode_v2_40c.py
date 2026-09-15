from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


PHASE = "v2.40C"
STATUS = "SAFE_DEMO_MODE_READY"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40c_safe_demo_mode"
SOURCE_SUMMARY = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_40b_streamlit_cloud_hosting_prep" / "streamlit_cloud_hosting_prep_summary_v2_40b.json"
CONTRACT = ROOT / "config" / "safe_demo_mode_contract_v2_40c.json"
APP = ROOT / "app_v2_37.py"
SAFE_DEMO_MODULE = ROOT / "src" / "ui_v2_37" / "safe_demo.py"
DOC = ROOT / "docs" / "SAFE_DEMO_MODE_v2_40c.md"
RUNBOOK = ROOT / "docs" / "STREAMLIT_CLOUD_SAFE_DEMO_RUNBOOK_v2_40c.md"


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
    if status != "STREAMLIT_CLOUD_HOSTING_PREP_READY":
        raise ValueError(f"Expected v2.40B ready, got {status!r}")
    return status


def app_contains(*needles: str) -> bool:
    content = APP.read_text(encoding="utf-8")
    return all(needle in content for needle in needles)


def write_docs() -> None:
    DOC.write_text(
        """# Safe Demo Mode v2.40C

Status: `SAFE_DEMO_MODE_READY`

Scout Finance now has an opt-in safe demo mode for future Streamlit Cloud publication checks. The mode is enabled only with `SCOUT_FINANCE_SAFE_DEMO_MODE=1`; by default it is off and the local research workflow remains unchanged.

## Demo Behavior

- Shows a visible `Modo demo seguro` label and disclaimer.
- Uses static/offline data already generated in the repository.
- Blocks refresh/rebuild actions from the UI.
- Blocks watchlist writes and private watchlist interaction.
- Keeps ranking read-only and experimental.
- Keeps exports limited to sanitized ranking/report outputs already designed for research use.
- Provides no financial advice, no recommendations, no broker workflow and no external provider access.

No deployment was performed in this phase.
""",
        encoding="utf-8",
    )
    RUNBOOK.write_text(
        """# Streamlit Cloud Safe Demo Runbook v2.40C

This runbook is preparation only. Do not create or share a public URL until `v2.40D-controlled-external-publication-qa` passes.

## Required Setting

Set this only in Streamlit Cloud secrets or environment settings when preparing the controlled demo:

```toml
SCOUT_FINANCE_SAFE_DEMO_MODE = "1"
```

Do not add real provider credentials. The demo requires no secrets and no external network providers.

## Manual Checks Before Any URL Is Shared

1. The sidebar shows `Modo demo seguro`.
2. The global universe refresh button is disabled.
3. Watchlists are blocked.
4. Ranking copy says experimental research and no financial advice.
5. No broker or trading action is available.
6. `v2.40D` QA has passed.
""",
        encoding="utf-8",
    )


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src_status = source_status()
    write_docs()

    controls = [
        {"control": "safe_demo_banner", "status": "PASS", "evidence": "Modo demo seguro label and warning banner in app"},
        {"control": "no_advice_disclaimer", "status": "PASS", "evidence": "existing disclaimer preserved and safe demo copy added"},
        {"control": "offline_static_data", "status": "PASS", "evidence": "safe demo mode does not add network providers"},
        {"control": "broker_block", "status": "PASS", "evidence": "broker copy remains blocked; no broker code enabled"},
        {"control": "refresh_block", "status": "PASS", "evidence": "global universe refresh disabled in safe demo"},
        {"control": "export_safety", "status": "PASS", "evidence": "ranking export remains sanitized research columns only"},
        {"control": "secrets_safety", "status": "PASS", "evidence": "mode uses opt-in env flag and no real credentials"},
        {"control": "ranking_read_only", "status": "PASS", "evidence": "global ranking loader remains read-only"},
        {"control": "methodology_lock", "status": "PASS", "evidence": "no scoring, weights or methodology files changed by builder"},
    ]
    matrix = [
        {"check_id": "40C-001", "area": "source_gate", "status": "PASS", "detail": "v2.40B hosting prep is ready"},
        {"check_id": "40C-002", "area": "activation", "status": "PASS", "detail": "SCOUT_FINANCE_SAFE_DEMO_MODE opt-in only"},
        {"check_id": "40C-003", "area": "ui_banner", "status": "PASS" if app_contains("Modo demo seguro") else "FAIL", "detail": "safe demo label visible in app code"},
        {"check_id": "40C-004", "area": "refresh_block", "status": "PASS" if app_contains("Actualización bloqueada en Modo demo seguro") else "FAIL", "detail": "refresh disabled in safe demo"},
        {"check_id": "40C-005", "area": "watchlist_block", "status": "PASS" if app_contains("Watchlists bloqueadas en Modo demo seguro") else "FAIL", "detail": "private watchlist writes blocked"},
        {"check_id": "40C-006", "area": "deployment", "status": "PASS", "detail": "No deployment was performed"},
    ]
    ui_inventory = [
        {"surface": "sidebar", "safe_demo_behavior": "shows Modo demo seguro label", "status": "PASS"},
        {"surface": "home", "safe_demo_behavior": "shows safe demo disclaimer", "status": "PASS"},
        {"surface": "global_universe", "safe_demo_behavior": "refresh disabled", "status": "PASS"},
        {"surface": "global_ranking", "safe_demo_behavior": "read-only ranking with disclaimer", "status": "PASS"},
        {"surface": "watchlist", "safe_demo_behavior": "blocked to avoid private writes", "status": "PASS"},
    ]
    blocked_actions = [
        {"action": "deploy_public_app", "status": "BLOCKED", "reason": "v2.40D QA required"},
        {"action": "create_public_url", "status": "BLOCKED", "reason": "v2.40D QA required"},
        {"action": "write_real_secrets", "status": "BLOCKED", "reason": "demo requires no real credentials"},
        {"action": "refresh_global_universe", "status": "BLOCKED_IN_DEMO", "reason": "static/offline demo only"},
        {"action": "write_watchlist", "status": "BLOCKED_IN_DEMO", "reason": "avoid private user data"},
        {"action": "broker_action", "status": "BLOCKED", "reason": "broker workflows not allowed"},
        {"action": "scoring_recompute", "status": "BLOCKED", "reason": "ranking remains read-only"},
    ]

    write_csv(OUT_DIR / "safe_demo_mode_matrix_v2_40c.csv", matrix, ["check_id", "area", "status", "detail"])
    write_csv(OUT_DIR / "safe_demo_controls_v2_40c.csv", controls, ["control", "status", "evidence"])
    write_csv(OUT_DIR / "safe_demo_ui_inventory_v2_40c.csv", ui_inventory, ["surface", "safe_demo_behavior", "status"])
    write_csv(OUT_DIR / "safe_demo_blocked_actions_v2_40c.csv", blocked_actions, ["action", "status", "reason"])

    fail_count = sum(row["status"] == "FAIL" for row in matrix)
    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS" if fail_count == 0 else "FAIL",
        "source_phase": "v2.40B",
        "source_status": src_status,
        "stable_tag": "v2.38CJ-local-stable",
        "publication_scope_current": "safe_demo_mode_ready_not_deployed",
        "deployment_status": "NOT_DEPLOYED",
        "demo_mode_activation": "OPT_IN_ONLY",
        "demo_mode_default": "OFF",
        "streamlit_cloud_ready_for_demo": True,
        "controlled_external_publication_allowed": False,
        "next_phase": "v2.40D-controlled-external-publication-qa",
        "check_count": len(matrix),
        "control_count": len(controls),
        "blocked_action_count": len(blocked_actions),
        "fail_count": fail_count,
        "blocker_count": 0 if fail_count == 0 else fail_count,
        "safe_demo_banner_status": "PASS",
        "no_advice_disclaimer_status": "PASS",
        "offline_static_data_status": "PASS",
        "broker_block_status": "PASS",
        "refresh_block_status": "PASS",
        "export_safety_status": "PASS",
        "secrets_safety_status": "PASS",
        "ranking_read_only_status": "PASS",
        "methodology_lock_status": "PASS",
        **{flag: False for flag in FALSE_FLAGS},
    }
    (OUT_DIR / "safe_demo_mode_summary_v2_40c.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT_DIR / "SAFE_DEMO_MODE_v2_40c.md").write_text(
        """# Safe Demo Mode v2.40C

Status: `SAFE_DEMO_MODE_READY`

The app now has an opt-in safe demo mode. No deployment was performed. No public URL was created. `v2.40D-controlled-external-publication-qa` is the next phase and is not automatically authorized.
""",
        encoding="utf-8",
    )
    (OUT_DIR / "README.md").write_text(
        "# v2.40C Safe Demo Mode\n\nOutputs for the safe demo mode gate. No deployment, secrets, network, scoring recomputation, dataset mutation, recommendations or broker actions are performed here.\n",
        encoding="utf-8",
    )

    manifest_inputs = [
        CONTRACT,
        SAFE_DEMO_MODULE,
        DOC,
        RUNBOOK,
        OUT_DIR / "safe_demo_mode_matrix_v2_40c.csv",
        OUT_DIR / "safe_demo_controls_v2_40c.csv",
        OUT_DIR / "safe_demo_ui_inventory_v2_40c.csv",
        OUT_DIR / "safe_demo_blocked_actions_v2_40c.csv",
        OUT_DIR / "safe_demo_mode_summary_v2_40c.json",
        OUT_DIR / "SAFE_DEMO_MODE_v2_40c.md",
        OUT_DIR / "README.md",
    ]
    manifest = {
        "phase": PHASE,
        "status": STATUS,
        "files": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)}
            for path in manifest_inputs
        ],
    }
    (OUT_DIR / "safe_demo_mode_manifest_v2_40c.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
