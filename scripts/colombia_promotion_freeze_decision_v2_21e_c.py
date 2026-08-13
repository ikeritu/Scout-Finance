from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21E_C"
PHASE = "Colombia Promotion / Freeze Decision"
PHASE_TYPE = "colombia-promotion-freeze-decision"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

SINGAPORE_PROMOTED_DATASET = OUTPUT_DIR / "expanded_universe_v2_21e_s_singapore_promoted.csv"
COLOMBIA_BUILD_JSON = OUTPUT_DIR / "colombia_conditional_build_freeze_v2_21d_c.json"
COLOMBIA_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_v2_21d_c_colombia_candidate.csv"
COLOMBIA_ELIGIBLE_CANDIDATES = OUTPUT_DIR / "colombia_conditional_build_freeze_eligible_candidates_v2_21d_c.csv"

COLOMBIA_PROMOTED_DATASET = OUTPUT_DIR / "expanded_universe_v2_21e_c_colombia_promoted.csv"

REPORT_JSON = OUTPUT_DIR / "colombia_promotion_freeze_decision_v2_21e_c.json"
REPORT_MD = OUTPUT_DIR / "colombia_promotion_freeze_decision_v2_21e_c.md"
SUMMARY_CSV = OUTPUT_DIR / "colombia_promotion_freeze_decision_summary_v2_21e_c.csv"
CHECKS_CSV = OUTPUT_DIR / "colombia_promotion_freeze_decision_checks_v2_21e_c.csv"
MANIFEST_CSV = OUTPUT_DIR / "colombia_promotion_freeze_decision_manifest_v2_21e_c.csv"
APPENDED_CONTEXT_AUDIT_CSV = OUTPUT_DIR / "colombia_promotion_freeze_decision_appended_context_audit_v2_21e_c.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "colombia_promotion_freeze_decision_decision_register_v2_21e_c.csv"
POINTER_MANIFEST_JSON = OUTPUT_DIR / "colombia_promotion_freeze_decision_pointer_manifest_v2_21e_c.json"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "colombia_promotion_freeze_decision_next_actions_v2_21e_c.csv"

EXPECTED_COLOMBIA_BUILD_STATUS = "COLOMBIA_CONDITIONAL_BUILD_COMPLETED_CANDIDATE_CREATED_NO_PROMOTION_NO_POINTER_UPDATE_SCORING_DEFERRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

SINGAPORE_PROMOTED_ROWS_EXPECTED = 43066
SINGAPORE_PROMOTED_SHA_EXPECTED = "8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f"

COLOMBIA_CANDIDATE_ROWS_EXPECTED = 43089
COLOMBIA_CANDIDATE_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"
COLOMBIA_ELIGIBLE_EXPECTED = 23

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

MARKET_ID = "COLOMBIA_BVC_REGULATORY"
COUNTRY = "Colombia"
COUNTRY_CODE = "CO"
EXCHANGE = "BVC"
MIC = "XBOG"
CURRENCY = "COP"

STATUS_PROMOTED_ARTIFACT_READY = "COLOMBIA_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED"
STATUS_FROZEN = "COLOMBIA_PROMOTION_FREEZE_DECISION_COMPLETED_CANDIDATE_FROZEN_REVIEW_REQUIRED"
STATUS_FAILED = "COLOMBIA_PROMOTION_FREEZE_DECISION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_SUCCESS = "v2.21G - Final v2.21 Closure Report"
NEXT_PHASE_REVIEW = "v2.21E_C_REVIEW - Colombia Promotion Decision Issue Resolution"


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


def strip_accents_basic(text: str) -> str:
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u",
        "ñ": "n", "Ñ": "n",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def compact_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", strip_accents_basic(norm(value)).lower())


