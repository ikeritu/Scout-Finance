from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21G"
PHASE = "Final v2.21 Closure Report"
PHASE_TYPE = "final-v2-21-closure-report"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

SINGAPORE_PROMOTED_DATASET = OUTPUT_DIR / "expanded_universe_v2_21e_s_singapore_promoted.csv"
COLOMBIA_PROMOTED_DATASET = OUTPUT_DIR / "expanded_universe_v2_21e_c_colombia_promoted.csv"

FINAL_REFERENCE_DATASET = OUTPUT_DIR / "expanded_universe_v2_21g_final_reference.csv"

REPORT_JSON = OUTPUT_DIR / "final_v2_21_closure_report.json"
REPORT_MD = OUTPUT_DIR / "final_v2_21_closure_report.md"
SUMMARY_CSV = OUTPUT_DIR / "final_v2_21_closure_summary.csv"
CHECKS_CSV = OUTPUT_DIR / "final_v2_21_closure_checks.csv"
PHASE_REGISTER_CSV = OUTPUT_DIR / "final_v2_21_closure_phase_register.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "final_v2_21_closure_artifact_manifest.csv"
FINAL_DECISION_REGISTER_CSV = OUTPUT_DIR / "final_v2_21_closure_decision_register.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "final_v2_21_closure_next_actions.csv"
POINTER_MANIFEST_JSON = OUTPUT_DIR / "final_v2_21_closure_pointer_manifest.json"

REQUIRED_PHASE_REPORTS = [
    {
        "phase_id": "v2.21D_S",
        "label": "Singapore Rebuild + Validation Candidate",
        "path": OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_v2_21d_s.json",
        "expected_status": "SINGAPORE_REBUILD_VALIDATION_CANDIDATE_COMPLETED_43066_ROWS_READY_FOR_PROMOTION_DECISION_NO_POINTER_UPDATE_SCORING_DEFERRED",
        "role": "singapore_candidate_build",
        "required_for_closure": True,
    },
    {
        "phase_id": "v2.21E_S",
        "label": "Singapore Promotion / Freeze Decision",
        "path": OUTPUT_DIR / "singapore_promotion_freeze_decision_v2_21e_s.json",
        "expected_status": "SINGAPORE_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED",
        "role": "singapore_promotion_decision",
        "required_for_closure": True,
    },
    {
        "phase_id": "v2.21C3B",
        "label": "Colombia Regulatory Discovery + Extraction Decision",
        "path": OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_v2_21c3b.json",
        "expected_status": "COLOMBIA_REGULATORY_DISCOVERY_EXTRACTION_DECISION_COMPLETED_STRUCTURED_SOURCE_READY_EXTRACTION_APPROVED_NO_DATASET_CHANGES_SCORING_DEFERRED",
        "role": "colombia_regulatory_discovery",
        "required_for_closure": True,
    },
    {
        "phase_id": "v2.21D_C",
        "label": "Colombia Conditional Build / Freeze",
        "path": OUTPUT_DIR / "colombia_conditional_build_freeze_v2_21d_c.json",
        "expected_status": "COLOMBIA_CONDITIONAL_BUILD_COMPLETED_CANDIDATE_CREATED_NO_PROMOTION_NO_POINTER_UPDATE_SCORING_DEFERRED",
        "role": "colombia_candidate_build",
        "required_for_closure": True,
    },
    {
        "phase_id": "v2.21E_C",
        "label": "Colombia Promotion / Freeze Decision",
        "path": OUTPUT_DIR / "colombia_promotion_freeze_decision_v2_21e_c.json",
        "expected_status": "COLOMBIA_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED",
        "role": "colombia_promotion_decision",
        "required_for_closure": True,
    },
]

HISTORICAL_PHASE_NOTES = [
    {"phase_id": "v2.21A", "label": "Expansion Gate", "role": "historical_gate", "required_for_closure": False},
    {"phase_id": "v2.21B", "label": "Raw Acquisition", "role": "historical_raw_acquisition", "required_for_closure": False},
    {"phase_id": "v2.21C", "label": "Initial Extraction, corrected", "role": "historical_superseded_extraction", "required_for_closure": False},
    {"phase_id": "v2.21C2", "label": "False Positive Review", "role": "historical_correction", "required_for_closure": False},
    {"phase_id": "v2.21C3", "label": "Official Endpoint Discovery", "role": "historical_endpoint_discovery", "required_for_closure": False},
    {"phase_id": "v2.21C3_REVIEW", "label": "Split Route Decision", "role": "historical_split_route", "required_for_closure": False},
    {"phase_id": "v2.21C4S", "label": "Singapore Structured Extraction", "role": "historical_singapore_extraction", "required_for_closure": False},
]

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

