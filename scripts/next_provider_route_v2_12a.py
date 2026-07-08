from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.12A"
PHASE = "Next Provider Route For Full Source 50k"
PHASE_TYPE = "route-selection-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CBOE_CLOSURE_JSON = OUTPUT_DIR / "cboe_europe_closure_report_v2_11g.json"

ROUTE_JSON = OUTPUT_DIR / "next_provider_route_v2_12a.json"
ROUTE_MD = OUTPUT_DIR / "next_provider_route_v2_12a.md"
ROUTE_CANDIDATES_CSV = OUTPUT_DIR / "next_provider_route_candidates_v2_12a.csv"
PLANNED_OUTPUTS_CSV = OUTPUT_DIR / "next_provider_planned_outputs_v2_12a.csv"

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
        ROUTE_JSON,
        ROUTE_MD,
        ROUTE_CANDIDATES_CSV,
        PLANNED_OUTPUTS_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.12A outputs:\n"
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

    cboe_closure = read_json(CBOE_CLOSURE_JSON)

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

    route_candidates = [
        {
            "rank": 1,
            "provider": "hkex_securities_list",
            "route_status": "SELECTED_AS_NEXT_PROVIDER_ROUTE",
            "readiness_score": 96,
            "provider_type": "official_exchange_file",
            "primary_url": "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx",
            "fallback_url": "https://www.hkex.com.hk/Services/Trading/Securities/Securities-Lists?sc_lang=en",
            "expected_format": "xlsx",
            "expected_schema_candidates": "stock_code,name_of_securities,category,sub_category,isin,board_lot",
            "expected_row_range": "3000-8000",
            "strengths": "Official direct XLSX route, includes security names and ISIN, low scraping risk.",
            "risks": "May include non-common-equity instruments; needs conservative filtering in validation.",
            "planned_phase_b": "v2.12B_HKEX_ACQUISITION_PLAN",
            "route_decision_reason": "Best next route because it is official, direct-file, schema-rich and low brittleness.",
        },
        {
            "rank": 2,
            "provider": "asx_listed_companies",
            "route_status": "BACKUP_ROUTE_READY",
            "readiness_score": 92,
            "provider_type": "official_exchange_csv",
            "primary_url": "https://www.asx.com.au/asx/research/ASXListedCompanies.csv",
            "fallback_url": "https://www.asx.com.au/markets/trade-our-cash-market/directory",
            "expected_format": "csv",
            "expected_schema_candidates": "company_name,asx_code,gics_industry_group",
            "expected_row_range": "1500-2500",
            "strengths": "Official direct CSV route, very low acquisition complexity.",
            "risks": "Likely too small alone for 50k; may lack ISIN.",
            "planned_phase_b": "v2.12B_ASX_ACQUISITION_PLAN_IF_HKEX_BLOCKED_OR_AFTER_HKEX",
            "route_decision_reason": "Excellent low-risk backup and possible add-on provider.",
        },
        {
            "rank": 3,
            "provider": "tsx_tmx_listed_company_directory",
            "route_status": "BACKUP_ROUTE_READY",
            "readiness_score": 86,
            "provider_type": "official_exchange_directory",
            "primary_url": "https://www.tsx.com/en/listings/listing-with-us/listed-company-directory",
            "fallback_url": "https://www.tsx.com/en/listings",
            "expected_format": "html_or_download_link",
            "expected_schema_candidates": "company_name,symbol,exchange,issuer_status",
            "expected_row_range": "3000-5000",
            "strengths": "Official issuer directory; may expose full issuer list download.",
            "risks": "Download link may require discovery; may mix TSX and TSXV.",
            "planned_phase_b": "v2.12B_TMX_ROUTE_IF_HKEX_OR_ASX_NOT_ENOUGH",
            "route_decision_reason": "Useful later route but not the cleanest immediate direct-file target.",
        },
        {
            "rank": 4,
            "provider": "euronext_equities_live_directory",
            "route_status": "DEFERRED_ROUTE_CANDIDATE",
            "readiness_score": 82,
            "provider_type": "official_exchange_directory",
            "primary_url": "https://live.euronext.com/en/products/equities/list",
            "fallback_url": "https://live.euronext.com/en/products/equities",
            "expected_format": "html_or_discovered_endpoint",
            "expected_schema_candidates": "name,symbol,isin,market,currency",
            "expected_row_range": "1500-8000",
            "strengths": "Official Euronext equity directory; potentially useful EU expansion.",
            "risks": "May require pagination or endpoint discovery; avoid brittle scraping.",
            "planned_phase_b": "v2.12B_EURONEXT_ROUTE_IF_DIRECT_ENDPOINT_FOUND",
            "route_decision_reason": "Promising but less direct than HKEX/ASX.",
        },
        {
            "rank": 5,
            "provider": "deutsche_boerse_xetra_tradable_instruments",
            "route_status": "DEFERRED_ROUTE_CANDIDATE",
            "readiness_score": 78,
            "provider_type": "official_exchange_directory_or_downloads",
            "primary_url": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra",
            "fallback_url": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra/Downloads",
            "expected_format": "html_or_downloads",
            "expected_schema_candidates": "instrument,name,isin,currency,market_segment",
            "expected_row_range": "5000-15000",
            "strengths": "Official Xetra tradable instruments route.",
            "risks": "Reference files may require document-guided discovery; avoid brittle parsing.",
            "planned_phase_b": "v2.12B_XETRA_ROUTE_IF_DIRECT_FILE_FOUND",
            "route_decision_reason": "High potential, but direct-file path needs more careful route discovery.",
        },
        {
            "rank": 6,
            "provider": "jpx_listed_company_search",
            "route_status": "DEFERRED_ROUTE_CANDIDATE",
            "readiness_score": 74,
            "provider_type": "official_exchange_search_page",
            "primary_url": "https://www.jpx.co.jp/english/listing/co-search/index.html",
            "fallback_url": "https://www.jpx.co.jp/english/listing/",
            "expected_format": "html_or_search_export",
            "expected_schema_candidates": "code,company_name,market_segment,isin_possible",
            "expected_row_range": "3500-4500",
            "strengths": "Official JPX listed company route.",
            "risks": "Export availability must be confirmed; may require HTML parsing.",
            "planned_phase_b": "v2.12B_JPX_ROUTE_IF_EXPORT_CONFIRMED",
            "route_decision_reason": "Good candidate but not selected first because HKEX has a clearer direct file.",
        },
    ]

    selected = route_candidates[0]

    planned_outputs = [
        {
            "phase": "v2.12B",
            "path": "scripts/hkex_acquisition_plan_v2_12b.py",
            "type": "script",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.12B",
            "path": "outputs/full_universe_source_acquisition/hkex_acquisition_plan_v2_12b.json",
            "type": "plan_json",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.12B",
            "path": "outputs/full_universe_source_acquisition/hkex_acquisition_plan_v2_12b.md",
            "type": "plan_report",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.12B",
            "path": "outputs/full_universe_source_acquisition/hkex_acquisition_contract_v2_12b.csv",
            "type": "contract",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.12B",
            "path": "outputs/full_universe_source_acquisition/hkex_planned_outputs_v2_12b.csv",
            "type": "planned_outputs",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
    ]

    route_payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "NEXT_PROVIDER_ROUTE_READY",
        "route_decision": "HKEX_SELECTED_AS_NEXT_PROVIDER_ROUTE",
        "selected_provider": selected["provider"],
        "selected_provider_readiness_score": selected["readiness_score"],
        "recommended_next_phase": "v2.12B — HKEX Acquisition Plan",
        "generated_at_utc": utc_now(),
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
            "first_expansion_unlocked": True,
            "full_source_unlocked": False,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
            "previous_closure_status": cboe_closure.get("status", "CBOE_EUROPE_CLOSED_FIRST_EXPANSION_UNLOCKED_FULL_SOURCE_BLOCKED"),
            "previous_commit": "4aa1928",
        },
        "hard_guards": hard_guards,
        "route_candidates": route_candidates,
        "planned_outputs_for_v2_12b": planned_outputs,
        "validation_questions_for_v2_12": [
            "Does HKEX ListOfSecurities.xlsx remain directly downloadable?",
            "Does it contain securities name, stock code, category and ISIN?",
            "How many rows exist before filtering?",
            "How many rows are ordinary equities versus ETFs, REITs, warrants, derivatives or other instruments?",
            "How many candidate symbols are net-new against expanded_universe_v2_11e?",
            "Can HKEX rows be normalized conservatively without brittle scraping?",
            "Does HKEX materially reduce the 19,646-row gap to 50k?",
            "Should HKEX be source provider, candidate provider, enrichment, reference-only or deferred?",
        ],
        "project_percentages": {
            "v2_12a_route_completed_after_commit": 100,
            "v2_12a_route_pending_after_commit": 0,
            "expanded_real_source_completed": EXPANDED_SOURCE_COMPLETED,
            "expanded_real_source_pending": EXPANDED_SOURCE_PENDING,
            "full_source_50k_59k_completed": 0,
            "full_source_50k_59k_pending": 100,
            "global_completed": GLOBAL_COMPLETED,
            "global_pending": GLOBAL_PENDING,
        },
    }

    write_json(ROUTE_JSON, route_payload)

    write_csv(
        ROUTE_CANDIDATES_CSV,
        route_candidates,
        [
            "rank",
            "provider",
            "route_status",
            "readiness_score",
            "provider_type",
            "primary_url",
            "fallback_url",
            "expected_format",
            "expected_schema_candidates",
            "expected_row_range",
            "strengths",
            "risks",
            "planned_phase_b",
            "route_decision_reason",
        ],
    )

    write_csv(
        PLANNED_OUTPUTS_CSV,
        planned_outputs,
        ["phase", "path", "type", "required", "overwrite_policy"],
    )

    candidates_md = "\n".join(
        f"{row['rank']}. **{row['provider']}** — {row['route_status']} — readiness {row['readiness_score']}/100 — {row['route_decision_reason']}"
        for row in route_candidates
    )

    md = f"""# {VERSION} — {PHASE}

Status: **NEXT_PROVIDER_ROUTE_READY**

Phase type: **route-selection-only**

Route decision: **HKEX_SELECTED_AS_NEXT_PROVIDER_ROUTE**

Selected provider: **{selected["provider"]}**

Readiness score: **{selected["readiness_score"]}/100**

Recommended next phase: **v2.12B — HKEX Acquisition Plan**

Generated at UTC: `{route_payload["generated_at_utc"]}`

## Current state

- Current expanded rows: {CURRENT_EXPANDED_ROWS}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Rows needed for full source: {ROWS_NEEDED_FULL_SOURCE}
- First expansion unlocked: true
- Full source unlocked: false
- Full 59k status: blocked until source >=50k and gate explicitly approved
- Previous closure commit: `4aa1928`

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

## Route candidates

{candidates_md}

## Selected route rationale

HKEX is selected because it exposes a clear official securities list route with a direct XLSX file candidate, expected security names and ISIN coverage, and low acquisition brittleness.

ASX is the best backup route because it exposes a direct official CSV, but its expected row contribution is probably too small to materially close the 19,646-row gap by itself.

Euronext, Xetra, JPX and TMX remain valid follow-up route candidates, but require more careful discovery or are less likely to close the full gap alone.

## v2.12B contract preview

v2.12B must be **plan-only**.

Allowed:

- Define a controlled HKEX acquisition plan.
- Define raw preservation rules for v2.12C.
- Define expected outputs for XLSX acquisition.
- Define validation questions for v2.12D.

Forbidden:

- No download.
- No rebuild.
- No scoring.
- No OpenAI.
- No broker/API trading calls.
- No full 59k launch.
- No overwrite of active outputs.

## v2.12 validation questions

{chr(10).join(f"- {question}" for question in route_payload["validation_questions_for_v2_12"])}

## Planned v2.12B outputs

{chr(10).join(f"- `{row['path']}`" for row in planned_outputs)}

## Project percentages

- v2.12A route: 100% completed / 0% pending after commit
- Fuente real expandida: {EXPANDED_SOURCE_COMPLETED}% completed / {EXPANDED_SOURCE_PENDING}% pending
- Fuente real completa 50k–59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: {GLOBAL_COMPLETED}% completed / {GLOBAL_PENDING}% pending
"""

    ROUTE_MD.write_text(md, encoding="utf-8")

    print("v2.12A route-selection-only completed.")
    print(f"- route json: {ROUTE_JSON}")
    print(f"- route report: {ROUTE_MD}")
    print(f"- candidates csv: {ROUTE_CANDIDATES_CSV}")
    print(f"- planned outputs csv: {PLANNED_OUTPUTS_CSV}")
    print("")
    print("DECISION:")
    print("- route_status: NEXT_PROVIDER_ROUTE_READY")
    print("- route_decision: HKEX_SELECTED_AS_NEXT_PROVIDER_ROUTE")
    print("- selected_provider: hkex_securities_list")
    print("- recommended_next_phase: v2.12B — HKEX Acquisition Plan")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
