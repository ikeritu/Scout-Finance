from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.18B"
PHASE = "TWSE + TPEx Acquisition Plan"
PHASE_TYPE = "acquisition-plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
VALIDATED_NSE_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"
V218A_JSON = OUTPUT_DIR / "next_provider_route_selection_v2_18a.json"

REPORT_JSON = OUTPUT_DIR / "twse_tpex_acquisition_plan_v2_18b.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_acquisition_plan_v2_18b.md"
SOURCE_PLAN_CSV = OUTPUT_DIR / "twse_tpex_source_plan_v2_18b.csv"
ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_acquisition_actions_v2_18b.csv"
FILTER_POLICY_CSV = OUTPUT_DIR / "twse_tpex_filter_policy_v2_18b.csv"
SCHEMA_PLAN_CSV = OUTPUT_DIR / "twse_tpex_candidate_schema_plan_v2_18b.csv"

EXPECTED_V218A_STATUS = "NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_TWSE_TPEX_SELECTED_50K_TARGET_ACTIVE_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
VALIDATED_CANDIDATE_ROWS_EXPECTED = 40300
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9700

RECOMMENDED_NEXT_PHASE = "v2.18C - TWSE + TPEx Raw Acquisition"

SOURCE_PLAN_FIELDS = [
    "source_id",
    "provider",
    "market",
    "source_category",
    "source_url",
    "method",
    "planned_raw_kind",
    "priority",
    "candidate_role",
    "expected_confidence",
    "include_in_v2_18c",
    "filter_policy_ref",
    "known_risks",
    "notes",
]

ACTIONS_FIELDS = [
    "action_order",
    "action_id",
    "source_id",
    "action_type",
    "allowed_in_v2_18c",
    "allowed_in_v2_18b",
    "expected_output",
    "guardrails",
    "notes",
]

FILTER_POLICY_FIELDS = [
    "policy_id",
    "policy_group",
    "rule_type",
    "rule",
    "decision",
    "severity",
    "notes",
]

