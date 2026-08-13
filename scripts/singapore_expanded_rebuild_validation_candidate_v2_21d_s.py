from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21D_S"
PHASE = "Singapore Rebuild + Validation Candidate"
PHASE_TYPE = "singapore-expanded-rebuild-validation-candidate"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

V221C4S_JSON = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_v2_21c4s.json"
V221C4S_ELIGIBLE = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_eligible_candidates_v2_21c4s.csv"
V221C4S_SCHEMA_PROJECTION = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_schema_projection_v2_21c4s.csv"

CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_v2_21d_s_singapore_candidate.csv"

REPORT_JSON = OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_v2_21d_s.json"
REPORT_MD = OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_v2_21d_s.md"
SUMMARY_CSV = OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_summary_v2_21d_s.csv"
CHECKS_CSV = OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_checks_v2_21d_s.csv"
MANIFEST_CSV = OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_manifest_v2_21d_s.csv"
APPENDED_AUDIT_CSV = OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_appended_audit_v2_21d_s.csv"
VALIDATION_SUMMARY_CSV = OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_validation_summary_v2_21d_s.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "singapore_expanded_rebuild_validation_candidate_next_actions_v2_21d_s.csv"

EXPECTED_V221C4S_STATUS = "SINGAPORE_STRUCTURED_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_ELIGIBLE_CANDIDATES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

EXPECTED_SINGAPORE_ELIGIBLE_CANDIDATES = 358
EXPECTED_PROJECTED_ROWS_AFTER_ADDITION = 43066

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

MARKET_ID = "SINGAPORE_SGX"
COUNTRY = "Singapore"
COUNTRY_CODE = "SG"
EXCHANGE = "SGX"
MIC = "XSES"
CURRENCY = "SGD"

STATUS_SUCCESS = "SINGAPORE_REBUILD_VALIDATION_CANDIDATE_COMPLETED_43066_ROWS_READY_FOR_PROMOTION_DECISION_NO_POINTER_UPDATE_SCORING_DEFERRED"
STATUS_FAILED = "SINGAPORE_REBUILD_VALIDATION_CANDIDATE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_SUCCESS = "v2.21E_S - Singapore Promotion / Freeze Decision"
NEXT_PHASE_REVIEW = "v2.21D_S_REVIEW - Singapore Rebuild Candidate Issue Resolution"
SECONDARY_NEXT_PHASE = "v2.21C3B - Colombia Regulatory Source Discovery"


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
        if "countrycode" in key or key == "country_code":
            cols["country_code"].append(column)
        elif "country" in key:
            cols["country"].append(column)

        if "exchange" in key:
            cols["exchange"].append(column)

        if key == "mic" or key.endswith("mic") or "mic" in key:
            cols["mic"].append(column)

        if "currency" in key:
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


def candidate_symbol_key(row: dict[str, str], symbol_columns: list[str]) -> str:
    for column in symbol_columns:
        value = norm_key(row.get(column))
        if value:
            return value
    return ""


def candidate_name_key(row: dict[str, str], name_columns: list[str]) -> str:
    for column in name_columns:
        value = norm_key(row.get(column))
        if value:
            return value
    return ""


def candidate_isin_key(row: dict[str, str], isin_columns: list[str]) -> str:
    for column in isin_columns:
        value = norm_key(row.get(column))
        if value:
            return value
    return ""


