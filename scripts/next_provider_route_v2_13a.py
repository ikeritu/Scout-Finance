from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.13A"
PHASE = "Next Provider Route For Full Source 50k"
PHASE_TYPE = "route-selection-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

HKEX_CLOSURE_JSON = OUTPUT_DIR / "hkex_closure_report_v2_12g.json"

ROUTE_JSON = OUTPUT_DIR / "next_provider_route_v2_13a.json"
ROUTE_MD = OUTPUT_DIR / "next_provider_route_v2_13a.md"
ROUTE_CANDIDATES_CSV = OUTPUT_DIR / "next_provider_route_candidates_v2_13a.csv"
PLANNED_OUTPUTS_CSV = OUTPUT_DIR / "next_provider_planned_outputs_v2_13a.csv"

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
        ROUTE_JSON,
        ROUTE_MD,
        ROUTE_CANDIDATES_CSV,
        PLANNED_OUTPUTS_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.13A outputs:\n"
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

    hkex_closure = read_json(HKEX_CLOSURE_JSON)

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
            "provider": "jpx_listed_securities_csv",
            "route_status": "SELECTED_AS_NEXT_PROVIDER_ROUTE",
            "readiness_score": 94,
            "provider_type": "official_exchange_csv_or_data_portal_download",
            "primary_url": "https://www.jpx.co.jp/english/markets/data-catalog/index.html",
            "fallback_url": "https://www.jpx.co.jp/english/listing/co-search/index.html",
            "expected_format": "csv",
            "expected_schema_candidates": "code,company_name,market_segment,industry,listing_date,isin_possible",
            "expected_row_range": "3500-5000",
            "expected_overlap_risk": "low_geographic_overlap_after_hkex_and_cboe_europe",
            "strengths": "Official JPX route, likely low overlap with existing Europe/HKEX/Nasdaq/SEC/Cboe sources, useful clean geographic expansion.",
            "risks": "Actual CSV endpoint may require discovery from data portal; market-segment filtering needed before rebuild.",
            "planned_phase_b": "v2.13B_JPX_ACQUISITION_PLAN",
            "route_decision_reason": "Best next route because it is official, geographically complementary and likely lower-overlap than Xetra/Euronext after Cboe Europe.",
        },
        {
            "rank": 2,
            "provider": "deutsche_boerse_xetra_all_tradable_instruments",
            "route_status": "BACKUP_ROUTE_READY_HIGH_ROW_POTENTIAL",
            "readiness_score": 90,
            "provider_type": "official_exchange_download_or_directory",
            "primary_url": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra/Downloads",
            "fallback_url": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra",
            "expected_format": "csv_or_download_link",
            "expected_schema_candidates": "name,isin,wkn,symbol,instrument_type,currency",
            "expected_row_range": "5000-15000",
            "expected_overlap_risk": "medium_high_due_to_existing_cboe_europe_reference_data",
            "strengths": "Official Deutsche Börse route with high instrument count and clear fields such as ISIN, symbol, instrument type and currency.",
            "risks": "Likely heavy overlap with Cboe Europe; includes ETFs/ETNs and other instruments needing conservative filtering.",
            "planned_phase_b": "v2.13B_XETRA_ACQUISITION_PLAN_IF_JPX_BLOCKED_OR_AFTER_JPX",
            "route_decision_reason": "Strong backup if JPX acquisition is blocked or insufficient.",
        },
        {
            "rank": 3,
            "provider": "asx_listed_companies",
            "route_status": "BACKUP_ROUTE_READY_LOW_COMPLEXITY",
            "readiness_score": 88,
            "provider_type": "official_exchange_csv",
            "primary_url": "https://www.asx.com.au/asx/research/ASXListedCompanies.csv",
            "fallback_url": "https://www.asx.com.au/markets/trade-our-cash-market/directory",
            "expected_format": "csv",
            "expected_schema_candidates": "company_name,asx_code,gics_industry_group",
            "expected_row_range": "1500-2500",
            "expected_overlap_risk": "low",
            "strengths": "Official direct CSV route and low acquisition complexity.",
            "risks": "Likely too small alone for the remaining 16,842-row gap and may lack ISIN.",
            "planned_phase_b": "v2.13B_ASX_ACQUISITION_PLAN_IF_JPX_BLOCKED_OR_AS_ADDON",
            "route_decision_reason": "Excellent backup/add-on route but smaller than JPX.",
        },
        {
            "rank": 4,
            "provider": "tsx_tmx_listed_company_directory",
            "route_status": "BACKUP_ROUTE_READY",
            "readiness_score": 84,
            "provider_type": "official_exchange_directory",
            "primary_url": "https://www.tsx.com/en/listings/listing-with-us/listed-company-directory",
            "fallback_url": "https://www.tsx.com/en/listings",
            "expected_format": "html_or_download_link",
            "expected_schema_candidates": "company_name,symbol,exchange,issuer_status",
            "expected_row_range": "3000-5000",
            "expected_overlap_risk": "low_medium",
            "strengths": "Official TSX/TSXV issuer directory with useful Canadian coverage.",
            "risks": "Download/export route may require discovery; must separate TSX and TSXV carefully.",
            "planned_phase_b": "v2.13B_TMX_ROUTE_IF_JPX_OR_ASX_NOT_ENOUGH",
            "route_decision_reason": "Good candidate but less direct than JPX/ASX.",
        },
        {
            "rank": 5,
            "provider": "euronext_equities_live_directory",
            "route_status": "DEFERRED_ROUTE_CANDIDATE",
            "readiness_score": 80,
            "provider_type": "official_exchange_directory_or_endpoint",
            "primary_url": "https://live.euronext.com/en/products/equities/list",
            "fallback_url": "https://www.euronext.com/en/data",
            "expected_format": "html_or_discovered_endpoint",
            "expected_schema_candidates": "name,symbol,isin,market,currency",
            "expected_row_range": "1500-8000",
            "expected_overlap_risk": "high_due_to_existing_cboe_europe_reference_data",
            "strengths": "Official Euronext equity route with broad European market coverage.",
            "risks": "Likely overlap with Cboe Europe; endpoint/pagination discovery may be required.",
            "planned_phase_b": "v2.13B_EURONEXT_ROUTE_IF_LOW_OVERLAP_STRATEGY_DEFINED",
            "route_decision_reason": "Deferred because Cboe Europe already covers much of Europe.",
        },
    ]

    selected = route_candidates[0]

    planned_outputs = [
        {
            "phase": "v2.13B",
            "path": "scripts/jpx_acquisition_plan_v2_13b.py",
            "type": "script",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.13B",
            "path": "outputs/full_universe_source_acquisition/jpx_acquisition_plan_v2_13b.json",
            "type": "plan_json",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.13B",
            "path": "outputs/full_universe_source_acquisition/jpx_acquisition_plan_v2_13b.md",
            "type": "plan_report",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.13B",
            "path": "outputs/full_universe_source_acquisition/jpx_acquisition_contract_v2_13b.csv",
            "type": "contract",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.13B",
            "path": "outputs/full_universe_source_acquisition/jpx_planned_outputs_v2_13b.csv",
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
        "route_decision": "JPX_SELECTED_AS_NEXT_PROVIDER_ROUTE",
        "selected_provider": selected["provider"],
        "selected_provider_readiness_score": selected["readiness_score"],
        "recommended_next_phase": "v2.13B - JPX Acquisition Plan",
        "generated_at_utc": utc_now(),
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
            "first_expansion_unlocked": True,
            "full_source_unlocked": False,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
            "previous_hkex_closure_status": hkex_closure.get("closure_status", "HKEX_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED"),
            "previous_commit": "c904c10",
        },
        "hard_guards": hard_guards,
        "route_candidates": route_candidates,
        "planned_outputs_for_v2_13b": planned_outputs,
        "validation_questions_for_v2_13": [
            "Does JPX expose a directly downloadable listed securities CSV through the official data portal?",
            "Does the file contain code, company name, market segment and security/instrument classification?",
            "How many rows exist before filtering?",
            "How many rows are ordinary listed companies versus ETFs, REITs, preferred shares, funds or other instruments?",
            "How many candidate identifiers are net-new against expanded_universe_v2_12e?",
            "Can JPX rows be normalized conservatively without brittle scraping?",
            "Does JPX materially reduce the 16,842-row gap to 50k?",
            "Should JPX be source provider, candidate provider, enrichment, reference-only or deferred?",
        ],
        "project_percentages": {
            "v2_13a_route_completed_after_commit": 100,
            "v2_13a_route_pending_after_commit": 0,
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
            "expected_overlap_risk",
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
        f"{row['rank']}. **{row['provider']}** — {row['route_status']} — readiness {row['readiness_score']}/100 — expected rows {row['expected_row_range']} — overlap risk {row['expected_overlap_risk']} — {row['route_decision_reason']}"
        for row in route_candidates
    )

    md = f"""# {VERSION} - {PHASE}

Status: **NEXT_PROVIDER_ROUTE_READY**

Phase type: **route-selection-only**

Route decision: **JPX_SELECTED_AS_NEXT_PROVIDER_ROUTE**

Selected provider: **{selected["provider"]}**

Readiness score: **{selected["readiness_score"]}/100**

Recommended next phase: **v2.13B - JPX Acquisition Plan**

Generated at UTC: `{route_payload["generated_at_utc"]}`

## Current state

- Current expanded rows: {CURRENT_EXPANDED_ROWS}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Rows needed for full source: {ROWS_NEEDED_FULL_SOURCE}
- First expansion unlocked: true
- Full source unlocked: false
- Full 59k status: blocked until source >=50k and gate explicitly approved
- Previous HKEX closure commit: `c904c10`

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

JPX is selected because it is an official exchange route, geographically complementary to the current source mix, and likely lower-overlap than Xetra or Euronext after the Cboe Europe expansion.

Xetra remains the strongest high-row backup route, but it carries higher overlap risk with Cboe Europe and includes many non-share instruments that require strict filtering.

ASX is the best low-complexity backup/add-on route, but likely too small alone to close the remaining 16,842-row gap.

## v2.13B contract preview

v2.13B must be **plan-only**.

Allowed:

- Define a controlled JPX acquisition plan.
- Define raw preservation rules for v2.13C.
- Define expected outputs for JPX CSV / data portal acquisition.
- Define validation questions for v2.13D.

Forbidden:

- No download.
- No rebuild.
- No scoring.
- No OpenAI.
- No broker/API trading calls.
- No full 59k launch.
- No overwrite of active outputs.

## v2.13 validation questions

{chr(10).join(f"- {question}" for question in route_payload["validation_questions_for_v2_13"])}

## Planned v2.13B outputs

{chr(10).join(f"- `{row['path']}`" for row in planned_outputs)}

## Project percentages

- v2.13A route: 100% completed / 0% pending after commit
- Fuente real expandida: {EXPANDED_SOURCE_COMPLETED}% completed / {EXPANDED_SOURCE_PENDING}% pending
- Fuente real completa 50k-59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: {GLOBAL_COMPLETED}% completed / {GLOBAL_PENDING}% pending
"""

    ROUTE_MD.write_text(md, encoding="utf-8")

    print("v2.13A route-selection-only completed.")
    print(f"- route json: {ROUTE_JSON}")
    print(f"- route report: {ROUTE_MD}")
    print(f"- candidates csv: {ROUTE_CANDIDATES_CSV}")
    print(f"- planned outputs csv: {PLANNED_OUTPUTS_CSV}")
    print("")
    print("DECISION:")
    print("- route_status: NEXT_PROVIDER_ROUTE_READY")
    print("- route_decision: JPX_SELECTED_AS_NEXT_PROVIDER_ROUTE")
    print("- selected_provider: jpx_listed_securities_csv")
    print("- recommended_next_phase: v2.13B - JPX Acquisition Plan")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
