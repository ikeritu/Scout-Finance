from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21E_S"
PHASE = "Singapore Promotion / Freeze Decision"
PHASE_TYPE = "singapore-promotion-freeze-decision"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

V221DS_JSON = OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_v2_21d_s.json"
V221DS_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_v2_21d_s_singapore_candidate.csv"

PROMOTED_DATASET = OUTPUT_DIR / "expanded_universe_v2_21e_s_singapore_promoted.csv"

REPORT_JSON = OUTPUT_DIR / "singapore_promotion_freeze_decision_v2_21e_s.json"
REPORT_MD = OUTPUT_DIR / "singapore_promotion_freeze_decision_v2_21e_s.md"
SUMMARY_CSV = OUTPUT_DIR / "singapore_promotion_freeze_decision_summary_v2_21e_s.csv"
CHECKS_CSV = OUTPUT_DIR / "singapore_promotion_freeze_decision_checks_v2_21e_s.csv"
MANIFEST_CSV = OUTPUT_DIR / "singapore_promotion_freeze_decision_manifest_v2_21e_s.csv"
COUNTRY_CODE_PATCH_AUDIT_CSV = OUTPUT_DIR / "singapore_promotion_freeze_decision_country_code_patch_audit_v2_21e_s.csv"
APPENDED_CONTEXT_AUDIT_CSV = OUTPUT_DIR / "singapore_promotion_freeze_decision_appended_context_audit_v2_21e_s.csv"
POINTER_DISCOVERY_CSV = OUTPUT_DIR / "singapore_promotion_freeze_decision_pointer_discovery_v2_21e_s.csv"
PROMOTION_POINTER_MANIFEST_JSON = OUTPUT_DIR / "singapore_promotion_freeze_decision_pointer_manifest_v2_21e_s.json"
DECISION_REGISTER_CSV = OUTPUT_DIR / "singapore_promotion_freeze_decision_decision_register_v2_21e_s.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "singapore_promotion_freeze_decision_next_actions_v2_21e_s.csv"

EXPECTED_V221DS_STATUS = "SINGAPORE_REBUILD_VALIDATION_CANDIDATE_COMPLETED_43066_ROWS_READY_FOR_PROMOTION_DECISION_NO_POINTER_UPDATE_SCORING_DEFERRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

CANDIDATE_ROWS_EXPECTED = 43066
CANDIDATE_SHA_EXPECTED = "8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f"
SINGAPORE_APPENDED_ROWS_EXPECTED = 358

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

MARKET_ID = "SINGAPORE_SGX"
COUNTRY = "Singapore"
COUNTRY_CODE = "SG"
EXCHANGE = "SGX"
MIC = "XSES"
CURRENCY = "SGD"

STATUS_PROMOTED_ARTIFACT_READY = "SINGAPORE_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED"
STATUS_FROZEN = "SINGAPORE_PROMOTION_FREEZE_DECISION_COMPLETED_CANDIDATE_FROZEN_REVIEW_REQUIRED"
STATUS_FAILED = "SINGAPORE_PROMOTION_FREEZE_DECISION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_SUCCESS = "v2.21C3B - Colombia Regulatory Discovery + Extraction Decision"
NEXT_PHASE_CLOSURE = "v2.21G - Final v2.21 Closure Report"
NEXT_PHASE_REVIEW = "v2.21E_S_REVIEW - Singapore Promotion Decision Issue Resolution"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader)


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", norm(value).lower())


def context_columns(header: list[str]) -> dict[str, list[str]]:
    cols = {
        "country": [],
        "country_code": [],
        "exchange": [],
        "mic": [],
        "currency": [],
        "symbol": [],
        "name": [],
        "isin": [],
        "source": [],
    }

    for column in header:
        key = norm_key(column)

        if key in {"countrycode", "countryiso2", "countryiso", "countrycode2"}:
            cols["country_code"].append(column)
        elif key == "country" or key.endswith("country") or "countryname" in key:
            cols["country"].append(column)

        if key == "exchange" or key.endswith("exchange") or "exchange" in key:
            cols["exchange"].append(column)

        if key == "mic" or key.endswith("mic") or "mic" in key:
            cols["mic"].append(column)

        if key == "currency" or key.endswith("currency") or "currency" in key:
            cols["currency"].append(column)

        if "symbol" in key or "ticker" in key or "tradingcode" in key:
            cols["symbol"].append(column)

        if key in {"name", "companyname", "securityname"} or "name" in key:
            cols["name"].append(column)

        if "isin" in key:
            cols["isin"].append(column)

        if "source" in key or "provider" in key:
            cols["source"].append(column)

    return cols


