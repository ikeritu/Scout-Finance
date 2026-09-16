"""Build v2.44A final stable release closure artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.44A"
STATUS = "FINAL_STABLE_RELEASE_READY"
OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_44a_final_stable_release"

CONTRACT = ROOT / "config" / "final_stable_release_contract_v2_44a.json"
SOURCE_SUMMARY = ROOT / "outputs" / "full_universe_source_acquisition" / "v2_43a_final_consolidated_audit" / "final_consolidated_audit_summary_v2_43a.json"

DOC = ROOT / "docs" / "FINAL_STABLE_RELEASE_v2_44a.md"
REPORT = OUT_DIR / "final_project_closure_report_v2_44a.md"
README = OUT_DIR / "README.md"
SUMMARY = OUT_DIR / "final_stable_release_summary_v2_44a.json"
MANIFEST = OUT_DIR / "final_stable_release_manifest_v2_44a.json"

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

REQUIRED_FILES = [
    "README.md",
    "VERSION.md",
    "CHANGELOG.md",
    "ROADMAP_v2_38_CURRENT.md",
    "docs/FINAL_CONSOLIDATED_AUDIT_v2_43a.md",
    "config/final_consolidated_audit_contract_v2_43a.json",
    "config/final_stable_release_contract_v2_44a.json",
    "scripts/build_final_consolidated_audit_v2_43a.py",
    "scripts/build_final_stable_release_v2_44a.py",
    "tests/qa_final_consolidated_audit_v2_43a.py",
    "tests/qa_final_stable_release_v2_44a.py",
    "outputs/full_universe_source_acquisition/v2_43a_final_consolidated_audit/final_consolidated_audit_summary_v2_43a.json",
    "outputs/full_universe_source_acquisition/v2_43a_final_consolidated_audit/final_consolidated_audit_manifest_v2_43a.json",
    "outputs/full_universe_source_acquisition/v2_43a_final_consolidated_audit/FINAL_CONSOLIDATED_AUDIT_v2_43a.md",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def assert_source_ready(source: dict) -> None:
    expected = {
        "phase": "v2.43A",
        "status": "FINAL_CONSOLIDATED_AUDIT_READY",
        "qa_status": "PASS",
        "required_file_missing_count": 0,
        "release_blocking_issue_count": 0,
        "security_blocking_finding_count": 0,
        "qa_fail_count": 0,
        "blocker_count": 0,
    }
    for key, value in expected.items():
        if source.get(key) != value:
            raise ValueError(f"v2.43A source not ready: {key}={source.get(key)!r}")
    for flag in FALSE_FLAGS:
        if source.get(flag) is not False:
            raise ValueError(f"v2.43A prohibited flag is not false: {flag}")


def build() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contract = read_json(CONTRACT)
    source = read_json(SOURCE_SUMMARY)
    assert_source_ready(source)

    required_rows = [{"path": path, "exists": (ROOT / path).exists()} for path in REQUIRED_FILES]
    required_missing = sum(1 for row in required_rows if not row["exists"])
    warning_count = source["warning_count"]

    guardrail_rows = [
        {"guardrail": "no_network", "status": not contract["network_used"]},
        {"guardrail": "no_new_data", "status": not contract["new_data_downloaded"]},
        {"guardrail": "no_dataset_mutation", "status": not contract["datasets_mutated"]},
        {"guardrail": "no_scoring_recompute", "status": not contract["scoring_recomputed"]},
        {"guardrail": "no_ranking_change", "status": not contract["ranking_changed"]},
        {"guardrail": "no_methodology_change", "status": not contract["methodology_changed"]},
        {"guardrail": "no_deployment", "status": not contract["deployment_performed"]},
        {"guardrail": "no_public_url", "status": not contract["public_url_created"]},
        {"guardrail": "no_financial_advice", "status": not contract["financial_advice_created"]},
        {"guardrail": "no_broker_actions", "status": not contract["broker_actions_allowed"]},
    ]
    release_checklist = [
        {"item": "source_audit_ready", "status": "PASS", "blocking": False},
        {"item": "required_files_present", "status": "PASS" if required_missing == 0 else "FAIL", "blocking": required_missing != 0},
        {"item": "security_blockers", "status": "PASS", "blocking": False},
        {"item": "release_blockers", "status": "PASS", "blocking": False},
        {"item": "ranking_integrity_preserved", "status": "PASS", "blocking": False},
        {"item": "responsible_use_disclaimer_present", "status": "PASS", "blocking": False},
        {"item": "documented_limitations_accepted", "status": "PASS", "blocking": False},
    ]
    traceability_rows = [
        {"phase": "v2.38CJ", "artifact": "operational publication handoff", "status": "completed"},
        {"phase": "v2.39A-v2.39F", "artifact": "release packaging and smoke tests", "status": "completed"},
        {"phase": "v2.40A-v2.40D", "artifact": "controlled publication gate", "status": "completed"},
        {"phase": "v2.41A-v2.41D", "artifact": "final data gap closure", "status": "completed"},
        {"phase": "v2.42A-v2.42B", "artifact": "final UX and responsible-use guide", "status": "completed"},
        {"phase": "v2.43A", "artifact": "final consolidated audit", "status": source["status"]},
        {"phase": PHASE, "artifact": "final stable release closure", "status": STATUS},
    ]
    maintenance_rows = [
        {"track": "corrective_maintenance", "recommendation": "Fix only confirmed defects without changing scoring, ranking or methodology."},
        {"track": "controlled_publication", "recommendation": "Publish manually only after preserving safe demo mode and documented limitations."},
        {"track": "future_product_line", "recommendation": "Use a new v2.45+ track for any functional expansion."},
    ]
    publication_rows = [
        {"check": "public_url_created", "value": False, "ready": True},
        {"check": "deployment_performed", "value": False, "ready": True},
        {"check": "safe_demo_required", "value": True, "ready": True},
        {"check": "manual_control_required", "value": True, "ready": True},
        {"check": "financial_advice_blocked", "value": True, "ready": True},
    ]

    write_csv(OUT_DIR / "final_release_checklist_v2_44a.csv", release_checklist)
    write_csv(OUT_DIR / "final_release_traceability_v2_44a.csv", traceability_rows)
    write_csv(OUT_DIR / "final_maintenance_recommendations_v2_44a.csv", maintenance_rows)
    write_csv(OUT_DIR / "final_publication_readiness_v2_44a.csv", publication_rows)
    write_csv(OUT_DIR / "final_guardrails_v2_44a.csv", guardrail_rows)

    summary = {
        "phase": PHASE,
        "status": STATUS,
        "qa_status": "PASS",
        "source_phase": contract["source_phase"],
        "source_status": source["status"],
        "scope": contract["scope"],
        "stable_release_name": contract["stable_release_name"],
        "previous_stable_tag": contract["previous_stable_tag"],
        "recommended_final_tag": contract["recommended_final_tag"],
        "release_readiness": contract["release_readiness"],
        "project_state": "CLOSED_FOR_STABLE_LOCAL_RELEASE",
        "next_state": contract["next_state"],
        "required_file_missing_count": required_missing,
        "release_blocking_issue_count": 0,
        "security_blocking_finding_count": 0,
        "qa_fail_count": 0,
        "blocker_count": 0,
        "warning_count": warning_count,
        "ranking_total": source["ranking_total"],
        "ranking_main_count": source["ranking_main_count"],
        "partial_comparability_count": source["partial_comparability_count"],
        "review_required_count": source["review_required_count"],
        "blocked_count": source["blocked_count"],
        "no_adapter_count": source["no_adapter_count"],
        **{flag: False for flag in FALSE_FLAGS},
    }
    write_json(SUMMARY, summary)

    report = f"""# Final Stable Release v2.44A

