from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.15B"
PHASE = "Euronext Acquisition Plan"
PHASE_TYPE = "plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

PLAN_JSON = OUTPUT_DIR / "euronext_acquisition_plan_v2_15b.json"
PLAN_MD = OUTPUT_DIR / "euronext_acquisition_plan_v2_15b.md"
SOURCE_CANDIDATES_CSV = OUTPUT_DIR / "euronext_source_candidates_v2_15b.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

SELECTED_PROVIDER_ID = "euronext_official_instruments_equities"
SELECTED_PROVIDER_NAME = "Euronext official instruments / listed equities"

SOURCE_CANDIDATES = [
    {
        "source_id": "euronext_live_all_equities",
        "source_name": "Euronext Live - All Equities",
        "source_url": "https://live.euronext.com/en/products/equities/list",
        "source_type": "official_public_web",
        "priority": 1,
        "expected_use": "Primary public discovery source for listed equities across Euronext markets.",
        "expected_formats": "html, possible embedded api/json/csv endpoints after inspection",
        "target_fields": "isin, symbol, name, market, venue/mic, instrument type, currency if available",
        "risk": "May require endpoint discovery from page assets or paginated requests.",
    },
    {
        "source_id": "euronext_live_market_equity_pages",
        "source_name": "Euronext Live market-specific equity pages",
        "source_url": "https://live.euronext.com/en/products/equities/list",
        "source_type": "official_public_web",
        "priority": 2,
        "expected_use": "Fallback or segmentation source for markets such as Amsterdam, Brussels, Dublin, Lisbon, Milan, Oslo and Paris.",
        "expected_formats": "html, market-specific query endpoints if discoverable",
        "target_fields": "isin, symbol, name, market segment, exchange",
        "risk": "Potential overlap and duplicate listings across segments.",
    },
    {
        "source_id": "euronext_advanced_reference_data",
        "source_name": "Euronext Advanced Reference Data",
        "source_url": "https://www.euronext.com/en/products-services/advanced-reference-data",
        "source_type": "official_reference_data_product",
        "priority": 3,
        "expected_use": "Reference source for machine-readable daily CSV reference data if accessible or documented.",
        "expected_formats": "csv via Euronext Datashop/SFTP according to product documentation",
        "target_fields": "issuer, instrument, ISIN, market, instrument type, events if available",
        "risk": "May be commercial or gated; should not be assumed freely downloadable.",
    },
    {
        "source_id": "euronext_static_reference_data",
        "source_name": "Euronext Static Reference Data - Equities & Bonds",
        "source_url": "https://www.euronext.com/en/products-services/static-reference-data",
        "source_type": "official_reference_data_product",
        "priority": 4,
        "expected_use": "Secondary official reference data candidate if public documentation confirms useful equity coverage.",
        "expected_formats": "structured machine-readable reference data, access may be commercial/gated",
        "target_fields": "ISIN, instrument reference, corporate action mapping, instrument changes",
        "risk": "May include unlisted instruments and bonds; requires strict taxonomy filters.",
    },
]

MARKET_SCOPE = [
    "Amsterdam",
    "Brussels",
    "Dublin",
    "Lisbon",
    "Milan",
    "Oslo",
    "Paris",
]

TAXONOMY_RULES = [
    {
        "rule_id": "include_common_equity_like",
        "decision": "include",
        "description": "Include ordinary/common listed equities where the instrument type or market segment clearly identifies equity shares.",
    },
    {
        "rule_id": "exclude_etf_etn_etc_funds_bonds_structured",
        "decision": "exclude",
        "description": "Exclude ETFs, ETNs, ETCs, funds, bonds, warrants, certificates, structured products and derivatives.",
    },
    {
        "rule_id": "exclude_ambiguous_without_manual_review",
        "decision": "exclude_or_hold",
        "description": "If instrument classification is ambiguous, do not add during rebuild; route to exclusions/manual review.",
    },
]

EXPECTED_OUTPUTS_NEXT_PHASE = [
    "raw official pages or endpoint payloads",
    "source discovery manifest",
    "download manifest with status codes and checksums",
    "candidate files stored without parsing decisions",
]

VALIDATION_PLAN = [
    "Confirm source accessibility and official origin.",
    "Identify whether a public export/API exists for all equities.",
    "Detect pagination, markets, endpoint parameters and rate limits.",
    "Verify required fields: ISIN, symbol/ticker, name, market/exchange, instrument type.",
    "Measure gross rows and market distribution.",
    "Validate taxonomy filters before any rebuild phase.",
    "Estimate net-new overlap against expanded_universe_v2_14e only in validation phase, not in this plan phase.",
]

