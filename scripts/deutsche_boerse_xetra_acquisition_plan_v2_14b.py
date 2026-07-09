from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.14B"
PHASE = "Deutsche Börse Xetra Acquisition Plan"
PHASE_TYPE = "plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

PLAN_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_acquisition_plan_v2_14b.json"
PLAN_MD = OUTPUT_DIR / "deutsche_boerse_xetra_acquisition_plan_v2_14b.md"
CONTRACT_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_acquisition_contract_v2_14b.csv"
PLANNED_OUTPUTS_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_planned_outputs_v2_14b.csv"
VALIDATION_QUESTIONS_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_validation_questions_v2_14b.csv"

CURRENT_EXPANDED_ROWS = 36863
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_FULL_SOURCE = 13137
GLOBAL_COMPLETED = 41
GLOBAL_PENDING = 59
SOURCE_TO_50K_COMPLETED = round((CURRENT_EXPANDED_ROWS / FULL_SOURCE_THRESHOLD) * 100, 1)
SOURCE_TO_50K_PENDING = round(100 - SOURCE_TO_50K_COMPLETED, 1)


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
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.14B outputs:\n"
            + "\n".join(existing)
        )


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

    hard_guards = {
        "phase_type": PHASE_TYPE,
        "network_download_performed": False,
        "raw_files_downloaded": False,
        "raw_files_modified": False,
        "workbook_or_csv_parsed": False,
        "normalization_performed": False,
        "net_new_filtering_performed": False,
        "expanded_universe_rebuilt": False,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
    }

    acquisition_contract = [
        {
            "step_id": "01",
            "route_type": "official_primary_downloads_page",
            "target": "deutsche_boerse_xetra_downloads_page",
            "url_or_discovery_rule": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra/Downloads",
            "expected_format": "html",
            "purpose": "Acquire official Xetra downloads page and discover T7 XETR all tradable instruments links.",
            "allowed_in_v2_14c": "HTTP GET raw HTML only, preserve bytes, compute SHA256, record links.",
            "prohibited_in_v2_14c": "No parsing acceptance, no normalization, no net-new filtering, no rebuild, no scoring.",
            "raw_preservation_policy": "Save raw HTML exactly as received under raw/deutsche_boerse_xetra_v2_14c/.",
            "validation_owner": "v2.14D",
        },
        {
            "step_id": "02",
            "route_type": "official_primary_all_tradable_instruments_page",
            "target": "deutsche_boerse_xetra_all_tradable_instruments_page",
            "url_or_discovery_rule": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra",
            "expected_format": "html",
            "purpose": "Acquire official all tradable instruments page for provenance and discovery.",
            "allowed_in_v2_14c": "HTTP GET raw HTML only, preserve bytes, compute SHA256, record candidate links.",
            "prohibited_in_v2_14c": "No accepted filtering, no row normalization, no rebuild.",
            "raw_preservation_policy": "Save raw HTML exactly as received under raw/deutsche_boerse_xetra_v2_14c/.",
            "validation_owner": "v2.14D",
        },
        {
            "step_id": "03",
            "route_type": "official_dataset_download_candidate",
            "target": "t7_xetr_all_tradable_instruments",
            "url_or_discovery_rule": "Discover only from official Deutsche Börse Xetra pages. Expected label: T7 (XETR) All tradable instruments.",
            "expected_format": "csv_or_download_file",
            "purpose": "Acquire official XETR all tradable instruments file as raw bytes if a direct official link is discovered.",
            "allowed_in_v2_14c": "Download only official direct file links discovered from official pages; preserve exact bytes and hashes.",
            "prohibited_in_v2_14c": "No parsing acceptance, no instrument type decisions, no rebuild.",
            "raw_preservation_policy": "Save raw file exactly as received under raw/deutsche_boerse_xetra_v2_14c/datasets/.",
            "validation_owner": "v2.14D",
        },
        {
            "step_id": "04",
            "route_type": "official_shares_reference_page",
            "target": "deutsche_boerse_xetra_list_of_tradable_shares_page",
            "url_or_discovery_rule": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Equities/list-of-tradable-shares",
            "expected_format": "html_or_dynamic_table",
            "purpose": "Acquire official shares reference page as shares-only fallback/provenance source.",
            "allowed_in_v2_14c": "HTTP GET raw HTML only; no dynamic scraping unless explicitly approved later.",
            "prohibited_in_v2_14c": "No fragile UI scraping, no accepted row extraction, no rebuild.",
            "raw_preservation_policy": "Save raw HTML exactly as received under raw/deutsche_boerse_xetra_v2_14c/.",
            "validation_owner": "v2.14D",
        },
        {
            "step_id": "05",
            "route_type": "semantic_caution",
            "target": "xetra_instrument_type_semantics",
            "url_or_discovery_rule": "Derived only during v2.14D from official source fields.",
            "expected_format": "validation_rule",
            "purpose": "Prevent inclusion of ETFs, ETCs, ETNs, active ETFs, funds, bonds, certificates and other non-common-equity instruments.",
            "allowed_in_v2_14c": "Record raw files and metadata only.",
            "prohibited_in_v2_14c": "No shares/equity acceptance decision during acquisition.",
            "raw_preservation_policy": "Do not mutate source fields.",
            "validation_owner": "v2.14D",
        },
        {
            "step_id": "06",
            "route_type": "overlap_caution",
            "target": "cboe_europe_overlap_risk",
            "url_or_discovery_rule": "Compare only during v2.14D against expanded_universe_v2_13e.",
            "expected_format": "validation_rule",
            "purpose": "Xetra likely overlaps with Cboe Europe and must be baseline-compared before rebuild.",
            "allowed_in_v2_14c": "No baseline compare during acquisition.",
            "prohibited_in_v2_14c": "No net-new filtering in acquisition phase.",
            "raw_preservation_policy": "Raw official files remain source of truth.",
            "validation_owner": "v2.14D",
        },
    ]

    planned_outputs = [
        {
            "phase": "v2.14C",
            "path": "scripts/deutsche_boerse_xetra_acquisition_v2_14c.py",
            "type": "script",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.14C",
            "path": "outputs/full_universe_source_acquisition/raw/deutsche_boerse_xetra_v2_14c/",
            "type": "raw_directory",
            "required": "yes",
            "overwrite_policy": "new_directory_or_fail",
        },
        {
            "phase": "v2.14C",
            "path": "outputs/full_universe_source_acquisition/deutsche_boerse_xetra_download_manifest_v2_14c.json",
            "type": "manifest_json",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.14C",
            "path": "outputs/full_universe_source_acquisition/deutsche_boerse_xetra_download_manifest_v2_14c.csv",
            "type": "manifest_csv",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.14C",
            "path": "outputs/full_universe_source_acquisition/deutsche_boerse_xetra_discovered_links_v2_14c.csv",
            "type": "discovery_manifest",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.14C",
            "path": "outputs/full_universe_source_acquisition/deutsche_boerse_xetra_acquisition_report_v2_14c.md",
            "type": "report",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
    ]

    validation_questions = [
        {"question_id": "Q01", "question": "Does the official Xetra downloads page expose a direct T7 XETR all tradable instruments file?", "validation_phase": "v2.14D"},
        {"question_id": "Q02", "question": "Is the downloaded file CSV, ZIP, XLSX or another structured format?", "validation_phase": "v2.14D"},
        {"question_id": "Q03", "question": "Which fields provide ISIN, WKN, mnemonic/symbol, name, currency, market and instrument type?", "validation_phase": "v2.14D"},
        {"question_id": "Q04", "question": "How many gross instruments are present before filtering?", "validation_phase": "v2.14D"},
        {"question_id": "Q05", "question": "How many are shares/equities versus ETFs, ETCs, ETNs, active ETFs, funds, bonds, certificates or other instruments?", "validation_phase": "v2.14D"},
        {"question_id": "Q06", "question": "How many share/equity candidates are net-new against expanded_universe_v2_13e?", "validation_phase": "v2.14D"},
        {"question_id": "Q07", "question": "How much overlap exists with existing Cboe Europe reference data?", "validation_phase": "v2.14D"},
        {"question_id": "Q08", "question": "Can the provider be normalized conservatively without brittle scraping?", "validation_phase": "v2.14D"},
        {"question_id": "Q09", "question": "Does Xetra materially reduce the remaining 13,137-row gap to 50k?", "validation_phase": "v2.14D"},
        {"question_id": "Q10", "question": "Should Xetra be source provider, candidate provider, enrichment/reference-only or fallback/deferred?", "validation_phase": "v2.14D"},
    ]

    plan = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "DEUTSCHE_BOERSE_XETRA_ACQUISITION_PLAN_READY",
        "decision": "PROCEED_TO_V2_14C_XETRA_ACQUISITION_ONLY_AFTER_V2_14B_VALIDATION_AND_COMMIT",
        "selected_provider": "deutsche_boerse_xetra_all_tradable_instruments",
        "generated_at_utc": utc_now(),
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED,
            "source_to_50k_pending_percent": SOURCE_TO_50K_PENDING,
            "full_source_unlocked": False,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
            "v2_14a_commit": "64cef21",
        },
        "hard_guards": hard_guards,
        "acquisition_contract_for_v2_14c": acquisition_contract,
        "planned_outputs_for_v2_14c": planned_outputs,
        "validation_questions_for_v2_14d": validation_questions,
        "project_percentages": {
            "global_completed": GLOBAL_COMPLETED,
            "global_pending": GLOBAL_PENDING,
            "source_to_50k_completed": SOURCE_TO_50K_COMPLETED,
            "source_to_50k_pending": SOURCE_TO_50K_PENDING,
            "full_source_gate_completed": 0,
            "full_source_gate_pending": 100,
            "full_59k_dry_run_completed": 0,
            "full_59k_dry_run_pending": 100,
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
            "allowed_in_v2_14c",
            "prohibited_in_v2_14c",
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

    PLAN_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **DEUTSCHE_BOERSE_XETRA_ACQUISITION_PLAN_READY**

Phase type: **plan-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Decision: **PROCEED_TO_V2_14C_XETRA_ACQUISITION_ONLY_AFTER_V2_14B_VALIDATION_AND_COMMIT**

## Current state

- Current expanded rows: {CURRENT_EXPANDED_ROWS}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Rows needed for full source: {ROWS_NEEDED_FULL_SOURCE}
- Source-to-50k completion: {SOURCE_TO_50K_COMPLETED}%
- Source-to-50k pending: {SOURCE_TO_50K_PENDING}%
- Full source unlocked: false
- Full 59k status: blocked until source >=50k and explicit gate approved

## Scope

v2.14B is plan-only.

It does not download data, parse workbooks, normalize rows, filter net-new rows, rebuild the universe, score, call OpenAI, call broker APIs or launch full 59k.

## Recommended next phase

**v2.14C - Deutsche Börse Xetra Acquisition Real**
""",
        encoding="utf-8",
    )

    print("v2.14B Deutsche Börse Xetra acquisition plan-only completed.")
    print(f"- plan json: {PLAN_JSON}")
    print(f"- plan report: {PLAN_MD}")
    print(f"- contract csv: {CONTRACT_CSV}")
    print(f"- planned outputs csv: {PLANNED_OUTPUTS_CSV}")
    print(f"- validation questions csv: {VALIDATION_QUESTIONS_CSV}")
    print("")
    print("DECISION:")
    print("- status: DEUTSCHE_BOERSE_XETRA_ACQUISITION_PLAN_READY")
    print("- selected_provider: deutsche_boerse_xetra_all_tradable_instruments")
    print("- recommended_next_phase: v2.14C - Deutsche Börse Xetra Acquisition Real")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