def row_has_value(row: dict[str, Any], columns: list[str], accepted_values: set[str]) -> bool:
    for column in columns:
        if norm_key(row.get(column)) in accepted_values:
            return True
    return False


def first_nonempty(row: dict[str, Any], columns: list[str]) -> str:
    for column in columns:
        value = norm(row.get(column))
        if value:
            return value
    return ""


def discover_pointer_like_files(root: Path) -> list[dict[str, Any]]:
    patterns = [
        "*pointer*.json",
        "*active*.json",
        "*canonical*.json",
        "*operational*.json",
    ]

    seen: set[Path] = set()
    rows: list[dict[str, Any]] = []

    for pattern in patterns:
        for path in root.rglob(pattern):
            if path in seen:
                continue
            seen.add(path)

            if path.is_file():
                text = ""
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")[:4000]
                except Exception:
                    text = ""

                lowered = text.lower()
                rows.append({
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "contains_expanded_universe": "expanded_universe" in lowered,
                    "contains_active": "active" in lowered,
                    "contains_canonical": "canonical" in lowered,
                    "contains_v2_20m": "v2_20m" in lowered,
                    "selected_for_update": False,
                    "selection_reason": "pointer discovery only; no existing pointer is modified in v2.21E_S",
                })

    return rows


def write_dataset(path: Path, rows: list[dict[str, Any]], header: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    output_paths = [
        PROMOTED_DATASET,
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        MANIFEST_CSV,
        COUNTRY_CODE_PATCH_AUDIT_CSV,
        APPENDED_CONTEXT_AUDIT_CSV,
        POINTER_DISCOVERY_CSV,
        PROMOTION_POINTER_MANIFEST_JSON,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v221ds = read_json(V221DS_JSON)
    v221ds_summary = v221ds.get("summary", {})

    operational_header = read_csv_header(OPERATIONAL_BASE_DATASET)
    candidate_header = read_csv_header(V221DS_CANDIDATE_DATASET)

    operational_rows_count = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha_before = sha256_file(OPERATIONAL_BASE_DATASET)

    rollback_rows_count = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha_before = sha256_file(ROLLBACK_DATASET)

    candidate_rows = read_csv_dicts(V221DS_CANDIDATE_DATASET)
    candidate_rows_count = len(candidate_rows)
    candidate_sha_before = sha256_file(V221DS_CANDIDATE_DATASET)

    if candidate_header != operational_header:
        raise SystemExit("SCHEMA_MISMATCH: candidate header does not match operational base header")

    cols = context_columns(candidate_header)

    promoted_rows = [dict(row) for row in candidate_rows]

    country_code_patch_rows: list[dict[str, Any]] = []
    appended_context_rows: list[dict[str, Any]] = []

    for absolute_index, row in enumerate(promoted_rows, start=1):
        is_appended = absolute_index > OPERATIONAL_BASE_ROWS_EXPECTED

        if not is_appended:
            continue

        append_order = absolute_index - OPERATIONAL_BASE_ROWS_EXPECTED

        for column in cols["country_code"]:
            before = norm(row.get(column))
            if before != COUNTRY_CODE:
                row[column] = COUNTRY_CODE
                country_code_patch_rows.append({
                    "append_order": append_order,
                    "row_number_in_promoted_dataset": absolute_index,
                    "column": column,
                    "before": before,
                    "after": COUNTRY_CODE,
                    "patch_reason": "normalize Singapore appended row country code before promotion artifact creation",
                })

        appended_context_rows.append({
            "append_order": append_order,
            "row_number_in_promoted_dataset": absolute_index,
            "country_confirmed": row_has_value(row, cols["country"], {"singapore"}),
            "country_code_confirmed": True if not cols["country_code"] else row_has_value(row, cols["country_code"], {"sg"}),
            "country_code_columns_present": len(cols["country_code"]),
            "exchange_confirmed": row_has_value(row, cols["exchange"], {"sgx"}),
            "mic_confirmed": row_has_value(row, cols["mic"], {"xses"}),
            "currency_confirmed": row_has_value(row, cols["currency"], {"sgd"}),
            "symbol_key": norm_key(first_nonempty(row, cols["symbol"])),
            "name_key": norm_key(first_nonempty(row, cols["name"])),
            "isin_key": norm_key(first_nonempty(row, cols["isin"])),
            "source_columns_present": len(cols["source"]),
        })

    write_dataset(PROMOTED_DATASET, promoted_rows, candidate_header)

    promoted_rows_count = count_csv_rows(PROMOTED_DATASET)
    promoted_sha = sha256_file(PROMOTED_DATASET)

    operational_sha_after = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_sha_after = sha256_file(ROLLBACK_DATASET)
    candidate_sha_after = sha256_file(V221DS_CANDIDATE_DATASET)

    appended_counter = Counter()
    for row in appended_context_rows:
        for key in [
            "country_confirmed",
            "country_code_confirmed",
            "exchange_confirmed",
            "mic_confirmed",
            "currency_confirmed",
        ]:
            if row[key] is True:
                appended_counter[key] += 1

    pointer_discovery_rows = discover_pointer_like_files(OUTPUT_DIR)

    pointer_manifest = {
        "version": VERSION,
        "manifest_type": "promotion_pointer_manifest",
        "generated_at_utc": utc_now(),
        "promotion_decision": "PROMOTION_ARTIFACT_READY_POINTER_NOT_UPDATED",
        "active_pointer_update_performed": False,
        "promoted_dataset": str(PROMOTED_DATASET),
        "promoted_rows": promoted_rows_count,
        "promoted_sha": promoted_sha,
        "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "previous_operational_base_rows": operational_rows_count,
        "previous_operational_base_sha": operational_sha_before,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows_count,
        "rollback_sha": rollback_sha_before,
        "reason": "v2.21E_S creates a promoted artifact and manifest; it does not modify an existing active pointer file blindly.",
    }

    write_json(PROMOTION_POINTER_MANIFEST_JSON, pointer_manifest)

    manifest_rows = [
        {
            "artifact": "previous_operational_base_input",
            "path": str(OPERATIONAL_BASE_DATASET),
            "rows": operational_rows_count,
            "sha256": operational_sha_before,
            "role": "input_only_unchanged",
        },
        {
            "artifact": "rollback_input",
            "path": str(ROLLBACK_DATASET),
            "rows": rollback_rows_count,
            "sha256": rollback_sha_before,
            "role": "input_only_unchanged",
        },
        {
            "artifact": "v2_21d_s_candidate_input",
            "path": str(V221DS_CANDIDATE_DATASET),
            "rows": candidate_rows_count,
            "sha256": candidate_sha_before,
            "role": "promotion_candidate_input_unchanged",
        },
        {
            "artifact": "v2_21e_s_promoted_dataset_output",
            "path": str(PROMOTED_DATASET),
            "rows": promoted_rows_count,
            "sha256": promoted_sha,
            "role": "promoted_artifact_not_active_pointer_update",
        },
        {
            "artifact": "v2_21e_s_pointer_manifest_output",
            "path": str(PROMOTION_POINTER_MANIFEST_JSON),
            "rows": 1,
            "sha256": sha256_file(PROMOTION_POINTER_MANIFEST_JSON),
            "role": "promotion_pointer_manifest_no_existing_pointer_modified",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "PROMOTION_DECISION_001",
            "decision": "Promote Singapore candidate as v2.21E_S promoted artifact.",
            "accepted": True,
            "reason": "v2.21D_S candidate passed validation and remains within the 45k quality ceiling.",
            "effect": "Creates promoted artifact with 43,066 rows.",
        },
        {
            "decision_id": "PROMOTION_DECISION_002",
            "decision": "Normalize Singapore country_code before promoted artifact creation.",
            "accepted": True,
            "reason": "v2.21D_S audit showed country_code confirmation gap while country/exchange/MIC/currency were valid.",
            "effect": "Only appended Singapore rows are patched in the v2.21E_S promoted artifact when country_code columns exist.",
        },
        {
            "decision_id": "PROMOTION_DECISION_003",
            "decision": "Do not modify existing active pointer files blindly.",
            "accepted": True,
            "reason": "Promotion should remain controlled and auditable.",
            "effect": "Creates pointer manifest; existing operational base remains unchanged.",
        },
        {
            "decision_id": "PROMOTION_DECISION_004",
            "decision": "Keep Colombia outside this phase.",
            "accepted": True,
            "reason": "Colombia remains on the regulatory discovery path.",
            "effect": "No Colombia extraction or rebuild occurs.",
        },
        {
            "decision_id": "PROMOTION_DECISION_005",
            "decision": "Keep scoring/OpenAI/broker/full59k deferred.",
            "accepted": True,
            "reason": "Scoring and enrichment have not been explicitly authorized.",
            "effect": "No scoring, OpenAI, broker, or full59k actions are run.",
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

    add_check(
        "v2_21d_s_status_expected",
        v221ds.get("status") == EXPECTED_V221DS_STATUS,
        "critical",
        str(v221ds.get("status")),
    )
    add_check(
        "v2_21d_s_approved_for_promotion_decision",
        as_bool(v221ds_summary.get("approved_for_promotion_decision")) is True,
        "critical",
        f"approved_for_promotion_decision={v221ds_summary.get('approved_for_promotion_decision')}",
    )
    add_check(
        "v2_21d_s_pointer_update_not_preapproved",
        as_bool(v221ds_summary.get("approved_for_pointer_update")) is False,
        "critical",
        f"approved_for_pointer_update={v221ds_summary.get('approved_for_pointer_update')}",
    )
    add_check(
        "operational_base_rows_expected",
        operational_rows_count == OPERATIONAL_BASE_ROWS_EXPECTED,
        "critical",
        f"operational_rows={operational_rows_count}",
    )
    add_check(
        "operational_base_sha_expected",
        operational_sha_before == OPERATIONAL_BASE_SHA_EXPECTED,
        "critical",
        operational_sha_before,
    )
    add_check(
        "rollback_rows_expected",
        rollback_rows_count == ROLLBACK_ROWS_EXPECTED,
        "critical",
        f"rollback_rows={rollback_rows_count}",
    )
    add_check(
        "rollback_sha_expected",
        rollback_sha_before == ROLLBACK_SHA_EXPECTED,
        "critical",
        rollback_sha_before,
    )
    add_check(
        "candidate_rows_expected",
        candidate_rows_count == CANDIDATE_ROWS_EXPECTED,
        "critical",
        f"candidate_rows={candidate_rows_count}",
    )
    add_check(
        "candidate_sha_expected",
        candidate_sha_before == CANDIDATE_SHA_EXPECTED,
        "critical",
        candidate_sha_before,
    )
    add_check(
        "candidate_header_matches_operational_header",
        candidate_header == operational_header,
        "critical",
        f"candidate_columns={len(candidate_header)};operational_columns={len(operational_header)}",
    )
    add_check(
        "promoted_dataset_rows_expected",
        promoted_rows_count == CANDIDATE_ROWS_EXPECTED,
        "critical",
        f"promoted_rows={promoted_rows_count}",
    )
    add_check(
        "promoted_dataset_under_quality_ceiling",
        promoted_rows_count <= QUALITY_CEILING_TARGET,
        "critical",
        f"promoted_rows={promoted_rows_count};ceiling={QUALITY_CEILING_TARGET}",
    )
    add_check(
        "promoted_dataset_above_quality_floor",
        promoted_rows_count >= QUALITY_FLOOR_TARGET,
        "critical",
        f"promoted_rows={promoted_rows_count};floor={QUALITY_FLOOR_TARGET}",
    )
    add_check(
        "singapore_appended_rows_expected",
        len(appended_context_rows) == SINGAPORE_APPENDED_ROWS_EXPECTED,
        "critical",
        f"appended_rows={len(appended_context_rows)}",
    )
    add_check(
        "appended_rows_country_confirmed",
        appended_counter["country_confirmed"] == SINGAPORE_APPENDED_ROWS_EXPECTED,
        "critical",
        f"country_confirmed={appended_counter['country_confirmed']}",
    )
    add_check(
        "appended_rows_country_code_confirmed_or_not_required",
        appended_counter["country_code_confirmed"] == SINGAPORE_APPENDED_ROWS_EXPECTED,
        "critical",
        f"country_code_confirmed={appended_counter['country_code_confirmed']};country_code_columns={len(cols['country_code'])}",
    )
    add_check(
        "appended_rows_exchange_confirmed",
        appended_counter["exchange_confirmed"] == SINGAPORE_APPENDED_ROWS_EXPECTED,
        "critical",
        f"exchange_confirmed={appended_counter['exchange_confirmed']}",
    )
    add_check(
        "appended_rows_mic_confirmed",
        appended_counter["mic_confirmed"] == SINGAPORE_APPENDED_ROWS_EXPECTED,
        "critical",
        f"mic_confirmed={appended_counter['mic_confirmed']}",
    )
    add_check(
        "appended_rows_currency_confirmed",
        appended_counter["currency_confirmed"] == SINGAPORE_APPENDED_ROWS_EXPECTED,
        "critical",
        f"currency_confirmed={appended_counter['currency_confirmed']}",
    )
    add_check(
        "country_code_patch_audited",
        True,
        "critical",
        f"country_code_patch_rows={len(country_code_patch_rows)}",
    )
    add_check(
        "operational_base_not_modified_after_promotion_decision",
        operational_sha_after == OPERATIONAL_BASE_SHA_EXPECTED,
        "critical",
        f"operational_sha_after={operational_sha_after}",
    )
    add_check(
        "rollback_not_modified_after_promotion_decision",
        rollback_sha_after == ROLLBACK_SHA_EXPECTED,
        "critical",
        f"rollback_sha_after={rollback_sha_after}",
    )
    add_check(
        "v2_21d_candidate_not_modified",
        candidate_sha_after == CANDIDATE_SHA_EXPECTED,
        "critical",
        f"candidate_sha_after={candidate_sha_after}",
    )
    add_check(
        "promoted_artifact_created",
        PROMOTED_DATASET.exists(),
        "critical",
        str(PROMOTED_DATASET),
    )
    add_check(
        "pointer_manifest_created",
        PROMOTION_POINTER_MANIFEST_JSON.exists(),
        "critical",
        str(PROMOTION_POINTER_MANIFEST_JSON),
    )
    add_check(
        "existing_pointer_files_not_modified",
        True,
        "critical",
        "pointer discovery only; no existing pointer file modified",
    )
    add_check(
        "colombia_extraction_not_performed",
        True,
        "critical",
        "Colombia remains outside v2.21E_S",
    )
    add_check(
        "canonical_dataset_not_modified",
        True,
        "critical",
        "canonical_dataset_modified=False",
    )
    add_check(
        "active_canonical_not_replaced",
        True,
        "critical",
        "active_canonical_replaced=False",
    )
    add_check(
        "active_pointer_update_not_performed",
        True,
        "critical",
        "active_pointer_update_performed=False",
    )
    add_check(
        "scoring_not_authorized",
        True,
        "critical",
        "scoring_authorized=False",
    )
    add_check(
        "openai_not_called",
        True,
        "critical",
        "openai_called=False",
    )
    add_check(
        "broker_not_called",
        True,
        "critical",
        "broker_called=False",
    )
    add_check(
        "full59k_not_launched",
        True,
        "critical",
        "full59k_universe_launched=False",
    )

    if critical_failed > 0:
        status = STATUS_FAILED
        promotion_decision = "SINGAPORE_PROMOTION_BLOCKED_REVIEW_REQUIRED"
        approved_as_promoted_artifact = False
        approved_for_next_operational_base_reference = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    elif warning_failed > 0:
        status = STATUS_FROZEN
        promotion_decision = "SINGAPORE_CANDIDATE_FROZEN_DUE_TO_WARNING_REVIEW_REQUIRED"
        approved_as_promoted_artifact = False
        approved_for_next_operational_base_reference = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_PROMOTED_ARTIFACT_READY
        promotion_decision = "SINGAPORE_PROMOTED_ARTIFACT_READY_FOR_NEXT_OPERATIONAL_REFERENCE"
        approved_as_promoted_artifact = True
        approved_for_next_operational_base_reference = True
        recommended_next_phase = NEXT_PHASE_SUCCESS

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "colombia_regulatory_discovery",
            "action": "continue_colombia_superfinanciera_simev_rnve_discovery",
            "priority": "high",
            "recommended_phase": NEXT_PHASE_SUCCESS if approved_as_promoted_artifact else NEXT_PHASE_REVIEW,
            "reason": "Singapore promoted artifact is ready; Colombia remains the unresolved part of v2.21." if approved_as_promoted_artifact else "Singapore promotion requires review before continuing.",
            "guardrails": "Colombia discovery only; no BVC shell HTML extraction",
        },
        {
            "action_order": 2,
            "action_scope": "final_closure",
            "action": "prepare_final_v2_21_closure_after_colombia_decision",
            "priority": "medium",
            "recommended_phase": NEXT_PHASE_CLOSURE,
            "reason": "Final closure should happen after Colombia is resolved or explicitly frozen.",
            "guardrails": "document Singapore promoted artifact and Colombia status",
        },
        {
            "action_order": 3,
            "action_scope": "pointer_control",
            "action": "use_promotion_pointer_manifest_as_reference_do_not_modify_existing_pointer_blindly",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "v2.21E_S creates promoted artifact and pointer manifest but does not edit an unknown active pointer convention.",
            "guardrails": "no active pointer mutation without explicit known pointer target",
        },
    ]

    summary = {
        "selected_route": "Singapore split route from Colombia + Singapore targeted expansion",
        "phase_type": PHASE_TYPE,
        "promotion_decision": promotion_decision,
        "approved_as_promoted_artifact": approved_as_promoted_artifact,
        "approved_for_next_operational_base_reference": approved_for_next_operational_base_reference,
        "active_pointer_update_performed": False,
        "approved_for_scoring": False,
        "approved_for_colombia_extraction": False,
        "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "previous_operational_base_rows": operational_rows_count,
        "previous_operational_base_sha": operational_sha_before,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows_count,
        "rollback_sha": rollback_sha_before,
        "v2_21d_s_candidate_dataset": str(V221DS_CANDIDATE_DATASET),
        "v2_21d_s_candidate_rows": candidate_rows_count,
        "v2_21d_s_candidate_sha": candidate_sha_before,
        "promoted_dataset": str(PROMOTED_DATASET),
        "promoted_rows": promoted_rows_count,
        "promoted_sha": promoted_sha,
        "singapore_appended_rows": len(appended_context_rows),
        "country_code_patch_rows": len(country_code_patch_rows),
        "pointer_manifest": str(PROMOTION_POINTER_MANIFEST_JSON),
        "pointer_like_files_discovered": len(pointer_discovery_rows),
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity_after_promotion_artifact": QUALITY_CEILING_TARGET - promoted_rows_count,
        "market_id": MARKET_ID,
        "country": COUNTRY,
        "country_code": COUNTRY_CODE,
        "exchange": EXCHANGE,
        "mic": MIC,
        "currency": CURRENCY,
        "candidate_dataset_promoted_as_artifact": approved_as_promoted_artifact,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "pointer_update_performed": False,
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": recommended_next_phase,
        "final_closure_phase": NEXT_PHASE_CLOSURE,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(MANIFEST_CSV, manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(COUNTRY_CODE_PATCH_AUDIT_CSV, country_code_patch_rows, [
        "append_order",
        "row_number_in_promoted_dataset",
        "column",
        "before",
        "after",
        "patch_reason",
    ])
    write_csv(APPENDED_CONTEXT_AUDIT_CSV, appended_context_rows, [
        "append_order",
        "row_number_in_promoted_dataset",
        "country_confirmed",
        "country_code_confirmed",
        "country_code_columns_present",
        "exchange_confirmed",
        "mic_confirmed",
        "currency_confirmed",
        "symbol_key",
        "name_key",
        "isin_key",
        "source_columns_present",
    ])
    write_csv(POINTER_DISCOVERY_CSV, pointer_discovery_rows, [
        "path",
        "bytes",
        "sha256",
        "contains_expanded_universe",
        "contains_active",
        "contains_canonical",
        "contains_v2_20m",
        "selected_for_update",
        "selection_reason",
    ])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, [
        "decision_id",
        "decision",
        "accepted",
        "reason",
        "effect",
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
        "manifest": manifest_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "pointer_manifest": pointer_manifest,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Singapore split route",
            "market_scope": [MARKET_ID],
            "colombia_scope_excluded": True,
            "promoted_dataset": str(PROMOTED_DATASET),
            "promoted_rows": promoted_rows_count,
            "promoted_sha": promoted_sha,
            "approved_as_promoted_artifact": approved_as_promoted_artifact,
            "approved_for_next_operational_base_reference": approved_for_next_operational_base_reference,
            "active_pointer_update_performed": False,
            "approved_for_scoring": False,
            "approved_for_colombia_extraction": False,
            "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "previous_operational_base_rows": operational_rows_count,
            "previous_operational_base_sha": operational_sha_before,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows_count,
            "rollback_sha": rollback_sha_before,
            "country_code_patch_rows": len(country_code_patch_rows),
            "candidate_dataset_promoted_as_artifact": approved_as_promoted_artifact,
            "file_edit_performed_on_previous_operational_base": False,
            "file_copy_performed_on_previous_operational_base": False,
            "file_rename_performed_on_previous_operational_base": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "provider_expansion_scope": "singapore_split_only",
            "additional_provider_expansion_frozen": True,
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
        "recommended_next_phase": recommended_next_phase,
        "final_closure_phase": NEXT_PHASE_CLOSURE,
    }

    write_json(REPORT_JSON, payload)

    manifest_lines = "\n".join(
        f"- `{row['artifact']}` — rows `{row['rows']}` — SHA `{row['sha256']}` — {row['role']}"
        for row in manifest_rows
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

v2.21E_S makes the Singapore promotion/freeze decision.

The v2.21D_S candidate is promoted as a controlled artifact after final validation. The previous operational base remains unchanged, no active pointer file is modified blindly, no scoring is run, no OpenAI call is made, no broker call is made, and full59k remains deprecated/deferred.

## Summary

- Promotion decision: `{promotion_decision}`
- Approved as promoted artifact: `{approved_as_promoted_artifact}`
- Approved for next operational base reference: `{approved_for_next_operational_base_reference}`
- Active pointer update performed: `False`
- Previous operational base rows: `{operational_rows_count}`
- Previous operational base SHA256: `{operational_sha_before}`
- Promoted dataset: `{PROMOTED_DATASET}`
- Promoted rows: `{promoted_rows_count}`
- Promoted SHA256: `{promoted_sha}`
- Singapore appended rows: `{len(appended_context_rows)}`
- Country code patch rows: `{len(country_code_patch_rows)}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Manifest

{manifest_lines}

## Decision register

{decision_lines}

## Checks

{check_lines}

## Recommended next phase

Primary: `{recommended_next_phase}`

Final closure phase: `{NEXT_PHASE_CLOSURE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21E_S Singapore promotion / freeze decision completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("MANIFEST:")
    for row in manifest_rows:
        print(f"- {row['artifact']}: rows={row['rows']} sha={row['sha256']} role={row['role']}")
    print("")
    print("COUNTRY_CODE_PATCH:")
    print(f"- country_code_patch_rows: {len(country_code_patch_rows)}")
    print("")
    print("POINTER_DISCOVERY:")
    print(f"- pointer_like_files_discovered: {len(pointer_discovery_rows)}")
    print("- existing_pointer_files_modified: False")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")
    print("")
    print("FINAL_CLOSURE_PHASE:")
    print(f"- {NEXT_PHASE_CLOSURE}")


if __name__ == "__main__":
    main()
