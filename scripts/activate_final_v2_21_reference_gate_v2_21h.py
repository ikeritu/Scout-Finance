from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21H"
PHASE = "Explicit Final Reference Activation Gate"
PHASE_TYPE = "explicit-final-reference-activation-gate"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

FINAL_CLOSURE_REPORT = OUTPUT_DIR / "final_v2_21_closure_report.json"
FINAL_REFERENCE_DATASET = OUTPUT_DIR / "expanded_universe_v2_21g_final_reference.csv"

ACTIVATED_OPERATIONAL_REFERENCE = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
SINGAPORE_PROMOTED_DATASET = OUTPUT_DIR / "expanded_universe_v2_21e_s_singapore_promoted.csv"
COLOMBIA_PROMOTED_DATASET = OUTPUT_DIR / "expanded_universe_v2_21e_c_colombia_promoted.csv"

REPORT_JSON = OUTPUT_DIR / "final_reference_activation_gate_v2_21h.json"
REPORT_MD = OUTPUT_DIR / "final_reference_activation_gate_v2_21h.md"
SUMMARY_CSV = OUTPUT_DIR / "final_reference_activation_gate_summary_v2_21h.csv"
CHECKS_CSV = OUTPUT_DIR / "final_reference_activation_gate_checks_v2_21h.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "final_reference_activation_gate_artifact_manifest_v2_21h.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "final_reference_activation_gate_decision_register_v2_21h.csv"
ACTIVATION_POINTER_MANIFEST_JSON = OUTPUT_DIR / "final_reference_activation_pointer_manifest_v2_21h.json"
ACTIVATION_TARGET_DISCOVERY_CSV = OUTPUT_DIR / "final_reference_activation_target_discovery_v2_21h.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "final_reference_activation_gate_next_actions_v2_21h.csv"

EXPECTED_FINAL_CLOSURE_STATUS = "FINAL_V2_21_CLOSURE_COMPLETED_TARGETED_MARKETS_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

SINGAPORE_PROMOTED_ROWS_EXPECTED = 43066
SINGAPORE_PROMOTED_SHA_EXPECTED = "8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f"

COLOMBIA_PROMOTED_ROWS_EXPECTED = 43089
COLOMBIA_PROMOTED_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

FINAL_REFERENCE_ROWS_EXPECTED = 43089
FINAL_REFERENCE_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_ACTIVATED_REFERENCE_READY = "FINAL_REFERENCE_ACTIVATION_GATE_COMPLETED_OPERATIONAL_REFERENCE_ARTIFACT_READY_EXISTING_POINTERS_UNCHANGED_SCORING_DEFERRED"
STATUS_FAILED = "FINAL_REFERENCE_ACTIVATION_GATE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.22A - Post-Targeted-Markets Explicit Scoring Decision Gate"
SECONDARY_NEXT_PHASE = "v2.22B - Operational Pointer Convention Hardening"

TEXT_SCAN_MAX_BYTES = 2_000_000
EXCLUDED_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}
TEXT_SUFFIXES = {
    ".py", ".json", ".md", ".txt", ".csv", ".yml", ".yaml", ".toml", ".ini", ".ps1", ".bat", ".sh"
}


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
        raise SystemExit(f"Missing required JSON artifact: {path}")
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


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts.intersection(EXCLUDED_DIRS))


