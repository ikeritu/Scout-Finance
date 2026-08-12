from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21A"
PHASE = "Colombia + Singapore Targeted Expansion Gate"
PHASE_TYPE = "targeted-market-gap-decision-gate-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
V220T_JSON = OUTPUT_DIR / "asx_final_promotion_closure_report_v2_20t.json"

REPORT_JSON = OUTPUT_DIR / "targeted_market_gap_decision_gate_v2_21a.json"
REPORT_MD = OUTPUT_DIR / "targeted_market_gap_decision_gate_v2_21a.md"
SUMMARY_CSV = OUTPUT_DIR / "targeted_market_gap_decision_gate_summary_v2_21a.csv"
CHECKS_CSV = OUTPUT_DIR / "targeted_market_gap_decision_gate_checks_v2_21a.csv"
TARGET_MARKETS_CSV = OUTPUT_DIR / "targeted_market_gap_decision_gate_target_markets_v2_21a.csv"
SOURCE_CANDIDATES_CSV = OUTPUT_DIR / "targeted_market_gap_decision_gate_source_candidates_v2_21a.csv"
COVERAGE_GAP_CSV = OUTPUT_DIR / "targeted_market_gap_decision_gate_current_coverage_gap_v2_21a.csv"
CAPACITY_CONTROLS_CSV = OUTPUT_DIR / "targeted_market_gap_decision_gate_capacity_controls_v2_21a.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "targeted_market_gap_decision_gate_decision_register_v2_21a.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "targeted_market_gap_decision_gate_next_actions_v2_21a.csv"

EXPECTED_V220T_STATUS = "ASX_FINAL_PROMOTION_CLOSURE_REPORT_COMPLETED_OPERATIONAL_BASE_RECOGNIZED_42708_ROWS_ROLLBACK_AVAILABLE_SCORING_DEFERRED_FULL59K_DEPRECATED"
EXPECTED_V220T_DECISION = "ASX_PROMOTION_CLOSED_PROMOTED_CANONICAL_RECOGNIZED_AS_OPERATIONAL_BASE_SCORING_DEFERRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

STATUS_SUCCESS = "TARGETED_MARKET_GAP_DECISION_GATE_COMPLETED_COLOMBIA_SINGAPORE_APPROVED_FOR_PLANNING_42708_ROWS_NO_DATA_CHANGES_SCORING_DEFERRED"
STATUS_FAILED = "TARGETED_MARKET_GAP_DECISION_GATE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.21B - Colombia/BVC + Singapore/SGX Acquisition & Raw Validation"
NEXT_PHASE_REVIEW = "v2.21A_REVIEW - Targeted Market Gap Decision Gate Review"


TARGET_MARKETS = [
    {
        "market_id": "COLOMBIA_BVC",
        "country": "Colombia",
        "country_codes": ["CO", "Colombia"],
        "exchange_candidates": ["BVC", "Bolsa de Valores de Colombia"],
        "mic_candidates": ["XBOG"],
        "currency_candidates": ["COP"],
        "priority": "high",
        "reason": "User-requested missing market; small targeted LatAm expansion.",
        "expected_capacity_profile": "small",
    },
    {
        "market_id": "SINGAPORE_SGX",
        "country": "Singapore",
        "country_codes": ["SG", "Singapore"],
        "exchange_candidates": ["SGX", "Singapore Exchange"],
        "mic_candidates": ["XSES"],
        "currency_candidates": ["SGD"],
        "priority": "high",
        "reason": "User-requested missing market; high-quality Asian developed market coverage.",
        "expected_capacity_profile": "small_to_medium",
    },
]


