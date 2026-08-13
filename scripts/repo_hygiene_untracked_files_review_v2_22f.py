from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.22F"
PHASE = "Repo Hygiene / Untracked Files Review"
PHASE_TYPE = "repo-hygiene-untracked-files-review"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

FREEZE_REPORT = OUTPUT_DIR / "scoring_promotion_freeze_decision_v2_22e.json"
CURRENT_POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
SCORING_OUTPUT = OUTPUT_DIR / "scoring_dry_run_no_promotion_scores_v2_22d.csv"

REPORT_JSON = OUTPUT_DIR / "repo_hygiene_untracked_files_review_v2_22f.json"
REPORT_MD = OUTPUT_DIR / "repo_hygiene_untracked_files_review_v2_22f.md"
SUMMARY_CSV = OUTPUT_DIR / "repo_hygiene_untracked_files_review_summary_v2_22f.csv"
CHECKS_CSV = OUTPUT_DIR / "repo_hygiene_untracked_files_review_checks_v2_22f.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "repo_hygiene_untracked_files_review_artifact_manifest_v2_22f.csv"
UNTRACKED_CLASSIFICATION_CSV = OUTPUT_DIR / "repo_hygiene_untracked_files_review_untracked_classification_v2_22f.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "repo_hygiene_untracked_files_review_decision_register_v2_22f.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "repo_hygiene_untracked_files_review_next_actions_v2_22f.csv"

EXPECTED_FREEZE_STATUS = "SCORING_PROMOTION_FREEZE_DECISION_COMPLETED_DRY_RUN_FROZEN_NOT_PROMOTED"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

SCORING_OUTPUT_ROWS_EXPECTED = 33498
SCORING_OUTPUT_SHA_EXPECTED = "a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1"

EXPECTED_UNTRACKED_REVIEW_TARGETS = [
    Path("Auditoria_Scout_Finance.docx"),
    OUTPUT_DIR / "country_breakdown_by_country.csv",
    OUTPUT_DIR / "country_breakdown_by_currency.csv",
    OUTPUT_DIR / "country_breakdown_by_exchange.csv",
    OUTPUT_DIR / "country_breakdown_by_mic.csv",
    OUTPUT_DIR / "country_breakdown_by_source_provider.csv",
]

