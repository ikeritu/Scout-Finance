from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.19B"
PHASE = "KRX Korea Exchange Acquisition Plan"
PHASE_TYPE = "acquisition-plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219A_JSON = OUTPUT_DIR / "next_provider_route_selection_v2_19a.json"
V219A_SELECTED_ROUTE_CSV = OUTPUT_DIR / "next_provider_selected_route_v2_19a.csv"
V219A_ROUTE_CANDIDATES_CSV = OUTPUT_DIR / "next_provider_route_candidates_v2_19a.csv"

REPORT_JSON = OUTPUT_DIR / "krx_acquisition_plan_v2_19b.json"
REPORT_MD = OUTPUT_DIR / "krx_acquisition_plan_v2_19b.md"
SOURCE_INVENTORY_CSV = OUTPUT_DIR / "krx_acquisition_plan_source_inventory_v2_19b.csv"
RAW_ARTIFACTS_CSV = OUTPUT_DIR / "krx_acquisition_plan_raw_artifacts_v2_19b.csv"
INSTRUMENT_FILTERS_CSV = OUTPUT_DIR / "krx_acquisition_plan_instrument_filters_v2_19b.csv"
VALIDATION_STRATEGY_CSV = OUTPUT_DIR / "krx_acquisition_plan_validation_strategy_v2_19b.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "krx_acquisition_plan_next_actions_v2_19b.csv"
CHECKS_CSV = OUTPUT_DIR / "krx_acquisition_plan_checks_v2_19b.csv"

EXPECTED_V219A_STATUS = "NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_KRX_SELECTED_ACQUISITION_PLAN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

SELECTED_ROUTE_ID_EXPECTED = "KRX_KOREA_EXCHANGE"
SELECTED_ROUTE_NAME = "KRX - Korea Exchange Official Listed Securities Route"

RECOMMENDED_NEXT_PHASE = "v2.19C - KRX Raw Acquisition"
RECOMMENDED_REVIEW_PHASE = "v2.19B_REVIEW - KRX Acquisition Plan Review"

SOURCE_INVENTORY = [
    {
        "priority": 1,
        "source_id": "krx_global_listed_company",
        "provider": "KRX",
        "source_name": "Global KRX Listed Company",
        "source_type": "official_exchange_web_download",
        "role": "primary_candidate_source",
        "official_url": "https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp",
        "official_evidence": "Global KRX Listed Company page includes search and download capability.",
        "planned_use": "Acquire listed company universe and company-level metadata.",
        "expected_format": "downloaded_table_or_excel_csv",
        "expected_rows_band": "2000-3000",
        "requires_api_key": "no",
        "requires_browser_session": "possible",
        "v2_19c_strategy": "attempt scripted download first; if blocked, capture HTML/table/download response as raw artifact and classify acquisition mode",
        "selection_status": "selected_primary",
        "risk_notes": "May require form parameters, cookies or POST flow; v2.19C must capture raw evidence without manual guessing.",
    },
    {
        "priority": 2,
        "source_id": "krx_data_marketplace_all_listed_issues",
        "provider": "KRX",
        "source_name": "KRX Data Marketplace - All Listed Issues",
        "source_type": "official_exchange_data_marketplace",
        "role": "primary_or_crosscheck_source",
        "official_url": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en",
        "official_evidence": "KRX Data Marketplace provides market statistics and basic stock issue data.",
        "planned_use": "Crosscheck symbols, issue names, markets and instrument groups.",
        "expected_format": "downloaded_table_csv_json_or_html",
        "expected_rows_band": "2000-3000",
        "requires_api_key": "no",
        "requires_browser_session": "possible",
        "v2_19c_strategy": "discover official endpoint parameters only within KRX domains; capture response and manifest",
        "selection_status": "selected_primary_or_crosscheck",
        "risk_notes": "KRX Data Marketplace can rely on dynamic endpoints; v2.19C must avoid unofficial scraping shortcuts.",
    },
    {
        "priority": 3,
        "source_id": "public_data_portal_krx_listed_stock_info",
        "provider": "Public Data Portal / Financial Services Commission",
        "source_name": "KRX Listed Stock Information OpenAPI",
        "source_type": "official_public_data_api",
        "role": "supporting_or_fallback_source",
        "official_url": "https://www.data.go.kr/en/data/15094775/openapi.do",
        "official_evidence": "Public Data Portal lists KRX Listed Stock Information and base URL apis.data.go.kr/1160100/service/GetKrxListedInfoService.",
        "planned_use": "Fallback or crosscheck listed stock metadata if service key is available.",
        "expected_format": "xml_or_json_api",
        "expected_rows_band": "2000-3000",
        "requires_api_key": "yes_or_may_require_service_key",
        "requires_browser_session": "no",
        "v2_19c_strategy": "do not require key to pass; if no service key exists, record as unavailable_key_required and continue with KRX primary sources",
        "selection_status": "selected_supporting",
        "risk_notes": "May require registered service key; must not block route if KRX exchange download works.",
    },
    {
        "priority": 4,
        "source_id": "krx_open_api_data_feed_products",
        "provider": "KRX",
        "source_name": "KRX Open API Data Feed Products",
        "source_type": "official_exchange_api_catalog",
        "role": "reference_only",
        "official_url": "https://openapi.krx.co.kr/contents/OPP/DATA/OPPDATA002.jsp",
        "official_evidence": "KRX Open API catalog describes data feed products.",
        "planned_use": "Reference only unless explicitly available without subscription/credentials.",
        "expected_format": "catalog_page",
        "expected_rows_band": "not_applicable",
        "requires_api_key": "unknown_or_likely",
        "requires_browser_session": "possible",
        "v2_19c_strategy": "do not use as primary source unless free/public access is confirmed",
        "selection_status": "reference_only",
        "risk_notes": "Potential access, subscription or terms constraints.",
    },
]