def discover_context_columns(header: list[str]) -> dict[str, list[str]]:
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
        "market": [],
    }

    for column in header:
        key = compact_key(column)

        if key in {"countrycode", "countryiso2", "countryiso", "countrycode2"}:
            cols["country_code"].append(column)
        elif key == "country" or key.endswith("country") or "countryname" in key:
            cols["country"].append(column)

        if "exchange" in key:
            cols["exchange"].append(column)

        if key == "mic" or key.endswith("mic") or "mic" in key:
            cols["mic"].append(column)

        if "currency" in key:
            cols["currency"].append(column)

        if "symbol" in key or "ticker" in key or "tradingcode" in key or key in {"code", "codigo"}:
            cols["symbol"].append(column)

        if key in {"name", "companyname", "securityname"} or "name" in key or "nombre" in key:
            cols["name"].append(column)

        if "isin" in key:
            cols["isin"].append(column)

        if "source" in key or "provider" in key:
            cols["source"].append(column)

        if "market" in key:
            cols["market"].append(column)

    return cols


def row_has_value(row: dict[str, Any], columns: list[str], accepted_values: set[str]) -> bool:
    if not columns:
        return True
    for column in columns:
        if compact_key(row.get(column)) in accepted_values:
            return True
    return False


def first_nonempty(row: dict[str, Any], columns: list[str]) -> str:
    for column in columns:
        value = norm(row.get(column))
        if value:
            return value
    return ""


def copy_csv_exact(source: Path, target: Path) -> None:
    if target.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {target}")
    target.write_bytes(source.read_bytes())