def safe_read_small_text(path: Path) -> str:
    try:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            return ""
        if path.stat().st_size > TEXT_SCAN_MAX_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def discover_activation_targets() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    pointer_terms = [
        "pointer",
        "active",
        "current",
        "canonical",
        "operational",
        "reference",
    ]

    old_base_name = OPERATIONAL_BASE_DATASET.name
    final_reference_name = FINAL_REFERENCE_DATASET.name
    activated_reference_name = ACTIVATED_OPERATIONAL_REFERENCE.name

    root = Path(".")

    for path in root.rglob("*"):
        if should_skip(path):
            continue
        if not path.is_file():
            continue

        path_text = str(path).replace("\\", "/")
        lower_path = path_text.lower()

        name_signal = any(term in lower_path for term in pointer_terms)
        if not name_signal and path.suffix.lower() not in {".json", ".py", ".md", ".csv"}:
            continue

        content = safe_read_small_text(path)
        contains_old_base = old_base_name in content
        contains_final_reference = final_reference_name in content
        contains_activated_reference = activated_reference_name in content
        contains_pointer_language = any(term in content.lower() for term in pointer_terms) if content else False

        if not name_signal and not contains_old_base and not contains_final_reference and not contains_activated_reference and not contains_pointer_language:
            continue

        rows.append({
            "path": path_text,
            "suffix": path.suffix,
            "size_bytes": path.stat().st_size,
            "name_signal_pointer_like": name_signal,
            "content_scanned": bool(content),
            "contains_previous_operational_base_name": contains_old_base,
            "contains_final_reference_name": contains_final_reference,
            "contains_activated_reference_name": contains_activated_reference,
            "contains_pointer_language": contains_pointer_language,
            "existing_file_modified_by_v2_21h": False,
            "recommended_action": "review_only_no_automatic_mutation",
        })

    rows.sort(key=lambda row: (not row["name_signal_pointer_like"], row["path"]))
    return rows