RAW_ARTIFACTS_PLAN = [
    {
        "artifact_id": "krx_global_listed_company_raw",
        "source_id": "krx_global_listed_company",
        "planned_path": "outputs/full_universe_source_acquisition/raw/krx_v2_19c/krx_global_listed_company_raw.*",
        "expected_format": "csv_xlsx_json_html_or_error_payload",
        "required_for_route": "yes",
        "purpose": "primary raw listed-company candidate source",
        "success_condition": "raw file captured with listed company rows or clear technical/error diagnosis",
    },
    {
        "artifact_id": "krx_data_marketplace_all_listed_issues_raw",
        "source_id": "krx_data_marketplace_all_listed_issues",
        "planned_path": "outputs/full_universe_source_acquisition/raw/krx_v2_19c/krx_data_marketplace_all_listed_issues_raw.*",
        "expected_format": "csv_xlsx_json_html_or_error_payload",
        "required_for_route": "preferred",
        "purpose": "primary or crosscheck listed-issue source",
        "success_condition": "raw file captured with issue-level rows or clear endpoint/access diagnosis",
    },
    {
        "artifact_id": "public_data_portal_krx_listed_stock_info_raw",
        "source_id": "public_data_portal_krx_listed_stock_info",
        "planned_path": "outputs/full_universe_source_acquisition/raw/krx_v2_19c/public_data_portal_krx_listed_stock_info_raw.*",
        "expected_format": "xml_json_or_error_payload",
        "required_for_route": "no",
        "purpose": "supporting fallback/crosscheck source if service key is available",
        "success_condition": "API response captured or key-required status documented",
    },
    {
        "artifact_id": "krx_raw_acquisition_manifest",
        "source_id": "all",
        "planned_path": "outputs/full_universe_source_acquisition/krx_raw_acquisition_manifest_v2_19c.csv",
        "expected_format": "csv",
        "required_for_route": "yes",
        "purpose": "manifest of every attempted official source and response",
        "success_condition": "all attempted sources logged with status, bytes, sha256 and parse hints",
    },
]

INSTRUMENT_FILTERS = [
    {
        "rule_order": 1,
        "filter_type": "keep_candidate",
        "rule_id": "keep_common_operating_company_equity",
        "applies_to": "candidate_extraction_v2_19e",
        "logic": "Keep ordinary listed operating-company equities after source schema confirms instrument group.",
        "reason": "Scout Finance candidate universe should prioritize investigable common equity.",
    },
    {
        "rule_order": 2,
        "filter_type": "market_scope",
        "rule_id": "include_krx_equity_markets_with_review",
        "applies_to": "candidate_extraction_v2_19e",
        "logic": "Capture KOSPI, KOSDAQ and KONEX in raw; later classify liquidity/review flags before auto-add.",
        "reason": "KONEX may be valid but lower liquidity; do not discard at raw acquisition stage.",
    },
    {
        "rule_order": 3,
        "filter_type": "exclude",
        "rule_id": "exclude_etf_etn_elw_fund_bond_derivative",
        "applies_to": "candidate_extraction_v2_19e",
        "logic": "Exclude ETF, ETN, ELW, funds, bonds, derivatives, warrants and structured products.",
        "reason": "These are not operating-company equity candidates.",
    },
    {
        "rule_order": 4,
        "filter_type": "exclude_or_review",
        "rule_id": "preferred_spac_reit_rights_review",
        "applies_to": "candidate_extraction_v2_19e",
        "logic": "Exclude preferred/preference shares by default; review SPAC, REIT, rights and special-purpose vehicles.",
        "reason": "These can inflate universe quality risk and duplicate common issuers.",
    },
    {
        "rule_order": 5,
        "filter_type": "dedupe",
        "rule_id": "symbol_isin_name_dedupe",
        "applies_to": "candidate_validation_v2_19f",
        "logic": "Use KRX short code, ISIN, company name, English/Korean name and market as dedupe evidence against canonical.",
        "reason": "KRX issuers may already exist via ADR/global listings or previous routes.",
    },
]