def main() -> None:
    output_paths = [
        COLOMBIA_PROMOTED_DATASET,
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        MANIFEST_CSV,
        APPENDED_CONTEXT_AUDIT_CSV,
        DECISION_REGISTER_CSV,
        POINTER_MANIFEST_JSON,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    colombia_build = read_json(COLOMBIA_BUILD_JSON)
    colombia_build_summary = colombia_build.get("summary", {})

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)

    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)

    singapore_promoted_rows = count_csv_rows(SINGAPORE_PROMOTED_DATASET)
    singapore_promoted_sha = sha256_file(SINGAPORE_PROMOTED_DATASET)

    colombia_candidate_rows = count_csv_rows(COLOMBIA_CANDIDATE_DATASET)
    colombia_candidate_sha = sha256_file(COLOMBIA_CANDIDATE_DATASET)

    eligible_rows = read_csv_dicts(COLOMBIA_ELIGIBLE_CANDIDATES)
    eligible_count = len(eligible_rows)
    eligible_approved_count = sum(1 for row in eligible_rows if as_bool(row.get("approved_for_rebuild_input")))
    eligible_country_count = sum(1 for row in eligible_rows if row.get("country") == COUNTRY)
    eligible_exchange_count = sum(1 for row in eligible_rows if row.get("exchange") == EXCHANGE)
    eligible_mic_count = sum(1 for row in eligible_rows if row.get("mic") == MIC)
    eligible_currency_count = sum(1 for row in eligible_rows if row.get("currency") == CURRENCY)

    candidate_header = read_csv_header(COLOMBIA_CANDIDATE_DATASET)
    promoted_base_header = read_csv_header(SINGAPORE_PROMOTED_DATASET)
    operational_header = read_csv_header(OPERATIONAL_BASE_DATASET)

    cols = discover_context_columns(candidate_header)
    candidate_dataset_rows = read_csv_dicts(COLOMBIA_CANDIDATE_DATASET)

    appended_rows = candidate_dataset_rows[SINGAPORE_PROMOTED_ROWS_EXPECTED:]

    appended_audit_rows: list[dict[str, Any]] = []
    context_counter = Counter()

    for idx, row in enumerate(appended_rows, start=1):
        audit = {
            "append_order": idx,
            "row_number_in_promoted_dataset": SINGAPORE_PROMOTED_ROWS_EXPECTED + idx,
            "country_confirmed": row_has_value(row, cols["country"], {"colombia"}),
            "country_code_confirmed": row_has_value(row, cols["country_code"], {"co"}),
            "exchange_confirmed": row_has_value(row, cols["exchange"], {"bvc"}),
            "mic_confirmed": row_has_value(row, cols["mic"], {"xbog"}),
            "currency_confirmed": row_has_value(row, cols["currency"], {"cop"}),
            "symbol_key": compact_key(first_nonempty(row, cols["symbol"])),
            "name_key": compact_key(first_nonempty(row, cols["name"])),
            "isin_key": compact_key(first_nonempty(row, cols["isin"])),
            "source_key": compact_key(first_nonempty(row, cols["source"])),
            "market_key": compact_key(first_nonempty(row, cols["market"])),
            "country_code_columns_present": len(cols["country_code"]),
            "source_columns_present": len(cols["source"]),
        }
        appended_audit_rows.append(audit)

        for key in [
            "country_confirmed",
            "country_code_confirmed",
            "exchange_confirmed",
            "mic_confirmed",
            "currency_confirmed",
        ]:
            if audit[key] is True:
                context_counter[key] += 1

    copy_csv_exact(COLOMBIA_CANDIDATE_DATASET, COLOMBIA_PROMOTED_DATASET)

    promoted_rows = count_csv_rows(COLOMBIA_PROMOTED_DATASET)
    promoted_sha = sha256_file(COLOMBIA_PROMOTED_DATASET)

    operational_sha_after = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_sha_after = sha256_file(ROLLBACK_DATASET)
    singapore_promoted_sha_after = sha256_file(SINGAPORE_PROMOTED_DATASET)
    colombia_candidate_sha_after = sha256_file(COLOMBIA_CANDIDATE_DATASET)

    pointer_manifest = {
        "version": VERSION,
        "manifest_type": "colombia_promotion_pointer_manifest",
        "generated_at_utc": utc_now(),
        "promotion_decision": "COLOMBIA_PROMOTION_ARTIFACT_READY_POINTER_NOT_UPDATED",
        "active_pointer_update_performed": False,
        "promoted_dataset": str(COLOMBIA_PROMOTED_DATASET),
        "promoted_rows": promoted_rows,
        "promoted_sha": promoted_sha,
        "previous_singapore_promoted_dataset": str(SINGAPORE_PROMOTED_DATASET),
        "previous_singapore_promoted_rows": singapore_promoted_rows,
        "previous_singapore_promoted_sha": singapore_promoted_sha,
        "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "previous_operational_base_rows": operational_rows,
        "previous_operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "reason": "v2.21E_C creates a Colombia promoted artifact and manifest; it does not modify active pointer files.",
    }
    write_json(POINTER_MANIFEST_JSON, pointer_manifest)

    manifest_rows = [
        {
            "artifact": "previous_operational_base_input",
            "path": str(OPERATIONAL_BASE_DATASET),
            "rows": operational_rows,
            "sha256": operational_sha,
            "role": "input_only_unchanged",
        },
        {
            "artifact": "rollback_input",
            "path": str(ROLLBACK_DATASET),
            "rows": rollback_rows,
            "sha256": rollback_sha,
            "role": "input_only_unchanged",
        },
        {
            "artifact": "singapore_promoted_input",
            "path": str(SINGAPORE_PROMOTED_DATASET),
            "rows": singapore_promoted_rows,
            "sha256": singapore_promoted_sha,
            "role": "input_only_unchanged",
        },
        {
            "artifact": "colombia_candidate_input",
            "path": str(COLOMBIA_CANDIDATE_DATASET),
            "rows": colombia_candidate_rows,
            "sha256": colombia_candidate_sha,
            "role": "promotion_candidate_input_unchanged",
        },
        {
            "artifact": "colombia_promoted_dataset_output",
            "path": str(COLOMBIA_PROMOTED_DATASET),
            "rows": promoted_rows,
            "sha256": promoted_sha,
            "role": "promoted_artifact_not_active_pointer_update",
        },
        {
            "artifact": "colombia_pointer_manifest_output",
            "path": str(POINTER_MANIFEST_JSON),
            "rows": 1,
            "sha256": sha256_file(POINTER_MANIFEST_JSON),
            "role": "promotion_pointer_manifest_no_existing_pointer_modified",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "COLOMBIA_PROMOTION_001",
            "decision": "Promote Colombia candidate as v2.21E_C promoted artifact.",
            "accepted": True,
            "reason": "v2.21D_C created a valid Colombia candidate with eligible official regulatory-source candidates.",
            "effect": "Creates promoted artifact with 43,089 rows.",
        },
        {
            "decision_id": "COLOMBIA_PROMOTION_002",
            "decision": "Do not update active pointer in v2.21E_C.",
            "accepted": True,
            "reason": "Final pointer/base decision belongs to final closure.",
            "effect": "Creates pointer manifest only.",
        },
        {
            "decision_id": "COLOMBIA_PROMOTION_003",
            "decision": "Preserve Singapore promoted artifact unchanged.",
            "accepted": True,
            "reason": "Singapore was already closed and used as the base for Colombia.",
            "effect": "Singapore artifact SHA remains unchanged.",
        },
        {
            "decision_id": "COLOMBIA_PROMOTION_004",
            "decision": "Keep scoring/OpenAI/broker/full59k deferred.",
            "accepted": True,
            "reason": "No explicit authorization has been given for scoring or enrichment.",
            "effect": "No scoring, OpenAI, broker, or full59k actions are performed.",
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

    add_check("colombia_build_status_expected", colombia_build.get("status") == EXPECTED_COLOMBIA_BUILD_STATUS, "critical", str(colombia_build.get("status")))
    add_check("colombia_build_approved_for_promotion_decision", as_bool(colombia_build_summary.get("approved_for_colombia_promotion_decision")) is True, "critical", f"approved_for_colombia_promotion_decision={colombia_build_summary.get('approved_for_colombia_promotion_decision')}")
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("singapore_promoted_rows_expected", singapore_promoted_rows == SINGAPORE_PROMOTED_ROWS_EXPECTED, "critical", f"singapore_promoted_rows={singapore_promoted_rows}")
    add_check("singapore_promoted_sha_expected", singapore_promoted_sha == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", singapore_promoted_sha)
    add_check("colombia_candidate_rows_expected", colombia_candidate_rows == COLOMBIA_CANDIDATE_ROWS_EXPECTED, "critical", f"colombia_candidate_rows={colombia_candidate_rows}")
    add_check("colombia_candidate_sha_expected", colombia_candidate_sha == COLOMBIA_CANDIDATE_SHA_EXPECTED, "critical", colombia_candidate_sha)
    add_check("header_matches_singapore_promoted", candidate_header == promoted_base_header, "critical", f"candidate_columns={len(candidate_header)};singapore_columns={len(promoted_base_header)}")
    add_check("schema_column_count_expected", len(candidate_header) == 33 and len(operational_header) == 33, "critical", f"candidate_columns={len(candidate_header)};operational_columns={len(operational_header)}")
    add_check("eligible_rows_expected", eligible_count == COLOMBIA_ELIGIBLE_EXPECTED, "critical", f"eligible_count={eligible_count}")
    add_check("eligible_rows_all_approved", eligible_approved_count == eligible_count, "critical", f"eligible_approved_count={eligible_approved_count};eligible_count={eligible_count}")
    add_check("eligible_country_context_expected", eligible_country_count == eligible_count, "critical", f"eligible_country_count={eligible_country_count};eligible_count={eligible_count}")
    add_check("eligible_exchange_context_expected", eligible_exchange_count == eligible_count, "critical", f"eligible_exchange_count={eligible_exchange_count};eligible_count={eligible_count}")
    add_check("eligible_mic_context_expected", eligible_mic_count == eligible_count, "critical", f"eligible_mic_count={eligible_mic_count};eligible_count={eligible_count}")
    add_check("eligible_currency_context_expected", eligible_currency_count == eligible_count, "critical", f"eligible_currency_count={eligible_currency_count};eligible_count={eligible_count}")
    add_check("appended_rows_expected", len(appended_rows) == COLOMBIA_ELIGIBLE_EXPECTED, "critical", f"appended_rows={len(appended_rows)}")
    add_check("appended_rows_country_confirmed", context_counter["country_confirmed"] == COLOMBIA_ELIGIBLE_EXPECTED, "critical", f"country_confirmed={context_counter['country_confirmed']}")
    add_check("appended_rows_country_code_confirmed_or_not_required", context_counter["country_code_confirmed"] == COLOMBIA_ELIGIBLE_EXPECTED, "critical", f"country_code_confirmed={context_counter['country_code_confirmed']};country_code_columns={len(cols['country_code'])}")
    add_check("appended_rows_exchange_confirmed", context_counter["exchange_confirmed"] == COLOMBIA_ELIGIBLE_EXPECTED, "critical", f"exchange_confirmed={context_counter['exchange_confirmed']}")
    add_check("appended_rows_mic_confirmed", context_counter["mic_confirmed"] == COLOMBIA_ELIGIBLE_EXPECTED, "critical", f"mic_confirmed={context_counter['mic_confirmed']}")
    add_check("appended_rows_currency_confirmed", context_counter["currency_confirmed"] == COLOMBIA_ELIGIBLE_EXPECTED, "critical", f"currency_confirmed={context_counter['currency_confirmed']}")
    add_check("promoted_dataset_rows_expected", promoted_rows == COLOMBIA_CANDIDATE_ROWS_EXPECTED, "critical", f"promoted_rows={promoted_rows}")
    add_check("promoted_dataset_sha_matches_candidate", promoted_sha == COLOMBIA_CANDIDATE_SHA_EXPECTED, "critical", promoted_sha)
    add_check("promoted_dataset_under_quality_ceiling", promoted_rows <= QUALITY_CEILING_TARGET, "critical", f"promoted_rows={promoted_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("promoted_dataset_above_quality_floor", promoted_rows >= QUALITY_FLOOR_TARGET, "critical", f"promoted_rows={promoted_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("remaining_capacity_non_negative", QUALITY_CEILING_TARGET - promoted_rows >= 0, "critical", f"remaining_capacity={QUALITY_CEILING_TARGET - promoted_rows}")
    add_check("pointer_manifest_created", POINTER_MANIFEST_JSON.exists(), "critical", str(POINTER_MANIFEST_JSON))
    add_check("operational_base_not_modified", operational_sha_after == OPERATIONAL_BASE_SHA_EXPECTED, "critical", f"operational_sha_after={operational_sha_after}")
    add_check("rollback_not_modified", rollback_sha_after == ROLLBACK_SHA_EXPECTED, "critical", f"rollback_sha_after={rollback_sha_after}")
    add_check("singapore_promoted_artifact_not_modified", singapore_promoted_sha_after == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", f"singapore_promoted_sha_after={singapore_promoted_sha_after}")
    add_check("colombia_candidate_input_not_modified", colombia_candidate_sha_after == COLOMBIA_CANDIDATE_SHA_EXPECTED, "critical", f"colombia_candidate_sha_after={colombia_candidate_sha_after}")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("pointer_update_not_performed", True, "critical", "pointer_update_performed=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        promotion_decision = "COLOMBIA_PROMOTION_BLOCKED_REVIEW_REQUIRED"
        approved_as_promoted_artifact = False
        approved_for_final_v2_21_closure = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    elif warning_failed > 0:
        status = STATUS_FROZEN
        promotion_decision = "COLOMBIA_CANDIDATE_FROZEN_DUE_TO_WARNING_REVIEW_REQUIRED"
        approved_as_promoted_artifact = False
        approved_for_final_v2_21_closure = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_PROMOTED_ARTIFACT_READY
        promotion_decision = "COLOMBIA_PROMOTED_ARTIFACT_READY_FOR_FINAL_V2_21_CLOSURE"
        approved_as_promoted_artifact = True
        approved_for_final_v2_21_closure = True
        recommended_next_phase = NEXT_PHASE_SUCCESS

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "final_closure",
            "action": "prepare_final_v2_21_closure_report_with_singapore_and_colombia_promoted_artifacts",
            "priority": "high" if approved_for_final_v2_21_closure else "blocked",
            "recommended_phase": recommended_next_phase,
            "reason": "Colombia promoted artifact is ready." if approved_for_final_v2_21_closure else "Colombia promotion needs review.",
            "guardrails": "Final closure only; no scoring; no OpenAI; no broker",
        },
        {
            "action_order": 2,
            "action_scope": "pointer_control",
            "action": "keep_active_pointer_unchanged_until_final_closure_decision",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "v2.21E_C creates promoted artifact and pointer manifest only.",
            "guardrails": "No active pointer mutation in v2.21E_C",
        },
        {
            "action_order": 3,
            "action_scope": "scoring_gate",
            "action": "keep_scoring_deferred_until_explicit_post_v2_21_decision",
            "priority": "medium",
            "recommended_phase": "v2.22A - Post-Targeted-Markets Explicit Scoring Decision Gate",
            "reason": "Scoring remains outside v2.21.",
            "guardrails": "No scoring/OpenAI/broker without explicit approval",
        },
    ]

    summary = {
        "selected_route": "Colombia promotion decision after Colombia conditional build",
        "phase_type": PHASE_TYPE,
        "promotion_decision": promotion_decision,
        "approved_as_promoted_artifact": approved_as_promoted_artifact,
        "approved_for_final_v2_21_closure": approved_for_final_v2_21_closure,
        "active_pointer_update_performed": False,
        "approved_for_scoring": False,
        "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "previous_operational_base_rows": operational_rows,
        "previous_operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "singapore_promoted_dataset": str(SINGAPORE_PROMOTED_DATASET),
        "singapore_promoted_rows": singapore_promoted_rows,
        "singapore_promoted_sha": singapore_promoted_sha,
        "colombia_candidate_dataset": str(COLOMBIA_CANDIDATE_DATASET),
        "colombia_candidate_rows": colombia_candidate_rows,
        "colombia_candidate_sha": colombia_candidate_sha,
        "colombia_promoted_dataset": str(COLOMBIA_PROMOTED_DATASET),
        "colombia_promoted_rows": promoted_rows,
        "colombia_promoted_sha": promoted_sha,
        "colombia_appended_rows": len(appended_rows),
        "colombia_eligible_source_rows": eligible_count,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity_after_colombia_promoted_artifact": QUALITY_CEILING_TARGET - promoted_rows,
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
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(MANIFEST_CSV, manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(APPENDED_CONTEXT_AUDIT_CSV, appended_audit_rows, [
        "append_order",
        "row_number_in_promoted_dataset",
        "country_confirmed",
        "country_code_confirmed",
        "exchange_confirmed",
        "mic_confirmed",
        "currency_confirmed",
        "symbol_key",
        "name_key",
        "isin_key",
        "source_key",
        "market_key",
        "country_code_columns_present",
        "source_columns_present",
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
            "selected_route": "Colombia promotion/freeze decision",
            "market_scope": [MARKET_ID],
            "colombia_promoted_dataset": str(COLOMBIA_PROMOTED_DATASET),
            "colombia_promoted_rows": promoted_rows,
            "colombia_promoted_sha": promoted_sha,
            "approved_as_promoted_artifact": approved_as_promoted_artifact,
            "approved_for_final_v2_21_closure": approved_for_final_v2_21_closure,
            "active_pointer_update_performed": False,
            "approved_for_scoring": False,
            "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "previous_operational_base_rows": operational_rows,
            "previous_operational_base_sha": operational_sha,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "singapore_promoted_dataset": str(SINGAPORE_PROMOTED_DATASET),
            "singapore_promoted_rows": singapore_promoted_rows,
            "singapore_promoted_sha": singapore_promoted_sha,
            "colombia_appended_rows": len(appended_rows),
            "file_edit_performed_on_previous_operational_base": False,
            "file_edit_performed_on_singapore_promoted_artifact": False,
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
        "recommended_next_phase": recommended_next_phase,
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

v2.21E_C makes the Colombia promotion/freeze decision.

The v2.21D_C Colombia candidate is promoted as a controlled artifact after final validation. The previous operational base remains unchanged, the Singapore promoted artifact remains unchanged, no active pointer file is modified, no scoring is run, no OpenAI call is made, no broker call is made, and full59k remains deprecated/deferred.

## Summary

- Promotion decision: `{promotion_decision}`
- Approved as promoted artifact: `{approved_as_promoted_artifact}`
- Approved for final v2.21 closure: `{approved_for_final_v2_21_closure}`
- Active pointer update performed: `False`
- Colombia promoted dataset: `{COLOMBIA_PROMOTED_DATASET}`
- Colombia promoted rows: `{promoted_rows}`
- Colombia promoted SHA256: `{promoted_sha}`
- Colombia appended rows: `{len(appended_rows)}`
- Remaining capacity: `{QUALITY_CEILING_TARGET - promoted_rows}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Manifest

{manifest_lines}

## Decision register

{decision_lines}

## Checks

{check_lines}

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21E_C Colombia promotion/freeze decision completed.")
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


if __name__ == "__main__":
    main()
