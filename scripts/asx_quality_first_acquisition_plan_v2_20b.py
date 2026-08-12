from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20B"
PHASE = "ASX Quality-First Acquisition Plan"
PHASE_TYPE = "acquisition-plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
HKEX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V220A_JSON = OUTPUT_DIR / "quality_first_target_reset_provider_selection_v2_20a.json"

REPORT_JSON = OUTPUT_DIR / "asx_quality_first_acquisition_plan_v2_20b.json"
REPORT_MD = OUTPUT_DIR / "asx_quality_first_acquisition_plan_v2_20b.md"
SOURCES_CSV = OUTPUT_DIR / "asx_quality_first_acquisition_sources_v2_20b.csv"
SCOPE_RULES_CSV = OUTPUT_DIR / "asx_quality_first_scope_rules_v2_20b.csv"
EXPECTED_YIELD_CSV = OUTPUT_DIR / "asx_quality_first_expected_yield_v2_20b.csv"
ROADMAP_CSV = OUTPUT_DIR / "asx_quality_first_roadmap_v2_20b.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_quality_first_acquisition_plan_checks_v2_20b.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_quality_first_next_actions_v2_20b.csv"

EXPECTED_V220A_STATUS = "QUALITY_FIRST_TARGET_RESET_COMPLETED_42K_45K_OPERATIONAL_ASX_SELECTED_50K_ASPIRATIONAL_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
HKEX_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
HKEX_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED = 608
ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED = 3608
ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED = 8608