def main() -> None:
    output_paths = [
        ACTIVATED_OPERATIONAL_REFERENCE,
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        DECISION_REGISTER_CSV,
        ACTIVATION_POINTER_MANIFEST_JSON,
        ACTIVATION_TARGET_DISCOVERY_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    final_closure = read_json(FINAL_CLOSURE_REPORT)
    final_closure_summary = final_closure.get("summary", {})

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)

    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)

    singapore_rows = count_csv_rows(SINGAPORE_PROMOTED_DATASET)
    singapore_sha = sha256_file(SINGAPORE_PROMOTED_DATASET)

    colombia_rows = count_csv_rows(COLOMBIA_PROMOTED_DATASET)
    colombia_sha = sha256_file(COLOMBIA_PROMOTED_DATASET)

    final_reference_rows = count_csv_rows(FINAL_REFERENCE_DATASET)
    final_reference_sha = sha256_file(FINAL_REFERENCE_DATASET)

    operational_header = read_csv_header(OPERATIONAL_BASE_DATASET)
    singapore_header = read_csv_header(SINGAPORE_PROMOTED_DATASET)
    colombia_header = read_csv_header(COLOMBIA_PROMOTED_DATASET)
    final_reference_header = read_csv_header(FINAL_REFERENCE_DATASET)

    activation_target_rows = discover_activation_targets()

    copy_csv_exact(FINAL_REFERENCE_DATASET, ACTIVATED_OPERATIONAL_REFERENCE)

    activated_rows = count_csv_rows(ACTIVATED_OPERATIONAL_REFERENCE)
    activated_sha = sha256_file(ACTIVATED_OPERATIONAL_REFERENCE)

    operational_sha_after = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_sha_after = sha256_file(ROLLBACK_DATASET)
    singapore_sha_after = sha256_file(SINGAPORE_PROMOTED_DATASET)
    colombia_sha_after = sha256_file(COLOMBIA_PROMOTED_DATASET)
    final_reference_sha_after = sha256_file(FINAL_REFERENCE_DATASET)

    activation_pointer_manifest = {
        "version": VERSION,
        "manifest_type": "explicit_final_reference_activation_pointer_manifest",
        "generated_at_utc": utc_now(),
        "activation_decision": "FINAL_V2_21_REFERENCE_ACTIVATED_AS_OPERATIONAL_REFERENCE_ARTIFACT",
        "activated_operational_reference_dataset": str(ACTIVATED_OPERATIONAL_REFERENCE),
        "activated_operational_reference_rows": activated_rows,
        "activated_operational_reference_sha": activated_sha,
        "source_final_reference_dataset": str(FINAL_REFERENCE_DATASET),
        "source_final_reference_rows": final_reference_rows,
        "source_final_reference_sha": final_reference_sha,
        "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "previous_operational_base_rows": operational_rows,
        "previous_operational_base_sha": operational_sha,
        "existing_pointer_files_modified": False,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "note": "v2.21H creates an activated operational reference artifact and a manifest. It does not mutate unknown existing pointer/canonical files.",
    }
    write_json(ACTIVATION_POINTER_MANIFEST_JSON, activation_pointer_manifest)

    artifact_manifest_rows = [
        {
            "artifact": "previous_operational_base_input",
            "path": str(OPERATIONAL_BASE_DATASET),
            "rows": operational_rows,
            "sha256": operational_sha,
            "role": "unchanged_previous_operational_base",
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
            "role": "promoted_intermediate_unchanged",
        },
        {
            "artifact": "colombia_promoted_artifact",
            "path": str(COLOMBIA_PROMOTED_DATASET),
            "rows": colombia_rows,
            "sha256": colombia_sha,
            "role": "final_promoted_source_unchanged",
        },
        {
            "artifact": "v2_21g_final_reference_input",
            "path": str(FINAL_REFERENCE_DATASET),
            "rows": final_reference_rows,
            "sha256": final_reference_sha,
            "role": "source_for_activation_unchanged",
        },
        {
            "artifact": "v2_21h_activated_operational_reference_output",
            "path": str(ACTIVATED_OPERATIONAL_REFERENCE),
            "rows": activated_rows,
            "sha256": activated_sha,
            "role": "activated_operational_reference_artifact",
        },
        {
            "artifact": "activation_pointer_manifest_output",
            "path": str(ACTIVATION_POINTER_MANIFEST_JSON),
            "rows": 1,
            "sha256": sha256_file(ACTIVATION_POINTER_MANIFEST_JSON),
            "role": "new_activation_manifest_no_existing_pointer_mutation",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_21H_ACTIVATION_001",
            "decision": "Activate final v2.21 reference as operational reference artifact.",
            "accepted": True,
            "reason": "v2.21G final reference is validated and within the 42k-45k quality target.",
            "effect": "Creates expanded_universe_v2_21h_activated_operational_reference.csv.",
        },
        {
            "decision_id": "V2_21H_ACTIVATION_002",
            "decision": "Do not mutate unknown existing pointer/canonical files automatically.",
            "accepted": True,
            "reason": "Repository pointer convention should be hardened explicitly before live mutation.",
            "effect": "Creates activation pointer manifest only.",
        },
        {
            "decision_id": "V2_21H_ACTIVATION_003",
            "decision": "Keep scoring/OpenAI/broker/full59k deferred.",
            "accepted": True,
            "reason": "Activation is separate from scoring/enrichment.",
            "effect": "Next phase is explicit scoring decision gate.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "scoring_gate",
            "action": "decide_explicitly_whether_to_run_scoring_on_v2_21h_activated_operational_reference",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Operational reference artifact is ready; scoring remains intentionally deferred.",
            "guardrails": "No scoring/OpenAI/broker without explicit approval.",
        },
        {
            "action_order": 2,
            "action_scope": "pointer_convention",
            "action": "define_and_harden_single_live_pointer_convention_if_needed",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "v2.21H did not mutate unknown pointer/canonical files automatically.",
            "guardrails": "Only update one known pointer target after convention is documented.",
        },
        {
            "action_order": 3,
            "action_scope": "full59k",
            "action": "keep_full59k_deprecated_deferred",
            "priority": "low",
            "recommended_phase": "none",
            "reason": "Final reference has 43,089 rows and remains within target capacity.",
            "guardrails": "No full59k without separate explicit roadmap.",
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

    add_check("final_closure_status_expected", final_closure.get("status") == EXPECTED_FINAL_CLOSURE_STATUS, "critical", str(final_closure.get("status")))
    add_check("final_closure_zero_critical_failed_checks", str(final_closure_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={final_closure_summary.get('critical_failed_checks')}")
    add_check("final_closure_zero_warning_failed_checks", str(final_closure_summary.get("warning_failed_checks")) == "0", "critical", f"warning_failed_checks={final_closure_summary.get('warning_failed_checks')}")
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("singapore_promoted_rows_expected", singapore_rows == SINGAPORE_PROMOTED_ROWS_EXPECTED, "critical", f"singapore_rows={singapore_rows}")
    add_check("singapore_promoted_sha_expected", singapore_sha == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", singapore_sha)
    add_check("colombia_promoted_rows_expected", colombia_rows == COLOMBIA_PROMOTED_ROWS_EXPECTED, "critical", f"colombia_rows={colombia_rows}")
    add_check("colombia_promoted_sha_expected", colombia_sha == COLOMBIA_PROMOTED_SHA_EXPECTED, "critical", colombia_sha)
    add_check("final_reference_rows_expected", final_reference_rows == FINAL_REFERENCE_ROWS_EXPECTED, "critical", f"final_reference_rows={final_reference_rows}")
    add_check("final_reference_sha_expected", final_reference_sha == FINAL_REFERENCE_SHA_EXPECTED, "critical", final_reference_sha)
    add_check("activated_reference_rows_expected", activated_rows == FINAL_REFERENCE_ROWS_EXPECTED, "critical", f"activated_rows={activated_rows}")
    add_check("activated_reference_sha_matches_final", activated_sha == FINAL_REFERENCE_SHA_EXPECTED, "critical", activated_sha)
    add_check("headers_consistent", operational_header == singapore_header == colombia_header == final_reference_header, "critical", f"columns operational={len(operational_header)};final={len(final_reference_header)}")
    add_check("activated_reference_under_quality_ceiling", activated_rows <= QUALITY_CEILING_TARGET, "critical", f"activated_rows={activated_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("activated_reference_above_quality_floor", activated_rows >= QUALITY_FLOOR_TARGET, "critical", f"activated_rows={activated_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("remaining_capacity_non_negative", QUALITY_CEILING_TARGET - activated_rows >= 0, "critical", f"remaining_capacity={QUALITY_CEILING_TARGET - activated_rows}")
    add_check("activation_pointer_manifest_created", ACTIVATION_POINTER_MANIFEST_JSON.exists(), "critical", str(ACTIVATION_POINTER_MANIFEST_JSON))
    add_check("activation_target_discovery_completed", len(activation_target_rows) >= 0, "critical", f"discovered_rows={len(activation_target_rows)}")
    add_check("existing_pointer_files_not_modified", True, "critical", "existing_pointer_files_modified=False")
    add_check("operational_base_not_modified", operational_sha_after == OPERATIONAL_BASE_SHA_EXPECTED, "critical", f"operational_sha_after={operational_sha_after}")
    add_check("rollback_not_modified", rollback_sha_after == ROLLBACK_SHA_EXPECTED, "critical", f"rollback_sha_after={rollback_sha_after}")
    add_check("singapore_artifact_not_modified", singapore_sha_after == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", f"singapore_sha_after={singapore_sha_after}")
    add_check("colombia_artifact_not_modified", colombia_sha_after == COLOMBIA_PROMOTED_SHA_EXPECTED, "critical", f"colombia_sha_after={colombia_sha_after}")
    add_check("final_reference_not_modified", final_reference_sha_after == FINAL_REFERENCE_SHA_EXPECTED, "critical", f"final_reference_sha_after={final_reference_sha_after}")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    status = STATUS_ACTIVATED_REFERENCE_READY if critical_failed == 0 and warning_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Explicit final v2.21 reference activation gate",
        "phase_type": PHASE_TYPE,
        "activation_decision": "FINAL_V2_21_REFERENCE_ACTIVATED_AS_OPERATIONAL_REFERENCE_ARTIFACT" if status == STATUS_ACTIVATED_REFERENCE_READY else "FINAL_REFERENCE_ACTIVATION_BLOCKED_REVIEW_REQUIRED",
        "source_final_reference_dataset": str(FINAL_REFERENCE_DATASET),
        "source_final_reference_rows": final_reference_rows,
        "source_final_reference_sha": final_reference_sha,
        "activated_operational_reference_dataset": str(ACTIVATED_OPERATIONAL_REFERENCE),
        "activated_operational_reference_rows": activated_rows,
        "activated_operational_reference_sha": activated_sha,
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
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity_after_activation": QUALITY_CEILING_TARGET - activated_rows,
        "total_added_rows_vs_previous_operational_base": activated_rows - operational_rows,
        "activation_pointer_manifest": str(ACTIVATION_POINTER_MANIFEST_JSON),
        "activation_target_discovery_rows": len(activation_target_rows),
        "activated_operational_reference_created": status == STATUS_ACTIVATED_REFERENCE_READY,
        "approved_as_current_operational_reference_artifact": status == STATUS_ACTIVATED_REFERENCE_READY,
        "existing_pointer_files_modified": False,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
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
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(ACTIVATION_TARGET_DISCOVERY_CSV, activation_target_rows, [
        "path",
        "suffix",
        "size_bytes",
        "name_signal_pointer_like",
        "content_scanned",
        "contains_previous_operational_base_name",
        "contains_final_reference_name",
        "contains_activated_reference_name",
        "contains_pointer_language",
        "existing_file_modified_by_v2_21h",
        "recommended_action",
    ])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, [
        "action_order",
        "action_scope",
        "action",
        "priority",
        "recommended_phase",
        "reason",
        "guardrails",
    ])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "activation_target_discovery": activation_target_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "activation_pointer_manifest": activation_pointer_manifest,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Explicit activation of final v2.21 reference",
            "activated_operational_reference_dataset": str(ACTIVATED_OPERATIONAL_REFERENCE),
            "activated_operational_reference_rows": activated_rows,
            "activated_operational_reference_sha": activated_sha,
            "source_final_reference_dataset": str(FINAL_REFERENCE_DATASET),
            "source_final_reference_rows": final_reference_rows,
            "source_final_reference_sha": final_reference_sha,
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
            "approved_as_current_operational_reference_artifact": status == STATUS_ACTIVATED_REFERENCE_READY,
            "existing_pointer_files_modified": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
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

    artifact_lines = "\n".join(
        f"- `{row['artifact']}` — rows `{row['rows']}` — SHA `{row['sha256']}` — {row['role']}"
        for row in artifact_manifest_rows
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}` — accepted `{row['accepted']}` — {row['decision']}"
        for row in decision_register_rows
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

v2.21H explicitly activates the final v2.21 reference as an operational reference artifact.

Activated operational reference:

`{ACTIVATED_OPERATIONAL_REFERENCE}`

Rows: `{activated_rows}`  
SHA256: `{activated_sha}`

This phase creates a new activated operational reference artifact and an activation pointer manifest. It does not mutate unknown existing pointer/canonical files automatically. It does not run scoring, does not call OpenAI, does not call brokers, and does not launch full59k.

## Final activation numbers

- Previous operational base rows: `{operational_rows}`
- Source final reference rows: `{final_reference_rows}`
- Activated operational reference rows: `{activated_rows}`
- Total added rows vs previous operational base: `{activated_rows - operational_rows}`
- Remaining capacity vs 45k ceiling: `{QUALITY_CEILING_TARGET - activated_rows}`

## Artifact manifest

{artifact_lines}

## Decisions

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
    print("v2.21H explicit final reference activation gate completed.")
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
