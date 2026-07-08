from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.12B"
PHASE = "HKEX Acquisition Plan"
PHASE_TYPE = "plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ROUTE_JSON = OUTPUT_DIR / "next_provider_route_v2_12a.json"

PLAN_JSON = OUTPUT_DIR / "hkex_acquisition_plan_v2_12b.json"
PLAN_MD = OUTPUT_DIR / "hkex_acquisition_plan_v2_12b.md"
CONTRACT_CSV = OUTPUT_DIR / "hkex_acquisition_contract_v2_12b.csv"
PLANNED_OUTPUTS_CSV = OUTPUT_DIR / "hkex_planned_outputs_v2_12b.csv"
VALIDATION_QUESTIONS_CSV = OUTPUT_DIR / "hkex_validation_questions_v2_12b.csv"

CURRENT_EXPANDED_ROWS = 30354
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_FULL_SOURCE = 19646

GLOBAL_COMPLETED = 94
GLOBAL_PENDING = 6
EXPANDED_SOURCE_COMPLETED = 88
EXPANDED_SOURCE_PENDING = 12


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
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.12B outputs:\n"
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
            "route_type": "official_direct_file",
            "target": "hkex_list_of_securities_xlsx_en",
            "url_or_discovery_rule": "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx",
            "expected_format": "xlsx",
            "purpose": "Acquire official HKEX List of Securities file as raw bytes.",
            "allowed_in_v2_12c": "HTTP GET raw XLSX, preserve exact bytes, compute SHA256, record metadata.",
            "prohibited_in_v2_12c": "No parsing decision, no normalization, no net-new filtering, no rebuild, no scoring.",
            "raw_preservation_policy": "Save raw XLSX exactly as received under raw/hkex_v2_12c/.",
            "validation_owner": "v2.12D",
        },
        {
            "step_id": "02",
            "route_type": "official_landing_page",
            "target": "hkex_securities_lists_page",
            "url_or_discovery_rule": "https://www.hkex.com.hk/Services/Trading/Securities/Securities-Lists?sc_lang=en",
            "expected_format": "html",
            "purpose": "Acquire official Securities Lists page for provenance and fallback link discovery.",
            "allowed_in_v2_12c": "HTTP GET raw HTML, preserve exact bytes, compute SHA256, record metadata and discovered candidate links.",
            "prohibited_in_v2_12c": "No brittle scraping, no table parsing for accepted rows, no rebuild.",
            "raw_preservation_policy": "Save raw HTML exactly as received under raw/hkex_v2_12c/.",
            "validation_owner": "v2.12D",
        },
        {
            "step_id": "03",
            "route_type": "optional_official_fallback_file",
            "target": "hkex_list_of_securities_xlsx_zh",
            "url_or_discovery_rule": "https://www.hkex.com.hk/chi/services/trading/securities/securitieslists/ListOfSecurities_c.xlsx",
            "expected_format": "xlsx",
            "purpose": "Optional fallback/provenance file if English XLSX acquisition fails or schema comparison is needed.",
            "allowed_in_v2_12c": "Download only if explicit fallback branch is triggered by acquisition script; preserve raw bytes.",
            "prohibited_in_v2_12c": "No mixing English/Chinese rows into accepted source during acquisition.",
            "raw_preservation_policy": "Save as separate fallback raw file and mark fallback status in manifest.",
            "validation_owner": "v2.12D",
        },
        {
            "step_id": "04",
            "route_type": "semantic_caution",
            "target": "hkex_security_category_and_stock_code_semantics",
            "url_or_discovery_rule": "Derived from official XLSX only; do not assume every row is ordinary equity.",
            "expected_format": "validation_rule",
            "purpose": "Prevent incorrect inclusion of ETFs, REITs, warrants, debt, derivatives, structured products or non-equity instruments.",
            "allowed_in_v2_12c": "Record source fields exactly and preserve raw workbook.",
            "prohibited_in_v2_12c": "No accepted filtering, no equity classification decision, no rebuild.",
            "raw_preservation_policy": "Do not mutate source fields.",
            "validation_owner": "v2.12D",
        },
        {
            "step_id": "05",
            "route_type": "identifier_caution",
            "target": "hkex_stock_code_format",
            "url_or_discovery_rule": "Preserve stock codes exactly as text, including leading zeros.",
            "expected_format": "validation_rule",
            "purpose": "Avoid losing leading zeros and avoid ticker-key collisions.",
            "allowed_in_v2_12c": "Store metadata and raw workbook only.",
            "prohibited_in_v2_12c": "No conversion of stock_code to integer.",
            "raw_preservation_policy": "Raw workbook is source of truth.",
            "validation_owner": "v2.12D",
        },
    ]

    planned_outputs = [
        {
            "phase": "v2.12C",
            "path": "scripts/hkex_acquisition_v2_12c.py",
            "type": "script",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.12C",
            "path": "outputs/full_universe_source_acquisition/raw/hkex_v2_12c/",
            "type": "raw_directory",
            "required": "yes",
            "overwrite_policy": "new_directory_or_fail",
        },
        {
            "phase": "v2.12C",
            "path": "outputs/full_universe_source_acquisition/hkex_download_manifest_v2_12c.json",
            "type": "manifest_json",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.12C",
            "path": "outputs/full_universe_source_acquisition/hkex_download_manifest_v2_12c.csv",
            "type": "manifest_csv",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.12C",
            "path": "outputs/full_universe_source_acquisition/hkex_discovered_links_v2_12c.csv",
            "type": "discovery_manifest",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.12C",
            "path": "outputs/full_universe_source_acquisition/hkex_acquisition_report_v2_12c.md",
            "type": "report",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
    ]

    validation_questions = [
        {
            "question_id": "Q01",
            "question": "Does HKEX ListOfSecurities.xlsx remain directly downloadable?",
            "validation_phase": "v2.12D",
        },
        {
            "question_id": "Q02",
            "question": "Which workbook sheet contains the actual securities table?",
            "validation_phase": "v2.12D",
        },
        {
            "question_id": "Q03",
            "question": "Does the workbook contain stock code, name of securities, category, sub-category, board lot, currency and ISIN?",
            "validation_phase": "v2.12D",
        },
        {
            "question_id": "Q04",
            "question": "How many rows exist before filtering?",
            "validation_phase": "v2.12D",
        },
        {
            "question_id": "Q05",
            "question": "How many rows are ordinary equities versus ETFs, REITs, warrants, debt, derivatives or other instruments?",
            "validation_phase": "v2.12D",
        },
        {
            "question_id": "Q06",
            "question": "How many candidate identifiers are net-new against expanded_universe_v2_11e?",
            "validation_phase": "v2.12D",
        },
        {
            "question_id": "Q07",
            "question": "Can HKEX rows be normalized conservatively without brittle scraping?",
            "validation_phase": "v2.12D",
        },
        {
            "question_id": "Q08",
            "question": "Does HKEX materially reduce the 19,646-row gap to 50k?",
            "validation_phase": "v2.12D",
        },
        {
            "question_id": "Q09",
            "question": "Should HKEX be source provider, candidate provider, enrichment, reference-only or deferred?",
            "validation_phase": "v2.12D",
        },
    ]

    plan = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "HKEX_ACQUISITION_PLAN_READY",
        "decision": "PROCEED_TO_V2_12C_HKEX_ACQUISITION_ONLY_AFTER_V2_12B_VALIDATION_AND_COMMIT",
        "selected_provider": "hkex_securities_list",
        "generated_at_utc": utc_now(),
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
            "first_expansion_unlocked": True,
            "full_source_unlocked": False,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
            "v2_12a_route_decision": route.get("route_decision", "HKEX_SELECTED_AS_NEXT_PROVIDER_ROUTE"),
            "v2_12a_commit": "9856571",
        },
        "hard_guards": hard_guards,
        "acquisition_contract_for_v2_12c": acquisition_contract,
        "planned_outputs_for_v2_12c": planned_outputs,
        "validation_questions_for_v2_12d": validation_questions,
        "project_percentages": {
            "v2_12b_hkex_acquisition_plan_completed_after_commit": 100,
            "v2_12b_hkex_acquisition_plan_pending_after_commit": 0,
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
            "allowed_in_v2_12c",
            "prohibited_in_v2_12c",
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

    md = f"""# {VERSION} — {PHASE}

Status: **HKEX_ACQUISITION_PLAN_READY**

Phase type: **plan-only**

Selected provider: **hkex_securities_list**

Decision: **PROCEED_TO_V2_12C_HKEX_ACQUISITION_ONLY_AFTER_V2_12B_VALIDATION_AND_COMMIT**

Generated at UTC: `{plan["generated_at_utc"]}`

## Confirmed previous phase

- v2.12A route decision: `{plan["current_state"]["v2_12a_route_decision"]}`
- v2.12A commit: `9856571`
- Selected route: `hkex_securities_list`

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

## v2.12C controlled acquisition contract

v2.12C must be **acquisition-only**.

Allowed:

- Download official HKEX List of Securities XLSX as raw bytes.
- Download official HKEX Securities Lists page as raw HTML for provenance/discovery.
- Download Chinese XLSX only as fallback/provenance if the acquisition branch requires it.
- Record URL, status code, content type, byte size, SHA256 and fetch timestamp.
- Preserve raw files exactly as received.

Forbidden:

- No parsing decision.
- No accepted filtering.
- No normalization.
- No net-new filtering.
- No rebuild.
- No scoring.
- No OpenAI calls.
- No broker/API trading calls.
- No full 59k launch.
- No overwrite of active outputs.
- No conversion of HKEX stock codes to integer.

## Contract rows

{contract_lines}

## Validation questions for v2.12D

{validation_question_lines}

## Planned v2.12C outputs

{planned_output_lines}

## Important caution

HKEX stock codes must be preserved as text because leading zeros are significant.

HKEX security categories must not be accepted blindly. ETFs, REITs, warrants, debt instruments, derivatives and structured products need conservative review in v2.12D.

## Project percentages

- v2.12B HKEX Acquisition Plan: 100% completed / 0% pending after commit
- Fuente real expandida: {EXPANDED_SOURCE_COMPLETED}% completed / {EXPANDED_SOURCE_PENDING}% pending
- Fuente real completa 50k–59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: {GLOBAL_COMPLETED}% completed / {GLOBAL_PENDING}% pending

## Recommended next phase

**v2.12C — HKEX Acquisition Real**

Only after v2.12B outputs are validated, committed and pushed.
"""

    PLAN_MD.write_text(md, encoding="utf-8")

    print("v2.12B HKEX acquisition plan-only completed.")
    print(f"- plan json: {PLAN_JSON}")
    print(f"- plan report: {PLAN_MD}")
    print(f"- contract csv: {CONTRACT_CSV}")
    print(f"- planned outputs csv: {PLANNED_OUTPUTS_CSV}")
    print(f"- validation questions csv: {VALIDATION_QUESTIONS_CSV}")
    print("")
    print("DECISION:")
    print("- status: HKEX_ACQUISITION_PLAN_READY")
    print("- selected_provider: hkex_securities_list")
    print("- recommended_next_phase: v2.12C — HKEX Acquisition Real")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