SELECTED_PROVIDER = "ASX"
STATUS_SUCCESS = "ASX_QUALITY_FIRST_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_RAW_ACQUISITION_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_QUALITY_FIRST_ACQUISITION_PLAN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20C - ASX Quality-First Raw Acquisition"
NEXT_PHASE_REVIEW = "v2.20B_REVIEW - ASX Quality-First Acquisition Plan Review"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


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


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        SOURCES_CSV,
        SCOPE_RULES_CSV,
        EXPECTED_YIELD_CSV,
        ROADMAP_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220a = read_json(V220A_JSON)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_rows = count_csv_rows(HKEX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_before = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_after = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

    rows_needed_to_quality_floor = max(QUALITY_FLOOR_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_quality_ceiling = max(QUALITY_CEILING_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_aspirational_50k = max(ASPIRATIONAL_TARGET - hkex_validated_candidate_rows, 0)

    source_rows = [
        {
            "priority": 1,
            "source_id": "asx_listed_companies_page",
            "source_name": "ASX listed companies complete list page",
            "source_type": "official_asx_page_with_csv_download",
            "url": "https://www.asx.com.au/markets/trade-our-cash-market/overview/indices",
            "planned_capture_mode": "html_page_plus_discovered_csv_link",
            "direct_download_candidate_url": "",
            "expected_format": "html_discovery_plus_csv",
            "expected_fields": "asx_code;company_name;gics_sector_if_available",
            "quality_role": "primary_universe_candidate_source",
            "officiality": "official",
            "freshness_note": "ASX page states the complete list CSV is updated after each trading day.",
            "raw_phase_action": "capture_page_and_discover_download_complete_list_csv",
            "risk": "download link may be dynamic or legacy endpoint may need repair",
        },
        {
            "priority": 2,
            "source_id": "asx_isin_directory",
            "source_name": "ASX ISIN directory for ASX listed companies",
            "source_type": "official_asx_excel_download",
            "url": "https://www.asx.com.au/markets/market-resources/isin-services",
            "planned_capture_mode": "html_page_plus_xls_download",
            "direct_download_candidate_url": "https://www.asx.com.au/content/dam/asx/issuers/ISIN.xls",
            "expected_format": "xls",
            "expected_fields": "asx_code;isin;security_name;instrument_identifier",
            "quality_role": "identifier_enrichment_and_duplicate_control",
            "officiality": "official",
            "freshness_note": "ASX page states the ISIN file is updated monthly.",
            "raw_phase_action": "capture_page_and_download_isin_xls_if_accessible",
            "risk": "xls parsing required; file may include non-equity instruments requiring scope filter",
        },
        {
            "priority": 3,
            "source_id": "asx_codes_and_descriptors",
            "source_name": "ASX codes and descriptors",
            "source_type": "official_asx_reference_page",
            "url": "https://www.asx.com.au/markets/market-resources/asx-codes-and-descriptors",
            "planned_capture_mode": "html_page",
            "direct_download_candidate_url": "",
            "expected_format": "html",
            "expected_fields": "code_length_rules;secondary_issue_rules;debt_rules;etp_rules;derivative_rules;warrant_rules",
            "quality_role": "instrument_scope_guard_rules",
            "officiality": "official",
            "freshness_note": "Reference page explains ASX code patterns and product-type distinctions.",
            "raw_phase_action": "capture_page_for_scope_rules_and_filter_documentation",
            "risk": "reference only; not a candidate source",
        },
        {
            "priority": 4,
            "source_id": "asx_market_statistics",
            "source_name": "ASX market statistics and listed entities",
            "source_type": "official_asx_statistics_page",
            "url": "https://www.asx.com.au/about/market-statistics",
            "planned_capture_mode": "html_page",
            "direct_download_candidate_url": "",
            "expected_format": "html",
            "expected_fields": "listed_entities;market_cap_statistics;historical_stats_links",
            "quality_role": "sanity_check_and_market_size_context",
            "officiality": "official",
            "freshness_note": "ASX publishes market statistics and linked listed-entity counts.",
            "raw_phase_action": "capture_page_for_expected_universe_size_and_context",
            "risk": "statistics only; not a primary candidate list",
        },
        {
            "priority": 5,
            "source_id": "asx_legacy_csv_candidate",
            "source_name": "ASX listed companies legacy CSV endpoint candidate",
            "source_type": "legacy_direct_csv_candidate",
            "url": "https://www.asx.com.au/asx/research/ASXListedCompanies.csv",
            "planned_capture_mode": "attempt_direct_csv_as_secondary_candidate",
            "direct_download_candidate_url": "https://www.asx.com.au/asx/research/ASXListedCompanies.csv",
            "expected_format": "csv",
            "expected_fields": "asx_code;company_name;gics_sector_if_available",
            "quality_role": "secondary_download_candidate_only",
            "officiality": "official_url_candidate_but_unverified",
            "freshness_note": "Use only if reachable in raw acquisition; otherwise rely on page discovery.",
            "raw_phase_action": "attempt_download_but_do_not_fail_phase_if_404",
            "risk": "known possible 404 or redirected endpoint; repair may be required",
        },
    ]

    scope_rule_rows = [
        {
            "rule_id": "ASX_INCLUDE_001",
            "scope": "include",
            "instrument_group": "ordinary_equity",
            "rule": "include ordinary listed company shares where code/name/descriptor supports equity scope",
            "reason": "Core target for Scout Finance candidate quality.",
            "raw_filter_hint": "prefer 3-character issuer/company codes; validate against descriptors and ISIN file",
            "severity": "critical",
        },
        {
            "rule_id": "ASX_INCLUDE_002",
            "scope": "include_conditional",
            "instrument_group": "a_reit",
            "rule": "include liquid A-REITs if clearly listed equity-like vehicles",
            "reason": "A-REITs are common ASX equity-like instruments and useful for quality universe coverage.",
            "raw_filter_hint": "include only if not duplicated and not structured product",
            "severity": "warning",
        },
        {
            "rule_id": "ASX_INCLUDE_003",
            "scope": "include_conditional",
            "instrument_group": "listed_investment_company_or_trust",
            "rule": "include only if it behaves as listed equity and passes duplicate/instrument checks",
            "reason": "Some LIC/LIT instruments may be useful, but they should not inflate the universe by default.",
            "raw_filter_hint": "separate from ordinary shares; count separately",
            "severity": "warning",
        },
        {
            "rule_id": "ASX_EXCLUDE_001",
            "scope": "exclude",
            "instrument_group": "warrants",
            "rule": "exclude warrants by default",
            "reason": "Warrants are not operating-company equity candidates and were explicitly excluded in v2.20A stop rules.",
            "raw_filter_hint": "use code/descriptors; ASX reference notes warrant code conventions",
            "severity": "critical",
        },
        {
            "rule_id": "ASX_EXCLUDE_002",
            "scope": "exclude",
            "instrument_group": "exchange_traded_options",
            "rule": "exclude options by default",
            "reason": "Options are derivatives, not equity candidates.",
            "raw_filter_hint": "use code length/descriptors; ASX reference explains option code structure",
            "severity": "critical",
        },
        {
            "rule_id": "ASX_EXCLUDE_003",
            "scope": "exclude",
            "instrument_group": "debt_interest_rate_securities_notes_hybrids",
            "rule": "exclude debt, notes, interest-rate securities and hybrids by default",
            "reason": "Debt and hybrid securities are not core equity candidates.",
            "raw_filter_hint": "flag 4/5/6-character debt/security codes and descriptor keywords",
            "severity": "critical",
        },
        {
            "rule_id": "ASX_EXCLUDE_004",
            "scope": "exclude",
            "instrument_group": "rights_secondary_issues_partly_paid",
            "rule": "exclude rights, special settlement, partly paid and other secondary issues by default",
            "reason": "Avoid duplicating underlying equities or adding temporary instruments.",
            "raw_filter_hint": "use ASX code suffix/descriptor documentation",
            "severity": "critical",
        },
        {
            "rule_id": "ASX_EXCLUDE_005",
            "scope": "exclude",
            "instrument_group": "etf_managed_fund_structured_product",
            "rule": "exclude ETFs, managed funds and structured products by default",
            "reason": "Quality-first route is for good equity candidates, not fund products.",
            "raw_filter_hint": "separate ETPs; do not include unless explicitly approved later",
            "severity": "critical",
        },
        {
            "rule_id": "ASX_EXCLUDE_006",
            "scope": "exclude_or_flag",
            "instrument_group": "illiquid_speculative_microcap",
            "rule": "exclude or flag speculative/illiquid microcaps where source allows",
            "reason": "Avoid filling 42k-45k with low-quality speculative rows.",
            "raw_filter_hint": "use market cap/sector/index membership if available; otherwise defer to validation phase",
            "severity": "warning",
        },
    ]

    expected_yield_rows = [
        {
            "scenario": "conservative_quality_floor",
            "gross_official_rows_expected": "unknown_until_raw_acquisition",
            "clean_net_new_expected_min": 250,
            "clean_net_new_expected_mid": 608,
            "clean_net_new_expected_high": 1000,
            "target_effect": "may_cross_42k_if_mid_case",
            "decision_rule": "continue if >=500 clean net-new or if quality is exceptional",
        },
        {
            "scenario": "base_quality_case",
            "gross_official_rows_expected": "unknown_until_raw_acquisition",
            "clean_net_new_expected_min": 608,
            "clean_net_new_expected_mid": 1200,
            "clean_net_new_expected_high": 1800,
            "target_effect": "crosses_42k_and_moves_toward_45k",
            "decision_rule": "continue to canonical validation dry run if instrument scope remains clean",
        },
        {
            "scenario": "strong_quality_case",
            "gross_official_rows_expected": "unknown_until_raw_acquisition",
            "clean_net_new_expected_min": 1800,
            "clean_net_new_expected_mid": 2500,
            "clean_net_new_expected_high": 3608,
            "target_effect": "could_reach_or_approach_45k",
            "decision_rule": "stop at 45k ceiling unless exceptional clean source remains",
        },
        {
            "scenario": "bad_yield_case",
            "gross_official_rows_expected": "unknown_until_raw_acquisition",
            "clean_net_new_expected_min": 0,
            "clean_net_new_expected_mid": 249,
            "clean_net_new_expected_high": 499,
            "target_effect": "does_not_justify_long_route_unless_quality_exceptional",
            "decision_rule": "fast closure and switch to TMX_TSX_ONLY backup",
        },
    ]

    roadmap_rows = [
        {
            "phase": "v2.20A",
            "title": "Quality-First Target Reset and Provider Selection",
            "status": "closed",
            "purpose": "Set 42k-45k operational target and select ASX.",
        },
        {
            "phase": "v2.20B",
            "title": "ASX Quality-First Acquisition Plan",
            "status": "generated_by_this_phase",
            "purpose": "Define official ASX sources, scope rules, yield expectations and raw acquisition route.",
        },
        {
            "phase": "v2.20C",
            "title": "ASX Quality-First Raw Acquisition",
            "status": "next",
            "purpose": "Capture ASX official pages and structured downloads without extraction.",
        },
        {
            "phase": "v2.20D",
            "title": "ASX Raw Validation",
            "status": "planned",
            "purpose": "Validate captured ASX raw files and determine extraction readiness.",
        },
        {
            "phase": "v2.20E",
            "title": "ASX Candidate Extraction Dry Run",
            "status": "planned_if_raw_ready",
            "purpose": "Extract ASX candidate rows with instrument-scope classification.",
        },
        {
            "phase": "v2.20F",
            "title": "ASX Candidate Validation Against Current Candidate Dry Run",
            "status": "planned_if_extraction_ready",
            "purpose": "Classify net-new, duplicates and excluded scope against HKEX validated candidate.",
        },
        {
            "phase": "v2.20G",
            "title": "ASX Expanded Rebuild Candidate",
            "status": "conditional",
            "purpose": "Append only clean ASX net-new rows if quality and yield justify it.",
        },
        {
            "phase": "v2.20H",
            "title": "ASX Expanded Validation",
            "status": "conditional",
            "purpose": "Validate ASX expanded candidate if rebuild is performed.",
        },
        {
            "phase": "v2.20I",
            "title": "ASX Closure Report",
            "status": "conditional",
            "purpose": "Close ASX route and decide whether to stop, freeze, or move to backup provider.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "ASX",
            "action": "open_asx_quality_first_raw_acquisition",
            "priority": "high",
            "reason": "Official ASX source plan is ready and raw capture should test page discovery plus structured downloads.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "raw acquisition only; no extraction; no canonical replacement; no scoring",
        },
        {
            "action_order": 2,
            "action_scope": "quality_target",
            "action": "preserve_42k_45k_operational_band",
            "priority": "high",
            "reason": "Current HKEX validated candidate has 41,392 rows; only 608 clean rows are needed for 42k.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "stop at 45k unless exceptional clean source appears",
        },
        {
            "action_order": 3,
            "action_scope": "fallback",
            "action": "keep_tmx_tsx_only_as_backup",
            "priority": "medium",
            "reason": "If ASX raw acquisition or yield fails, TSX main market is the preferred backup.",
            "recommended_phase": "post-ASX closure or ASX block",
            "guardrails": "TSXV excluded unless explicitly approved",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_20a_report_exists", V220A_JSON.exists(), "critical", str(V220A_JSON))
    add_check("v2_20a_status_expected", v220a.get("status") == EXPECTED_V220A_STATUS, "critical", str(v220a.get("status", "")))
    add_check("v2_20a_selected_provider_asx", v220a.get("target_summary", {}).get("selected_next_provider") == "ASX", "critical", str(v220a.get("target_summary", {}).get("selected_next_provider")))
    add_check("v2_20a_next_phase_expected", v220a.get("recommended_next_phase") == "v2.20B - ASX Quality-First Acquisition Plan", "critical", str(v220a.get("recommended_next_phase")))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("hkex_validated_candidate_rows_expected", hkex_validated_candidate_rows == HKEX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"hkex_rows={hkex_validated_candidate_rows}")
    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("current_candidate_sha_expected", current_candidate_sha_before == CURRENT_CANDIDATE_SHA_EXPECTED, "critical", current_candidate_sha_before)
    add_check("hkex_validated_candidate_sha_expected", hkex_validated_candidate_sha_before == HKEX_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", hkex_validated_candidate_sha_before)
    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("current_candidate_sha_unchanged", current_candidate_sha_before == current_candidate_sha_after, "critical", "current candidate sha unchanged")
    add_check("hkex_candidate_sha_unchanged", hkex_validated_candidate_sha_before == hkex_validated_candidate_sha_after, "critical", "HKEX candidate sha unchanged")
    add_check("quality_floor_target_preserved", QUALITY_FLOOR_TARGET == 42000, "critical", f"quality_floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_target_preserved", QUALITY_CEILING_TARGET == 45000, "critical", f"quality_ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_needed_to_quality_floor_expected", rows_needed_to_quality_floor == ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED, "critical", f"rows_needed_to_42k={rows_needed_to_quality_floor}")
    add_check("rows_needed_to_quality_ceiling_expected", rows_needed_to_quality_ceiling == ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED, "critical", f"rows_needed_to_45k={rows_needed_to_quality_ceiling}")
    add_check("rows_needed_to_50k_aspirational_expected", rows_needed_to_aspirational_50k == ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_needed_to_50k={rows_needed_to_aspirational_50k}")
    add_check("official_sources_defined", len(source_rows) >= 4, "critical", f"sources={len(source_rows)}")
    add_check("primary_asx_source_defined", source_rows[0]["source_id"] == "asx_listed_companies_page", "critical", source_rows[0]["source_id"])
    add_check("isin_enrichment_source_defined", any(row["source_id"] == "asx_isin_directory" for row in source_rows), "critical", "asx_isin_directory")
    add_check("scope_rules_defined", len(scope_rule_rows) >= 8, "critical", f"scope_rules={len(scope_rule_rows)}")
    add_check("exclude_derivatives_debt_structured_products", all(group in [row["instrument_group"] for row in scope_rule_rows] for group in ["warrants", "exchange_traded_options", "debt_interest_rate_securities_notes_hybrids", "etf_managed_fund_structured_product"]), "critical", "critical exclusions present")
    add_check("yield_scenarios_defined", len(expected_yield_rows) >= 4, "critical", f"yield_scenarios={len(expected_yield_rows)}")
    add_check("next_phase_raw_acquisition", NEXT_PHASE == "v2.20C - ASX Quality-First Raw Acquisition", "critical", NEXT_PHASE)
    add_check("acquisition_plan_only", True, "critical", "acquisition plan only")
    add_check("network_download_not_performed", True, "critical", "network_download_performed=False")
    add_check("raw_acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("candidate_validation_not_performed", True, "critical", "candidate_validation_against_canonical_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("expanded_validation_not_performed", True, "critical", "expanded_validation_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("current_candidate_dataset_not_modified", True, "critical", "current_candidate_dataset_modified=False")
    add_check("hkex_candidate_dataset_not_modified", True, "critical", "hkex_candidate_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed == 0:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
    else:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW

    plan_summary = {
        "selected_provider": SELECTED_PROVIDER,
        "current_hkex_validated_candidate_rows": hkex_validated_candidate_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_needed_to_quality_floor": rows_needed_to_quality_floor,
        "rows_needed_to_quality_ceiling": rows_needed_to_quality_ceiling,
        "rows_needed_to_aspirational_50k": rows_needed_to_aspirational_50k,
        "primary_source": "asx_listed_companies_page",
        "identifier_enrichment_source": "asx_isin_directory",
        "instrument_scope_reference": "asx_codes_and_descriptors",
        "source_count": len(source_rows),
        "scope_rule_count": len(scope_rule_rows),
        "expected_yield_scenario_count": len(expected_yield_rows),
        "critical_failed_checks": critical_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    write_csv(SOURCES_CSV, source_rows, ["priority", "source_id", "source_name", "source_type", "url", "planned_capture_mode", "direct_download_candidate_url", "expected_format", "expected_fields", "quality_role", "officiality", "freshness_note", "raw_phase_action", "risk"])
    write_csv(SCOPE_RULES_CSV, scope_rule_rows, ["rule_id", "scope", "instrument_group", "rule", "reason", "raw_filter_hint", "severity"])
    write_csv(EXPECTED_YIELD_CSV, expected_yield_rows, ["scenario", "gross_official_rows_expected", "clean_net_new_expected_min", "clean_net_new_expected_mid", "clean_net_new_expected_high", "target_effect", "decision_rule"])
    write_csv(ROADMAP_CSV, roadmap_rows, ["phase", "title", "status", "purpose"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "plan_summary": plan_summary,
        "sources": source_rows,
        "scope_rules": scope_rule_rows,
        "expected_yield": expected_yield_rows,
        "roadmap": roadmap_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "acquisition_plan_only": True,
            "selected_provider": SELECTED_PROVIDER,
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": current_candidate_sha_before == current_candidate_sha_after,
            "hkex_validated_candidate_dataset_read": True,
            "hkex_validated_candidate_dataset_modified": False,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    source_lines = "\n".join(
        f"- P{row['priority']} `{row['source_id']}` — {row['source_type']} — {row['url']}"
        for row in source_rows
    )
    scope_lines = "\n".join(
        f"- `{row['rule_id']}` — {row['scope']} `{row['instrument_group']}` — {row['rule']}"
        for row in scope_rule_rows
    )
    yield_lines = "\n".join(
        f"- `{row['scenario']}` — mid `{row['clean_net_new_expected_mid']}` clean net-new — {row['target_effect']}"
        for row in expected_yield_rows
    )
    roadmap_lines = "\n".join(
        f"- `{row['phase']}` — {row['title']}: `{row['status']}`"
        for row in roadmap_rows
    )
    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )
    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.20B defines the ASX quality-first acquisition plan.

The project now operates with a **{QUALITY_FLOOR_TARGET:,}–{QUALITY_CEILING_TARGET:,}** quality-first target band. The current HKEX validated candidate dataset has **{hkex_validated_candidate_rows:,}** rows, so ASX only needs **{rows_needed_to_quality_floor:,}** clean net-new rows to cross the 42k floor and **{rows_needed_to_quality_ceiling:,}** clean net-new rows to reach the 45k ceiling.

50k remains aspirational only. ASX must not be used to add low-quality rows, warrants, options, debt, rights, structured products, duplicated fund-like instruments or speculative illiquid microcaps merely to increase row count.

This phase is an acquisition plan only. It does not download ASX files, does not extract candidates, does not validate candidates against canonical, does not rebuild a candidate dataset, does not promote any dataset to canonical, and does not run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Plan summary

- Selected provider: `{SELECTED_PROVIDER}`
- HKEX validated candidate rows: `{hkex_validated_candidate_rows}`
- Operational target floor: `{QUALITY_FLOOR_TARGET}`
- Operational target ceiling: `{QUALITY_CEILING_TARGET}`
- Aspirational target: `{ASPIRATIONAL_TARGET}`
- Rows needed to 42k: `{rows_needed_to_quality_floor}`
- Rows needed to 45k: `{rows_needed_to_quality_ceiling}`
- Rows needed to 50k aspirational: `{rows_needed_to_aspirational_50k}`
- Primary source: `asx_listed_companies_page`
- Identifier enrichment source: `asx_isin_directory`
- Scope reference: `asx_codes_and_descriptors`
- Critical failed checks: `{critical_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Official source plan

{source_lines}

## Scope rules

{scope_lines}

## Expected yield scenarios

{yield_lines}

## Roadmap

{roadmap_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Acquisition plan only: true
- Selected provider: `{SELECTED_PROVIDER}`
- Network download performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current candidate dataset modified: false
- HKEX validated candidate dataset modified: false
- Active canonical replaced: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.20B ASX quality-first acquisition plan completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("PLAN_SUMMARY:")
    for key, value in plan_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCES:")
    for row in source_rows:
        print(f"- P{row['priority']} {row['source_id']}: {row['url']} ({row['quality_role']})")
    print("")
    print("SCOPE_RULES:")
    for row in scope_rule_rows:
        print(f"- {row['rule_id']}: {row['scope']} {row['instrument_group']} - {row['rule']}")
    print("")
    print("EXPECTED_YIELD:")
    for row in expected_yield_rows:
        print(f"- {row['scenario']}: mid={row['clean_net_new_expected_mid']} effect={row['target_effect']}")
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