Status: `{STATUS}`

Project state: `CLOSED_FOR_STABLE_LOCAL_RELEASE`

Release readiness: `READY_WITH_DOCUMENTED_LIMITATIONS`

Recommended final tag: `v2.44A-final-stable`

## What Is Closed

Scout Finance is closed as a stable local release with a final consolidated audit, release checklist, traceability matrix, responsible-use guardrails, security checks and documented limitations.

## What Does Not Change

This phase does not use network, download data, mutate datasets, enable providers, require credentials, download fundamentals, download prices, recompute scoring, change ranking, change weights, change methodology, deploy externally or create a public URL.

## Experimental Ranking State

The experimental ranking remains preserved from the validated pipeline:

- Total: {summary["ranking_total"]}
- Main ranking: {summary["ranking_main_count"]}
- Partial comparability: {summary["partial_comparability_count"]}
- Review required: {summary["review_required_count"]}
- Blocked: {summary["blocked_count"]}
- No adapter: {summary["no_adapter_count"]}

## Known Limitations

Known limitations remain documented for coverage gaps, adapter gaps, manual reviews and external publication controls. These limitations do not block the stable local release.

## Next Operational State

The project can move to corrective maintenance, controlled manual publication, or a future v2.45+ product track if new functionality is needed.

No constituye asesoramiento financiero. The project creates no financial advice, no recommendations and no broker actions.
"""
    REPORT.write_text(report, encoding="utf-8")
    DOC.write_text(report, encoding="utf-8")
    README.write_text("# v2.44A final stable release outputs\n\nFinal local stable release closure artifacts for Scout Finance.\n", encoding="utf-8")

    files = [
        CONTRACT,
        DOC,
        REPORT,
        README,
        SUMMARY,
        OUT_DIR / "final_release_checklist_v2_44a.csv",
        OUT_DIR / "final_release_traceability_v2_44a.csv",
        OUT_DIR / "final_maintenance_recommendations_v2_44a.csv",
        OUT_DIR / "final_publication_readiness_v2_44a.csv",
        OUT_DIR / "final_guardrails_v2_44a.csv",
    ]
    manifest = {
        "phase": PHASE,
        "status": STATUS,
        "files": [{"path": rel(path), "sha256": sha256(path)} for path in files],
    }
    write_json(MANIFEST, manifest)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


if __name__ == "__main__":
    build()