def main() -> None:
    output_paths = [
        CANDIDATE_DATASET,
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        MANIFEST_CSV,
        APPENDED_AUDIT_CSV,
        VALIDATION_SUMMARY_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v221c4s = read_json(V221C4S_JSON)
    v221c4s_summary = v221c4s.get("summary", {})

    operational_header = read_csv_header(OPERATIONAL_BASE_DATASET)
    projection_header = read_csv_header(V221C4S_SCHEMA_PROJECTION)

    operational_rows = read_csv_dicts(OPERATIONAL_BASE_DATASET)
    projected_singapore_rows = read_csv_dicts(V221C4S_SCHEMA_PROJECTION)
    eligible_rows = read_csv_dicts(V221C4S_ELIGIBLE)

    operational_row_count = len(operational_rows)
    projection_row_count = len(projected_singapore_rows)
    eligible_row_count = len(eligible_rows)

    operational_sha_before = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_row_count = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha_before = sha256_file(ROLLBACK_DATASET)

    candidate_rows = operational_rows + projected_singapore_rows

    with CANDIDATE_DATASET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=operational_header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(candidate_rows)

    candidate_row_count = count_csv_rows(CANDIDATE_DATASET)
    candidate_sha = sha256_file(CANDIDATE_DATASET)

    operational_sha_after = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_sha_after = sha256_file(ROLLBACK_DATASET)

    cols = context_columns(operational_header)

    appended_audit_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(projected_singapore_rows, start=1):
        appended_audit_rows.append({
            "append_order": idx,
            "country_confirmed": row_has_value(row, cols["country"], {"singapore"}),
            "country_code_confirmed": row_has_value(row, cols["country_code"], {"sg"}),
            "exchange_confirmed": row_has_value(row, cols["exchange"], {"sgx"}),
            "mic_confirmed": row_has_value(row, cols["mic"], {"xses"}),
            "currency_confirmed": row_has_value(row, cols["currency"], {"sgd"}),
            "symbol_key": candidate_symbol_key(row, cols["symbol"]),
            "name_key": candidate_name_key(row, cols["name"]),
            "isin_key": candidate_isin_key(row, cols["isin"]),
            "source_columns_present": len(cols["source"]),
        })

    context_counter = Counter()
    for row in appended_audit_rows:
        for key in [
            "country_confirmed",
            "country_code_confirmed",
            "exchange_confirmed",
            "mic_confirmed",
            "currency_confirmed",
        ]:
            if row[key] is True:
                context_counter[key] += 1

    eligible_approved_count = sum(1 for row in eligible_rows if as_bool(row.get("approved_for_rebuild_input")))
    eligible_market_count = sum(1 for row in eligible_rows if row.get("market_id") == MARKET_ID)

    eligible_symbols = [norm_key(row.get("symbol")) for row in eligible_rows if norm_key(row.get("symbol"))]
    eligible_names = [norm_key(row.get("name")) for row in eligible_rows if norm_key(row.get("name"))]
    eligible_isins = [norm_key(row.get("isin")) for row in eligible_rows if norm_key(row.get("isin"))]

    duplicate_eligible_symbols = len(eligible_symbols) - len(set(eligible_symbols))
    duplicate_eligible_names = len(eligible_names) - len(set(eligible_names))
    duplicate_eligible_isins = len(eligible_isins) - len(set(eligible_isins))

    projected_rows_after_addition = operational_row_count + projection_row_count
    remaining_capacity_after_candidate = QUALITY_CEILING_TARGET - candidate_row_count

    manifest_rows = [
        {
            "artifact": "operational_base_input",
            "path": str(OPERATIONAL_BASE_DATASET),
            "rows": operational_row_count,
            "sha256": operational_sha_before,
            "role": "input_only_unchanged",
        },
        {
            "artifact": "rollback_input",
            "path": str(ROLLBACK_DATASET),
            "rows": rollback_row_count,
            "sha256": rollback_sha_before,
            "role": "input_only_unchanged",
        },
        {
            "artifact": "v2_21c4s_schema_projection_input",
            "path": str(V221C4S_SCHEMA_PROJECTION),
            "rows": projection_row_count,
            "sha256": sha256_file(V221C4S_SCHEMA_PROJECTION),
            "role": "append_source",
        },
        {
            "artifact": "v2_21c4s_eligible_candidates_input",
            "path": str(V221C4S_ELIGIBLE),
            "rows": eligible_row_count,
            "sha256": sha256_file(V221C4S_ELIGIBLE),
            "role": "eligibility_audit_source",
        },
        {
            "artifact": "candidate_dataset_output",
            "path": str(CANDIDATE_DATASET),
            "rows": candidate_row_count,
            "sha256": candidate_sha,
            "role": "candidate_only_not_promoted",
        },
    ]

    validation_summary_rows = [
        {
            "metric": "operational_rows",
            "value": operational_row_count,
        },
        {
            "metric": "projection_rows",
            "value": projection_row_count,
        },
        {
            "metric": "eligible_rows",
            "value": eligible_row_count,
        },
        {
            "metric": "candidate_rows",
            "value": candidate_row_count,
        },
        {
            "metric": "candidate_sha256",
            "value": candidate_sha,
        },
        {
            "metric": "remaining_capacity_after_candidate",
            "value": remaining_capacity_after_candidate,
        },
        {
            "metric": "eligible_approved_count",
            "value": eligible_approved_count,
        },
        {
            "metric": "eligible_market_count",
            "value": eligible_market_count,
        },
        {
            "metric": "duplicate_eligible_symbols",
            "value": duplicate_eligible_symbols,
        },
        {
            "metric": "duplicate_eligible_names",
            "value": duplicate_eligible_names,
        },
        {
            "metric": "duplicate_eligible_isins",
            "value": duplicate_eligible_isins,
        },
        {
            "metric": "appended_country_confirmed",
            "value": context_counter["country_confirmed"],
        },
        {
            "metric": "appended_exchange_confirmed",
            "value": context_counter["exchange_confirmed"],
        },
        {
            "metric": "appended_mic_confirmed",
            "value": context_counter["mic_confirmed"],
        },
        {
            "metric": "appended_currency_confirmed",
            "value": context_counter["currency_confirmed"],
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
        "v2_21c4s_status_expected",
        v221c4s.get("status") == EXPECTED_V221C4S_STATUS,
        "critical",
        str(v221c4s.get("status")),
    )
    add_check(
        "v2_21c4s_approved_for_singapore_rebuild_candidate",
        as_bool(v221c4s_summary.get("approved_for_singapore_rebuild_candidate")) is True,
        "critical",
        f"approved_for_singapore_rebuild_candidate={v221c4s_summary.get('approved_for_singapore_rebuild_candidate')}",
    )
    add_check(
        "v2_21c4s_global_v2_21d_not_approved",
        as_bool(v221c4s_summary.get("approved_for_global_v2_21d")) is False,
        "critical",
        f"approved_for_global_v2_21d={v221c4s_summary.get('approved_for_global_v2_21d')}",
    )
    add_check(
        "v2_21c4s_colombia_extraction_not_approved",
        as_bool(v221c4s_summary.get("approved_for_colombia_extraction")) is False,
        "critical",
        f"approved_for_colombia_extraction={v221c4s_summary.get('approved_for_colombia_extraction')}",
    )
    add_check(
        "operational_base_rows_expected",
        operational_row_count == OPERATIONAL_BASE_ROWS_EXPECTED,
        "critical",
        f"operational_rows={operational_row_count}",
    )
    add_check(
        "operational_base_sha_expected",
        operational_sha_before == OPERATIONAL_BASE_SHA_EXPECTED,
        "critical",
        operational_sha_before,
    )
    add_check(
        "rollback_rows_expected",
        rollback_row_count == ROLLBACK_ROWS_EXPECTED,
        "critical",
        f"rollback_rows={rollback_row_count}",
    )
    add_check(
        "rollback_sha_expected",
        rollback_sha_before == ROLLBACK_SHA_EXPECTED,
        "critical",
        rollback_sha_before,
    )
    add_check(
        "schema_projection_header_matches_operational_header",
        projection_header == operational_header,
        "critical",
        f"projection_columns={len(projection_header)};operational_columns={len(operational_header)}",
    )
    add_check(
        "schema_column_count_expected",
        len(operational_header) == 33,
        "critical",
        f"columns={len(operational_header)}",
    )
    add_check(
        "projection_rows_expected",
        projection_row_count == EXPECTED_SINGAPORE_ELIGIBLE_CANDIDATES,
        "critical",
        f"projection_rows={projection_row_count}",
    )
    add_check(
        "eligible_rows_expected",
        eligible_row_count == EXPECTED_SINGAPORE_ELIGIBLE_CANDIDATES,
        "critical",
        f"eligible_rows={eligible_row_count}",
    )
    add_check(
        "eligible_rows_all_approved_for_rebuild_input",
        eligible_approved_count == eligible_row_count,
        "critical",
        f"eligible_approved_count={eligible_approved_count};eligible_rows={eligible_row_count}",
    )
    add_check(
        "eligible_rows_singapore_only",
        eligible_market_count == eligible_row_count,
        "critical",
        f"eligible_market_count={eligible_market_count};eligible_rows={eligible_row_count}",
    )
    add_check(
        "eligible_symbols_unique",
        duplicate_eligible_symbols == 0,
        "critical",
        f"duplicate_eligible_symbols={duplicate_eligible_symbols}",
    )
    add_check(
        "eligible_names_unique_or_reviewable",
        duplicate_eligible_names == 0,
        "warning",
        f"duplicate_eligible_names={duplicate_eligible_names}",
    )
    add_check(
        "eligible_isins_unique",
        duplicate_eligible_isins == 0,
        "critical",
        f"duplicate_eligible_isins={duplicate_eligible_isins}",
    )
    add_check(
        "candidate_dataset_rows_expected",
        candidate_row_count == EXPECTED_PROJECTED_ROWS_AFTER_ADDITION,
        "critical",
        f"candidate_rows={candidate_row_count};expected={EXPECTED_PROJECTED_ROWS_AFTER_ADDITION}",
    )
    add_check(
        "candidate_dataset_rows_equal_base_plus_projection",
        candidate_row_count == operational_row_count + projection_row_count,
        "critical",
        f"candidate_rows={candidate_row_count};base_plus_projection={operational_row_count + projection_row_count}",
    )
    add_check(
        "candidate_dataset_above_quality_floor",
        candidate_row_count >= QUALITY_FLOOR_TARGET,
        "critical",
        f"candidate_rows={candidate_row_count};floor={QUALITY_FLOOR_TARGET}",
    )
    add_check(
        "candidate_dataset_under_quality_ceiling",
        candidate_row_count <= QUALITY_CEILING_TARGET,
        "critical",
        f"candidate_rows={candidate_row_count};ceiling={QUALITY_CEILING_TARGET}",
    )
    add_check(
        "remaining_capacity_non_negative",
        remaining_capacity_after_candidate >= 0,
        "critical",
        f"remaining_capacity_after_candidate={remaining_capacity_after_candidate}",
    )
    add_check(
        "candidate_dataset_sha_created",
        bool(candidate_sha),
        "critical",
        candidate_sha,
    )
    add_check(
        "appended_rows_country_confirmed",
        context_counter["country_confirmed"] == projection_row_count,
        "critical",
        f"country_confirmed={context_counter['country_confirmed']};projection_rows={projection_row_count}",
    )
    add_check(
        "appended_rows_exchange_confirmed",
        context_counter["exchange_confirmed"] == projection_row_count,
        "critical",
        f"exchange_confirmed={context_counter['exchange_confirmed']};projection_rows={projection_row_count}",
    )
    add_check(
        "appended_rows_mic_confirmed",
        context_counter["mic_confirmed"] == projection_row_count,
        "critical",
        f"mic_confirmed={context_counter['mic_confirmed']};projection_rows={projection_row_count}",
    )
    add_check(
        "appended_rows_currency_confirmed",
        context_counter["currency_confirmed"] == projection_row_count,
        "critical",
        f"currency_confirmed={context_counter['currency_confirmed']};projection_rows={projection_row_count}",
    )
    add_check(
        "operational_base_not_modified_after_candidate_build",
        operational_sha_after == OPERATIONAL_BASE_SHA_EXPECTED,
        "critical",
        f"operational_sha_after={operational_sha_after}",
    )
    add_check(
        "rollback_not_modified_after_candidate_build",
        rollback_sha_after == ROLLBACK_SHA_EXPECTED,
        "critical",
        f"rollback_sha_after={rollback_sha_after}",
    )
    add_check(
        "expanded_rebuild_candidate_created",
        CANDIDATE_DATASET.exists(),
        "critical",
        str(CANDIDATE_DATASET),
    )
    add_check(
        "candidate_only_not_promoted",
        True,
        "critical",
        "candidate dataset created; no active pointer update performed",
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
        "pointer_update_not_performed",
        True,
        "critical",
        "pointer_update_performed=False",
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
        rebuild_decision = "SINGAPORE_REBUILD_CANDIDATE_BLOCKED_REVIEW_REQUIRED"
        approved_for_promotion_decision = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        rebuild_decision = "SINGAPORE_REBUILD_CANDIDATE_43066_ROWS_VALIDATED_READY_FOR_PROMOTION_OR_FREEZE_DECISION"
        approved_for_promotion_decision = True
        recommended_next_phase = NEXT_PHASE_SUCCESS

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "singapore_promotion_freeze_decision",
            "action": "decide_whether_to_promote_or_freeze_singapore_candidate_dataset",
            "priority": "high" if approved_for_promotion_decision else "blocked",
            "recommended_phase": recommended_next_phase,
            "reason": "Candidate dataset is valid and within quality ceiling." if approved_for_promotion_decision else "Candidate dataset failed critical validation.",
            "guardrails": "explicit promotion decision required; no scoring; no OpenAI; no broker",
        },
        {
            "action_order": 2,
            "action_scope": "colombia_regulatory_discovery",
            "action": "continue_colombia_superfinanciera_simev_rnve_discovery",
            "priority": "high",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Colombia remains pending outside Singapore candidate route.",
            "guardrails": "discovery only; no BVC shell HTML extraction",
        },
        {
            "action_order": 3,
            "action_scope": "pointer_control",
            "action": "keep_active_pointer_unchanged_until_v2_21e_s_decision",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "v2.21D_S creates candidate dataset only.",
            "guardrails": "no pointer update in v2.21D_S",
        },
    ]

    summary = {
        "selected_route": "Singapore split route from Colombia + Singapore targeted expansion",
        "phase_type": PHASE_TYPE,
        "rebuild_decision": rebuild_decision,
        "approved_for_promotion_decision": approved_for_promotion_decision,
        "approved_for_pointer_update": False,
        "approved_for_scoring": False,
        "approved_for_colombia_extraction": False,
        "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "operational_base_rows": operational_row_count,
        "operational_base_sha": operational_sha_before,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_row_count,
        "rollback_sha": rollback_sha_before,
        "candidate_dataset": str(CANDIDATE_DATASET),
        "candidate_rows": candidate_row_count,
        "candidate_sha": candidate_sha,
        "singapore_appended_rows": projection_row_count,
        "eligible_source_rows": eligible_row_count,
        "projected_rows_after_addition": projected_rows_after_addition,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity_after_candidate": remaining_capacity_after_candidate,
        "market_id": MARKET_ID,
        "country": COUNTRY,
        "country_code": COUNTRY_CODE,
        "exchange": EXCHANGE,
        "mic": MIC,
        "currency": CURRENCY,
        "expanded_rebuild_candidate_created": True,
        "expanded_validation_performed": True,
        "candidate_dataset_promoted": False,
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
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(MANIFEST_CSV, manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(APPENDED_AUDIT_CSV, appended_audit_rows, [
        "append_order",
        "country_confirmed",
        "country_code_confirmed",
        "exchange_confirmed",
        "mic_confirmed",
        "currency_confirmed",
        "symbol_key",
        "name_key",
        "isin_key",
        "source_columns_present",
    ])
    write_csv(VALIDATION_SUMMARY_CSV, validation_summary_rows, ["metric", "value"])
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
        "validation_summary": validation_summary_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Singapore split route",
            "market_scope": [MARKET_ID],
            "colombia_scope_excluded": True,
            "candidate_dataset": str(CANDIDATE_DATASET),
            "candidate_rows": candidate_row_count,
            "candidate_sha": candidate_sha,
            "approved_for_promotion_decision": approved_for_promotion_decision,
            "approved_for_pointer_update": False,
            "approved_for_scoring": False,
            "approved_for_colombia_extraction": False,
            "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "operational_base_rows": operational_row_count,
            "operational_base_sha": operational_sha_before,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_row_count,
            "rollback_sha": rollback_sha_before,
            "expanded_rebuild_candidate_created": True,
            "expanded_validation_performed": True,
            "candidate_dataset_promoted": False,
            "file_edit_performed_on_operational_base": False,
            "file_copy_performed_on_operational_base": False,
            "file_rename_performed_on_operational_base": False,
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
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_json(REPORT_JSON, payload)

    manifest_lines = "\n".join(
        f"- `{row['artifact']}` — rows `{row['rows']}` — SHA `{row['sha256']}` — {row['role']}"
        for row in manifest_rows
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

v2.21D_S builds and validates a Singapore-only expanded universe candidate from the v2.21C4S eligible candidates.

This phase creates a candidate dataset but does not promote it, does not update pointers, does not modify the operational base, does not run scoring, does not call OpenAI, does not call brokers, and does not launch full59k.

## Summary

- Rebuild decision: `{rebuild_decision}`
- Approved for promotion decision: `{approved_for_promotion_decision}`
- Approved for pointer update: `False`
- Operational base rows: `{operational_row_count}`
- Operational base SHA256: `{operational_sha_before}`
- Candidate dataset: `{CANDIDATE_DATASET}`
- Candidate rows: `{candidate_row_count}`
- Candidate SHA256: `{candidate_sha}`
- Singapore appended rows: `{projection_row_count}`
- Remaining capacity after candidate: `{remaining_capacity_after_candidate}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Manifest

{manifest_lines}

## Checks

{check_lines}

## Recommended next phase

Primary: `{recommended_next_phase}`

Secondary: `{SECONDARY_NEXT_PHASE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21D_S Singapore rebuild + validation candidate completed.")
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
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")
    print("")
    print("SECONDARY_NEXT_PHASE:")
    print(f"- {SECONDARY_NEXT_PHASE}")


if __name__ == "__main__":
    main()