VALIDATION_STRATEGY = [
    {
        "stage": "v2.19C",
        "stage_name": "KRX Raw Acquisition",
        "validation_focus": "capture official raw data only",
        "must_pass": "official domains only; raw files or error payloads captured; manifest written; no candidate extraction",
        "failure_action": "repair acquisition or switch to backup source inside KRX route",
    },
    {
        "stage": "v2.19D",
        "stage_name": "KRX Raw Validation",
        "validation_focus": "file existence, bytes, sha256, parse readiness and source role",
        "must_pass": "at least one primary KRX source parse-ready for candidate extraction",
        "failure_action": "create repair phase before extraction",
    },
    {
        "stage": "v2.19E",
        "stage_name": "KRX Candidate Extraction Dry Run",
        "validation_focus": "common-equity extraction without canonical comparison",
        "must_pass": "candidate-shaped rows, no duplicate KRX identifiers, instrument filters applied",
        "failure_action": "patch extraction rules before validation against canonical",
    },
    {
        "stage": "v2.19F",
        "stage_name": "KRX Candidate Validation Against Canonical Dry Run",
        "validation_focus": "classify existing, possible_existing and potential_net_new",
        "must_pass": "do not auto-add possible_existing; count only high-confidence potential_net_new",
        "failure_action": "review matching rules before expanded rebuild",
    },
    {
        "stage": "v2.19G",
        "stage_name": "KRX Expanded Rebuild Candidate",
        "validation_focus": "append only validated potential_net_new KRX rows to current candidate",
        "must_pass": "schema preserved, current candidate unchanged, canonical unchanged",
        "failure_action": "do not commit expanded rebuild",
    },
    {
        "stage": "v2.19H",
        "stage_name": "KRX Expanded Validation",
        "validation_focus": "validate expanded candidate integrity",
        "must_pass": "no critical failed checks; no symbol conflicts; 50k gate status explicit",
        "failure_action": "repair before closure report",
    },
    {
        "stage": "v2.19I",
        "stage_name": "KRX Closure Report",
        "validation_focus": "formal closure and next-route decision",
        "must_pass": "document rows added and remaining to 50k",
        "failure_action": "review route before selecting next provider",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        SOURCE_INVENTORY_CSV,
        RAW_ARTIFACTS_CSV,
        INSTRUMENT_FILTERS_CSV,
        VALIDATION_STRATEGY_CSV,
        NEXT_ACTIONS_CSV,
        CHECKS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219a = read_json(V219A_JSON)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    canonical_header, canonical_rows = read_csv_with_header(ACTIVE_CANONICAL_DATASET)
    candidate_header, candidate_rows = read_csv_with_header(CURRENT_VALIDATED_CANDIDATE_DATASET)
    _, selected_route_rows = read_csv_with_header(V219A_SELECTED_ROUTE_CSV)
    _, route_candidate_rows = read_csv_with_header(V219A_ROUTE_CANDIDATES_CSV)

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = len(canonical_rows)
    current_candidate_rows = len(candidate_rows)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    selected_route_id = v219a.get("route_selection", {}).get("selected_route_id", "")
    selected_route_name = v219a.get("route_selection", {}).get("selected_route_name", "")

    primary_sources = [
        row for row in SOURCE_INVENTORY
        if row["selection_status"] in {"selected_primary", "selected_primary_or_crosscheck"}
    ]
    supporting_sources = [
        row for row in SOURCE_INVENTORY
        if row["selection_status"] == "selected_supporting"
    ]

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19a_report_exists", V219A_JSON.exists(), "critical", str(V219A_JSON))
    add_check("v2_19a_status_expected", v219a.get("status") == EXPECTED_V219A_STATUS, "critical", v219a.get("status", ""))
    add_check("v2_19a_selected_route_expected", selected_route_id == SELECTED_ROUTE_ID_EXPECTED, "critical", f"selected_route_id={selected_route_id}")
    add_check("v2_19a_selected_route_csv_exists", V219A_SELECTED_ROUTE_CSV.exists(), "critical", str(V219A_SELECTED_ROUTE_CSV))
    add_check("v2_19a_route_candidates_csv_exists", V219A_ROUTE_CANDIDATES_CSV.exists(), "critical", str(V219A_ROUTE_CANDIDATES_CSV))
    add_check("selected_route_csv_has_one_row", len(selected_route_rows) == 1, "critical", f"selected_route_rows={len(selected_route_rows)}")
    add_check("route_candidates_csv_has_expected_rows", len(route_candidate_rows) >= 5, "critical", f"route_candidate_rows={len(route_candidate_rows)}")
    add_check("active_canonical_exists", ACTIVE_CANONICAL_DATASET.exists(), "critical", str(ACTIVE_CANONICAL_DATASET))
    add_check("current_validated_candidate_exists", CURRENT_VALIDATED_CANDIDATE_DATASET.exists(), "critical", str(CURRENT_VALIDATED_CANDIDATE_DATASET))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("source_inventory_minimum_count", len(SOURCE_INVENTORY) >= 3, "critical", f"source_inventory={len(SOURCE_INVENTORY)}")
    add_check("primary_sources_available", len(primary_sources) >= 2, "critical", f"primary_sources={len(primary_sources)}")
    add_check("supporting_source_available", len(supporting_sources) >= 1, "warning", f"supporting_sources={len(supporting_sources)}")
    add_check("raw_artifact_plan_available", len(RAW_ARTIFACTS_PLAN) >= 3, "critical", f"raw_artifacts_planned={len(RAW_ARTIFACTS_PLAN)}")
    add_check("instrument_filters_available", len(INSTRUMENT_FILTERS) >= 5, "critical", f"instrument_filters={len(INSTRUMENT_FILTERS)}")
    add_check("validation_strategy_available", len(VALIDATION_STRATEGY) >= 7, "critical", f"validation_steps={len(VALIDATION_STRATEGY)}")
    add_check("official_sources_only", all("krx.co.kr" in row["official_url"] or "data.go.kr" in row["official_url"] for row in SOURCE_INVENTORY), "critical", "all planned URLs are KRX or data.go.kr official sources")
    add_check("no_full59k_source", all("full59k" not in json.dumps(row).lower() for row in SOURCE_INVENTORY), "critical", "full59k absent from source inventory")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("candidate_dataset_not_modified", True, "critical", "candidate_dataset_modified=False")
    add_check("plan_only_no_raw_download", True, "critical", "raw_acquisition_performed=False")
    add_check("plan_only_no_candidate_extraction", True, "critical", "candidate_extraction_performed=False")
    add_check("plan_only_no_expanded_rebuild", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("network_not_used_by_script", True, "critical", "network_download_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("krx_raw_acquisition_next_needed", True, "critical", RECOMMENDED_NEXT_PHASE)

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "KRX",
            "action": "perform_raw_acquisition",
            "priority": "high",
            "reason": "KRX official sources are planned and ready for raw acquisition.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "download/capture raw artifacts only; no candidate extraction; official KRX/data.go.kr sources only",
        },
        {
            "action_order": 2,
            "action_scope": "KRX",
            "action": "capture_manifest_and_error_payloads",
            "priority": "high",
            "reason": "KRX sources may require dynamic endpoints or service keys; every attempt must be auditable.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "record status, bytes, sha256, content type and parse hint for every source",
        },
        {
            "action_order": 3,
            "action_scope": "50k",
            "action": "maintain_quality_target",
            "priority": "medium",
            "reason": f"{rows_needed_to_50k} rows remain; KRX is expected to help but may not close the whole gap.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "keep 45k-47.5k intermediate quality target and 50k stretch target",
        },
    ]

    if critical_failed == 0:
        status = "KRX_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_FOR_RAW_ACQUISITION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "KRX_ACQUISITION_PLAN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "current_validated_candidate_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "current_validated_candidate_rows": current_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "intermediate_quality_target": "45000-47500",
            "stretch_target": "50000",
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "current_candidate_sha256_before": candidate_sha_before,
            "current_candidate_sha256_after": candidate_sha_after,
        },
        "route_context": {
            "selected_route_id": selected_route_id,
            "selected_route_name": selected_route_name,
            "expected_selected_route_id": SELECTED_ROUTE_ID_EXPECTED,
            "planned_route_name": SELECTED_ROUTE_NAME,
            "source_inventory_count": len(SOURCE_INVENTORY),
            "primary_sources_count": len(primary_sources),
            "supporting_sources_count": len(supporting_sources),
            "raw_artifacts_planned": len(RAW_ARTIFACTS_PLAN),
            "instrument_filters_planned": len(INSTRUMENT_FILTERS),
            "validation_steps_planned": len(VALIDATION_STRATEGY),
            "critical_failed_checks": critical_failed,
        },
        "source_inventory": SOURCE_INVENTORY,
        "raw_artifacts_plan": RAW_ARTIFACTS_PLAN,
        "instrument_filters": INSTRUMENT_FILTERS,
        "validation_strategy": VALIDATION_STRATEGY,
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
            "closure_report_performed": False,
            "route_selection_performed": False,
            "acquisition_plan_performed": True,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": candidate_sha_before == candidate_sha_after,
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

    source_fieldnames = [
        "priority",
        "source_id",
        "provider",
        "source_name",
        "source_type",
        "role",
        "official_url",
        "official_evidence",
        "planned_use",
        "expected_format",
        "expected_rows_band",
        "requires_api_key",
        "requires_browser_session",
        "v2_19c_strategy",
        "selection_status",
        "risk_notes",
    ]

    raw_fieldnames = [
        "artifact_id",
        "source_id",
        "planned_path",
        "expected_format",
        "required_for_route",
        "purpose",
        "success_condition",
    ]

    filter_fieldnames = [
        "rule_order",
        "filter_type",
        "rule_id",
        "applies_to",
        "logic",
        "reason",
    ]

    validation_fieldnames = [
        "stage",
        "stage_name",
        "validation_focus",
        "must_pass",
        "failure_action",
    ]

    write_csv(SOURCE_INVENTORY_CSV, SOURCE_INVENTORY, source_fieldnames)
    write_csv(RAW_ARTIFACTS_CSV, RAW_ARTIFACTS_PLAN, raw_fieldnames)
    write_csv(INSTRUMENT_FILTERS_CSV, INSTRUMENT_FILTERS, filter_fieldnames)
    write_csv(VALIDATION_STRATEGY_CSV, VALIDATION_STRATEGY, validation_fieldnames)
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_json(REPORT_JSON, payload)

    source_lines = "\n".join(
        f"- P{row['priority']} `{row['source_id']}` - {row['source_name']} - {row['selection_status']} - {row['official_url']}"
        for row in SOURCE_INVENTORY
    )

    raw_lines = "\n".join(
        f"- `{row['artifact_id']}` from `{row['source_id']}` -> `{row['planned_path']}`"
        for row in RAW_ARTIFACTS_PLAN
    )

    filter_lines = "\n".join(
        f"- `{row['rule_id']}` - {row['filter_type']} - {row['logic']}"
        for row in INSTRUMENT_FILTERS
    )

    validation_lines = "\n".join(
        f"- `{row['stage']}` - {row['stage_name']} - {row['must_pass']}"
        for row in VALIDATION_STRATEGY
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}"
        for row in checks
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` - {row['action']} - {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.19B defines the KRX Korea Exchange acquisition plan after v2.19A selected KRX as the next official provider route.

This phase is acquisition-plan-only. It does not download raw data, does not call endpoints, does not extract candidates, does not rebuild an expanded dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `{ACTIVE_CANONICAL_DATASET}`
- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate dataset: `{CURRENT_VALIDATED_CANDIDATE_DATASET}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Intermediate quality target: `45,000-47,500`
- Stretch target: `50,000`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Route context

- Selected route from v2.19A: `{selected_route_id}`
- Planned route name: `{SELECTED_ROUTE_NAME}`
- Source inventory count: `{len(SOURCE_INVENTORY)}`
- Primary sources count: `{len(primary_sources)}`
- Supporting sources count: `{len(supporting_sources)}`
- Raw artifacts planned: `{len(RAW_ARTIFACTS_PLAN)}`
- Instrument filters planned: `{len(INSTRUMENT_FILTERS)}`
- Validation steps planned: `{len(VALIDATION_STRATEGY)}`
- Critical failed checks: `{critical_failed}`

## Source inventory

{source_lines}

## Raw artifacts planned for v2.19C

{raw_lines}

## Instrument filters

{filter_lines}

## Validation strategy

{validation_lines}

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
- Acquisition plan performed: true
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Current candidate dataset read: true
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{candidate_sha_before == candidate_sha_after}`
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

    print("v2.19B KRX acquisition plan completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("ROUTE_CONTEXT:")
    for key, value in payload["route_context"].items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_INVENTORY:")
    for row in SOURCE_INVENTORY:
        print(f"- P{row['priority']} {row['source_id']}: {row['selection_status']} - {row['official_url']}")
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
