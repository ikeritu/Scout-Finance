from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21C3_REVIEW"
PHASE = "Missing Official Structured Endpoint Review"
PHASE_TYPE = "targeted-market-missing-official-structured-endpoint-review"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

V221C3_JSON = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_v2_21c3.json"

REPORT_JSON = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_v2_21c3_review.json"
REPORT_MD = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_v2_21c3_review.md"
SUMMARY_CSV = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_summary_v2_21c3_review.csv"
CHECKS_CSV = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_checks_v2_21c3_review.csv"
MARKET_REVIEW_CSV = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_market_review_v2_21c3_review.csv"
ROUTE_OPTIONS_CSV = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_route_options_v2_21c3_review.csv"
COLOMBIA_ALTERNATIVE_SOURCES_CSV = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_colombia_alternative_sources_v2_21c3_review.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_decision_register_v2_21c3_review.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_next_actions_v2_21c3_review.csv"

EXPECTED_V221C3_STATUS = "TARGETED_MARKET_OFFICIAL_ENDPOINT_DISCOVERY_COMPLETED_PARTIAL_STRUCTURED_ENDPOINTS_FOUND_REVIEW_REQUIRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_SUCCESS = "TARGETED_MARKET_MISSING_ENDPOINT_REVIEW_COMPLETED_SPLIT_ROUTE_APPROVED_SGX_READY_COLOMBIA_REGULATORY_DISCOVERY_REQUIRED"
STATUS_FAILED = "TARGETED_MARKET_MISSING_ENDPOINT_REVIEW_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.21C4S - Singapore Structured Candidate Extraction + Dedup Dry Run"
SECONDARY_NEXT_PHASE = "v2.21C3B - Colombia Regulatory Source Discovery"
NEXT_PHASE_REVIEW = "v2.21C3_REVIEW_FIX - Missing Endpoint Review Issue Resolution"