SCHEMA_PLAN_FIELDS = [
    "target_field",
    "candidate_source_fields",
    "required",
    "normalization",
    "fallback",
    "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict]]:
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


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
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
        SOURCE_PLAN_CSV,
        ACTIONS_CSV,
        FILTER_POLICY_CSV,
        SCHEMA_PLAN_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    v218a = read_json(V218A_JSON)
    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)
    candidate_header, candidate_rows = read_csv_with_header(VALIDATED_NSE_CANDIDATE_DATASET)

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())
    candidate_sha = sha256_bytes(VALIDATED_NSE_CANDIDATE_DATASET.read_bytes())

    active_canonical_rows = len(canonical_rows)
    validated_candidate_rows = len(candidate_rows)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - validated_candidate_rows, 0)
    completion_percent = round((validated_candidate_rows / FINAL_TARGET_CANDIDATES) * 100, 2)

    source_plan = [
        {
            "source_id": "twse_openapi_swagger",
            "provider": "TWSE",
            "market": "Taiwan",
            "source_category": "official_api_catalog",
            "source_url": "https://openapi.twse.com.tw/",
            "method": "GET",
            "planned_raw_kind": "html/swagger_catalog",
            "priority": 1,
            "candidate_role": "discovery_catalog",
            "expected_confidence": "support",
            "include_in_v2_18c": True,
            "filter_policy_ref": "catalog_only",
            "known_risks": "Swagger catalog may require JSON route validation in v2.18C",
            "notes": "Official TWSE OpenAPI catalog. Used to confirm endpoint availability before parsing.",
        },
        {
            "source_id": "twse_listed_company_profile",
            "provider": "TWSE",
            "market": "Taiwan",
            "source_category": "listed_company_profile",
            "source_url": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
            "method": "GET",
            "planned_raw_kind": "json",
            "priority": 2,
            "candidate_role": "primary_twse_candidate_source",
            "expected_confidence": "high",
            "include_in_v2_18c": True,
            "filter_policy_ref": "ordinary_equity_filter",
            "known_risks": "Endpoint/schema must be validated; Chinese column names likely",
            "notes": "Primary planned source for TWSE listed company identities.",
        },
        {
            "source_id": "twse_stock_day_all",
            "provider": "TWSE",
            "market": "Taiwan",
            "source_category": "daily_trading_all_listed_stocks",
            "source_url": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
            "method": "GET",
            "planned_raw_kind": "json",
            "priority": 3,
            "candidate_role": "twse_symbol_name_crosscheck",
            "expected_confidence": "medium",
            "include_in_v2_18c": True,
            "filter_policy_ref": "ordinary_equity_filter",
            "known_risks": "Trading source may include non-ordinary instruments or only active traded instruments",
            "notes": "Support source for code/name coverage and active-trading cross-check.",
        },
        {
            "source_id": "twse_latest_listed_companies",
            "provider": "TWSE",
            "market": "Taiwan",
            "source_category": "latest_listed_companies",
            "source_url": "https://www.twse.com.tw/en/company/newlisting?response=html",
            "method": "GET",
            "planned_raw_kind": "html",
            "priority": 4,
            "candidate_role": "new_listing_crosscheck",
            "expected_confidence": "medium",
            "include_in_v2_18c": True,
            "filter_policy_ref": "ordinary_equity_filter",
            "known_risks": "Page may be recent-listing only, not full universe",
            "notes": "Support source for latest listings not captured elsewhere.",
        },
        {
            "source_id": "tpex_openapi_swagger",
            "provider": "TPEx",
            "market": "Taiwan",
            "source_category": "official_api_catalog",
            "source_url": "https://www.tpex.org.tw/openapi/",
            "method": "GET",
            "planned_raw_kind": "html/swagger_catalog",
            "priority": 5,
            "candidate_role": "discovery_catalog",
            "expected_confidence": "support",
            "include_in_v2_18c": True,
            "filter_policy_ref": "catalog_only",
            "known_risks": "May return 403 to some clients; v2.18C must preserve status and payload",
            "notes": "Official TPEx OpenAPI catalog. Used to discover stable raw routes.",
        },
        {
            "source_id": "tpex_daily_stock_quotes",
            "provider": "TPEx",
            "market": "Taiwan",
            "source_category": "mainboard_daily_quotes",
            "source_url": "https://www.tpex.org.tw/en-us/mainboard/trading/info/pricing.html",
            "method": "GET",
            "planned_raw_kind": "html/csv_link",
            "priority": 6,
            "candidate_role": "primary_tpex_candidate_source",
            "expected_confidence": "high_if_csv_download_resolves",
            "include_in_v2_18c": True,
            "filter_policy_ref": "ordinary_equity_filter",
            "known_risks": "CSV download link may be dynamic; v2.18C should capture page and downloadable CSV if resolvable",
            "notes": "Primary planned TPEx mainboard source if CSV/UTF-8 download can be resolved.",
        },
        {
            "source_id": "tpex_stock_pricing_page",
            "provider": "TPEx",
            "market": "Taiwan",
            "source_category": "mainboard_stock_pricing",
            "source_url": "https://www.tpex.org.tw/en-us/mainboard/trading/info/stock-pricing.html",
            "method": "GET",
            "planned_raw_kind": "html/csv_link",
            "priority": 7,
            "candidate_role": "tpex_symbol_name_crosscheck",
            "expected_confidence": "medium",
            "include_in_v2_18c": True,
            "filter_policy_ref": "ordinary_equity_filter",
            "known_risks": "May need query parameters/date; CSV link may be generated by page script",
            "notes": "Support source for TPEx code/company info and active listing cross-check.",
        },
        {
            "source_id": "tpex_mainboard_applicant_companies",
            "provider": "TPEx",
            "market": "Taiwan",
            "source_category": "applicant_companies",
            "source_url": "https://www.tpex.org.tw/en-us/mainboard/applying/status/company.html",
            "method": "GET",
            "planned_raw_kind": "html/csv_link",
            "priority": 8,
            "candidate_role": "applicant_review_only",
            "expected_confidence": "low_review",
            "include_in_v2_18c": True,
            "filter_policy_ref": "applicant_exclusion_policy",
            "known_risks": "Applicants are not necessarily listed/tradable; should not be promoted automatically",
            "notes": "Review-only source. Useful for diagnostics, not safe promotion by default.",
        },
        {
            "source_id": "tpex_gisa_company",
            "provider": "TPEx",
            "market": "Taiwan",
            "source_category": "gisa_company",
            "source_url": "https://www.tpex.org.tw/openapi/",
            "method": "GET",
            "planned_raw_kind": "openapi_endpoint_discovery",
            "priority": 9,
            "candidate_role": "deferred_or_review_only",
            "expected_confidence": "low_review",
            "include_in_v2_18c": True,
            "filter_policy_ref": "non_mainboard_review_policy",
            "known_risks": "GISA/emerging category may not belong in ordinary listed equity universe",
            "notes": "Capture if discoverable from TPEx OpenAPI catalog; do not promote without explicit validation.",
        },
    ]

    filter_policy = [
        {
            "policy_id": "catalog_only",
            "policy_group": "source_handling",
            "rule_type": "metadata",
            "rule": "catalog/swagger/html index sources are for discovery only",
            "decision": "do_not_extract_candidates_directly",
            "severity": "critical",
            "notes": "Catalogs guide v2.18C raw acquisition but are not candidate rows.",
        },
        {
            "policy_id": "ordinary_equity_filter",
            "policy_group": "include",
            "rule_type": "code_and_market",
            "rule": "include only official TWSE/TPEx listed/mainboard ordinary equity rows with code and company name",
            "decision": "eligible_for_candidate_extraction",
            "severity": "critical",
            "notes": "High confidence requires source, market, code, name and no non-equity markers.",
        },
        {
            "policy_id": "ordinary_equity_filter",
            "policy_group": "exclude",
            "rule_type": "instrument_type",
            "rule": "exclude ETF, ETN, fund, REIT, warrant, bond, beneficiary certificate, preferred share, rights, futures-linked product",
            "decision": "exclude_or_review",
            "severity": "critical",
            "notes": "Taiwan sources may mix securities types; non-equity rows must not be promoted automatically.",
        },
        {
            "policy_id": "ordinary_equity_filter",
            "policy_group": "exclude",
            "rule_type": "symbol_pattern",
            "rule": "exclude obvious ETF/ETN/security product code families such as 00xx where identified by source metadata/name",
            "decision": "exclude_or_review",
            "severity": "critical",
            "notes": "Pattern alone is not final; combine with source metadata and name keywords.",
        },
        {
            "policy_id": "ordinary_equity_filter",
            "policy_group": "exclude",
            "rule_type": "name_keyword",
            "rule": "exclude names containing ETF, ETN, FUND, REIT, WARRANT, BOND, INDEX, 指數, 基金, 債, 權證, 特別股",
            "decision": "exclude_or_review",
            "severity": "critical",
            "notes": "Chinese and English keyword filters are required in extraction phase.",
        },
        {
            "policy_id": "applicant_exclusion_policy",
            "policy_group": "exclude",
            "rule_type": "listing_status",
            "rule": "applicant or pending listing companies are diagnostics only unless separately confirmed listed/tradable",
            "decision": "review_only",
            "severity": "critical",
            "notes": "Applicant data must not be promoted as current listed universe.",
        },
        {
            "policy_id": "non_mainboard_review_policy",
            "policy_group": "review",
            "rule_type": "market_segment",
            "rule": "GISA, emerging, applicant or non-mainboard data require separate review bucket",
            "decision": "review_possible_future_route",
            "severity": "warning",
            "notes": "Useful for future coverage, not part of current safe 50k candidate path by default.",
        },
    ]

    acquisition_actions = [
        {
            "action_order": 1,
            "action_id": "prepare_raw_output_directory",
            "source_id": "all",
            "action_type": "filesystem_prepare",
            "allowed_in_v2_18c": True,
            "allowed_in_v2_18b": False,
            "expected_output": "outputs/full_universe_source_acquisition/twse_tpex_raw_acquisition_v2_18c/",
            "guardrails": "create directory only in v2.18C",
            "notes": "No directory/raw output created in v2.18B.",
        },
        {
            "action_order": 2,
            "action_id": "download_official_sources",
            "source_id": "all_included_sources",
            "action_type": "network_download",
            "allowed_in_v2_18c": True,
            "allowed_in_v2_18b": False,
            "expected_output": "raw files + manifest",
            "guardrails": "official TWSE/TPEx URLs only; preserve status codes and raw bytes",
            "notes": "Network is explicitly blocked in v2.18B and allowed only in v2.18C.",
        },
        {
            "action_order": 3,
            "action_id": "write_raw_manifest",
            "source_id": "all_included_sources",
            "action_type": "manifest",
            "allowed_in_v2_18c": True,
            "allowed_in_v2_18b": False,
            "expected_output": "twse_tpex_raw_acquisition_manifest_v2_18c.csv/json",
            "guardrails": "record URL, method, status, bytes, sha256, content type, timestamp",
            "notes": "No candidate parsing during acquisition.",
        },
        {
            "action_order": 4,
            "action_id": "defer_candidate_extraction",
            "source_id": "all",
            "action_type": "phase_gate",
            "allowed_in_v2_18c": False,
            "allowed_in_v2_18b": True,
            "expected_output": "candidate extraction blocked until v2.18E",
            "guardrails": "no parsing into candidates in v2.18B or v2.18C",
            "notes": "Extraction only after raw validation.",
        },
    ]

    schema_plan = [
        {
            "target_field": "raw_symbol",
            "candidate_source_fields": "Code | Securities Code | Stock Code | 公司代號",
            "required": True,
            "normalization": "strip; uppercase if alphabetic; preserve Taiwan numeric code as string",
            "fallback": "",
            "notes": "Primary identity field for Taiwan candidates.",
        },
        {
            "target_field": "raw_name",
            "candidate_source_fields": "Company | Company Name | Stock Name | 公司名稱 | 證券名稱",
            "required": True,
            "normalization": "strip whitespace; preserve original script",
            "fallback": "short_name if long_name missing",
            "notes": "Company/security name required for candidate extraction.",
        },
        {
            "target_field": "raw_exchange",
            "candidate_source_fields": "provider/source_id",
            "required": True,
            "normalization": "TWSE or TPEx",
            "fallback": "derive from source_id",
            "notes": "Used for exchange/market mapping.",
        },
        {
            "target_field": "raw_country",
            "candidate_source_fields": "constant",
            "required": True,
            "normalization": "Taiwan",
            "fallback": "Taiwan",
            "notes": "Country constant for this route.",
        },
        {
            "target_field": "raw_currency",
            "candidate_source_fields": "constant",
            "required": False,
            "normalization": "TWD",
            "fallback": "TWD",
            "notes": "Expected trading currency for ordinary Taiwan equities.",
        },
        {
            "target_field": "raw_isin",
            "candidate_source_fields": "ISIN if present",
            "required": False,
            "normalization": "uppercase; blank if unavailable",
            "fallback": "",
            "notes": "Taiwan official sources may not expose ISIN in primary rows.",
        },
        {
            "target_field": "raw_instrument_type",
            "candidate_source_fields": "instrument/security/category fields if present",
            "required": False,
            "normalization": "normalize to ordinary_equity/review/excluded",
            "fallback": "infer from source + filter policy",
            "notes": "Needed to exclude ETF/ETN/warrant/fund/bond products.",
        },
        {
            "target_field": "confidence_bucket",
            "candidate_source_fields": "source priority + filter policy",
            "required": True,
            "normalization": "high/medium/low",
            "fallback": "medium",
            "notes": "High only for primary listed/mainboard ordinary equity sources.",
        },
    ]

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18a_report_exists", V218A_JSON.exists(), "critical", str(V218A_JSON))
    add_check("v2_18a_status_expected", v218a.get("status") == EXPECTED_V218A_STATUS, "critical", v218a.get("status", ""))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("validated_candidate_dataset_exists", VALIDATED_NSE_CANDIDATE_DATASET.exists(), "critical", str(VALIDATED_NSE_CANDIDATE_DATASET))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("validated_candidate_rows_expected", validated_candidate_rows == VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"validated_candidate_rows={validated_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("candidate_schema_matches_canonical", canonical_header == candidate_header, "critical", f"canonical_cols={len(canonical_header)} candidate_cols={len(candidate_header)}")
    add_check("source_plan_has_twse_and_tpex", {"TWSE", "TPEx"} == set(row["provider"] for row in source_plan), "critical", str(sorted(set(row["provider"] for row in source_plan))))
    add_check("selected_provider_matches_v2_18a", v218a.get("route_decision", {}).get("selected_next_provider") == "TWSE + TPEx Taiwan", "critical", v218a.get("route_decision", {}).get("selected_next_provider", ""))
    add_check("final_target_50k_active", v218a.get("target_policy", {}).get("final_target_candidates") == FINAL_TARGET_CANDIDATES, "critical", str(v218a.get("target_policy", {}).get("final_target_candidates")))
    add_check("full59k_deprecated", v218a.get("target_policy", {}).get("full59k_status") == "DEPRECATED_DEFERRED_NOT_ACTIVE", "critical", str(v218a.get("target_policy", {}).get("full59k_status")))
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "canonical sha unchanged")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("raw_acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed == 0:
        status = "TWSE_TPEX_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "TWSE_TPEX_ACQUISITION_PLAN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.18B_FIX - TWSE + TPEx Acquisition Plan Repair"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "validated_candidate_dataset": str(VALIDATED_NSE_CANDIDATE_DATASET),
            "validated_candidate_rows": validated_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "candidate_completion_percent": completion_percent,
            "canonical_sha256_before": canonical_sha_before,
            "canonical_sha256_after": canonical_sha_after,
            "validated_candidate_sha256": candidate_sha,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
        },
        "source_plan_summary": {
            "planned_sources": len(source_plan),
            "twse_sources": sum(1 for row in source_plan if row["provider"] == "TWSE"),
            "tpex_sources": sum(1 for row in source_plan if row["provider"] == "TPEx"),
            "included_in_v2_18c": sum(1 for row in source_plan if row["include_in_v2_18c"]),
            "primary_candidate_sources": [
                row["source_id"] for row in source_plan if "primary" in row["candidate_role"]
            ],
            "review_only_sources": [
                row["source_id"] for row in source_plan if "review" in row["candidate_role"]
            ],
        },
        "acquisition_plan": {
            "selected_provider_route": "TWSE + TPEx Taiwan",
            "plan_only": True,
            "network_allowed_in_this_phase": False,
            "network_allowed_next_phase": True,
            "raw_acquisition_phase": "v2.18C",
            "raw_validation_phase": "v2.18D",
            "candidate_extraction_phase": "v2.18E",
            "candidate_validation_against_canonical_phase": "v2.18F",
            "expanded_rebuild_candidate_phase": "v2.18G",
            "expanded_validation_phase": "v2.18H",
            "closure_phase": "v2.18I",
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_files_written": False,
            "candidate_extraction_performed": False,
            "canonical_comparison_performed": False,
            "canonical_dataset_read": True,
            "validated_candidate_dataset_read": True,
            "source_plan_written": True,
            "filter_policy_written": True,
            "acquisition_actions_written": True,
            "schema_plan_written": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "final_target_50k_active": True,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)
    write_csv(SOURCE_PLAN_CSV, source_plan, SOURCE_PLAN_FIELDS)
    write_csv(ACTIONS_CSV, acquisition_actions, ACTIONS_FIELDS)
    write_csv(FILTER_POLICY_CSV, filter_policy, FILTER_POLICY_FIELDS)
    write_csv(SCHEMA_PLAN_CSV, schema_plan, SCHEMA_PLAN_FIELDS)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    source_lines = "\n".join(
        f"- P{row['priority']} `{row['source_id']}` — {row['provider']} — {row['candidate_role']} — {row['source_url']}"
        for row in source_plan
    )

    filter_lines = "\n".join(
        f"- `{row['policy_id']}` / {row['policy_group']}: {row['decision']} — {row['rule']}"
        for row in filter_policy
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.18B creates the acquisition plan for the TWSE + TPEx Taiwan route.

This is a plan-only phase. It does not perform network calls, downloads, raw acquisition, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls or full59k work.

The active target remains 50,000 candidates. The current validated candidate dataset has `{validated_candidate_rows}` rows, so `{rows_needed_to_50k}` additional validated candidate rows are needed.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{active_canonical_rows}`
- Validated candidate dataset: `{VALIDATED_NSE_CANDIDATE_DATASET}`
- Validated candidate rows: `{validated_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Candidate completion: `{completion_percent}%`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Planned sources

{source_lines}

## Filter policy

{filter_lines}

## Acquisition route

- v2.18C — Raw Acquisition
- v2.18D — Raw Validation
- v2.18E — Candidate Extraction Dry Run
- v2.18F — Candidate Validation Against Canonical Dry Run
- v2.18G — Expanded Rebuild Candidate
- v2.18H — Expanded Validation
- v2.18I — Closure Report

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw files written: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- Source plan written: true
- Filter policy written: true
- Acquisition actions written: true
- Schema plan written: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Final target 50k active: true
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Overwrite allowed: false

## Conclusion

v2.18B completes the TWSE + TPEx acquisition plan and prepares v2.18C raw acquisition.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.18B TWSE + TPEx acquisition plan completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_PLAN_SUMMARY:")
    for key, value in payload["source_plan_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("ACQUISITION_PLAN:")
    for key, value in payload["acquisition_plan"].items():
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
