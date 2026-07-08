from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.14A"
PHASE = "Next Provider Route For Remaining Full Source Gap"
PHASE_TYPE = "route-selection-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

PREVIOUS_CLOSURE_JSON = OUTPUT_DIR / "jpx_closure_report_v2_13g.json"

ROUTE_JSON = OUTPUT_DIR / "next_provider_route_v2_14a.json"
ROUTE_MD = OUTPUT_DIR / "next_provider_route_v2_14a.md"
CANDIDATES_CSV = OUTPUT_DIR / "next_provider_route_candidates_v2_14a.csv"
PLANNED_OUTPUTS_CSV = OUTPUT_DIR / "next_provider_planned_outputs_v2_14a.csv"

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
        ROUTE_JSON,
        ROUTE_MD,
        CANDIDATES_CSV,
        PLANNED_OUTPUTS_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.14A outputs:\n"
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

    previous_closure = read_json(PREVIOUS_CLOSURE_JSON)

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

    candidates = [
        {
            "rank": 1,
            "provider": "deutsche_boerse_xetra_all_tradable_instruments",
            "route_status": "SELECTED_AS_NEXT_PROVIDER_ROUTE",
            "readiness_score": 93,
            "official_surface": "Deutsche Börse / Xetra All Tradable Instruments",
            "expected_format": "html_plus_download_or_csv",
            "expected_row_range": "5000-15000_gross",
            "expected_net_new_range": "3000-10000_after_conservative_filters",
            "expected_overlap_risk": "medium_high_due_to_existing_cboe_europe_reference_data",
            "main_strength": "highest_remaining_row_potential_and_official_instrument_reference_surface",
            "main_risk": "contains ETFs, ETCs, ETNs, active ETFs and possible overlap; requires strict shares-only validation",
            "recommended_role": "primary_route_for_v2_14",
            "selected": "yes",
        },
        {
            "rank": 2,
            "provider": "tsx_tmx_listed_company_directory",
            "route_status": "BACKUP_ROUTE_READY",
            "readiness_score": 88,
            "official_surface": "TMX TSX/TSXV Listed Company Directory",
            "expected_format": "html_or_directory_endpoint",
            "expected_row_range": "3000-5000_gross",
            "expected_net_new_range": "2500-4500_after_conservative_filters",
            "expected_overlap_risk": "low_medium",
            "main_strength": "good geographic diversification_and_official_directory",
            "main_risk": "may require careful acquisition path if directory is dynamic",
            "recommended_role": "backup_route_if_xetra_acquisition_fails_or_underperforms",
            "selected": "no",
        },
        {
            "rank": 3,
            "provider": "asx_listed_companies_csv",
            "route_status": "BACKUP_ROUTE_READY_LOW_COMPLEXITY",
            "readiness_score": 87,
            "official_surface": "ASX Listed Companies CSV",
            "expected_format": "csv",
            "expected_row_range": "1500-2500_gross",
            "expected_net_new_range": "1500-2500_after_conservative_filters",
            "expected_overlap_risk": "low",
            "main_strength": "very clean official CSV and low complexity",
            "main_risk": "too small to materially close 13,137-row gap alone",
            "recommended_role": "fast_follow_provider_after_xetra_or_tmx",
            "selected": "no",
        },
        {
            "rank": 4,
            "provider": "euronext_equities_live_directory",
            "route_status": "DEFERRED_ROUTE_CANDIDATE",
            "readiness_score": 79,
            "official_surface": "Euronext live equities directory",
            "expected_format": "html_or_discovered_endpoint",
            "expected_row_range": "1500-8000_gross",
            "expected_net_new_range": "unknown_due_to_cboe_europe_overlap",
            "expected_overlap_risk": "high_due_to_existing_cboe_europe_reference_data",
            "main_strength": "potential European coverage",
            "main_risk": "large overlap risk after Cboe Europe provider already added 21,154 rows",
            "recommended_role": "defer_until_non_european_or_xetra_paths_are_exhausted",
            "selected": "no",
        },
    ]

    planned_outputs = [
        {
            "phase": "v2.14B",
            "path": "scripts/deutsche_boerse_xetra_acquisition_plan_v2_14b.py",
            "type": "script",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.14B",
            "path": "outputs/full_universe_source_acquisition/deutsche_boerse_xetra_acquisition_plan_v2_14b.json",
            "type": "plan_json",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.14B",
            "path": "outputs/full_universe_source_acquisition/deutsche_boerse_xetra_acquisition_plan_v2_14b.md",
            "type": "plan_report",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.14B",
            "path": "outputs/full_universe_source_acquisition/deutsche_boerse_xetra_acquisition_contract_v2_14b.csv",
            "type": "contract_csv",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.14C",
            "path": "outputs/full_universe_source_acquisition/raw/deutsche_boerse_xetra_v2_14c/",
            "type": "future_raw_directory",
            "required": "planned_only",
            "overwrite_policy": "new_directory_or_fail_in_v2_14c",
        },
    ]

    selected = candidates[0]

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "NEXT_PROVIDER_ROUTE_SELECTED_FULL_SOURCE_STILL_BLOCKED",
        "route_decision": "DEUTSCHE_BOERSE_XETRA_SELECTED_AS_NEXT_PROVIDER_ROUTE",
        "selected_provider": selected["provider"],
        "generated_at_utc": utc_now(),
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED,
            "source_to_50k_pending_percent": SOURCE_TO_50K_PENDING,
            "first_expansion_unlocked": True,
            "full_source_unlocked": False,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
            "previous_jpx_closure_status": previous_closure.get(
                "closure_status",
                "JPX_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED",
            ),
            "previous_commit": "ef14563",
        },
        "hard_guards": hard_guards,
        "selection_rationale": {
            "why_selected": (
                "The remaining gap is still 13,137 rows. Deutsche Börse/Xetra has the strongest "
                "gross row potential among remaining official provider routes, while still offering "
                "an official reference surface. Because it includes non-common-equity instruments "
                "and likely overlaps with existing Cboe Europe coverage, v2.14B/v2.14C/v2.14D must "
                "use strict raw preservation, shares-only validation and conservative rebuild gates."
            ),
            "why_not_asx_first": (
                "ASX has a cleaner official CSV and low complexity, but its expected row contribution "
                "is too small to materially close the remaining 13,137-row gap by itself."
            ),
            "why_not_tmx_first": (
                "TMX is a strong backup and may be preferable if Xetra acquisition is blocked, "
                "but Xetra has higher immediate row potential."
            ),
        },
        "candidates": candidates,
        "planned_outputs": planned_outputs,
        "recommended_next_phase": "v2.14B - Deutsche Börse Xetra Acquisition Plan",
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

    write_json(ROUTE_JSON, payload)

    write_csv(
        CANDIDATES_CSV,
        candidates,
        [
            "rank",
            "provider",
            "route_status",
            "readiness_score",
            "official_surface",
            "expected_format",
            "expected_row_range",
            "expected_net_new_range",
            "expected_overlap_risk",
            "main_strength",
            "main_risk",
            "recommended_role",
            "selected",
        ],
    )

    write_csv(
        PLANNED_OUTPUTS_CSV,
        planned_outputs,
        ["phase", "path", "type", "required", "overwrite_policy"],
    )

    candidate_lines = "\n".join(
        f"- Rank {row['rank']}: `{row['provider']}` — {row['route_status']} — "
        f"readiness {row['readiness_score']} — expected net-new {row['expected_net_new_range']}"
        for row in candidates
    )

    planned_lines = "\n".join(
        f"- `{row['path']}`"
        for row in planned_outputs
    )

    guard_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in hard_guards.items()
    )

    md = f"""# {VERSION} - {PHASE}

Status: **NEXT_PROVIDER_ROUTE_SELECTED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **route-selection-only**

Generated at UTC: `{payload["generated_at_utc"]}`

## Decision

- Route decision: **DEUTSCHE_BOERSE_XETRA_SELECTED_AS_NEXT_PROVIDER_ROUTE**
- Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**
- Recommended next phase: **v2.14B - Deutsche Börse Xetra Acquisition Plan**

## Current state

- Current expanded rows: {CURRENT_EXPANDED_ROWS}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Rows needed for full source: {ROWS_NEEDED_FULL_SOURCE}
- Source-to-50k completion: {SOURCE_TO_50K_COMPLETED}%
- Source-to-50k pending: {SOURCE_TO_50K_PENDING}%
- Full source unlocked: false
- Full 59k status: blocked until source >=50k and explicit gate approved
- Previous JPX closure commit: `ef14563`

## Why Deutsche Börse / Xetra next

The remaining gap is still **13,137 rows**.

Deutsche Börse/Xetra is selected because it has the strongest remaining gross row potential among official provider routes.

The route must be treated conservatively because the official surface includes non-common-equity instruments and likely overlaps with existing Cboe Europe coverage.

v2.14B must therefore plan strict source preservation and v2.14D must enforce shares-only filtering before any rebuild.

## Candidate ranking

{candidate_lines}

## Planned outputs

{planned_lines}

## Hard guards

{guard_lines}

## Percentages

- GLOBAL corrected: {GLOBAL_COMPLETED}% completed / {GLOBAL_PENDING}% pending
- Source to 50k: {SOURCE_TO_50K_COMPLETED}% completed / {SOURCE_TO_50K_PENDING}% pending
- Full source gate: 0% completed / 100% pending
- Full 59k dry-run: 0% completed / 100% pending

## Scope note

v2.14A is route-selection-only.

It does not download data, parse workbooks, normalize rows, filter net-new rows, rebuild the universe, score, call OpenAI, call broker APIs or launch full 59k.
"""

    ROUTE_MD.write_text(md, encoding="utf-8")

    print("v2.14A next provider route-selection-only completed.")
    print(f"- route json: {ROUTE_JSON}")
    print(f"- route report: {ROUTE_MD}")
    print(f"- candidates csv: {CANDIDATES_CSV}")
    print(f"- planned outputs csv: {PLANNED_OUTPUTS_CSV}")
    print("")
    print("DECISION:")
    print("- status: NEXT_PROVIDER_ROUTE_SELECTED_FULL_SOURCE_STILL_BLOCKED")
    print("- route_decision: DEUTSCHE_BOERSE_XETRA_SELECTED_AS_NEXT_PROVIDER_ROUTE")
    print("- selected_provider: deutsche_boerse_xetra_all_tradable_instruments")
    print("- recommended_next_phase: v2.14B - Deutsche Börse Xetra Acquisition Plan")
    print("")
    print("CURRENT_STATE:")
    print(f"- current_expanded_rows: {CURRENT_EXPANDED_ROWS}")
    print(f"- full_source_threshold: {FULL_SOURCE_THRESHOLD}")
    print(f"- rows_needed_full_source: {ROWS_NEEDED_FULL_SOURCE}")
    print(f"- source_to_50k_completed_percent: {SOURCE_TO_50K_COMPLETED}")
    print(f"- global_completed_corrected: {GLOBAL_COMPLETED}")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
