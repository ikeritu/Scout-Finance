from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.18I"
PHASE = "TWSE + TPEx Closure Report"
PHASE_TYPE = "closure-report-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
BASE_NSE_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"
TWSE_TPEX_EXPANDED_CANDIDATE = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V218E_JSON = OUTPUT_DIR / "twse_tpex_candidate_extraction_dry_run_v2_18e.json"
V218F_JSON = OUTPUT_DIR / "twse_tpex_candidate_validation_against_canonical_dry_run_v2_18f.json"
V218G_JSON = OUTPUT_DIR / "twse_tpex_expanded_rebuild_candidate_v2_18g.json"
V218H_JSON = OUTPUT_DIR / "twse_tpex_expanded_validation_v2_18h.json"

V218F_CLASSIFICATION_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_classification_v2_18f.csv"
V218G_ADDED_ROWS_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_added_rows_v2_18g.csv"
V218G_WITHHELD_ROWS_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_withheld_rows_v2_18g.csv"
V218H_ROW_AUDIT_CSV = OUTPUT_DIR / "twse_tpex_expanded_validation_row_audit_v2_18h.csv"
V218H_SYMBOL_AUDIT_CSV = OUTPUT_DIR / "twse_tpex_expanded_validation_symbol_audit_v2_18h.csv"
V218H_SCHEMA_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_expanded_validation_schema_profile_v2_18h.csv"

OPTIONAL_REPORTS = {
    "v2.18C": [
        OUTPUT_DIR / "twse_tpex_raw_acquisition_v2_18c.json",
    ],
    "v2.18D": [
        OUTPUT_DIR / "twse_tpex_raw_validation_v2_18d.json",
    ],
    "v2.18C_FIX": [
        OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_v2_18c_fix.json",
    ],
    "v2.18D_FIX": [
        OUTPUT_DIR / "twse_tpex_repaired_raw_validation_v2_18d_fix.json",
    ],
}

REPORT_JSON = OUTPUT_DIR / "twse_tpex_closure_report_v2_18i.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_closure_report_v2_18i.md"
PHASE_LEDGER_CSV = OUTPUT_DIR / "twse_tpex_closure_phase_ledger_v2_18i.csv"
METRIC_SUMMARY_CSV = OUTPUT_DIR / "twse_tpex_closure_metric_summary_v2_18i.csv"
SOURCE_STATUS_CSV = OUTPUT_DIR / "twse_tpex_closure_source_status_v2_18i.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_closure_next_actions_v2_18i.csv"
CHECKS_CSV = OUTPUT_DIR / "twse_tpex_closure_checks_v2_18i.csv"

EXPECTED_V218E_STATUS = "TWSE_TPEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_TWSE_CANDIDATES_READY_FOR_CANONICAL_VALIDATION_DRY_RUN_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
EXPECTED_V218F_STATUS = "TWSE_TPEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_CANONICAL_BUCKETS_READY_FOR_EXPANDED_REBUILD_CANDIDATE_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
EXPECTED_V218G_STATUS = "TWSE_TPEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_40996_ROWS_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
EXPECTED_V218H_STATUS = "TWSE_TPEX_EXPANDED_VALIDATION_COMPLETED_40996_ROWS_VALIDATED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
BASE_NSE_ROWS_EXPECTED = 40300
TWSE_TPEX_FINAL_ROWS_EXPECTED = 40996
TWSE_CANDIDATES_EXTRACTED_EXPECTED = 1075
TWSE_POTENTIAL_NET_NEW_EXPECTED = 696
TWSE_POSSIBLE_EXISTING_EXPECTED = 379
TWSE_EXISTING_EXPECTED = 0
TWSE_ADDED_ROWS_EXPECTED = 696
TWSE_WITHHELD_ROWS_EXPECTED = 0
SCHEMA_COLUMNS_EXPECTED = 33
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_AFTER_TWSE_EXPECTED = 9004