STATUS_COMPLETED = "REPO_HYGIENE_UNTRACKED_FILES_REVIEW_COMPLETED_UNTRACKED_FILES_CLASSIFIED_NO_AUTO_ADD"
STATUS_FAILED = "REPO_HYGIENE_UNTRACKED_FILES_REVIEW_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.23A - Scoring Model Calibration Roadmap"
SECONDARY_NEXT_PHASE = "v2.23B - Metadata Coverage Improvement Plan"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        raise SystemExit(f"Missing required CSV artifact: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def git_status_porcelain() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line.rstrip("\n") for line in result.stdout.splitlines() if line.strip()]


def classify_untracked_target(path: Path) -> dict[str, Any]:
    exists = path.exists()
    suffix = path.suffix.lower()

    if suffix == ".docx":
        file_kind = "document"
        recommendation = "defer_do_not_add_automatically"
        reason = "Manual audit document. Not part of deterministic pipeline outputs and should not be committed without explicit review."
        rows = ""
    elif suffix == ".csv" and path.name.startswith("country_breakdown_by_"):
        file_kind = "ad_hoc_country_breakdown_csv"
        recommendation = "defer_do_not_add_automatically"
        reason = "Ad hoc breakdown artifact. Useful for local inspection but not currently part of versioned v2.22 pipeline."
        rows = count_csv_rows(path) if exists else ""
    else:
        file_kind = "unknown_untracked_file"
        recommendation = "manual_review_required"
        reason = "File does not match known v2.22F review target pattern."
        rows = count_csv_rows(path) if exists and suffix == ".csv" else ""

    return {
        "path": str(path),
        "exists": exists,
        "file_kind": file_kind,
        "size_bytes": path.stat().st_size if exists else "",
        "rows": rows,
        "sha256": sha256_file(path) if exists else "",
        "recommendation": recommendation,
        "reason": reason,
    }


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        UNTRACKED_CLASSIFICATION_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    freeze_report = read_json(FREEZE_REPORT)
    freeze_summary = freeze_report.get("summary", {})
    pointer = read_json(CURRENT_POINTER)

    current_rows = count_csv_rows(CURRENT_DATASET)
    current_sha = sha256_file(CURRENT_DATASET)

    scoring_rows = count_csv_rows(SCORING_OUTPUT)
    scoring_sha = sha256_file(SCORING_OUTPUT)

    freeze_sha = sha256_file(FREEZE_REPORT)
    pointer_sha = sha256_file(CURRENT_POINTER)

    status_lines_before_outputs = git_status_porcelain()

    tracked_modifications = [
        line
        for line in status_lines_before_outputs
        if not line.startswith("?? ")
    ]

    untracked_paths_before_outputs = [
        Path(line[3:])
        for line in status_lines_before_outputs
        if line.startswith("?? ")
    ]

    expected_target_set = {str(path) for path in EXPECTED_UNTRACKED_REVIEW_TARGETS}
    phase_script = Path("scripts/repo_hygiene_untracked_files_review_v2_22f.py")

    allowed_phase_untracked = {str(phase_script)}

    unexpected_untracked_before_outputs = [
        str(path)
        for path in untracked_paths_before_outputs
        if str(path) not in expected_target_set and str(path) not in allowed_phase_untracked
    ]

    classification_rows = [classify_untracked_target(path) for path in EXPECTED_UNTRACKED_REVIEW_TARGETS]

    expected_targets_existing = sum(1 for row in classification_rows if row["exists"])
    docx_targets = sum(1 for row in classification_rows if row["file_kind"] == "document")
    breakdown_targets = sum(1 for row in classification_rows if row["file_kind"] == "ad_hoc_country_breakdown_csv")
    auto_add_recommended = sum(1 for row in classification_rows if row["recommendation"] == "add_to_git")
    defer_recommended = sum(1 for row in classification_rows if row["recommendation"] == "defer_do_not_add_automatically")
    manual_review_required = sum(1 for row in classification_rows if row["recommendation"] == "manual_review_required")

    checks: list[dict[str, Any]] = []
    critical_failed = 0
    warning_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed, warning_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        if severity == "warning" and not passed:
            warning_failed += 1

        checks.append({
            "check": check,
            "passed": bool(passed),
            "severity": severity,
            "detail": detail,
        })

    add_check("freeze_status_expected", freeze_report.get("status") == EXPECTED_FREEZE_STATUS, "critical", str(freeze_report.get("status")))
    add_check("freeze_critical_failed_checks_zero", str(freeze_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={freeze_summary.get('critical_failed_checks')}")
    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("scoring_rows_expected", scoring_rows == SCORING_OUTPUT_ROWS_EXPECTED, "critical", f"scoring_rows={scoring_rows}")
    add_check("scoring_sha_expected", scoring_sha == SCORING_OUTPUT_SHA_EXPECTED, "critical", scoring_sha)
    add_check("expected_untracked_targets_present", expected_targets_existing == len(EXPECTED_UNTRACKED_REVIEW_TARGETS), "critical", f"present={expected_targets_existing};expected={len(EXPECTED_UNTRACKED_REVIEW_TARGETS)}")
    add_check("tracked_modifications_absent", len(tracked_modifications) == 0, "critical", f"tracked_modifications={tracked_modifications}")
    add_check("unexpected_untracked_absent_before_outputs", len(unexpected_untracked_before_outputs) == 0, "critical", f"unexpected_untracked={unexpected_untracked_before_outputs}")
    add_check("auto_add_not_recommended", auto_add_recommended == 0, "critical", f"auto_add_recommended={auto_add_recommended}")
    add_check("defer_recommendations_expected", defer_recommended == len(EXPECTED_UNTRACKED_REVIEW_TARGETS), "critical", f"defer_recommended={defer_recommended}")
    add_check("manual_review_required_zero", manual_review_required == 0, "critical", f"manual_review_required={manual_review_required}")
    add_check("canonical_dataset_not_modified", sha256_file(CURRENT_DATASET) == CURRENT_SHA_EXPECTED, "critical", f"current_sha_after={sha256_file(CURRENT_DATASET)}")
    add_check("scoring_output_not_modified", sha256_file(SCORING_OUTPUT) == SCORING_OUTPUT_SHA_EXPECTED, "critical", f"scoring_sha_after={sha256_file(SCORING_OUTPUT)}")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    status = STATUS_COMPLETED if critical_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Repo hygiene review of persistent untracked files",
        "phase_type": PHASE_TYPE,
        "hygiene_decision": "UNTRACKED_FILES_CLASSIFIED_NO_AUTO_ADD" if status == STATUS_COMPLETED else "REPO_HYGIENE_REVIEW_FAILED",
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows,
        "current_dataset_sha": current_sha,
        "scoring_output": str(SCORING_OUTPUT),
        "scoring_output_rows": scoring_rows,
        "scoring_output_sha": scoring_sha,
        "expected_untracked_targets": len(EXPECTED_UNTRACKED_REVIEW_TARGETS),
        "expected_untracked_targets_existing": expected_targets_existing,
        "docx_targets": docx_targets,
        "country_breakdown_csv_targets": breakdown_targets,
        "auto_add_recommended": auto_add_recommended,
        "defer_do_not_add_automatically": defer_recommended,
        "manual_review_required": manual_review_required,
        "tracked_modifications": len(tracked_modifications),
        "unexpected_untracked_before_outputs": len(unexpected_untracked_before_outputs),
        "untracked_files_committed": False,
        "gitignore_modified": False,
        "git_info_exclude_modified": False,
        "canonical_dataset_modified": False,
        "scoring_output_modified": False,
        "openai_authorized": False,
        "openai_called": False,
        "broker_authorized": False,
        "broker_called": False,
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": NEXT_PHASE,
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    decision_register_rows = [
        {
            "decision_id": "V2_22F_HYGIENE_001",
            "decision": "Classify persistent untracked files but do not add them automatically.",
            "accepted": True,
            "reason": "The files are ad hoc/manual review artifacts outside the deterministic v2.22 pipeline.",
            "effect": "No automatic git add for docx or country_breakdown files.",
        },
        {
            "decision_id": "V2_22F_HYGIENE_002",
            "decision": "Keep Auditoria_Scout_Finance.docx out of the repo unless explicitly requested.",
            "accepted": True,
            "reason": "Manual document; could be useful, but it is not a required pipeline artifact.",
            "effect": "Recommendation is defer_do_not_add_automatically.",
        },
        {
            "decision_id": "V2_22F_HYGIENE_003",
            "decision": "Keep country_breakdown_by_*.csv files out of this commit unless converted into a formal phase output later.",
            "accepted": True,
            "reason": "They are ad hoc breakdowns, not part of the versioned v2.22 outputs.",
            "effect": "Recommendation is defer_do_not_add_automatically.",
        },
        {
            "decision_id": "V2_22F_HYGIENE_004",
            "decision": "Do not modify .gitignore or .git/info/exclude in this phase.",
            "accepted": True,
            "reason": "The safest hygiene action is explicit classification first, not silently hiding files.",
            "effect": "gitignore_modified=False; git_info_exclude_modified=False.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "scoring_model",
            "action": "plan_scoring_model_calibration_before_any_production_promotion",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "v2.22E froze dry-run scoring as non-promoted reference.",
            "guardrails": "No production scoring or canonical replacement without explicit future gate.",
        },
        {
            "action_order": 2,
            "action_scope": "metadata_coverage",
            "action": "improve_country_currency_mic_asset_type_coverage_before_production_scoring",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "v2.22D showed top_country_by_scorable_rows=__MISSING__.",
            "guardrails": "No full59k; no broker/OpenAI unless separately approved.",
        },
    ]

    artifact_manifest_rows = [
        {
            "artifact": "freeze_report_input",
            "path": str(FREEZE_REPORT),
            "rows": 1,
            "sha256": freeze_sha,
            "role": "input_freeze_report",
        },
        {
            "artifact": "current_operational_pointer_input",
            "path": str(CURRENT_POINTER),
            "rows": 1,
            "sha256": pointer_sha,
            "role": "input_pointer",
        },
        {
            "artifact": "current_dataset_input",
            "path": str(CURRENT_DATASET),
            "rows": current_rows,
            "sha256": current_sha,
            "role": "input_dataset_no_modification",
        },
        {
            "artifact": "scoring_output_input",
            "path": str(SCORING_OUTPUT),
            "rows": scoring_rows,
            "sha256": scoring_sha,
            "role": "input_scoring_output_no_modification",
        },
    ]

    write_csv(UNTRACKED_CLASSIFICATION_CSV, classification_rows, [
        "path",
        "exists",
        "file_kind",
        "size_bytes",
        "rows",
        "sha256",
        "recommendation",
        "reason",
    ])

    untracked_classification_sha = sha256_file(UNTRACKED_CLASSIFICATION_CSV)

    artifact_manifest_rows.append({
        "artifact": "untracked_classification_output",
        "path": str(UNTRACKED_CLASSIFICATION_CSV),
        "rows": len(classification_rows),
        "sha256": untracked_classification_sha,
        "role": "repo_hygiene_classification_output",
    })

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    report = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "git_status_porcelain_before_outputs": status_lines_before_outputs,
        "tracked_modifications": tracked_modifications,
        "unexpected_untracked_before_outputs": unexpected_untracked_before_outputs,
        "untracked_classification": classification_rows,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "untracked_files_committed": False,
            "auto_add_recommended": auto_add_recommended,
            "gitignore_modified": False,
            "git_info_exclude_modified": False,
            "current_dataset": str(CURRENT_DATASET),
            "current_dataset_rows": current_rows,
            "current_dataset_sha": current_sha,
            "scoring_output": str(SCORING_OUTPUT),
            "scoring_output_rows": scoring_rows,
            "scoring_output_sha": scoring_sha,
            "canonical_dataset_modified": False,
            "scoring_output_modified": False,
            "production_scoring_authorized": False,
            "openai_authorized": False,
            "openai_called": False,
            "broker_authorized": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
            "history_rewrite_performed": False,
            "force_push_required": False,
        },
        "recommended_next_phase": NEXT_PHASE,
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_json(REPORT_JSON, report)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    classification_lines = "\n".join(
        f"- `{row['path']}` — {row['recommendation']} — {row['reason']}"
        for row in classification_rows
    )

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{report["generated_at_utc"]}`

## Decision

Repo hygiene decision: **{summary["hygiene_decision"]}**

The persistent untracked files are classified but not automatically added to Git.

## Untracked classification

{classification_lines}

## Guardrails

- Untracked files committed: `False`
- Auto-add recommended: `{auto_add_recommended}`
- .gitignore modified: `False`
- .git/info/exclude modified: `False`
- Canonical dataset modified: `False`
- Scoring output modified: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

{check_lines}

## Recommended next phase

Primary: `{NEXT_PHASE}`

Secondary: `{SECONDARY_NEXT_PHASE}`
""",
    )

    print("")
    print("v2.22F repo hygiene / untracked files review completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("UNTRACKED_CLASSIFICATION:")
    for row in classification_rows:
        print(f"- {row['path']}: {row['recommendation']} ({row['reason']})")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
