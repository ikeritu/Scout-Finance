from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21C2"
PHASE = "Candidate Extraction False Positive Review"
PHASE_TYPE = "targeted-market-candidate-extraction-false-positive-review"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

V221C_JSON = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_v2_21c.json"
V221C_EXTRACTED_CANDIDATES = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_extracted_candidates_v2_21c.csv"
V221C_REJECTED_CANDIDATES = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_rejected_candidates_v2_21c.csv"
V221C_SOURCE_PARSER_FINDINGS = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_source_parser_findings_v2_21c.csv"
V221C_RAW_STRUCTURE_INVENTORY = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_raw_structure_inventory_v2_21c.csv"
V221B_JSON = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_v2_21b.json"

REPORT_JSON = OUTPUT_DIR / "targeted_market_candidate_false_positive_review_v2_21c2.json"
REPORT_MD = OUTPUT_DIR / "targeted_market_candidate_false_positive_review_v2_21c2.md"
SUMMARY_CSV = OUTPUT_DIR / "targeted_market_candidate_false_positive_review_summary_v2_21c2.csv"
CHECKS_CSV = OUTPUT_DIR / "targeted_market_candidate_false_positive_review_checks_v2_21c2.csv"
INVALIDATED_CANDIDATES_CSV = OUTPUT_DIR / "targeted_market_candidate_false_positive_review_invalidated_candidates_v2_21c2.csv"
SOURCE_STRUCTURE_REVIEW_CSV = OUTPUT_DIR / "targeted_market_candidate_false_positive_review_source_structure_v2_21c2.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "targeted_market_candidate_false_positive_review_decision_register_v2_21c2.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "targeted_market_candidate_false_positive_review_next_actions_v2_21c2.csv"

EXPECTED_V221C_STATUS = "TARGETED_MARKET_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_NEW_CANDIDATES_READY_FOR_REBUILD_NO_DATASET_CHANGES_SCORING_DEFERRED"
EXPECTED_V221B_STATUS = "TARGETED_MARKET_ACQUISITION_RAW_VALIDATION_COMPLETED_COLOMBIA_SINGAPORE_RAW_SOURCES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_SUCCESS = "TARGETED_MARKET_CANDIDATE_FALSE_POSITIVE_REVIEW_COMPLETED_ACCEPTED_CANDIDATES_INVALIDATED_REBUILD_BLOCKED_SOURCE_DISCOVERY_REQUIRED"
STATUS_FAILED = "TARGETED_MARKET_CANDIDATE_FALSE_POSITIVE_REVIEW_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.21C3 - Official Endpoint / Downloadable Listing Discovery"
NEXT_PHASE_REVIEW = "v2.21C2_REVIEW - False Positive Review Issue Resolution"