RISKS_AND_MITIGATIONS = [
    {
        "risk": "Euronext public list may use dynamic endpoints not visible in static HTML.",
        "mitigation": "v2.15C should save both HTML and discovered JS/API references for later validation.",
    },
    {
        "risk": "Reference data products may be gated/commercial.",
        "mitigation": "Use public Euronext Live pages first; treat reference data product pages as documentation/fallback, not guaranteed input.",
    },
    {
        "risk": "Overlap with Cboe Europe and Xetra may be significant.",
        "mitigation": "v2.15D must perform ISIN and exchange+ticker overlap checks before rebuild.",
    },
    {
        "risk": "Non-equity instruments may be mixed into source lists.",
        "mitigation": "Strict taxonomy: exclude ETF, ETN, ETC, funds, bonds, structured products and derivatives.",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in [PLAN_JSON, PLAN_MD, SOURCE_CANDIDATES_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "EURONEXT_ACQUISITION_PLAN_CREATED_NO_DOWNLOADS_PERFORMED",
        "generated_at_utc": utc_now(),
        "selected_provider": {
            "provider_id": SELECTED_PROVIDER_ID,
            "provider_name": SELECTED_PROVIDER_NAME,
            "previous_route_phase": "v2.15A",
            "previous_route_commit": "f803505",
        },
        "current_state": {
            "canonical_dataset": CURRENT_CANONICAL_DATASET,
            "current_rows": CURRENT_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED_PERCENT,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "official_source_candidates": SOURCE_CANDIDATES,
        "market_scope": MARKET_SCOPE,
        "taxonomy_rules": TAXONOMY_RULES,
        "expected_outputs_next_phase": EXPECTED_OUTPUTS_NEXT_PHASE,
        "validation_plan": VALIDATION_PLAN,
        "risks_and_mitigations": RISKS_AND_MITIGATIONS,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed": False,
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
        "recommended_next_phase": "v2.15C - Euronext Raw Acquisition",
    }

    write_json(PLAN_JSON, payload)

    write_csv(
        SOURCE_CANDIDATES_CSV,
        SOURCE_CANDIDATES,
        [
            "source_id",
            "source_name",
            "source_url",
            "source_type",
            "priority",
            "expected_use",
            "expected_formats",
            "target_fields",
            "risk",
        ],
    )

    source_lines = "\n".join(
        f"- P{row['priority']} `{row['source_id']}` - {row['source_name']} - {row['source_url']}"
        for row in SOURCE_CANDIDATES
    )

    risk_lines = "\n".join(
        f"- Risk: {row['risk']}\n  Mitigation: {row['mitigation']}"
        for row in RISKS_AND_MITIGATIONS
    )

    taxonomy_lines = "\n".join(
        f"- `{row['rule_id']}`: {row['decision']} - {row['description']}"
        for row in TAXONOMY_RULES
    )

    validation_lines = "\n".join(f"- {item}" for item in VALIDATION_PLAN)

    PLAN_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **EURONEXT_ACQUISITION_PLAN_CREATED_NO_DOWNLOADS_PERFORMED**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Selected provider

- Provider ID: `{SELECTED_PROVIDER_ID}`
- Provider name: **{SELECTED_PROVIDER_NAME}**
- Route phase: `v2.15A`
- Route commit: `f803505`

## Current state

- Canonical dataset: `{CURRENT_CANONICAL_DATASET}`
- Current rows: `{CURRENT_ROWS}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completed: `{SOURCE_TO_50K_COMPLETED_PERCENT}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Official source candidates

{source_lines}

## Market scope

{", ".join(MARKET_SCOPE)}

## Taxonomy rules

{taxonomy_lines}

## Validation plan for v2.15D

{validation_lines}

## Risks and mitigations

{risk_lines}

## Expected outputs in v2.15C

- Raw official pages or endpoint payloads.
- Source discovery manifest.
- Download manifest with status codes and checksums.
- Candidate files stored without parsing decisions.

## Guards

- Network download performed: false
- Raw files downloaded: false
- Raw files modified after write: false
- Workbook/CSV parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Recommended next phase

`v2.15C - Euronext Raw Acquisition`

## Important note

This phase creates the acquisition plan only. It does not download, parse, normalize, rebuild, score, call OpenAI, call brokers or launch full 59k.
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15B Euronext acquisition plan completed.")
    print("")
    print("STATUS:")
    print("- EURONEXT_ACQUISITION_PLAN_CREATED_NO_DOWNLOADS_PERFORMED")
    print("")
    print("SELECTED_PROVIDER:")
    print(f"- provider_id: {SELECTED_PROVIDER_ID}")
    print(f"- provider_name: {SELECTED_PROVIDER_NAME}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_CANDIDATES:")
    for row in SOURCE_CANDIDATES:
        print(f"- P{row['priority']} {row['source_id']}: {row['source_url']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print("- v2.15C - Euronext Raw Acquisition")


if __name__ == "__main__":
    main()
