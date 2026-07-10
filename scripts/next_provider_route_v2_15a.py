from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.15A"
PHASE = "Next Provider Route For Remaining Full Source Gap"
PHASE_TYPE = "route-selection-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ROUTE_JSON = OUTPUT_DIR / "next_provider_route_v2_15a.json"
ROUTE_MD = OUTPUT_DIR / "next_provider_route_v2_15a.md"
CANDIDATES_CSV = OUTPUT_DIR / "next_provider_candidates_v2_15a.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

PREVIOUS_PROVIDER_CLOSURES = [
    "cboe_listed_symbols",
    "sec_company_tickers_exchange",
    "nasdaq_trader_nasdaqlisted",
    "nasdaq_trader_otherlisted",
    "cboe_europe_reference_data",
    "hkex_securities_list",
    "jpx_listed_securities",
    "deutsche_boerse_xetra_all_tradable_instruments",
]

CANDIDATES = [
    {
        "provider_id": "euronext_official_instruments_equities",
        "provider_name": "Euronext official instruments / listed equities",
        "region": "Europe",
        "expected_impact": "high",
        "official_source_likelihood": "high",
        "duplicate_risk": "medium",
        "taxonomy_complexity": "medium",
        "access_complexity": "medium",
        "reason": "Large official European venue group; likely to add listings not fully covered by previous providers while complementing Xetra, HKEX and JPX.",
        "route_score": 94,
    },
    {
        "provider_id": "tmx_tsx_tsxv_listed_issuers",
        "provider_name": "TMX / TSX / TSXV listed issuers",
        "region": "Canada",
        "expected_impact": "medium_high",
        "official_source_likelihood": "high",
        "duplicate_risk": "low_medium",
        "taxonomy_complexity": "medium",
        "access_complexity": "medium",
        "reason": "Canada can add a meaningful block of common equities and ETFs require filtering; good diversification outside US/Europe/Asia already covered.",
        "route_score": 88,
    },
    {
        "provider_id": "asx_official_listed_companies",
        "provider_name": "ASX official listed companies",
        "region": "Australia",
        "expected_impact": "medium",
        "official_source_likelihood": "high",
        "duplicate_risk": "low",
        "taxonomy_complexity": "low_medium",
        "access_complexity": "low_medium",
        "reason": "Clear official exchange candidate with likely clean symbol/company data and manageable taxonomy.",
        "route_score": 84,
    },
    {
        "provider_id": "krx_kind_listed_companies",
        "provider_name": "KRX / KIND listed companies",
        "region": "South Korea",
        "expected_impact": "medium",
        "official_source_likelihood": "high",
        "duplicate_risk": "low",
        "taxonomy_complexity": "medium_high",
        "access_complexity": "medium_high",
        "reason": "Large Asian market candidate; language/access/taxonomy may be more complex than ASX/TMX.",
        "route_score": 79,
    },
    {
        "provider_id": "sgx_securities_list",
        "provider_name": "SGX securities list",
        "region": "Singapore",
        "expected_impact": "low_medium",
        "official_source_likelihood": "high",
        "duplicate_risk": "low",
        "taxonomy_complexity": "medium",
        "access_complexity": "medium",
        "reason": "Good official venue candidate but likely smaller net-new contribution than Euronext/TMX/ASX.",
        "route_score": 73,
    },
    {
        "provider_id": "bme_spanish_listed_instruments",
        "provider_name": "BME Spanish listed instruments",
        "region": "Spain",
        "expected_impact": "low_medium",
        "official_source_likelihood": "high",
        "duplicate_risk": "medium_high",
        "taxonomy_complexity": "medium",
        "access_complexity": "medium",
        "reason": "Relevant European source but may overlap heavily with Cboe Europe and other European coverage.",
        "route_score": 69,
    },
]

SELECTED_PROVIDER_ID = "euronext_official_instruments_equities"


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

    for path in [ROUTE_JSON, ROUTE_MD, CANDIDATES_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    selected = next(c for c in CANDIDATES if c["provider_id"] == SELECTED_PROVIDER_ID)

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "NEXT_PROVIDER_ROUTE_SELECTED_FULL_SOURCE_STILL_BLOCKED",
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
        "previous_provider_closures": PREVIOUS_PROVIDER_CLOSURES,
        "selected_provider": selected,
        "candidate_ranking": sorted(CANDIDATES, key=lambda row: row["route_score"], reverse=True),
        "decision": {
            "selected_provider_id": selected["provider_id"],
            "selected_provider_name": selected["provider_name"],
            "reason": selected["reason"],
            "why_now": "Highest route score among remaining candidates; broad official exchange coverage; suitable next attempt to reduce the 11,713-row remaining gap.",
            "next_phase": "v2.15B - Euronext Acquisition Plan",
        },
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
        "recommended_next_phase": "v2.15B - Euronext Acquisition Plan",
    }

    write_json(ROUTE_JSON, payload)

    fieldnames = [
        "provider_id",
        "provider_name",
        "region",
        "expected_impact",
        "official_source_likelihood",
        "duplicate_risk",
        "taxonomy_complexity",
        "access_complexity",
        "route_score",
        "reason",
    ]
    write_csv(CANDIDATES_CSV, payload["candidate_ranking"], fieldnames)

    candidate_lines = "\n".join(
        f"- {row['route_score']} — `{row['provider_id']}` — {row['provider_name']} — {row['reason']}"
        for row in payload["candidate_ranking"]
    )

    ROUTE_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **NEXT_PROVIDER_ROUTE_SELECTED_FULL_SOURCE_STILL_BLOCKED**

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

## Selected provider

`{selected["provider_id"]}`

Name: **{selected["provider_name"]}**

Region: **{selected["region"]}**

Route score: **{selected["route_score"]}**

Reason:

{selected["reason"]}

## Candidate ranking

{candidate_lines}

## Decision

Selected provider for the next cycle:

`{selected["provider_id"]}`

Recommended next phase:

`v2.15B - Euronext Acquisition Plan`

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

## Important note

This phase only selects the next provider route. It does not download, parse, normalize, rebuild, score, call OpenAI, call brokers or launch full 59k.
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15A next provider route completed.")
    print("")
    print("STATUS:")
    print("- NEXT_PROVIDER_ROUTE_SELECTED_FULL_SOURCE_STILL_BLOCKED")
    print("")
    print("SELECTED_PROVIDER:")
    print(f"- provider_id: {selected['provider_id']}")
    print(f"- provider_name: {selected['provider_name']}")
    print(f"- route_score: {selected['route_score']}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print("- v2.15B - Euronext Acquisition Plan")


if __name__ == "__main__":
    main()