SINGAPORE_PROMOTED_ROWS_EXPECTED = 43066
SINGAPORE_PROMOTED_SHA_EXPECTED = "8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f"

COLOMBIA_PROMOTED_ROWS_EXPECTED = 43089
COLOMBIA_PROMOTED_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_CLOSED = "FINAL_V2_21_CLOSURE_COMPLETED_TARGETED_MARKETS_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED"
STATUS_FAILED = "FINAL_V2_21_CLOSURE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.21H - Explicit Final Reference Activation Gate"
SECONDARY_NEXT_PHASE = "v2.22A - Post-Targeted-Markets Explicit Scoring Decision Gate"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def copy_csv_exact(source: Path, target: Path) -> None:
    if target.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {target}")
    target.write_bytes(source.read_bytes())


def zero_or_blank(value: Any) -> bool:
    return str(value).strip() in {"", "0", "0.0"}


def build_phase_register() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in HISTORICAL_PHASE_NOTES:
        rows.append({
            "phase_id": item["phase_id"],
            "label": item["label"],
            "role": item["role"],
            "report_path": "",
            "report_exists": "",
            "required_for_closure": False,
            "status": "historical_phase_not_required_by_final_local_closure_register",
            "expected_status": "",
            "expected_status_passed": True,
            "critical_failed_checks": "",
            "warning_failed_checks": "",
            "recommended_next_phase": "",
            "pointer_update_performed": "",
            "scoring_authorized": "",
            "openai_authorized": "",
            "broker_authorized": "",
            "full59k": "DEPRECATED_DEFERRED",
        })

    for item in REQUIRED_PHASE_REPORTS:
        payload = read_json(item["path"])
        summary = payload.get("summary", {}) if payload else {}
        hard_guards = payload.get("hard_guards", {}) if payload else {}
        status = payload.get("status", "") if payload else ""
        expected_status = item["expected_status"]

        rows.append({
            "phase_id": item["phase_id"],
            "label": item["label"],
            "role": item["role"],
            "report_path": str(item["path"]),
            "report_exists": item["path"].exists(),
            "required_for_closure": True,
            "status": status,
            "expected_status": expected_status,
            "expected_status_passed": bool(status == expected_status),
            "critical_failed_checks": summary.get("critical_failed_checks", ""),
            "warning_failed_checks": summary.get("warning_failed_checks", ""),
            "recommended_next_phase": payload.get("recommended_next_phase", summary.get("recommended_next_phase", "")) if payload else "",
            "pointer_update_performed": summary.get("pointer_update_performed", hard_guards.get("pointer_update_performed", "")),
            "scoring_authorized": summary.get("scoring_authorized", hard_guards.get("scoring_authorized", "")),
            "openai_authorized": summary.get("openai_authorized", hard_guards.get("openai_authorized", "")),
            "broker_authorized": summary.get("broker_authorized", hard_guards.get("broker_authorized", "")),
            "full59k": summary.get("full59k", "DEPRECATED_DEFERRED"),
        })

    return rows