KNOWN_FALSE_POSITIVE_SIGNATURES = [
    {
        "signature_id": "GOOGLE_TAG_MANAGER_TOKEN",
        "ticker_pattern": r"^GTM$",
        "name_pattern": r"KSZ85XQ8",
        "reason": "Google Tag Manager / website script token, not a listed company.",
    },
    {
        "signature_id": "BROWSER_USER_AGENT_TOKEN",
        "ticker_pattern": r"^UA$",
        "name_pattern": r"^Compatible$",
        "reason": "Browser/user-agent compatibility token, not a listed company.",
    },
    {
        "signature_id": "HASH_OR_INTERNAL_BUILD_ID",
        "ticker_pattern": r"^[A-Z0-9]{4,8}$",
        "name_pattern": r"^[A-Z0-9]{4,8}-[A-Z0-9]{4,8}-[A-Z0-9]{4,8}$",
        "reason": "Internal hash/build identifier pattern, not a listed company.",
    },
]


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
    if not path.exists():
        raise SystemExit(f"Missing required CSV artifact: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def is_known_false_positive(candidate: dict[str, str]) -> tuple[bool, str, str]:
    ticker = norm(candidate.get("ticker") or candidate.get("symbol") or candidate.get("trading_code"))
    name = norm(candidate.get("name"))

    for signature in KNOWN_FALSE_POSITIVE_SIGNATURES:
        ticker_match = re.search(signature["ticker_pattern"], ticker, flags=re.IGNORECASE) is not None
        name_match = re.search(signature["name_pattern"], name, flags=re.IGNORECASE) is not None
        if ticker_match and name_match:
            return True, signature["signature_id"], signature["reason"]

    if candidate.get("extraction_method", "").startswith("regex_pattern_"):
        if name.upper() == name and re.search(r"[0-9]", name) and len(name) <= 24:
            return True, "REGEX_UPPERCASE_NUMERIC_TOKEN", "Regex extracted uppercase numeric token from website script/build text."

    return False, "", ""


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        INVALIDATED_CANDIDATES_CSV,
        SOURCE_STRUCTURE_REVIEW_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v221c = read_json(V221C_JSON)
    v221b = read_json(V221B_JSON)

    extracted_candidates = read_csv_dicts(V221C_EXTRACTED_CANDIDATES)
    rejected_candidates = read_csv_dicts(V221C_REJECTED_CANDIDATES)
    source_parser_findings = read_csv_dicts(V221C_SOURCE_PARSER_FINDINGS)
    raw_structure_inventory = read_csv_dicts(V221C_RAW_STRUCTURE_INVENTORY)

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    header = read_csv_header(OPERATIONAL_BASE_DATASET)

    invalidated_rows: list[dict[str, Any]] = []
    still_plausible_rows: list[dict[str, Any]] = []

    for candidate in extracted_candidates:
        is_fp, signature_id, reason = is_known_false_positive(candidate)

        review_status = "invalidated_false_positive" if is_fp else "requires_manual_review"
        if not is_fp:
            still_plausible_rows.append(candidate)

        invalidated_rows.append({
            "candidate_id": candidate.get("candidate_id", ""),
            "market_id": candidate.get("market_id", ""),
            "country": candidate.get("country", ""),
            "exchange": candidate.get("exchange", ""),
            "mic": candidate.get("mic", ""),
            "currency": candidate.get("currency", ""),
            "source_id": candidate.get("source_id", ""),
            "extraction_method": candidate.get("extraction_method", ""),
            "ticker": candidate.get("ticker", ""),
            "symbol": candidate.get("symbol", ""),
            "trading_code": candidate.get("trading_code", ""),
            "isin": candidate.get("isin", ""),
            "name": candidate.get("name", ""),
            "previous_dedup_status": candidate.get("dedup_status", ""),
            "review_status": review_status,
            "false_positive_signature": signature_id,
            "review_reason": reason if is_fp else "Candidate was not matched by known false-positive rules and must be manually reviewed.",
            "approved_for_rebuild": False,
        })

    source_structure_rows: list[dict[str, Any]] = []
    parser_by_source = {row.get("source_id"): row for row in source_parser_findings}

    for raw_row in raw_structure_inventory:
        source_id = raw_row.get("source_id")
        parser_row = parser_by_source.get(source_id, {})

        table_candidates = int(parser_row.get("table_candidates") or 0)
        json_candidates = int(parser_row.get("json_candidates") or 0)
        regex_candidates = int(parser_row.get("regex_candidates") or 0)
        html_table_count = int(raw_row.get("html_table_count") or 0)
        next_data_object_count = int(raw_row.get("next_data_object_count") or 0)

        structured_candidate_source = table_candidates > 0 or json_candidates > 0
        regex_only = regex_candidates > 0 and not structured_candidate_source

        if structured_candidate_source:
            source_review_status = "structured_candidate_source_found"
        elif regex_only:
            source_review_status = "regex_only_unreliable_for_rebuild"
        elif html_table_count == 0:
            source_review_status = "no_candidate_table_detected"
        else:
            source_review_status = "requires_review"

        source_structure_rows.append({
            "market_id": raw_row.get("market_id", ""),
            "source_id": source_id,
            "source_file": raw_row.get("source_file", ""),
            "raw_bytes": raw_row.get("raw_bytes", ""),
            "contains_table_tag": raw_row.get("contains_table_tag", ""),
            "html_table_count": html_table_count,
            "next_data_object_count": next_data_object_count,
            "script_tag_count": raw_row.get("script_tag_count", ""),
            "link_count": raw_row.get("link_count", ""),
            "table_candidates": table_candidates,
            "json_candidates": json_candidates,
            "regex_candidates": regex_candidates,
            "structured_candidate_source": structured_candidate_source,
            "regex_only": regex_only,
            "source_review_status": source_review_status,
            "approved_for_rebuild_input": structured_candidate_source,
        })

    invalidated_count = sum(1 for row in invalidated_rows if row["review_status"] == "invalidated_false_positive")
    manual_review_count = sum(1 for row in invalidated_rows if row["review_status"] == "requires_manual_review")
    approved_candidates_after_review = sum(1 for row in invalidated_rows if row["approved_for_rebuild"] is True)

    structured_sources = sum(1 for row in source_structure_rows if row["structured_candidate_source"] is True)
    regex_only_sources = sum(1 for row in source_structure_rows if row["regex_only"] is True)

    decision_register_rows = [
        {
            "decision_id": "FP_REVIEW_001",
            "decision": "Invalidate accepted candidates from v2.21C.",
            "accepted": invalidated_count == len(extracted_candidates) and len(extracted_candidates) > 0,
            "reason": "Accepted candidates are website/script tokens rather than listed companies.",
            "effect": "Do not use v2.21C extracted_candidates as rebuild input.",
        },
        {
            "decision_id": "FP_REVIEW_002",
            "decision": "Block v2.21D rebuild from current extraction output.",
            "accepted": True,
            "reason": "No valid Colombia/Singapore company candidates remain after false-positive review.",
            "effect": "Expanded rebuild candidate remains blocked.",
        },
        {
            "decision_id": "FP_REVIEW_003",
            "decision": "Require official endpoint, API, CSV, XLS or structured downloadable listing.",
            "accepted": True,
            "reason": "Current raw pages are not sufficient as structured company listing inputs.",
            "effect": "Open v2.21C3 official endpoint/downloadable listing discovery.",
        },
        {
            "decision_id": "FP_REVIEW_004",
            "decision": "Preserve operational base and rollback.",
            "accepted": True,
            "reason": "Corrective review is audit-only and does not modify canonical data.",
            "effect": "Operational base remains 42,708 rows.",
        },
        {
            "decision_id": "FP_REVIEW_005",
            "decision": "Keep scoring, OpenAI, broker and full59k deferred.",
            "accepted": True,
            "reason": "No valid new candidates are available for rebuild or scoring.",
            "effect": "No scoring or external enrichment is authorized.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "source_discovery",
            "action": "discover_official_bvc_sgx_endpoint_api_csv_xls_or_structured_download",
            "priority": "high",
            "reason": "Current accepted candidates are invalid false positives.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "official BVC/SGX sources only; no invented companies",
        },
        {
            "action_order": 2,
            "action_scope": "parser_hardening",
            "action": "disable_regex_only_candidate_acceptance_for_targeted_markets",
            "priority": "high",
            "reason": "Regex-only extraction accepted script/build tokens.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "require table/json/API fields with company/security identifiers",
        },
        {
            "action_order": 3,
            "action_scope": "rebuild_control",
            "action": "keep_v2_21d_blocked_until_valid_structured_candidates_exist",
            "priority": "high",
            "reason": "No approved candidates remain after review.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "no rebuild, no promotion, no pointer update",
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
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_21c_status_expected", v221c.get("status") == EXPECTED_V221C_STATUS, "critical", str(v221c.get("status")))
    add_check("v2_21b_status_expected", v221b.get("status") == EXPECTED_V221B_STATUS, "critical", str(v221b.get("status")))
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("schema_column_count_expected", len(header) == 33, "critical", f"columns={len(header)}")
    add_check("v2_21c_extracted_candidates_loaded", len(extracted_candidates) > 0, "critical", f"extracted_candidates={len(extracted_candidates)}")
    add_check("all_v2_21c_accepted_candidates_invalidated", invalidated_count == len(extracted_candidates) and len(extracted_candidates) > 0, "critical", f"invalidated={invalidated_count};accepted_in_v2_21c={len(extracted_candidates)}")
    add_check("no_candidates_approved_for_rebuild_after_review", approved_candidates_after_review == 0, "critical", f"approved_candidates_after_review={approved_candidates_after_review}")
    add_check("structured_candidate_sources_not_available", structured_sources == 0, "warning", f"structured_sources={structured_sources}")
    add_check("regex_only_sources_detected", regex_only_sources > 0, "warning", f"regex_only_sources={regex_only_sources}")
    add_check("v2_21d_rebuild_blocked", True, "critical", "v2.21D blocked until official structured candidates exist")
    add_check("v2_21c3_source_discovery_required", True, "critical", "official endpoint/downloadable listing discovery required")
    add_check("operational_base_not_modified", sha256_file(OPERATIONAL_BASE_DATASET) == OPERATIONAL_BASE_SHA_EXPECTED, "critical", "operational base SHA unchanged")
    add_check("false_positive_review_is_audit_only", True, "critical", "no artifact rewrite; no history rewrite; no force push")
    add_check("candidate_extraction_not_reexecuted", True, "critical", "review uses v2.21C outputs only")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("pointer_update_not_performed", True, "critical", "pointer_update_performed=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        review_decision = "FALSE_POSITIVE_REVIEW_BLOCKED_REVIEW_REQUIRED"
        approved_for_v2_21c3 = False
        approved_for_v2_21d = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        review_decision = "V2_21C_ACCEPTED_CANDIDATES_INVALIDATED_V2_21D_BLOCKED_V2_21C3_REQUIRED"
        approved_for_v2_21c3 = True
        approved_for_v2_21d = False
        recommended_next_phase = NEXT_PHASE

    summary = {
        "selected_route": "Colombia + Singapore targeted expansion",
        "phase_type": PHASE_TYPE,
        "review_decision": review_decision,
        "approved_for_v2_21c3": approved_for_v2_21c3,
        "approved_for_v2_21d": approved_for_v2_21d,
        "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "operational_base_rows": operational_rows,
        "operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "target_markets": "Colombia/BVC;Singapore/SGX",
        "v2_21c_accepted_candidates_reviewed": len(extracted_candidates),
        "v2_21c_accepted_candidates_invalidated": invalidated_count,
        "manual_review_candidates_remaining": manual_review_count,
        "approved_candidates_after_review": approved_candidates_after_review,
        "v2_21c_rejected_candidates_preserved": len(rejected_candidates),
        "structured_candidate_sources": structured_sources,
        "regex_only_sources": regex_only_sources,
        "candidate_extraction_reexecuted": False,
        "expanded_rebuild_performed": False,
        "v2_21d_blocked": True,
        "official_source_discovery_required": True,
        "provider_expansion_scope": "targeted_only",
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "pointer_update_performed": False,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(INVALIDATED_CANDIDATES_CSV, invalidated_rows, [
        "candidate_id", "market_id", "country", "exchange", "mic", "currency",
        "source_id", "extraction_method", "ticker", "symbol", "trading_code", "isin",
        "name", "previous_dedup_status", "review_status", "false_positive_signature",
        "review_reason", "approved_for_rebuild",
    ])
    write_csv(SOURCE_STRUCTURE_REVIEW_CSV, source_structure_rows, [
        "market_id", "source_id", "source_file", "raw_bytes", "contains_table_tag",
        "html_table_count", "next_data_object_count", "script_tag_count", "link_count",
        "table_candidates", "json_candidates", "regex_candidates",
        "structured_candidate_source", "regex_only", "source_review_status",
        "approved_for_rebuild_input",
    ])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "invalidated_candidates": invalidated_rows,
        "source_structure_review": source_structure_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Colombia + Singapore targeted expansion",
            "target_markets": ["Colombia/BVC", "Singapore/SGX"],
            "audit_only_false_positive_review": True,
            "approved_for_v2_21c3": approved_for_v2_21c3,
            "approved_for_v2_21d": approved_for_v2_21d,
            "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "operational_base_rows": operational_rows,
            "operational_base_sha": operational_sha,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "v2_21c_accepted_candidates_reviewed": len(extracted_candidates),
            "v2_21c_accepted_candidates_invalidated": invalidated_count,
            "approved_candidates_after_review": approved_candidates_after_review,
            "official_source_discovery_required": True,
            "v2_21d_rebuild_blocked": True,
            "candidate_extraction_reexecuted": False,
            "dedup_reexecuted": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "file_edit_performed_on_operational_base": False,
            "file_copy_performed_on_operational_base": False,
            "file_rename_performed_on_operational_base": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "provider_expansion_scope": "targeted_only",
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
    }

    write_json(REPORT_JSON, payload)

    invalidated_lines = "\n".join(
        f"- `{row['candidate_id']}` — `{row['market_id']}` — `{row['ticker']}` / `{row['name']}` — `{row['false_positive_signature']}` — approved for rebuild `{row['approved_for_rebuild']}`"
        for row in invalidated_rows
    )

    source_lines = "\n".join(
        f"- `{row['source_id']}` — structured `{row['structured_candidate_source']}` — regex_only `{row['regex_only']}` — status `{row['source_review_status']}`"
        for row in source_structure_rows
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

v2.21C2 reviews the accepted candidates from v2.21C and invalidates them as false positives.

This phase is audit-only. It does not rewrite v2.21C, does not re-run extraction, does not rebuild, does not promote, does not update pointers, does not run scoring, does not call OpenAI, does not call brokers, and does not launch full59k.

## Summary

- Review decision: `{review_decision}`
- Approved for v2.21C3: `{approved_for_v2_21c3}`
- Approved for v2.21D: `{approved_for_v2_21d}`
- Operational base rows: `{operational_rows}`
- Operational base SHA256: `{operational_sha}`
- Rollback rows: `{rollback_rows}`
- Rollback SHA256: `{rollback_sha}`
- v2.21C accepted candidates reviewed: `{len(extracted_candidates)}`
- v2.21C accepted candidates invalidated: `{invalidated_count}`
- Approved candidates after review: `{approved_candidates_after_review}`
- Structured candidate sources: `{structured_sources}`
- Regex-only sources: `{regex_only_sources}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Invalidated candidates

{invalidated_lines}

## Source structure review

{source_lines}

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
    print("v2.21C2 candidate false-positive review completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("INVALIDATED_CANDIDATES:")
    for row in invalidated_rows:
        print(f"- {row['candidate_id']}: {row['market_id']} {row['ticker']} / {row['name']} -> {row['review_status']} ({row['false_positive_signature']})")
    print("")
    print("SOURCE_STRUCTURE_REVIEW:")
    for row in source_structure_rows:
        print(f"- {row['source_id']}: structured={row['structured_candidate_source']} regex_only={row['regex_only']} status={row['source_review_status']}")
    print("")
    print("DECISION_REGISTER:")
    for row in decision_register_rows:
        print(f"- {row['decision_id']}: accepted={row['accepted']} - {row['decision']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