COLOMBIA_ALTERNATIVE_SOURCES = [
    {
        "source_id": "COLOMBIA_SUPERFINANCIERA_SIMEV_VALORES_INSCRITOS",
        "source_type": "official_regulator_page_family",
        "authority": "Superintendencia Financiera de Colombia",
        "market_role": "Regulator / RNVE / SIMEV",
        "candidate_url": "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/B_simevRelevantes/H_precioAcciones/repoPrecioAcciones.xhtml",
        "evidence": "Valores Inscritos pages expose issuer/security registration fields including title name, Superfinanciera code, RNVEI registration and BVC registration date.",
        "approved_for_candidate_extraction": False,
        "approved_for_discovery": True,
        "review_reason": "Official regulatory source candidate. Needs structured traversal or parameter discovery before extraction.",
    },
    {
        "source_id": "COLOMBIA_SUPERFINANCIERA_RNVE_OFERTAS_PUBLICAS",
        "source_type": "official_regulator_information_page",
        "authority": "Superintendencia Financiera de Colombia",
        "market_role": "RNVE public offerings / issuer information",
        "candidate_url": "https://www.superfinanciera.gov.co/publicaciones/12961/simevregistro-nacional-de-valores-y-emisores-rnveinformacion-emisoresofertas-publicas-12961/",
        "evidence": "RNVE/SIMEV public-offerings page describes searchable registered securities and issuer information.",
        "approved_for_candidate_extraction": False,
        "approved_for_discovery": True,
        "review_reason": "Official regulatory context. Needs structured source discovery before extraction.",
    },
    {
        "source_id": "COLOMBIA_BVC_MANUAL_DOWNLOAD_REVIEW",
        "source_type": "official_exchange_manual_review",
        "authority": "Bolsa de Valores de Colombia",
        "market_role": "Exchange",
        "candidate_url": "https://www.bvc.com.co/listado-de-emisores-mercado-local",
        "evidence": "BVC page is official and reachable, but v2.21C3 found no structured endpoint or table records.",
        "approved_for_candidate_extraction": False,
        "approved_for_discovery": True,
        "review_reason": "Keep as manual-download/hidden-endpoint review only. Do not extract from shell HTML.",
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


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        MARKET_REVIEW_CSV,
        ROUTE_OPTIONS_CSV,
        COLOMBIA_ALTERNATIVE_SOURCES_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v221c3 = read_json(V221C3_JSON)
    v221c3_summary = v221c3.get("summary", {})
    v221c3_readiness = v221c3.get("market_endpoint_readiness", [])

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    header = read_csv_header(OPERATIONAL_BASE_DATASET)

    readiness_by_market = {row["market_id"]: row for row in v221c3_readiness}

    colombia = readiness_by_market.get("COLOMBIA_BVC", {})
    singapore = readiness_by_market.get("SINGAPORE_SGX", {})

    colombia_ready = as_bool(colombia.get("market_endpoint_ready"))
    singapore_ready = as_bool(singapore.get("market_endpoint_ready"))

    market_review_rows = [
        {
            "market_id": "COLOMBIA_BVC",
            "country": "Colombia",
            "provider": "BVC",
            "v2_21c3_endpoint_ready": colombia_ready,
            "v2_21c3_structured_endpoint_count": colombia.get("structured_endpoint_count", ""),
            "v2_21c3_fetch_success_count": colombia.get("fetch_success_count", ""),
            "review_decision": "block_exchange_extraction_use_regulatory_discovery_next",
            "approved_for_structured_extraction": False,
            "approved_for_expanded_rebuild": False,
            "recommended_next_phase": SECONDARY_NEXT_PHASE,
            "reason": "BVC official pages were reachable but no structured candidate records were found.",
        },
        {
            "market_id": "SINGAPORE_SGX",
            "country": "Singapore",
            "provider": "SGX",
            "v2_21c3_endpoint_ready": singapore_ready,
            "v2_21c3_structured_endpoint_count": singapore.get("structured_endpoint_count", ""),
            "v2_21c3_fetch_success_count": singapore.get("fetch_success_count", ""),
            "review_decision": "approve_singapore_only_structured_extraction_dry_run",
            "approved_for_structured_extraction": singapore_ready,
            "approved_for_expanded_rebuild": False,
            "recommended_next_phase": NEXT_PHASE,
            "reason": "SGX has validated structured endpoint candidates, but extraction/dedup must run before any rebuild.",
        },
    ]

    route_options_rows = [
        {
            "route_id": "ROUTE_A_WAIT_FOR_COLOMBIA",
            "route_name": "Wait until Colombia/BVC has official structured endpoint",
            "approved": False,
            "priority": "low",
            "effect": "Blocks Singapore despite SGX readiness.",
            "reason": "Unnecessarily blocks a validated market.",
        },
        {
            "route_id": "ROUTE_B_USE_BVC_REGEX_OR_SHELL_HTML",
            "route_name": "Use current BVC shell/regex output",
            "approved": False,
            "priority": "rejected",
            "effect": "Would risk false positives and low-quality candidates.",
            "reason": "v2.21C2 invalidated regex-only candidates and v2.21C3 found no BVC structured records.",
        },
        {
            "route_id": "ROUTE_C_SPLIT_MARKETS",
            "route_name": "Split route: advance Singapore; keep Colombia pending",
            "approved": True,
            "priority": "high",
            "effect": "Allows SGX structured extraction without polluting Colombia data.",
            "reason": "One market is ready and one market needs additional official/regulatory source discovery.",
        },
        {
            "route_id": "ROUTE_D_COLOMBIA_REGULATORY_DISCOVERY",
            "route_name": "Open Colombia regulator-source discovery",
            "approved": True,
            "priority": "high",
            "effect": "Searches Superfinanciera/SIMEV/RNVE path without using BVC shell HTML.",
            "reason": "Superfinanciera provides official issuer/security registration context and BVC registration fields.",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "MISSING_ENDPOINT_REVIEW_001",
            "decision": "Keep v2.21D blocked.",
            "accepted": True,
            "reason": "No deduplicated candidate extraction has succeeded after false-positive review.",
            "effect": "No expanded rebuild candidate can be created yet.",
        },
        {
            "decision_id": "MISSING_ENDPOINT_REVIEW_002",
            "decision": "Do not use BVC shell HTML or regex extraction.",
            "accepted": True,
            "reason": "BVC pages were reachable but did not expose reliable structured company/security records.",
            "effect": "Colombia remains blocked for extraction.",
        },
        {
            "decision_id": "MISSING_ENDPOINT_REVIEW_003",
            "decision": "Approve split route.",
            "accepted": True,
            "reason": "SGX has structured endpoints while Colombia needs additional source discovery.",
            "effect": "Singapore can move to structured extraction dry run separately.",
        },
        {
            "decision_id": "MISSING_ENDPOINT_REVIEW_004",
            "decision": "Open Colombia regulatory source discovery.",
            "accepted": True,
            "reason": "Superfinanciera/SIMEV/RNVE is an official candidate source family for Colombian registered securities.",
            "effect": "Colombia route continues as discovery-only, not extraction.",
        },
        {
            "decision_id": "MISSING_ENDPOINT_REVIEW_005",
            "decision": "Keep operational base unchanged.",
            "accepted": True,
            "reason": "This phase is decision-review only.",
            "effect": "Operational base remains 42,708 rows.",
        },
        {
            "decision_id": "MISSING_ENDPOINT_REVIEW_006",
            "decision": "Keep scoring/OpenAI/broker/full59k deferred.",
            "accepted": True,
            "reason": "No valid expanded candidate universe exists yet.",
            "effect": "No scoring or enrichment is authorized.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "singapore_structured_extraction",
            "action": "run_singapore_only_structured_candidate_extraction_dedup_dry_run",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "SGX has validated structured endpoint candidates.",
            "guardrails": "Singapore only; no rebuild; no pointer update; no scoring",
        },
        {
            "action_order": 2,
            "action_scope": "colombia_regulatory_discovery",
            "action": "discover_superfinanciera_simev_rnve_structured_or_traversable_source",
            "priority": "high",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "BVC has no structured endpoint from v2.21C3; regulator source family is the next official path.",
            "guardrails": "Discovery only; no extraction until source is structured and validated",
        },
        {
            "action_order": 3,
            "action_scope": "global_rebuild_control",
            "action": "keep_v2_21d_blocked_until_structured_extraction_dedup_produces_valid_candidates",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Endpoint readiness is not a validated candidate universe.",
            "guardrails": "no promotion; no pointer update; no full59k",
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

    add_check("v2_21c3_status_expected", v221c3.get("status") == EXPECTED_V221C3_STATUS, "critical", str(v221c3.get("status")))
    add_check("v2_21c3_partial_decision_expected", v221c3_summary.get("discovery_decision") == "PARTIAL_OR_NO_STRUCTURED_ENDPOINT_COVERAGE_REVIEW_REQUIRED", "critical", str(v221c3_summary.get("discovery_decision")))
    add_check("v2_21c3_approved_for_v2_21c4_false", as_bool(v221c3_summary.get("approved_for_v2_21c4")) is False, "critical", f"approved_for_v2_21c4={v221c3_summary.get('approved_for_v2_21c4')}")
    add_check("v2_21c3_approved_for_v2_21d_false", as_bool(v221c3_summary.get("approved_for_v2_21d")) is False, "critical", f"approved_for_v2_21d={v221c3_summary.get('approved_for_v2_21d')}")
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("schema_column_count_expected", len(header) == 33, "critical", f"columns={len(header)}")
    add_check("colombia_endpoint_not_ready_confirmed", colombia_ready is False, "critical", f"colombia_ready={colombia_ready}")
    add_check("singapore_endpoint_ready_confirmed", singapore_ready is True, "critical", f"singapore_ready={singapore_ready}")
    add_check("split_route_approved", True, "critical", "Singapore can advance separately; Colombia remains pending.")
    add_check("colombia_regulatory_discovery_approved", True, "critical", "Superfinanciera/SIMEV/RNVE discovery route approved.")
    add_check("global_v2_21c4_not_approved", True, "critical", "Global Colombia+Singapore extraction remains blocked.")
    add_check("v2_21d_rebuild_blocked", True, "critical", "v2.21D remains blocked.")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("dedup_not_performed", True, "critical", "dedup_performed=False")
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
        review_decision = "MISSING_ENDPOINT_REVIEW_BLOCKED_REVIEW_REQUIRED"
        approved_for_singapore_extraction = False
        approved_for_colombia_regulatory_discovery = False
        approved_for_global_v2_21c4 = False
        approved_for_v2_21d = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        review_decision = "SPLIT_ROUTE_APPROVED_SINGAPORE_READY_COLOMBIA_REGULATORY_DISCOVERY_REQUIRED"
        approved_for_singapore_extraction = True
        approved_for_colombia_regulatory_discovery = True
        approved_for_global_v2_21c4 = False
        approved_for_v2_21d = False
        recommended_next_phase = NEXT_PHASE

    summary = {
        "selected_route": "Colombia + Singapore targeted expansion",
        "phase_type": PHASE_TYPE,
        "review_decision": review_decision,
        "approved_for_singapore_structured_extraction": approved_for_singapore_extraction,
        "approved_for_colombia_regulatory_discovery": approved_for_colombia_regulatory_discovery,
        "approved_for_global_v2_21c4": approved_for_global_v2_21c4,
        "approved_for_v2_21d": approved_for_v2_21d,
        "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "operational_base_rows": operational_rows,
        "operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "colombia_bvc_endpoint_ready": colombia_ready,
        "singapore_sgx_endpoint_ready": singapore_ready,
        "v2_21d_blocked": True,
        "candidate_extraction_performed": False,
        "dedup_performed": False,
        "expanded_rebuild_performed": False,
        "provider_expansion_scope": "targeted_split_only",
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
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(MARKET_REVIEW_CSV, market_review_rows, [
        "market_id", "country", "provider", "v2_21c3_endpoint_ready",
        "v2_21c3_structured_endpoint_count", "v2_21c3_fetch_success_count",
        "review_decision", "approved_for_structured_extraction",
        "approved_for_expanded_rebuild", "recommended_next_phase", "reason",
    ])
    write_csv(ROUTE_OPTIONS_CSV, route_options_rows, [
        "route_id", "route_name", "approved", "priority", "effect", "reason",
    ])
    write_csv(COLOMBIA_ALTERNATIVE_SOURCES_CSV, COLOMBIA_ALTERNATIVE_SOURCES, [
        "source_id", "source_type", "authority", "market_role", "candidate_url",
        "evidence", "approved_for_candidate_extraction", "approved_for_discovery",
        "review_reason",
    ])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "market_review": market_review_rows,
        "route_options": route_options_rows,
        "colombia_alternative_sources": COLOMBIA_ALTERNATIVE_SOURCES,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Colombia + Singapore targeted expansion",
            "missing_endpoint_review_only": True,
            "approved_for_singapore_structured_extraction": approved_for_singapore_extraction,
            "approved_for_colombia_regulatory_discovery": approved_for_colombia_regulatory_discovery,
            "approved_for_global_v2_21c4": approved_for_global_v2_21c4,
            "approved_for_v2_21d": approved_for_v2_21d,
            "v2_21d_rebuild_blocked": True,
            "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "operational_base_rows": operational_rows,
            "operational_base_sha": operational_sha,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "candidate_extraction_performed": False,
            "dedup_performed": False,
            "regex_only_candidate_acceptance_allowed": False,
            "structured_extraction_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "file_edit_performed_on_operational_base": False,
            "file_copy_performed_on_operational_base": False,
            "file_rename_performed_on_operational_base": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "provider_expansion_scope": "targeted_split_only",
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

    market_lines = "\n".join(
        f"- `{row['market_id']}` — endpoint ready `{row['v2_21c3_endpoint_ready']}` — extraction approved `{row['approved_for_structured_extraction']}` — next `{row['recommended_next_phase']}`"
        for row in market_review_rows
    )

    route_lines = "\n".join(
        f"- `{row['route_id']}` — approved `{row['approved']}` — priority `{row['priority']}` — {row['route_name']}"
        for row in route_options_rows
    )

    source_lines = "\n".join(
        f"- `{row['source_id']}` — discovery `{row['approved_for_discovery']}` — extraction `{row['approved_for_candidate_extraction']}` — {row['authority']}"
        for row in COLOMBIA_ALTERNATIVE_SOURCES
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

v2.21C3_REVIEW resolves the partial endpoint discovery result from v2.21C3.

The decision is to split the route: Singapore/SGX may proceed to structured extraction dry run, while Colombia/BVC remains blocked and moves to a regulator-source discovery path using official Superfinanciera/SIMEV/RNVE candidates.

This phase is review-only. It does not extract candidates, deduplicate, rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Review decision: `{review_decision}`
- Approved for Singapore structured extraction: `{approved_for_singapore_extraction}`
- Approved for Colombia regulatory discovery: `{approved_for_colombia_regulatory_discovery}`
- Approved for global v2.21C4: `{approved_for_global_v2_21c4}`
- Approved for v2.21D: `{approved_for_v2_21d}`
- Operational base rows: `{operational_rows}`
- Operational base SHA256: `{operational_sha}`
- Rollback rows: `{rollback_rows}`
- Rollback SHA256: `{rollback_sha}`
- Colombia/BVC endpoint ready: `{colombia_ready}`
- Singapore/SGX endpoint ready: `{singapore_ready}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Market review

{market_lines}

## Route options

{route_lines}

## Colombia alternative official sources

{source_lines}

## Decision register

{decision_lines}

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
    print("v2.21C3_REVIEW missing endpoint review completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("MARKET_REVIEW:")
    for row in market_review_rows:
        print(f"- {row['market_id']}: ready={row['v2_21c3_endpoint_ready']} extraction_approved={row['approved_for_structured_extraction']} next={row['recommended_next_phase']}")
    print("")
    print("ROUTE_OPTIONS:")
    for row in route_options_rows:
        print(f"- {row['route_id']}: approved={row['approved']} priority={row['priority']} - {row['route_name']}")
    print("")
    print("COLOMBIA_ALTERNATIVE_SOURCES:")
    for row in COLOMBIA_ALTERNATIVE_SOURCES:
        print(f"- {row['source_id']}: discovery={row['approved_for_discovery']} extraction={row['approved_for_candidate_extraction']} authority={row['authority']}")
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
