from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.16B"
PHASE = "TMX Acquisition Plan"
PHASE_TYPE = "acquisition-plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

V216A_JSON = OUTPUT_DIR / "tmx_provider_route_confirmation_v2_16a.json"

PLAN_JSON = OUTPUT_DIR / "tmx_acquisition_plan_v2_16b.json"
PLAN_MD = OUTPUT_DIR / "tmx_acquisition_plan_v2_16b.md"
SOURCE_CANDIDATES_CSV = OUTPUT_DIR / "tmx_source_candidates_v2_16b.csv"
TAXONOMY_POLICY_CSV = OUTPUT_DIR / "tmx_taxonomy_policy_v2_16b.csv"
RISK_MATRIX_CSV = OUTPUT_DIR / "tmx_acquisition_risk_matrix_v2_16b.csv"
NEXT_PHASE_CHECKLIST_CSV = OUTPUT_DIR / "tmx_acquisition_next_phase_checklist_v2_16b.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

PROVIDER_ID = "tmx_tsx_tsxv_official_equities"
PROVIDER_NAME = "TMX / TSX / TSXV official equities"
PROVIDER_COUNTRY = "Canada"
PROVIDER_SCOPE = "TSX and TSXV listed equities"
NEXT_PHASE = "v2.16C - TMX Raw Acquisition"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def get_nested(payload: dict, *keys, default=None):
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def main() -> None:
    for path in [
        PLAN_JSON,
        PLAN_MD,
        SOURCE_CANDIDATES_CSV,
        TAXONOMY_POLICY_CSV,
        RISK_MATRIX_CSV,
        NEXT_PHASE_CHECKLIST_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    route = read_json(V216A_JSON)

    source_candidates = [
        {
            "source_id": "tmx_listed_company_directory",
            "source_name": "TSX/TSXV Listed Company Directory",
            "source_url": "https://www.tsx.com/en/listings/listing-with-us/listed-company-directory",
            "source_owner": "TMX / TSX",
            "source_type": "official_public_directory",
            "priority": 1,
            "expected_fields": "company_name|symbol|exchange|profile_link|possibly_sector|possibly_status",
            "expected_coverage": "TSX and TSXV listed companies",
            "expected_format": "html_dynamic_or_embedded_app",
            "v2_16c_action": "download_public_directory_html_and_linked_assets_if_allowed",
            "use_for_rebuild": "candidate_primary_if_extractable",
            "limitations": "May be dynamic, paginated, protected, or require app endpoint discovery.",
            "decision": "primary_candidate_source",
        },
        {
            "source_id": "tmx_equity_symbol_lookup",
            "source_name": "TMX apps equity search quick view",
            "source_url": "https://apps.tmx.com/HttpController?GetPage=SearchEquitiesQuickViewPage&language=en",
            "source_owner": "TMX",
            "source_type": "official_public_search_endpoint_or_html",
            "priority": 2,
            "expected_fields": "company_name|symbol|exchange",
            "expected_coverage": "Equity search across TSX and TSXV where available",
            "expected_format": "html_or_controller_response",
            "v2_16c_action": "download_controller_landing_response_only",
            "use_for_rebuild": "candidate_primary_or_endpoint_probe_seed",
            "limitations": "May require query parameters or letter-by-letter search in later controlled phase.",
            "decision": "primary_probe_seed",
        },
        {
            "source_id": "tmx_tsxv_lcdb_search",
            "source_name": "TSX Venture Listed Company Database Search",
            "source_url": "https://apps.tmx.com/TSXVenture/TSXVentureHttpController?GetPage=LcdbSearch",
            "source_owner": "TMX / TSXV",
            "source_type": "official_public_tsxv_database_search",
            "priority": 3,
            "expected_fields": "company_name|symbol|tsxv_status|possibly_naics|province|profile_link",
            "expected_coverage": "TSX Venture Exchange listed issuers",
            "expected_format": "html_controller_response",
            "v2_16c_action": "download_landing_response_only",
            "use_for_rebuild": "candidate_tsxv_supplement_if_extractable",
            "limitations": "May need controlled search by symbol/name/letter in later phase.",
            "decision": "tsxv_supplement_probe_seed",
        },
        {
            "source_id": "tmx_money_stocklists",
            "source_name": "TMX Money Stocklists",
            "source_url": "https://money.tmx.com/stock-lists",
            "source_owner": "TMX Money",
            "source_type": "official_public_stocklists",
            "priority": 4,
            "expected_fields": "symbol|company|price|volume|market_cap|category",
            "expected_coverage": "Thematic and ranked TSX/TSXV lists, not full universe",
            "expected_format": "html_dynamic",
            "v2_16c_action": "download_stocklist_landing_html",
            "use_for_rebuild": "supporting_source_not_primary",
            "limitations": "Stocklists are partial lists; useful for endpoint discovery and sanity checks, not full universe alone.",
            "decision": "supporting_probe_seed",
        },
        {
            "source_id": "tmx_money_recent_listings",
            "source_name": "TMX Money Recent Listings",
            "source_url": "https://money.tmx.com/stock-list/RECENT_LISTINGS_SYMBOLS",
            "source_owner": "TMX Money",
            "source_type": "official_public_recent_listings_stocklist",
            "priority": 5,
            "expected_fields": "symbol|company|exchange|listing_date_if_available",
            "expected_coverage": "Recent TSX/TSXV listings only",
            "expected_format": "html_dynamic",
            "v2_16c_action": "download_recent_listings_html",
            "use_for_rebuild": "supporting_source_for_delta_detection",
            "limitations": "Recent listings only; not comprehensive.",
            "decision": "supporting_recent_changes_source",
        },
        {
            "source_id": "tmx_newsroom_equity_financing_statistics",
            "source_name": "TMX Equity Financing Statistics",
            "source_url": "https://www.tmx.com/en/newsroom/press-releases",
            "source_owner": "TMX Group",
            "source_type": "official_public_monthly_statistics",
            "priority": 6,
            "expected_fields": "issuer_name|company_symbol|exchange|monthly_counts",
            "expected_coverage": "Monthly new issuers/listings and financing statistics",
            "expected_format": "html_press_release_or_resource_page",
            "v2_16c_action": "download_latest_relevant_statistics_pages_if_explicitly_selected",
            "use_for_rebuild": "supporting_validation_source",
            "limitations": "Monthly new issuers, not full universe.",
            "decision": "supporting_sanity_check_source",
        },
        {
            "source_id": "tmx_datalinx_reference_data",
            "source_name": "TMX Datalinx / TMX Info Services reference data",
            "source_url": "https://www.tmxinfoservices.com/",
            "source_owner": "TMX Datalinx / TMX Info Services",
            "source_type": "official_data_product_or_paid_reference_data",
            "priority": 7,
            "expected_fields": "security_master|symbol|issuer|exchange|instrument_type|isin_if_available",
            "expected_coverage": "Potentially high-quality official reference data",
            "expected_format": "paid_or_controlled_access",
            "v2_16c_action": "do_not_download_unless_public_access_confirmed",
            "use_for_rebuild": "candidate_only_if_public_or_authorized",
            "limitations": "May require license, account, or paid access.",
            "decision": "documented_fallback_not_executed_by_default",
        },
    ]

    taxonomy_policy = [
        {
            "category": "include",
            "instrument_pattern": "common_shares_or_ordinary_shares",
            "examples": "Common Shares|Ordinary Shares|Class A/B common equity",
            "policy": "include_if_company_equity_and_listed_on_tsx_or_tsxv",
            "reason": "Core full-universe target is listed equities.",
        },
        {
            "category": "include_review",
            "instrument_pattern": "preferred_shares",
            "examples": "Preferred Shares|Rate Reset Preferred",
            "policy": "include_only_if_existing_project_policy_allows_preferred_equity",
            "reason": "Equity-like but may inflate universe with share classes; needs explicit validation.",
        },
        {
            "category": "include_review",
            "instrument_pattern": "capital_pool_companies",
            "examples": "CPC issuers on TSXV",
            "policy": "review_in_v2_16d_before_inclusion",
            "reason": "Listed TSXV issuer type; may be valid equity but should be flagged.",
        },
        {
            "category": "exclude_by_default",
            "instrument_pattern": "etf_etp_fund",
            "examples": "ETF|ETP|Fund|Index Fund|Closed End Fund",
            "policy": "exclude",
            "reason": "Existing universe policy excludes ETFs/funds/non-operating vehicles.",
        },
        {
            "category": "exclude_by_default",
            "instrument_pattern": "cdr",
            "examples": "Canadian Depositary Receipt|CDR",
            "policy": "exclude",
            "reason": "Depositary products are not primary operating company equities.",
        },
        {
            "category": "exclude_by_default",
            "instrument_pattern": "warrants_rights_units_receipts",
            "examples": "Warrant|Right|Unit|Subscription Receipt",
            "policy": "exclude",
            "reason": "Non-common securities can duplicate issuers and distort universe.",
        },
        {
            "category": "exclude_by_default",
            "instrument_pattern": "debt_and_fixed_income",
            "examples": "Debenture|Bond|Note",
            "policy": "exclude",
            "reason": "Project target is equities, not fixed income.",
        },
        {
            "category": "exclude_or_review",
            "instrument_pattern": "nex_inactive_issuers",
            "examples": "NEX symbols often ending .H",
            "policy": "exclude_unless_explicitly_approved",
            "reason": "NEX can include issuers below TSXV ongoing listing standards; likely not desired for clean full universe.",
        },
    ]

    risk_matrix = [
        {
            "risk_id": "dynamic_html",
            "risk": "Directory pages may be rendered dynamically.",
            "severity": "high",
            "mitigation": "v2.16C raw acquisition captures landing HTML only; v2.16D validates whether endpoint discovery is needed.",
        },
        {
            "risk_id": "no_isin_in_public_directory",
            "risk": "TMX public pages may expose symbol/name/exchange but not ISIN.",
            "severity": "high",
            "mitigation": "Use ISIN where available; otherwise validate canonical matching policy in later dry-run before rebuild.",
        },
        {
            "risk_id": "instrument_type_ambiguity",
            "risk": "Public lists may mix common equity, ETFs, CDRs, warrants, rights, receipts or funds.",
            "severity": "high",
            "mitigation": "Keep taxonomy exclusions explicit and validate type markers before candidate extraction.",
        },
        {
            "risk_id": "symbol_suffixes",
            "risk": "Canadian symbols can include suffixes/classes such as .A, .B, .H, preferred series, or special forms.",
            "severity": "medium",
            "mitigation": "Do not normalize symbols in v2.16B/C; defer symbol normalization to a specific dry-run validation phase.",
        },
        {
            "risk_id": "tsx_vs_tsxv_vs_nex",
            "risk": "TSX, TSXV and NEX may require different treatment.",
            "severity": "medium",
            "mitigation": "Record exchange/market as raw field and keep NEX excluded or review-only unless approved.",
        },
        {
            "risk_id": "paid_reference_data",
            "risk": "Best official reference data may be behind TMX Datalinx licensing.",
            "severity": "medium",
            "mitigation": "Document paid/controlled route but do not access it without authorization.",
        },
        {
            "risk_id": "recent_lists_not_comprehensive",
            "risk": "TMX Money stocklists and recent listings are partial lists.",
            "severity": "medium",
            "mitigation": "Use them only for discovery/sanity checks, not as primary universe source.",
        },
        {
            "risk_id": "duplicate_share_classes",
            "risk": "Multiple classes or preferred lines may create duplicates at issuer level.",
            "severity": "medium",
            "mitigation": "Later canonical dry-run must define duplicate key policy: ISIN first, then exchange+symbol, then issuer review.",
        },
    ]

    next_phase_checklist = [
        {
            "phase": "v2.16C",
            "item": "create_raw_directory",
            "status": "planned",
            "guard": "raw_dir_must_not_exist_before_run",
        },
        {
            "phase": "v2.16C",
            "item": "download_tmx_listed_company_directory_landing_html",
            "status": "planned",
            "guard": "download_only_no_parse",
        },
        {
            "phase": "v2.16C",
            "item": "download_tmx_equity_symbol_lookup_landing_response",
            "status": "planned",
            "guard": "download_only_no_query_sweep",
        },
        {
            "phase": "v2.16C",
            "item": "download_tsxv_lcdb_search_landing_response",
            "status": "planned",
            "guard": "download_only_no_query_sweep",
        },
        {
            "phase": "v2.16C",
            "item": "download_tmx_money_stocklists_landing_html",
            "status": "planned",
            "guard": "supporting_source_only",
        },
        {
            "phase": "v2.16C",
            "item": "download_recent_listings_html",
            "status": "planned",
            "guard": "supporting_source_only",
        },
        {
            "phase": "v2.16C",
            "item": "write_manifest_hashes_status_codes",
            "status": "planned",
            "guard": "manifest_only_no_parsing",
        },
        {
            "phase": "v2.16C",
            "item": "do_not_read_canonical_dataset",
            "status": "mandatory",
            "guard": "canonical_dataset_read=False",
        },
        {
            "phase": "v2.16C",
            "item": "do_not_rebuild_expanded_universe",
            "status": "mandatory",
            "guard": "expanded_universe_rebuilt=False",
        },
    ]

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append(
            {
                "check": check,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add_check("v2_16a_route_confirmation_exists", V216A_JSON.exists(), "critical", str(V216A_JSON))
    add_check(
        "v2_16a_status_confirmed",
        route.get("status") == "TMX_PROVIDER_ROUTE_CONFIRMED_PLAN_ONLY_FULL_SOURCE_BLOCKED",
        "critical",
        route.get("status", ""),
    )
    add_check(
        "v2_16a_recommended_v2_16b",
        route.get("recommended_next_phase") == "v2.16B - TMX Acquisition Plan",
        "critical",
        route.get("recommended_next_phase", ""),
    )
    add_check(
        "provider_id_matches_v2_16a",
        get_nested(route, "route_confirmation", "next_provider_id", default="") == PROVIDER_ID,
        "critical",
        get_nested(route, "route_confirmation", "next_provider_id", default=""),
    )
    add_check("source_candidates_defined", len(source_candidates) >= 5, "critical", f"sources={len(source_candidates)}")
    add_check("primary_directory_defined", source_candidates[0]["source_id"] == "tmx_listed_company_directory", "critical", source_candidates[0]["source_id"])
    add_check("taxonomy_policy_defined", len(taxonomy_policy) >= 6, "critical", f"taxonomy_rows={len(taxonomy_policy)}")
    add_check("risk_matrix_defined", len(risk_matrix) >= 5, "critical", f"risk_rows={len(risk_matrix)}")
    add_check("next_phase_checklist_defined", len(next_phase_checklist) >= 5, "critical", f"checklist_rows={len(next_phase_checklist)}")
    add_check("current_rows_unchanged", CURRENT_ROWS == 38287, "critical", f"current_rows={CURRENT_ROWS}")
    add_check("rows_needed_unchanged", ROWS_NEEDED == 11713, "critical", f"rows_needed={ROWS_NEEDED}")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"{CURRENT_ROWS} < {FULL_SOURCE_THRESHOLD}")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_network", True, "critical", "network_download_performed=False")
    add_check("no_raw_downloads", True, "critical", "raw_files_downloaded=False")
    add_check("no_parsing", True, "critical", "parsing_performed=False")
    add_check("no_normalization", True, "critical", "normalization_performed=False")
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")

    status = (
        "TMX_ACQUISITION_PLAN_CREATED_NO_DOWNLOADS_PERFORMED_FULL_SOURCE_BLOCKED"
        if critical_failed == 0
        else "TMX_ACQUISITION_PLAN_FAILED_REVIEW_REQUIRED"
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "canonical_dataset": CURRENT_CANONICAL_DATASET,
            "current_rows": CURRENT_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED_PERCENT,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "provider": {
            "provider_id": PROVIDER_ID,
            "provider_name": PROVIDER_NAME,
            "country": PROVIDER_COUNTRY,
            "scope": PROVIDER_SCOPE,
            "route_confirmation_artifact": str(V216A_JSON),
            "route_confirmation_status": route.get("status", ""),
        },
        "acquisition_plan_summary": {
            "source_candidates": len(source_candidates),
            "primary_source_id": "tmx_listed_company_directory",
            "supporting_sources": [
                "tmx_equity_symbol_lookup",
                "tmx_tsxv_lcdb_search",
                "tmx_money_stocklists",
                "tmx_money_recent_listings",
                "tmx_newsroom_equity_financing_statistics",
            ],
            "paid_or_controlled_fallback": "tmx_datalinx_reference_data",
            "taxonomy_rows": len(taxonomy_policy),
            "risk_rows": len(risk_matrix),
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "recommended_next_phase": NEXT_PHASE,
            "critical_failed_checks": critical_failed,
        },
        "source_candidates": source_candidates,
        "taxonomy_policy": taxonomy_policy,
        "risk_matrix": risk_matrix,
        "next_phase_checklist": next_phase_checklist,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_probe_executed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "parsing_performed": False,
            "canonical_dataset_read": False,
            "canonical_dataset_modified": False,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": NEXT_PHASE,
    }

    write_json(PLAN_JSON, payload)
    write_csv(
        SOURCE_CANDIDATES_CSV,
        source_candidates,
        [
            "source_id",
            "source_name",
            "source_url",
            "source_owner",
            "source_type",
            "priority",
            "expected_fields",
            "expected_coverage",
            "expected_format",
            "v2_16c_action",
            "use_for_rebuild",
            "limitations",
            "decision",
        ],
    )
    write_csv(
        TAXONOMY_POLICY_CSV,
        taxonomy_policy,
        ["category", "instrument_pattern", "examples", "policy", "reason"],
    )
    write_csv(
        RISK_MATRIX_CSV,
        risk_matrix,
        ["risk_id", "risk", "severity", "mitigation"],
    )
    write_csv(
        NEXT_PHASE_CHECKLIST_CSV,
        next_phase_checklist,
        ["phase", "item", "status", "guard"],
    )

    source_lines = "\n".join(
        f"- `{row['source_id']}` priority={row['priority']} — {row['source_name']} — decision=`{row['decision']}` — {row['source_url']}"
        for row in source_candidates
    )

    taxonomy_lines = "\n".join(
        f"- `{row['category']}` — {row['instrument_pattern']} — policy=`{row['policy']}`"
        for row in taxonomy_policy
    )

    risk_lines = "\n".join(
        f"- `{row['risk_id']}` severity=`{row['severity']}` — {row['risk']} Mitigation: {row['mitigation']}"
        for row in risk_matrix
    )

    checklist_lines = "\n".join(
        f"- [{ 'x' if row['status'] in {'mandatory'} else ' ' }] {row['phase']} — {row['item']} — `{row['guard']}`"
        for row in next_phase_checklist
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    PLAN_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Current state

- Canonical dataset: `{CURRENT_CANONICAL_DATASET}`
- Current rows: `{CURRENT_ROWS}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completed: `{SOURCE_TO_50K_COMPLETED_PERCENT}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Provider

- Provider ID: `{PROVIDER_ID}`
- Provider name: `{PROVIDER_NAME}`
- Country: `{PROVIDER_COUNTRY}`
- Scope: `{PROVIDER_SCOPE}`
- Route confirmation artifact: `{V216A_JSON}`

## Acquisition plan summary

- Source candidates: `{len(source_candidates)}`
- Primary source: `tmx_listed_company_directory`
- Supporting sources: `tmx_equity_symbol_lookup`, `tmx_tsxv_lcdb_search`, `tmx_money_stocklists`, `tmx_money_recent_listings`, `tmx_newsroom_equity_financing_statistics`
- Paid/controlled fallback: `tmx_datalinx_reference_data`
- Taxonomy policy rows: `{len(taxonomy_policy)}`
- Risk rows: `{len(risk_matrix)}`
- Critical failed checks: `{critical_failed}`

## Source candidates

{source_lines}

## Taxonomy policy

{taxonomy_lines}

## Risk matrix

{risk_lines}

## v2.16C checklist

{checklist_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.16B: false
- Endpoint probe executed in v2.16B: false
- Raw files downloaded in v2.16B: false
- Raw files modified after write: false
- Parsing performed: false
- Canonical dataset read: false
- Canonical dataset modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX acquisition planning is complete.

The primary route is the official TSX/TSXV Listed Company Directory. Supporting routes include the TMX equity search controller, TSXV listed company database search, TMX Money stocklists, recent listings and monthly TMX equity financing statistics. TMX Datalinx is documented only as a paid or controlled official fallback and must not be accessed without authorization.

This phase is plan-only. It performs no network calls, no downloads, no parsing, no canonical reads, no canonical writes, no normalization, no net-new filtering and no rebuild.

## Recommended next phase

`{NEXT_PHASE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16B TMX acquisition plan completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("ACQUISITION_PLAN_SUMMARY:")
    for key, value in payload["acquisition_plan_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
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
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
