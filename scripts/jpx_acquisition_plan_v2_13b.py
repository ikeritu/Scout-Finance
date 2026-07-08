from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.13B"
PHASE = "JPX Acquisition Plan"
PHASE_TYPE = "plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ROUTE_JSON = OUTPUT_DIR / "next_provider_route_v2_13a.json"

PLAN_JSON = OUTPUT_DIR / "jpx_acquisition_plan_v2_13b.json"
PLAN_MD = OUTPUT_DIR / "jpx_acquisition_plan_v2_13b.md"
CONTRACT_CSV = OUTPUT_DIR / "jpx_acquisition_contract_v2_13b.csv"
PLANNED_OUTPUTS_CSV = OUTPUT_DIR / "jpx_planned_outputs_v2_13b.csv"
VALIDATION_QUESTIONS_CSV = OUTPUT_DIR / "jpx_validation_questions_v2_13b.csv"

CURRENT_EXPANDED_ROWS = 33158
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_FULL_SOURCE = 16842

GLOBAL_COMPLETED = 95
GLOBAL_PENDING = 5
EXPANDED_SOURCE_COMPLETED = 91
EXPANDED_SOURCE_PENDING = 9


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        PLAN_JSON,
        PLAN_MD,
        CONTRACT_CSV,
        PLANNED_OUTPUTS_CSV,
        VALIDATION_QUESTIONS_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.13B outputs:\n"
            + "\n".join(existing)
        )


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    no_overwrite_guard()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    route = read_json(ROUTE_JSON)

    hard_guards = {
        "phase_type": PHASE_TYPE,
        "network_download_performed": False,
        "raw_files_downloaded": False,
        "expanded_universe_rebuilt": False,
        "normalization_performed": False,
        "net_new_filtering_performed": False,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
    }

    acquisition_contract = [
        {
            "step_id": "01",
            "route_type": "official_data_portal_catalog",
            "target": "jpxdata_portal_catalog",
            "url_or_discovery_rule": "https://www.jpx.co.jp/english/markets/data-catalog/index.html",
            "expected_format": "html",
            "purpose": "Acquire JPX official data portal page for provenance and discovery of listed securities dataset.",
            "allowed_in_v2_13c": "HTTP GET raw HTML only, preserve bytes, compute SHA256, record metadata and candidate links.",
            "prohibited_in_v2_13c": "No parsing decision, no normalization, no net-new filtering, no rebuild, no scoring.",
            "raw_preservation_policy": "Save raw HTML exactly as received under raw/jpx_v2_13c/.",
            "validation_owner": "v2.13D",
        },
        {
            "step_id": "02",
            "route_type": "official_client_portal_catalog_entry",
            "target": "jpx_list_of_tse_listed_issues_catalog_entry",
            "url_or_discovery_rule": "https://clientportal.jpx.co.jp/ClientPortalEN/s/datacatalog/DataCatalog__c",
            "expected_format": "html_or_dynamic_catalog",
            "purpose": "Acquire official catalog entry/search surface where List of TSE-listed Issues is listed as free monthly Excel data.",
            "allowed_in_v2_13c": "HTTP GET raw HTML if accessible, preserve bytes, discover workbook/download links without accepting rows.",
            "prohibited_in_v2_13c": "No browser automation unless explicitly approved, no fragile scraping, no rebuild.",
            "raw_preservation_policy": "Save raw HTML exactly as received under raw/jpx_v2_13c/.",
            "validation_owner": "v2.13D",
        },
        {
            "step_id": "03",
            "route_type": "official_dataset_download_candidate",
            "target": "jpx_list_of_tse_listed_issues_workbook",
            "url_or_discovery_rule": "Discover only from official JPX data portal/catalog entry. Expected dataset title: List of TSE-listed Issues.",
            "expected_format": "xlsx_or_csv",
            "purpose": "Acquire official listed issues file as raw bytes if a direct official download link is discovered in v2.13C.",
            "allowed_in_v2_13c": "Download only direct official workbook/CSV discovered from JPX pages; preserve exact bytes, compute SHA256.",
            "prohibited_in_v2_13c": "No accepted filtering, no normalization, no net-new filtering, no rebuild.",
            "raw_preservation_policy": "Save raw workbook/CSV exactly as received under raw/jpx_v2_13c/.",
            "validation_owner": "v2.13D",
        },
        {
            "step_id": "04",
            "route_type": "official_fallback_search_page",
            "target": "jpx_listed_company_search",
            "url_or_discovery_rule": "https://www.jpx.co.jp/english/listing/co-search/index.html",
            "expected_format": "html_or_search_page",
            "purpose": "Acquire official listed company search page as fallback/provenance if the data portal route is dynamic or blocked.",
            "allowed_in_v2_13c": "HTTP GET raw HTML only, preserve bytes and candidate links.",
            "prohibited_in_v2_13c": "No scraping accepted rows from dynamic search UI, no rebuild.",
            "raw_preservation_policy": "Save raw HTML exactly as received under raw/jpx_v2_13c/.",
            "validation_owner": "v2.13D",
        },
        {
            "step_id": "05",
            "route_type": "semantic_caution",
            "target": "jpx_security_type_and_market_segment_semantics",
            "url_or_discovery_rule": "Derived only from official JPX listed issues file during validation.",
            "expected_format": "validation_rule",
            "purpose": "Prevent inclusion of ETFs, REITs, funds, preferred securities, foreign stocks or other non-common-equity instruments without review.",
            "allowed_in_v2_13c": "Record raw files and metadata only.",
            "prohibited_in_v2_13c": "No equity classification decision during acquisition.",
            "raw_preservation_policy": "Do not mutate source fields.",
            "validation_owner": "v2.13D",
        },
        {
            "step_id": "06",
            "route_type": "identifier_caution",
            "target": "jpx_local_code_format",
            "url_or_discovery_rule": "Preserve JPX/TSE local security codes exactly as text.",
            "expected_format": "validation_rule",
            "purpose": "Avoid numeric conversion and preserve leading zeros or special suffixes if present.",
            "allowed_in_v2_13c": "Store source file exactly and leave parsing decisions to validation.",
            "prohibited_in_v2_13c": "No conversion of local code to integer.",
            "raw_preservation_policy": "Raw official file remains source of truth.",
            "validation_owner": "v2.13D",
        },
    ]

    planned_outputs = [
        {
            "phase": "v2.13C",
            "path": "scripts/jpx_acquisition_v2_13c.py",
            "type": "script",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.13C",
            "path": "outputs/full_universe_source_acquisition/raw/jpx_v2_13c/",
            "type": "raw_directory",
            "required": "yes",
            "overwrite_policy": "new_directory_or_fail",
        },
        {
            "phase": "v2.13C",
            "path": "outputs/full_universe_source_acquisition/jpx_download_manifest_v2_13c.json",
            "type": "manifest_json",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.13C",
            "path": "outputs/full_universe_source_acquisition/jpx_download_manifest_v2_13c.csv",
            "type": "manifest_csv",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.13C",
            "path": "outputs/full_universe_source_acquisition/jpx_discovered_links_v2_13c.csv",
            "type": "discovery_manifest",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.13C",
            "path": "outputs/full_universe_source_acquisition/jpx_acquisition_report_v2_13c.md",
            "type": "report",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
    ]

    validation_questions = [
        {
            "question_id": "Q01",
            "question": "Does JPX expose a directly downloadable List of TSE-listed Issues file from official pages?",
            "validation_phase": "v2.13D",
        },
        {
            "question_id": "Q02",
            "question": "Is the downloaded file Excel, CSV or another structured format?",
            "validation_phase": "v2.13D",
        },
        {
            "question_id": "Q03",
            "question": "Which sheet/table contains the listed securities table?",
            "validation_phase": "v2.13D",
        },
        {
            "question_id": "Q04",
            "question": "Does the dataset contain local code, company name, market segment, security type, industry and ISIN?",
            "validation_phase": "v2.13D",
        },
        {
            "question_id": "Q05",
            "question": "How many rows exist before filtering?",
            "validation_phase": "v2.13D",
        },
        {
            "question_id": "Q06",
            "question": "How many rows are ordinary listed companies versus ETFs, REITs, preferred securities, funds, foreign stocks or other instruments?",
            "validation_phase": "v2.13D",
        },
        {
            "question_id": "Q07",
            "question": "How many candidate identifiers are net-new against expanded_universe_v2_12e?",
            "validation_phase": "v2.13D",
        },
        {
            "question_id": "Q08",
            "question": "Can JPX rows be normalized conservatively without brittle scraping?",
            "validation_phase": "v2.13D",
        },
        {
            "question_id": "Q09",
            "question": "Does JPX materially reduce the 16,842-row gap to 50k?",
            "validation_phase": "v2.13D",
        },
        {
            "question_id": "Q10",
            "question": "Should JPX be source provider, candidate provider, enrichment, reference-only or deferred?",
            "validation_phase": "v2.13D",
        },
    ]

    plan = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "JPX_ACQUISITION_PLAN_READY",
        "decision": "PROCEED_TO_V2_13C_JPX_ACQUISITION_ONLY_AFTER_V2_13B_VALIDATION_AND_COMMIT",
        "selected_provider": "jpx_listed_securities_csv",
        "generated_at_utc": utc_now(),
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
            "first_expansion_unlocked": True,
            "full_source_unlocked": False,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
            "v2_13a_route_decision": route.get("route_decision", "JPX_SELECTED_AS_NEXT_PROVIDER_ROUTE"),
            "v2_13a_commit": "642de26",
        },
        "hard_guards": hard_guards,
        "acquisition_contract_for_v2_13c": acquisition_contract,
        "planned_outputs_for_v2_13c": planned_outputs,
        "validation_questions_for_v2_13d": validation_questions,
        "project_percentages": {
            "v2_13b_jpx_acquisition_plan_completed_after_commit": 100,
            "v2_13b_jpx_acquisition_plan_pending_after_commit": 0,
            "expanded_real_source_completed": EXPANDED_SOURCE_COMPLETED,
            "expanded_real_source_pending": EXPANDED_SOURCE_PENDING,
            "full_source_50k_59k_completed": 0,
            "full_source_50k_59k_pending": 100,
            "global_completed": GLOBAL_COMPLETED,
            "global_pending": GLOBAL_PENDING,
        },
    }

    write_json(PLAN_JSON, plan)

    write_csv(
        CONTRACT_CSV,
        acquisition_contract,
        [
            "step_id",
            "route_type",
            "target",
            "url_or_discovery_rule",
            "expected_format",
            "purpose",
            "allowed_in_v2_13c",
            "prohibited_in_v2_13c",
            "raw_preservation_policy",
            "validation_owner",
        ],
    )

    write_csv(
        PLANNED_OUTPUTS_CSV,
        planned_outputs,
        ["phase", "path", "type", "required", "overwrite_policy"],
    )

    write_csv(
        VALIDATION_QUESTIONS_CSV,
        validation_questions,
        ["question_id", "question", "validation_phase"],
    )

    contract_lines = "\n".join(
        f"- {row['step_id']} `{row['target']}` — {row['route_type']} — {row['purpose']}"
        for row in acquisition_contract
    )

    planned_output_lines = "\n".join(
        f"- `{row['path']}`"
        for row in planned_outputs
    )

    validation_question_lines = "\n".join(
        f"- {row['question_id']}: {row['question']}"
        for row in validation_questions
    )

    md = f"""# {VERSION} - {PHASE}

Status: **JPX_ACQUISITION_PLAN_READY**

Phase type: **plan-only**

Selected provider: **jpx_listed_securities_csv**

Decision: **PROCEED_TO_V2_13C_JPX_ACQUISITION_ONLY_AFTER_V2_13B_VALIDATION_AND_COMMIT**

Generated at UTC: `{plan["generated_at_utc"]}`

## Confirmed previous phase

- v2.13A route decision: `{plan["current_state"]["v2_13a_route_decision"]}`
- v2.13A commit: `642de26`
- Selected route: `jpx_listed_securities_csv`

## Current state

- Current expanded rows: {CURRENT_EXPANDED_ROWS}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Rows needed for full source: {ROWS_NEEDED_FULL_SOURCE}
- First expansion unlocked: true
- Full source unlocked: false
- Full 59k status: blocked until source >=50k and gate explicitly approved

## Hard guards

- Network download performed: false
- Raw files downloaded: false
- Expanded universe rebuilt: false
- Normalization performed: false
- Net-new filtering performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## v2.13C controlled acquisition contract

v2.13C must be **acquisition-only**.

Allowed:

- Download official JPX data portal/catalog pages as raw HTML.
- Discover official workbook/CSV links related to List of TSE-listed Issues.
- Download only direct official listed-issues workbook/CSV if discovered from official JPX pages.
- Record URL, status code, content type, byte size, SHA256 and fetch timestamp.
- Preserve raw files exactly as received.

Forbidden:

- No accepted filtering.
- No normalization.
- No net-new filtering.
- No rebuild.
- No scoring.
- No OpenAI calls.
- No broker/API trading calls.
- No full 59k launch.
- No overwrite of active outputs.
- No conversion of JPX local code to integer.

## Contract rows

{contract_lines}

## Validation questions for v2.13D

{validation_question_lines}

## Planned v2.13C outputs

{planned_output_lines}

## Important cautions

JPX local security codes must be preserved as text.

JPX market segment and security type must not be accepted blindly. ETFs, REITs, preferred securities, funds, foreign stocks and other non-common-equity instruments need conservative review in v2.13D.

## Project percentages

- v2.13B JPX Acquisition Plan: 100% completed / 0% pending after commit
- Fuente real expandida: {EXPANDED_SOURCE_COMPLETED}% completed / {EXPANDED_SOURCE_PENDING}% pending
- Fuente real completa 50k-59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: {GLOBAL_COMPLETED}% completed / {GLOBAL_PENDING}% pending

## Recommended next phase

**v2.13C - JPX Acquisition Real**

Only after v2.13B outputs are validated, committed and pushed.
"""

    PLAN_MD.write_text(md, encoding="utf-8")

    print("v2.13B JPX acquisition plan-only completed.")
    print(f"- plan json: {PLAN_JSON}")
    print(f"- plan report: {PLAN_MD}")
    print(f"- contract csv: {CONTRACT_CSV}")
    print(f"- planned outputs csv: {PLANNED_OUTPUTS_CSV}")
    print(f"- validation questions csv: {VALIDATION_QUESTIONS_CSV}")
    print("")
    print("DECISION:")
    print("- status: JPX_ACQUISITION_PLAN_READY")
    print("- selected_provider: jpx_listed_securities_csv")
    print("- recommended_next_phase: v2.13C - JPX Acquisition Real")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