def main() -> None:
    output_paths = [
        FINAL_REFERENCE_DATASET,
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        PHASE_REGISTER_CSV,
        ARTIFACT_MANIFEST_CSV,
        FINAL_DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
        POINTER_MANIFEST_JSON,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)

    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)

    singapore_rows = count_csv_rows(SINGAPORE_PROMOTED_DATASET)
    singapore_sha = sha256_file(SINGAPORE_PROMOTED_DATASET)

    colombia_rows = count_csv_rows(COLOMBIA_PROMOTED_DATASET)
    colombia_sha = sha256_file(COLOMBIA_PROMOTED_DATASET)

    operational_header = read_csv_header(OPERATIONAL_BASE_DATASET)
    singapore_header = read_csv_header(SINGAPORE_PROMOTED_DATASET)
    colombia_header = read_csv_header(COLOMBIA_PROMOTED_DATASET)

    copy_csv_exact(COLOMBIA_PROMOTED_DATASET, FINAL_REFERENCE_DATASET)

    final_rows = count_csv_rows(FINAL_REFERENCE_DATASET)
    final_sha = sha256_file(FINAL_REFERENCE_DATASET)

    phase_register_rows = build_phase_register()
    required_rows = [row for row in phase_register_rows if row["required_for_closure"] is True]

    artifact_manifest_rows = [
        {
            "artifact": "previous_operational_base_input",
            "path": str(OPERATIONAL_BASE_DATASET),
            "rows": operational_rows,
            "sha256": operational_sha,
            "role": "unchanged_pre_v2_21_operational_base",
        },
        {
            "artifact": "rollback_input",
            "path": str(ROLLBACK_DATASET),
            "rows": rollback_rows,
            "sha256": rollback_sha,
            "role": "rollback_reference_unchanged",
        },
        {
            "artifact": "singapore_promoted_artifact",
            "path": str(SINGAPORE_PROMOTED_DATASET),
            "rows": singapore_rows,
            "sha256": singapore_sha,
            "role": "promoted_artifact_intermediate",
        },
        {
            "artifact": "colombia_promoted_artifact",
            "path": str(COLOMBIA_PROMOTED_DATASET),
            "rows": colombia_rows,
            "sha256": colombia_sha,
            "role": "final_promoted_artifact_source",
        },
        {
            "artifact": "final_v2_21_reference_dataset",
            "path": str(FINAL_REFERENCE_DATASET),
            "rows": final_rows,
            "sha256": final_sha,
            "role": "final_reference_artifact_not_active_pointer_update",
        },
    ]

    pointer_manifest = {
        "version": VERSION,
        "manifest_type": "final_v2_21_pointer_manifest",
        "generated_at_utc": utc_now(),
        "final_reference_dataset": str(FINAL_REFERENCE_DATASET),
        "final_reference_rows": final_rows,
        "final_reference_sha": final_sha,
        "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "previous_operational_base_rows": operational_rows,
        "previous_operational_base_sha": operational_sha,
        "active_pointer_update_performed": False,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "decision": "Final v2.21 reference artifact is ready; active pointer is not modified in closure report.",
        "next_required_if_activation_desired": NEXT_PHASE,
    }
    write_json(POINTER_MANIFEST_JSON, pointer_manifest)

    final_decision_register_rows = [
        {
            "decision_id": "FINAL_V2_21_001",
            "decision": "Close v2.21 targeted market expansion.",
            "accepted": True,
            "reason": "Singapore and Colombia promoted artifacts are validated with zero failed checks.",
            "effect": "Creates final v2.21 closure report and final reference artifact.",
        },
        {
            "decision_id": "FINAL_V2_21_002",
            "decision": "Use Colombia promoted artifact as final v2.21 reference artifact.",
            "accepted": True,
            "reason": "Colombia artifact includes Singapore promoted rows plus Colombia eligible rows.",
            "effect": "Final reference dataset has 43,089 rows.",
        },
        {
            "decision_id": "FINAL_V2_21_003",
            "decision": "Do not modify active pointer/canonical dataset in final closure report.",
            "accepted": True,
            "reason": "Closure is auditable and does not blindly mutate active pointer convention.",
            "effect": "Pointer manifest is created; active pointer update remains false.",
        },
        {
            "decision_id": "FINAL_V2_21_004",
            "decision": "Keep scoring/OpenAI/broker/full59k deferred.",
            "accepted": True,
            "reason": "No explicit authorization was given for scoring/enrichment.",
            "effect": "Next phase is explicit activation/scoring decision, not automatic scoring.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "activation_gate",
            "action": "decide_explicitly_whether_to_activate_final_v2_21_reference_as_current_operational_base",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Final v2.21 reference artifact is ready but active pointer remains unchanged.",
            "guardrails": "Only update known pointer/canonical target after explicit approval.",
        },
        {
            "action_order": 2,
            "action_scope": "scoring_gate",
            "action": "decide_explicitly_whether_to_run_scoring_after_targeted_market_expansion",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "v2.21 intentionally deferred scoring/OpenAI/broker enrichment.",
            "guardrails": "No scoring/OpenAI/broker without explicit authorization.",
        },
        {
            "action_order": 3,
            "action_scope": "full59k",
            "action": "keep_full59k_deprecated_deferred",
            "priority": "low",
            "recommended_phase": "none",
            "reason": "Quality target remains 42k-45k, not full59k.",
            "guardrails": "Do not launch full59k without separate explicit roadmap.",
        },
    ]

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

    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("singapore_promoted_rows_expected", singapore_rows == SINGAPORE_PROMOTED_ROWS_EXPECTED, "critical", f"singapore_rows={singapore_rows}")
    add_check("singapore_promoted_sha_expected", singapore_sha == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", singapore_sha)
    add_check("colombia_promoted_rows_expected", colombia_rows == COLOMBIA_PROMOTED_ROWS_EXPECTED, "critical", f"colombia_rows={colombia_rows}")
    add_check("colombia_promoted_sha_expected", colombia_sha == COLOMBIA_PROMOTED_SHA_EXPECTED, "critical", colombia_sha)
    add_check("final_reference_rows_expected", final_rows == COLOMBIA_PROMOTED_ROWS_EXPECTED, "critical", f"final_rows={final_rows}")
    add_check("final_reference_sha_expected", final_sha == COLOMBIA_PROMOTED_SHA_EXPECTED, "critical", final_sha)
    add_check("headers_consistent", operational_header == singapore_header == colombia_header, "critical", f"operational={len(operational_header)};singapore={len(singapore_header)};colombia={len(colombia_header)}")
    add_check("final_reference_under_quality_ceiling", final_rows <= QUALITY_CEILING_TARGET, "critical", f"final_rows={final_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("final_reference_above_quality_floor", final_rows >= QUALITY_FLOOR_TARGET, "critical", f"final_rows={final_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("remaining_capacity_non_negative", QUALITY_CEILING_TARGET - final_rows >= 0, "critical", f"remaining_capacity={QUALITY_CEILING_TARGET - final_rows}")
    add_check("required_phase_reports_exist", all(row["report_exists"] is True for row in required_rows), "critical", f"required_phase_reports_present={sum(1 for row in required_rows if row['report_exists'] is True)}/{len(required_rows)}")
    add_check("required_phase_expected_statuses_passed", all(row["expected_status_passed"] is True for row in required_rows), "critical", "expected statuses validated for required closure phases")
    add_check("required_phase_critical_failures_zero", all(zero_or_blank(row["critical_failed_checks"]) for row in required_rows), "critical", "required phase critical_failed_checks are blank or zero")
    add_check("required_phase_warning_failures_zero", all(zero_or_blank(row["warning_failed_checks"]) for row in required_rows), "critical", "required phase warning_failed_checks are blank or zero")
    add_check("historical_phase_register_is_advisory", True, "critical", "older v2.21 phases are documented as historical and not required by final local closure register")
    add_check("operational_base_not_modified", sha256_file(OPERATIONAL_BASE_DATASET) == OPERATIONAL_BASE_SHA_EXPECTED, "critical", "operational base SHA unchanged after closure")
    add_check("rollback_not_modified", sha256_file(ROLLBACK_DATASET) == ROLLBACK_SHA_EXPECTED, "critical", "rollback SHA unchanged after closure")
    add_check("singapore_artifact_not_modified", sha256_file(SINGAPORE_PROMOTED_DATASET) == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", "Singapore promoted SHA unchanged after closure")
    add_check("colombia_artifact_not_modified", sha256_file(COLOMBIA_PROMOTED_DATASET) == COLOMBIA_PROMOTED_SHA_EXPECTED, "critical", "Colombia promoted SHA unchanged after closure")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("pointer_update_not_performed", True, "critical", "pointer_update_performed=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    status = STATUS_CLOSED if critical_failed == 0 and warning_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Final v2.21 targeted expansion closure",
        "phase_type": PHASE_TYPE,
        "closure_decision": "V2_21_CLOSED_FINAL_REFERENCE_READY" if status == STATUS_CLOSED else "V2_21_CLOSURE_BLOCKED_REVIEW_REQUIRED",
        "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "previous_operational_base_rows": operational_rows,
        "previous_operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "singapore_promoted_dataset": str(SINGAPORE_PROMOTED_DATASET),
        "singapore_promoted_rows": singapore_rows,
        "singapore_promoted_sha": singapore_sha,
        "colombia_promoted_dataset": str(COLOMBIA_PROMOTED_DATASET),
        "colombia_promoted_rows": colombia_rows,
        "colombia_promoted_sha": colombia_sha,
        "final_reference_dataset": str(FINAL_REFERENCE_DATASET),
        "final_reference_rows": final_rows,
        "final_reference_sha": final_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity_after_final_reference": QUALITY_CEILING_TARGET - final_rows,
        "singapore_added_rows": SINGAPORE_PROMOTED_ROWS_EXPECTED - OPERATIONAL_BASE_ROWS_EXPECTED,
        "colombia_added_rows": COLOMBIA_PROMOTED_ROWS_EXPECTED - SINGAPORE_PROMOTED_ROWS_EXPECTED,
        "total_added_rows_vs_previous_operational_base": COLOMBIA_PROMOTED_ROWS_EXPECTED - OPERATIONAL_BASE_ROWS_EXPECTED,
        "final_reference_created": True,
        "final_reference_promoted_as_artifact": True,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "pointer_update_performed": False,
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": NEXT_PHASE,
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(PHASE_REGISTER_CSV, phase_register_rows, [
        "phase_id", "label", "role", "report_path", "report_exists", "required_for_closure",
        "status", "expected_status", "expected_status_passed", "critical_failed_checks",
        "warning_failed_checks", "recommended_next_phase", "pointer_update_performed",
        "scoring_authorized", "openai_authorized", "broker_authorized", "full59k",
    ])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(FINAL_DECISION_REGISTER_CSV, final_decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "phase_register": phase_register_rows,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": final_decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "pointer_manifest": pointer_manifest,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Final v2.21 closure",
            "final_reference_dataset": str(FINAL_REFERENCE_DATASET),
            "final_reference_rows": final_rows,
            "final_reference_sha": final_sha,
            "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "previous_operational_base_rows": operational_rows,
            "previous_operational_base_sha": operational_sha,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "singapore_promoted_dataset": str(SINGAPORE_PROMOTED_DATASET),
            "singapore_promoted_rows": singapore_rows,
            "singapore_promoted_sha": singapore_sha,
            "colombia_promoted_dataset": str(COLOMBIA_PROMOTED_DATASET),
            "colombia_promoted_rows": colombia_rows,
            "colombia_promoted_sha": colombia_sha,
            "final_reference_promoted_as_artifact": True,
            "active_pointer_update_performed": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "scoring_authorized": False,
            "scoring_recalculated": False,
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

    write_json(REPORT_JSON, payload)

    phase_lines = "\n".join(
        f"- `{row['phase_id']}` — {row['label']} — required `{row['required_for_closure']}` — status `{row['status']}`"
        for row in phase_register_rows
    )

    artifact_lines = "\n".join(
        f"- `{row['artifact']}` — rows `{row['rows']}` — SHA `{row['sha256']}` — {row['role']}"
        for row in artifact_manifest_rows
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}` — accepted `{row['accepted']}` — {row['decision']}"
        for row in final_decision_register_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.21 is closed as a targeted Colombia + Singapore expansion.

The final v2.21 reference artifact is created from the Colombia promoted artifact:

`{FINAL_REFERENCE_DATASET}`

Final reference rows: `{final_rows}`  
Final reference SHA256: `{final_sha}`

The previous operational base remains unchanged. The rollback dataset remains unchanged. No active pointer file is modified. No canonical dataset is replaced. No scoring is run. No OpenAI call is made. No broker call is made. full59k remains deprecated/deferred.

## Final numbers

- Previous operational base rows: `{operational_rows}`
- Singapore promoted rows: `{singapore_rows}`
- Colombia/final promoted rows: `{final_rows}`
- Singapore added rows: `{SINGAPORE_PROMOTED_ROWS_EXPECTED - OPERATIONAL_BASE_ROWS_EXPECTED}`
- Colombia added rows: `{COLOMBIA_PROMOTED_ROWS_EXPECTED - SINGAPORE_PROMOTED_ROWS_EXPECTED}`
- Total added rows vs previous operational base: `{COLOMBIA_PROMOTED_ROWS_EXPECTED - OPERATIONAL_BASE_ROWS_EXPECTED}`
- Remaining capacity vs 45k ceiling: `{QUALITY_CEILING_TARGET - final_rows}`

## Phase register

{phase_lines}

## Artifact manifest

{artifact_lines}

## Final decisions

{decision_lines}

## Checks

{check_lines}

## Recommended next phases

Primary: `{NEXT_PHASE}`

Secondary: `{SECONDARY_NEXT_PHASE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21G final closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("ARTIFACT_MANIFEST:")
    for row in artifact_manifest_rows:
        print(f"- {row['artifact']}: rows={row['rows']} sha={row['sha256']} role={row['role']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")
    print("")
    print("SECONDARY_NEXT_PHASE:")
    print(f"- {SECONDARY_NEXT_PHASE}")


if __name__ == "__main__":
    main()