SOURCE_CANDIDATES = [
    {
        "market_id": "COLOMBIA_BVC",
        "source_id": "BVC_OFFICIAL_ISSUERS_AND_PROSPECTUSES",
        "provider": "BVC",
        "source_type": "official_exchange_issuer_information",
        "expected_fields": "issuer_name,ticker_or_security_name,isin_if_available,instrument_type,country,currency",
        "allowed_in_v2_21a": False,
        "planned_for": "v2.21B",
        "notes": "Use official BVC issuer/prospectus/results information; acquisition is not performed in this gate.",
    },
    {
        "market_id": "COLOMBIA_BVC",
        "source_id": "BVC_RESULTS_AND_ISSUER_INFORMATION",
        "provider": "BVC",
        "source_type": "official_exchange_results_and_issuer_information",
        "expected_fields": "issuer_name,security_type,market_segment,listing_or_issue_reference",
        "allowed_in_v2_21a": False,
        "planned_for": "v2.21B",
        "notes": "Candidate secondary official source for issuer/result cross-checking.",
    },
    {
        "market_id": "SINGAPORE_SGX",
        "source_id": "SGX_SECURITIES_PRICES",
        "provider": "SGX",
        "source_type": "official_exchange_securities_prices",
        "expected_fields": "security_name,trading_code,exchange,primary_listing,currency,security_type",
        "allowed_in_v2_21a": False,
        "planned_for": "v2.21B",
        "notes": "Use official SGX securities prices/listed securities information; acquisition is not performed in this gate.",
    },
    {
        "market_id": "SINGAPORE_SGX",
        "source_id": "SGX_CORPORATE_INFORMATION",
        "provider": "SGX",
        "source_type": "official_exchange_corporate_information",
        "expected_fields": "company_name,stock_code,sector,listing_board,country,currency",
        "allowed_in_v2_21a": False,
        "planned_for": "v2.21B",
        "notes": "Candidate secondary official source for company metadata enrichment.",
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
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
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
    return str(value or "").strip()


def lower(value: Any) -> str:
    return norm(value).lower()


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        TARGET_MARKETS_CSV,
        SOURCE_CANDIDATES_CSV,
        COVERAGE_GAP_CSV,
        CAPACITY_CONTROLS_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220t = read_json(V220T_JSON)
    v220t_summary = v220t.get("closure_summary", {})

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)

    header = read_csv_header(OPERATIONAL_BASE_DATASET)
    rows = read_csv_dicts(OPERATIONAL_BASE_DATASET)

    columns = set(header)

    country_counter = Counter(norm(row.get("country", "")) for row in rows)
    exchange_counter = Counter(norm(row.get("exchange", "")) for row in rows)
    mic_counter = Counter(norm(row.get("mic", "")) for row in rows)
    currency_counter = Counter(norm(row.get("currency", "")) for row in rows)

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

    add_check("v2_20t_status_expected", v220t.get("status") == EXPECTED_V220T_STATUS, "critical", str(v220t.get("status")))
    add_check("v2_20t_closure_decision_expected", v220t_summary.get("closure_decision") == EXPECTED_V220T_DECISION, "critical", str(v220t_summary.get("closure_decision")))
    add_check("v2_20t_asx_promotion_closed", bool(v220t_summary.get("asx_promotion_closed")) is True, "critical", f"asx_promotion_closed={v220t_summary.get('asx_promotion_closed')}")
    add_check("v2_20t_scoring_deferred", bool(v220t_summary.get("scoring_authorized")) is False, "critical", f"scoring_authorized={v220t_summary.get('scoring_authorized')}")
    add_check("v2_20t_provider_expansion_was_frozen_before_new_gate", bool(v220t_summary.get("provider_expansion_frozen")) is True, "critical", f"provider_expansion_frozen={v220t_summary.get('provider_expansion_frozen')}")
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("schema_column_count_expected", len(header) == 33, "critical", f"columns={len(header)}")
    add_check("required_country_column_present", "country" in columns, "critical", "country column present")
    add_check("required_exchange_column_present", "exchange" in columns, "critical", "exchange column present")
    add_check("required_mic_column_present", "mic" in columns, "critical", "mic column present")
    add_check("required_currency_column_present", "currency" in columns, "critical", "currency column present")

    remaining_capacity = QUALITY_CEILING_TARGET - operational_rows
    add_check("operational_floor_already_achieved", operational_rows >= QUALITY_FLOOR_TARGET, "critical", f"rows={operational_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("operational_ceiling_capacity_available", remaining_capacity > 0, "critical", f"remaining_capacity={remaining_capacity}")
    add_check("remaining_capacity_at_least_100_rows", remaining_capacity >= 100, "warning", f"remaining_capacity={remaining_capacity}")

    target_market_rows: list[dict[str, Any]] = []
    coverage_gap_rows: list[dict[str, Any]] = []

    all_target_markets_missing = True

    for market in TARGET_MARKETS:
        market_id = market["market_id"]
        country_values = set(market["country_codes"])
        exchange_values = set(market["exchange_candidates"])
        mic_values = set(market["mic_candidates"])
        currency_values = set(market["currency_candidates"])

        country_hits = sum(count for value, count in country_counter.items() if value in country_values)
        exchange_hits = sum(count for value, count in exchange_counter.items() if value in exchange_values)
        mic_hits = sum(count for value, count in mic_counter.items() if value in mic_values)
        currency_hits = sum(count for value, count in currency_counter.items() if value in currency_values)

        market_present = any([country_hits > 0, exchange_hits > 0, mic_hits > 0, currency_hits > 0])
        if market_present:
            all_target_markets_missing = False

        target_market_rows.append({
            "market_id": market_id,
            "country": market["country"],
            "country_codes": "|".join(market["country_codes"]),
            "exchange_candidates": "|".join(market["exchange_candidates"]),
            "mic_candidates": "|".join(market["mic_candidates"]),
            "currency_candidates": "|".join(market["currency_candidates"]),
            "priority": market["priority"],
            "expected_capacity_profile": market["expected_capacity_profile"],
            "currently_present": market_present,
            "approved_for_planning": not market_present,
            "reason": market["reason"],
        })

        coverage_gap_rows.append({
            "market_id": market_id,
            "country": market["country"],
            "country_hits": country_hits,
            "exchange_hits": exchange_hits,
            "mic_hits": mic_hits,
            "currency_hits": currency_hits,
            "market_present": market_present,
            "gap_confirmed": not market_present,
        })

        add_check(f"target_market_gap_confirmed::{market_id}", not market_present, "warning", f"country_hits={country_hits};exchange_hits={exchange_hits};mic_hits={mic_hits};currency_hits={currency_hits}")

    source_candidate_rows = SOURCE_CANDIDATES

    capacity_control_rows = [
        {
            "control_id": "CAPACITY_001",
            "control": "operational_base_current_rows",
            "value": operational_rows,
            "limit": QUALITY_CEILING_TARGET,
            "passed": operational_rows <= QUALITY_CEILING_TARGET,
            "detail": "Current operational base remains under quality ceiling.",
        },
        {
            "control_id": "CAPACITY_002",
            "control": "remaining_capacity_to_quality_ceiling",
            "value": remaining_capacity,
            "limit": QUALITY_CEILING_TARGET,
            "passed": remaining_capacity > 0,
            "detail": "Capacity available for targeted Colombia + Singapore expansion.",
        },
        {
            "control_id": "CAPACITY_003",
            "control": "expansion_scope",
            "value": "Colombia + Singapore only",
            "limit": "no_global_expansion",
            "passed": True,
            "detail": "No full59k, no global provider sweep, no additional markets.",
        },
        {
            "control_id": "CAPACITY_004",
            "control": "overflow_rule",
            "value": "apply_quality_filters_if_candidate_exceeds_ceiling",
            "limit": QUALITY_CEILING_TARGET,
            "passed": True,
            "detail": "If expanded candidate exceeds 45k, prioritize common equities and exclude ETFs/funds/warrants/rights/structured products.",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "TARGET_GAP_001",
            "decision": "Approve Colombia + Singapore targeted expansion planning.",
            "accepted": critical_failed == 0,
            "reason": "User requested both markets; current operational base has capacity below 45k ceiling.",
            "effect": "Open v2.21B acquisition/raw validation planning for BVC and SGX only.",
        },
        {
            "decision_id": "TARGET_GAP_002",
            "decision": "Keep expansion narrow.",
            "accepted": True,
            "reason": "This is a market gap patch, not a global expansion route.",
            "effect": "No additional providers beyond Colombia/BVC and Singapore/SGX.",
        },
        {
            "decision_id": "TARGET_GAP_003",
            "decision": "Do not authorize scoring.",
            "accepted": True,
            "reason": "Scoring remains deferred until after targeted markets closure.",
            "effect": "No scoring, OpenAI or broker calls in v2.21A.",
        },
        {
            "decision_id": "TARGET_GAP_004",
            "decision": "Keep full59k deprecated/deferred.",
            "accepted": True,
            "reason": "50k remains aspirational and outside quality-first targeted expansion.",
            "effect": "No full59k/global renormalization.",
        },
        {
            "decision_id": "TARGET_GAP_005",
            "decision": "Preserve ASX operational base and v2_14e rollback.",
            "accepted": True,
            "reason": "This gate does not edit datasets or pointers.",
            "effect": "Operational base remains unchanged at 42,708 rows.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "acquisition",
            "action": "run_colombia_bvc_singapore_sgx_acquisition_and_raw_validation",
            "priority": "high",
            "reason": "Decision gate approves narrow acquisition planning for the two missing markets.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "official sources only; no scoring/OpenAI/broker/full59k",
        },
        {
            "action_order": 2,
            "action_scope": "capacity",
            "action": "enforce_45k_quality_ceiling",
            "priority": "high",
            "reason": "Operational base has 2,292 rows remaining before ceiling.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "if raw candidates exceed capacity, apply quality filters before rebuild",
        },
        {
            "action_order": 3,
            "action_scope": "normalization",
            "action": "normalize_country_exchange_mic_currency",
            "priority": "medium",
            "reason": "New markets must enter as Colombia/BVC/XBOG/COP and Singapore/SGX/XSES/SGD.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "no country-format fragmentation like USA/US or Australia/AU",
        },
    ]

    add_check("decision_gate_only", True, "critical", "targeted market gap decision gate only")
    add_check("network_download_not_performed", True, "critical", "network_download_performed=False")
    add_check("raw_acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("file_edit_not_performed", True, "critical", "file_edit_performed=False")
    add_check("file_copy_not_performed", True, "critical", "file_copy_performed=False")
    add_check("file_rename_not_performed", True, "critical", "file_rename_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("pointer_update_not_performed", True, "critical", "pointer_update_performed=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        gate_decision = "TARGETED_MARKET_GAP_DECISION_BLOCKED_REVIEW_REQUIRED"
        recommended_next_phase = NEXT_PHASE_REVIEW
        approved_for_next_phase = False
    else:
        status = STATUS_SUCCESS
        gate_decision = "COLOMBIA_SINGAPORE_TARGETED_EXPANSION_APPROVED_FOR_ACQUISITION_AND_RAW_VALIDATION"
        recommended_next_phase = NEXT_PHASE
        approved_for_next_phase = True

    summary = {
        "selected_route": "Colombia + Singapore targeted expansion",
        "phase_type": PHASE_TYPE,
        "gate_decision": gate_decision,
        "approved_for_next_phase": approved_for_next_phase,
        "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "operational_base_rows": operational_rows,
        "operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity_to_quality_ceiling": remaining_capacity,
        "target_markets": "Colombia/BVC;Singapore/SGX",
        "target_markets_missing_in_current_base": all_target_markets_missing,
        "source_candidates_total": len(source_candidate_rows),
        "country_values_total": len(country_counter),
        "exchange_values_total": len(exchange_counter),
        "mic_values_total": len(mic_counter),
        "currency_values_total": len(currency_counter),
        "provider_expansion_scope": "targeted_only",
        "provider_expansion_frozen_except_targets": True,
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(TARGET_MARKETS_CSV, target_market_rows, ["market_id", "country", "country_codes", "exchange_candidates", "mic_candidates", "currency_candidates", "priority", "expected_capacity_profile", "currently_present", "approved_for_planning", "reason"])
    write_csv(SOURCE_CANDIDATES_CSV, source_candidate_rows, ["market_id", "source_id", "provider", "source_type", "expected_fields", "allowed_in_v2_21a", "planned_for", "notes"])
    write_csv(COVERAGE_GAP_CSV, coverage_gap_rows, ["market_id", "country", "country_hits", "exchange_hits", "mic_hits", "currency_hits", "market_present", "gap_confirmed"])
    write_csv(CAPACITY_CONTROLS_CSV, capacity_control_rows, ["control_id", "control", "value", "limit", "passed", "detail"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "target_markets": target_market_rows,
        "source_candidates": source_candidate_rows,
        "coverage_gap": coverage_gap_rows,
        "capacity_controls": capacity_control_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "targeted_market_gap_decision_gate_only": True,
            "selected_route": "Colombia + Singapore targeted expansion",
            "target_markets": ["Colombia/BVC", "Singapore/SGX"],
            "approved_for_next_phase": approved_for_next_phase,
            "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "operational_base_rows": operational_rows,
            "operational_base_sha": operational_sha,
            "rollback_available": rollback_sha == ROLLBACK_SHA_EXPECTED,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "remaining_capacity_to_quality_ceiling": remaining_capacity,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "raw_acquisition_performed": False,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "dedup_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "file_edit_performed": False,
            "file_copy_performed": False,
            "file_rename_performed": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "promoted_canonical_dataset_read": True,
            "promoted_canonical_dataset_modified": False,
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
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    target_lines = "\n".join(
        f"- `{row['market_id']}` — present `{row['currently_present']}` — approved `{row['approved_for_planning']}` — {row['reason']}"
        for row in target_market_rows
    )

    source_lines = "\n".join(
        f"- `{row['source_id']}` — provider `{row['provider']}` — planned for `{row['planned_for']}`"
        for row in source_candidate_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}` — accepted `{row['accepted']}` — {row['decision']}"
        for row in decision_register_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.21A opens a narrow targeted market-gap decision gate for Colombia and Singapore.

It does not acquire data, edit files, replace canonical, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Gate summary

- Gate decision: `{gate_decision}`
- Approved for next phase: `{approved_for_next_phase}`
- Operational base dataset: `{OPERATIONAL_BASE_DATASET}`
- Operational base rows: `{operational_rows}`
- Operational base SHA256: `{operational_sha}`
- Rollback dataset: `{ROLLBACK_DATASET}`
- Rollback rows: `{rollback_rows}`
- Rollback SHA256: `{rollback_sha}`
- Remaining capacity to 45k ceiling: `{remaining_capacity}`
- Target markets: `Colombia/BVC`, `Singapore/SGX`
- Provider expansion scope: `targeted_only`
- Scoring authorized: `False`
- OpenAI authorized: `False`
- Broker authorized: `False`
- full59k: `DEPRECATED_DEFERRED`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Target markets

{target_lines}

## Source candidates

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

    print("v2.21A targeted market gap decision gate completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("TARGET_MARKETS:")
    for row in target_market_rows:
        print(f"- {row['market_id']}: present={row['currently_present']} approved_for_planning={row['approved_for_planning']}")
    print("")
    print("COVERAGE_GAP:")
    for row in coverage_gap_rows:
        print(f"- {row['market_id']}: country_hits={row['country_hits']} exchange_hits={row['exchange_hits']} mic_hits={row['mic_hits']} currency_hits={row['currency_hits']} gap_confirmed={row['gap_confirmed']}")
    print("")
    print("SOURCE_CANDIDATES:")
    for row in source_candidate_rows:
        print(f"- {row['source_id']}: provider={row['provider']} planned_for={row['planned_for']}")
    print("")
    print("CAPACITY_CONTROLS:")
    for row in capacity_control_rows:
        print(f"- {row['control_id']}: {row['control']} passed={row['passed']} value={row['value']} limit={row['limit']}")
    print("")
    print("DECISION_REGISTER:")
    for row in decision_register_rows:
        print(f"- {row['decision_id']}: accepted={row['accepted']} - {row['decision']}")
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