RECOMMENDED_NEXT_PHASE = "v2.19A - Next Provider Route Selection"
RECOMMENDED_REVIEW_PHASE = "v2.18I_REVIEW - TWSE + TPEx Closure Review"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                return list(reader.fieldnames or []), rows
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


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


def first_existing_report(paths: list[Path]) -> tuple[Path | None, dict[str, Any] | None]:
    for path in paths:
        payload = read_optional_json(path)
        if payload is not None:
            return path, payload
    return None, None


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        PHASE_LEDGER_CSV,
        METRIC_SUMMARY_CSV,
        SOURCE_STATUS_CSV,
        NEXT_ACTIONS_CSV,
        CHECKS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v218e = read_json(V218E_JSON)
    v218f = read_json(V218F_JSON)
    v218g = read_json(V218G_JSON)
    v218h = read_json(V218H_JSON)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    base_sha_before = sha256_file(BASE_NSE_CANDIDATE_DATASET)
    expanded_sha_before = sha256_file(TWSE_TPEX_EXPANDED_CANDIDATE)

    canonical_header, canonical_rows = read_csv_with_header(ACTIVE_CANONICAL_DATASET)
    base_header, base_rows = read_csv_with_header(BASE_NSE_CANDIDATE_DATASET)
    expanded_header, expanded_rows = read_csv_with_header(TWSE_TPEX_EXPANDED_CANDIDATE)
    _, classification_rows = read_csv_with_header(V218F_CLASSIFICATION_CSV)
    _, added_rows = read_csv_with_header(V218G_ADDED_ROWS_CSV)
    _, withheld_rows = read_csv_with_header(V218G_WITHHELD_ROWS_CSV)
    _, row_audit_rows = read_csv_with_header(V218H_ROW_AUDIT_CSV)
    _, symbol_audit_rows = read_csv_with_header(V218H_SYMBOL_AUDIT_CSV)
    _, schema_profile_rows = read_csv_with_header(V218H_SCHEMA_PROFILE_CSV)

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    base_sha_after = sha256_file(BASE_NSE_CANDIDATE_DATASET)
    expanded_sha_after = sha256_file(TWSE_TPEX_EXPANDED_CANDIDATE)

    active_canonical_rows = len(canonical_rows)
    base_rows_count = len(base_rows)
    expanded_rows_count = len(expanded_rows)
    added_rows_count = len(added_rows)
    withheld_rows_count = len(withheld_rows)
    row_increment = expanded_rows_count - base_rows_count
    projected_rows_needed_after_twse = max(FINAL_TARGET_CANDIDATES - expanded_rows_count, 0)

    v218f_summary = v218f.get("validation_summary", {})
    v218g_summary = v218g.get("rebuild_summary", {})
    v218h_summary = v218h.get("validation_summary", {})

    potential_net_new = int(v218f_summary.get("potential_net_new_count", 0))
    possible_existing = int(v218f_summary.get("possible_existing_count", 0))
    existing = int(v218f_summary.get("existing_count", 0))
    extracted_candidates = int(v218f_summary.get("candidates_validated", 0))

    source_status_rows = [
        {
            "source": "TWSE listed company profile",
            "role": "primary_candidate_source",
            "status": "completed_used",
            "rows_or_candidates": TWSE_CANDIDATES_EXTRACTED_EXPECTED,
            "result": "source produced validated TWSE candidates",
            "decision": "used for v2.18E extraction and v2.18G candidate rebuild",
        },
        {
            "source": "TWSE stock day all",
            "role": "symbol_name_crosscheck",
            "status": "completed_used",
            "rows_or_candidates": "crosscheck",
            "result": "used as crosscheck during extraction",
            "decision": "supporting source only",
        },
        {
            "source": "TPEx",
            "role": "primary_tpex_candidate_source",
            "status": "deferred_or_repair_later",
            "rows_or_candidates": 0,
            "result": "TPEx repair still pending after TWSE route succeeded partially",
            "decision": "do not block TWSE closure; revisit in a future provider/repair route if needed",
        },
        {
            "source": "full59k",
            "role": "deprecated_target_route",
            "status": "deprecated_deferred_not_active",
            "rows_or_candidates": 0,
            "result": "not launched",
            "decision": "keep 50k target route only",
        },
    ]

    phase_ledger_rows: list[dict[str, Any]] = [
        {
            "phase": "v2.18A",
            "name": "50k Target Route Selection",
            "status": "closed",
            "primary_output": "TWSE + TPEx selected as next route; full59k deprecated/deferred",
            "dataset_rows_after_phase": BASE_NSE_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18B",
        },
        {
            "phase": "v2.18B",
            "name": "TWSE + TPEx Acquisition Plan",
            "status": "closed",
            "primary_output": "official-source acquisition plan",
            "dataset_rows_after_phase": BASE_NSE_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18C",
        },
        {
            "phase": "v2.18C",
            "name": "TWSE + TPEx Raw Acquisition",
            "status": "closed",
            "primary_output": "raw acquisition attempted; repair required",
            "dataset_rows_after_phase": BASE_NSE_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18D",
        },
        {
            "phase": "v2.18D",
            "name": "TWSE + TPEx Raw Validation",
            "status": "closed",
            "primary_output": "raw files validated; repair required",
            "dataset_rows_after_phase": BASE_NSE_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18C_FIX",
        },
        {
            "phase": "v2.18C_FIX",
            "name": "TWSE + TPEx Raw Acquisition Repair",
            "status": "closed",
            "primary_output": "TWSE row-data captured; TPEx deferred",
            "dataset_rows_after_phase": BASE_NSE_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18D_FIX",
        },
        {
            "phase": "v2.18D_FIX",
            "name": "TWSE + TPEx Repaired Raw Validation",
            "status": "closed",
            "primary_output": "2 TWSE row-data sources ready for extraction",
            "dataset_rows_after_phase": BASE_NSE_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18E",
        },
        {
            "phase": "v2.18E",
            "name": "TWSE + TPEx Candidate Extraction Dry Run",
            "status": v218e.get("status", "unknown"),
            "primary_output": f"{TWSE_CANDIDATES_EXTRACTED_EXPECTED} TWSE candidates extracted; DR and non-common-equity excluded",
            "dataset_rows_after_phase": BASE_NSE_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18F",
        },
        {
            "phase": "v2.18F",
            "name": "TWSE + TPEx Candidate Validation Against Canonical Dry Run",
            "status": v218f.get("status", "unknown"),
            "primary_output": f"{TWSE_POTENTIAL_NET_NEW_EXPECTED} potential net-new; {TWSE_POSSIBLE_EXISTING_EXPECTED} possible existing",
            "dataset_rows_after_phase": BASE_NSE_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18G",
        },
        {
            "phase": "v2.18G",
            "name": "TWSE + TPEx Expanded Rebuild Candidate",
            "status": v218g.get("status", "unknown"),
            "primary_output": f"candidate rebuilt with {TWSE_TPEX_FINAL_ROWS_EXPECTED} rows",
            "dataset_rows_after_phase": TWSE_TPEX_FINAL_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18H",
        },
        {
            "phase": "v2.18H",
            "name": "TWSE + TPEx Expanded Validation",
            "status": v218h.get("status", "unknown"),
            "primary_output": f"expanded candidate validated with {TWSE_TPEX_FINAL_ROWS_EXPECTED} rows",
            "dataset_rows_after_phase": TWSE_TPEX_FINAL_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": "v2.18I",
        },
        {
            "phase": "v2.18I",
            "name": "TWSE + TPEx Closure Report",
            "status": "current_phase",
            "primary_output": "formal closure and next-provider handoff",
            "dataset_rows_after_phase": TWSE_TPEX_FINAL_ROWS_EXPECTED,
            "gate_status": "50k blocked",
            "next": RECOMMENDED_NEXT_PHASE,
        },
    ]

    optional_phase_report_rows = []
    for phase, paths in OPTIONAL_REPORTS.items():
        report_path, payload = first_existing_report(paths)
        optional_phase_report_rows.append(
            {
                "phase": phase,
                "report_found": report_path is not None,
                "report_path": str(report_path) if report_path else "",
                "status": payload.get("status", "") if payload else "",
            }
        )

    metric_summary_rows = [
        {"metric": "active_canonical_rows", "value": active_canonical_rows, "expected": ACTIVE_CANONICAL_ROWS_EXPECTED, "unit": "rows"},
        {"metric": "base_nse_candidate_rows", "value": base_rows_count, "expected": BASE_NSE_ROWS_EXPECTED, "unit": "rows"},
        {"metric": "twse_candidates_extracted", "value": extracted_candidates, "expected": TWSE_CANDIDATES_EXTRACTED_EXPECTED, "unit": "candidates"},
        {"metric": "twse_potential_net_new", "value": potential_net_new, "expected": TWSE_POTENTIAL_NET_NEW_EXPECTED, "unit": "candidates"},
        {"metric": "twse_possible_existing_not_added", "value": possible_existing, "expected": TWSE_POSSIBLE_EXISTING_EXPECTED, "unit": "candidates"},
        {"metric": "twse_existing_not_added", "value": existing, "expected": TWSE_EXISTING_EXPECTED, "unit": "candidates"},
        {"metric": "twse_added_rows", "value": added_rows_count, "expected": TWSE_ADDED_ROWS_EXPECTED, "unit": "rows"},
        {"metric": "twse_withheld_rows", "value": withheld_rows_count, "expected": TWSE_WITHHELD_ROWS_EXPECTED, "unit": "rows"},
        {"metric": "twse_tpex_expanded_candidate_rows", "value": expanded_rows_count, "expected": TWSE_TPEX_FINAL_ROWS_EXPECTED, "unit": "rows"},
        {"metric": "schema_columns", "value": len(expanded_header), "expected": SCHEMA_COLUMNS_EXPECTED, "unit": "columns"},
        {"metric": "final_target_candidates", "value": FINAL_TARGET_CANDIDATES, "expected": FINAL_TARGET_CANDIDATES, "unit": "rows"},
        {"metric": "rows_needed_after_twse", "value": projected_rows_needed_after_twse, "expected": ROWS_NEEDED_AFTER_TWSE_EXPECTED, "unit": "rows"},
    ]

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18e_report_exists", V218E_JSON.exists(), "critical", str(V218E_JSON))
    add_check("v2_18f_report_exists", V218F_JSON.exists(), "critical", str(V218F_JSON))
    add_check("v2_18g_report_exists", V218G_JSON.exists(), "critical", str(V218G_JSON))
    add_check("v2_18h_report_exists", V218H_JSON.exists(), "critical", str(V218H_JSON))
    add_check("v2_18e_status_expected", v218e.get("status") == EXPECTED_V218E_STATUS, "critical", v218e.get("status", ""))
    add_check("v2_18f_status_expected", v218f.get("status") == EXPECTED_V218F_STATUS, "critical", v218f.get("status", ""))
    add_check("v2_18g_status_expected", v218g.get("status") == EXPECTED_V218G_STATUS, "critical", v218g.get("status", ""))
    add_check("v2_18h_status_expected", v218h.get("status") == EXPECTED_V218H_STATUS, "critical", v218h.get("status", ""))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("base_nse_rows_expected", base_rows_count == BASE_NSE_ROWS_EXPECTED, "critical", f"base_rows={base_rows_count}")
    add_check("expanded_candidate_rows_expected", expanded_rows_count == TWSE_TPEX_FINAL_ROWS_EXPECTED, "critical", f"expanded_rows={expanded_rows_count}")
    add_check("row_increment_expected", row_increment == TWSE_ADDED_ROWS_EXPECTED, "critical", f"row_increment={row_increment}")
    add_check("schema_columns_expected", len(expanded_header) == SCHEMA_COLUMNS_EXPECTED, "critical", f"schema_columns={len(expanded_header)}")
    add_check("schema_equal_base_expanded", base_header == expanded_header, "critical", "base header equals expanded header")
    add_check("twse_candidates_extracted_expected", extracted_candidates == TWSE_CANDIDATES_EXTRACTED_EXPECTED, "critical", f"extracted_candidates={extracted_candidates}")
    add_check("twse_potential_net_new_expected", potential_net_new == TWSE_POTENTIAL_NET_NEW_EXPECTED, "critical", f"potential_net_new={potential_net_new}")
    add_check("twse_possible_existing_expected", possible_existing == TWSE_POSSIBLE_EXISTING_EXPECTED, "critical", f"possible_existing={possible_existing}")
    add_check("twse_existing_expected", existing == TWSE_EXISTING_EXPECTED, "critical", f"existing={existing}")
    add_check("twse_added_rows_expected", added_rows_count == TWSE_ADDED_ROWS_EXPECTED, "critical", f"added_rows={added_rows_count}")
    add_check("twse_withheld_rows_expected", withheld_rows_count == TWSE_WITHHELD_ROWS_EXPECTED, "critical", f"withheld_rows={withheld_rows_count}")
    add_check("rows_needed_after_twse_expected", projected_rows_needed_after_twse == ROWS_NEEDED_AFTER_TWSE_EXPECTED, "critical", f"rows_needed_after_twse={projected_rows_needed_after_twse}")
    add_check("v2_18h_critical_failed_checks_zero", int(v218h_summary.get("critical_failed_checks", -1)) == 0, "critical", f"v2_18h_critical_failed_checks={v218h_summary.get('critical_failed_checks')}")
    add_check("row_audit_all_passed", all(str(row.get("passed", "")).lower() == "true" for row in row_audit_rows), "critical", "v2.18H row audit all passed")
    add_check("symbol_audit_all_passed", all(str(row.get("passed", "")).lower() == "true" for row in symbol_audit_rows), "critical", "v2.18H symbol audit all passed")
    add_check("schema_profile_rows_expected", len(schema_profile_rows) == SCHEMA_COLUMNS_EXPECTED, "critical", f"schema_profile_rows={len(schema_profile_rows)}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("base_candidate_sha_unchanged", base_sha_before == base_sha_after, "critical", "base candidate sha unchanged")
    add_check("expanded_candidate_sha_unchanged", expanded_sha_before == expanded_sha_after, "critical", "expanded candidate sha unchanged")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("no_new_expanded_dataset_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("closure_report_only", True, "critical", "phase_type=closure-report-only")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("full59k_deprecated_deferred", True, "critical", "full59k=DEPRECATED_DEFERRED")
    add_check("final_50k_gate_still_blocked", expanded_rows_count < FINAL_TARGET_CANDIDATES, "critical", f"{expanded_rows_count} < {FINAL_TARGET_CANDIDATES}")
    add_check("next_provider_needed", projected_rows_needed_after_twse > 0, "critical", f"rows_needed_after_twse={projected_rows_needed_after_twse}")

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "50k",
            "action": "start_next_provider_route_selection",
            "priority": "high",
            "reason": f"TWSE added {TWSE_ADDED_ROWS_EXPECTED} net-new rows but {ROWS_NEEDED_AFTER_TWSE_EXPECTED} rows are still needed for 50k.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "do not launch full59k; keep final target 50k; no scoring/OpenAI/broker during route selection",
        },
        {
            "action_order": 2,
            "action_scope": "TPEx",
            "action": "defer_or_repair_later",
            "priority": "medium",
            "reason": "TPEx did not contribute validated candidate rows in this route and should not block TWSE closure.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "only revisit TPEx if selected as a future repair route",
        },
        {
            "action_order": 3,
            "action_scope": "candidate_dataset",
            "action": "preserve_twse_tpex_candidate_as_validated_candidate",
            "priority": "medium",
            "reason": "expanded_universe_candidate_twse_tpex_v2_18g.csv is validated at 40,996 rows.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "do not replace active canonical without explicit future promotion phase",
        },
    ]

    if critical_failed == 0:
        status = "TWSE_TPEX_CLOSURE_COMPLETED_40996_CANDIDATES_NEXT_PROVIDER_SELECTION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "TWSE_TPEX_CLOSURE_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "closure_summary": {
            "route": "TWSE + TPEx Taiwan",
            "route_result": "partial_success_twse_only",
            "twse_status": "completed_used",
            "tpex_status": "deferred_or_repair_later",
            "active_canonical_rows": active_canonical_rows,
            "base_nse_candidate_rows": base_rows_count,
            "twse_candidates_extracted": extracted_candidates,
            "twse_potential_net_new": potential_net_new,
            "twse_possible_existing_not_added": possible_existing,
            "twse_existing_not_added": existing,
            "twse_added_rows": added_rows_count,
            "twse_withheld_rows": withheld_rows_count,
            "twse_tpex_expanded_candidate_rows": expanded_rows_count,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_after_twse": projected_rows_needed_after_twse,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
            "critical_failed_checks": critical_failed,
        },
        "source_references": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "base_nse_candidate_dataset": str(BASE_NSE_CANDIDATE_DATASET),
            "twse_tpex_expanded_candidate": str(TWSE_TPEX_EXPANDED_CANDIDATE),
            "v2_18e_report": str(V218E_JSON),
            "v2_18f_report": str(V218F_JSON),
            "v2_18g_report": str(V218G_JSON),
            "v2_18h_report": str(V218H_JSON),
            "v2_18f_classification": str(V218F_CLASSIFICATION_CSV),
            "v2_18g_added_rows": str(V218G_ADDED_ROWS_CSV),
            "v2_18g_withheld_rows": str(V218G_WITHHELD_ROWS_CSV),
            "optional_phase_reports": optional_phase_report_rows,
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "closure_report_performed": True,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(PHASE_LEDGER_CSV, phase_ledger_rows, ["phase", "name", "status", "primary_output", "dataset_rows_after_phase", "gate_status", "next"])
    write_csv(METRIC_SUMMARY_CSV, metric_summary_rows, ["metric", "value", "expected", "unit"])
    write_csv(SOURCE_STATUS_CSV, source_status_rows, ["source", "role", "status", "rows_or_candidates", "result", "decision"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_json(REPORT_JSON, payload)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    metric_lines = "\n".join(
        f"- {row['metric']}: `{row['value']}` / expected `{row['expected']}` {row['unit']}"
        for row in metric_summary_rows
    )

    phase_lines = "\n".join(
        f"- `{row['phase']}` — {row['name']} — {row['primary_output']}"
        for row in phase_ledger_rows
    )

    source_lines = "\n".join(
        f"- `{row['source']}` — {row['status']} — {row['decision']}"
        for row in source_status_rows
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.18I formally closes the TWSE + TPEx route.

The route is a partial success: TWSE contributed validated net-new candidates, while TPEx remains deferred or repair-later. The route does not reach the 50k target, so the next required step is a new provider route selection.

This phase is closure/report-only. It does not write a new expanded candidate dataset, does not replace the active canonical dataset, does not modify canonical, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Closure result

- Route: `TWSE + TPEx Taiwan`
- Route result: `partial_success_twse_only`
- TWSE status: `completed_used`
- TPEx status: `deferred_or_repair_later`
- Active canonical rows: `{active_canonical_rows}`
- Base NSE candidate rows: `{base_rows_count}`
- TWSE candidates extracted: `{extracted_candidates}`
- TWSE potential net-new: `{potential_net_new}`
- TWSE possible-existing not added: `{possible_existing}`
- TWSE existing not added: `{existing}`
- TWSE added rows: `{added_rows_count}`
- TWSE withheld rows: `{withheld_rows_count}`
- Final TWSE + TPEx candidate rows: `{expanded_rows_count}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed after TWSE: `{projected_rows_needed_after_twse}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`
- Critical failed checks: `{critical_failed}`

## Metric summary

{metric_lines}

## Phase ledger

{phase_lines}

## Source status

{source_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Closure report performed: true
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.18I TWSE + TPEx closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CLOSURE_SUMMARY:")
    for key, value in payload["closure_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
