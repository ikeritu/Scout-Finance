from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.11B"
PHASE = "Cboe Europe Acquisition Plan"
PHASE_TYPE = "plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

PLAN_JSON = OUTPUT_DIR / "cboe_europe_acquisition_plan_v2_11b.json"
PLAN_MD = OUTPUT_DIR / "cboe_europe_acquisition_plan_v2_11b.md"
CONTRACT_CSV = OUTPUT_DIR / "cboe_europe_acquisition_contract_v2_11b.csv"
PLANNED_DOWNLOADS_CSV = OUTPUT_DIR / "cboe_europe_planned_downloads_v2_11b.csv"
EXPECTED_OUTPUTS_CSV = OUTPUT_DIR / "cboe_europe_expected_outputs_v2_11b.csv"


def no_overwrite_guard(paths: list[Path]) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing outputs:\n"
            + "\n".join(existing)
        )


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    no_overwrite_guard(
        [
            PLAN_JSON,
            PLAN_MD,
            CONTRACT_CSV,
            PLANNED_DOWNLOADS_CSV,
            EXPECTED_OUTPUTS_CSV,
        ]
    )

    generated_at_utc = datetime.now(timezone.utc).isoformat()

    hard_guards = {
        "phase_type": PHASE_TYPE,
        "network_download_performed": False,
        "raw_files_downloaded": False,
        "expanded_universe_rebuilt": False,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
        "rebuild_allowed": False,
    }

    source_context = {
        "previous_phase": "v2.11A",
        "previous_phase_status": "CBOE_EUROPE_ROUTE_READY",
        "previous_phase_commit": "581fff8",
        "current_expanded_rows": 9200,
        "rows_needed_first_expansion": 5800,
        "rows_needed_full_source": 40800,
        "first_expansion_threshold": 15000,
        "full_source_threshold": 50000,
        "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
    }

    contract_rows = [
        {
            "step_id": "01",
            "route_type": "official_reference_page",
            "target": "cboe_europe_reference_data_page",
            "url_or_discovery_rule": "https://www.cboe.com/europe/equities/support/reference_data/",
            "purpose": "Download official reference data page as raw HTML and discover official CSV links.",
            "allowed_in_v2_11c": "HTTP GET raw HTML, preserve exact bytes, compute SHA256, record metadata, discover links.",
            "prohibited_in_v2_11c": "No normalization, no net-new filtering, no rebuild, no scoring.",
            "raw_preservation_policy": "Save raw HTML exactly as received under raw/cboe_europe_v2_11c/.",
            "validation_owner": "v2.11D",
        },
        {
            "step_id": "02",
            "route_type": "official_discovered_csv",
            "target": "live_symbols_csv",
            "url_or_discovery_rule": "DISCOVER_FROM_REFERENCE_DATA_PAGE: links mentioning live symbols CSV.",
            "purpose": "Acquire official Live Symbols CSV files if exposed by Cboe Europe.",
            "allowed_in_v2_11c": "Download discovered CSV files only, preserve raw bytes, compute SHA256, record metadata.",
            "prohibited_in_v2_11c": "No schema coercion, no row filtering, no issuer inference, no rebuild.",
            "raw_preservation_policy": "Save each CSV exactly as received with stable filename and manifest entry.",
            "validation_owner": "v2.11D",
        },
        {
            "step_id": "03",
            "route_type": "official_discovered_csv",
            "target": "live_symbols_enhanced_csv",
            "url_or_discovery_rule": "DISCOVER_FROM_REFERENCE_DATA_PAGE: links mentioning enhanced live symbols CSV.",
            "purpose": "Prefer enhanced CSV only if it contains richer symbol/name/MIC/country/currency fields.",
            "allowed_in_v2_11c": "Download discovered enhanced CSV files, preserve raw bytes, compute SHA256, record metadata.",
            "prohibited_in_v2_11c": "No preference decision in acquisition phase; preference belongs to validation.",
            "raw_preservation_policy": "Save raw enhanced CSV separately from non-enhanced CSV.",
            "validation_owner": "v2.11D",
        },
        {
            "step_id": "04",
            "route_type": "fallback_html_page",
            "target": "symbols_traded_cxe",
            "url_or_discovery_rule": "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=cxe",
            "purpose": "Fallback acquisition if official CSV links are not sufficient.",
            "allowed_in_v2_11c": "Download raw HTML only and record metadata.",
            "prohibited_in_v2_11c": "No brittle scraping, no table extraction, no rebuild.",
            "raw_preservation_policy": "Save raw HTML exactly as received.",
            "validation_owner": "v2.11D",
        },
        {
            "step_id": "05",
            "route_type": "fallback_html_page",
            "target": "symbols_traded_bxe",
            "url_or_discovery_rule": "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=bxe",
            "purpose": "Fallback acquisition if official CSV links are not sufficient.",
            "allowed_in_v2_11c": "Download raw HTML only and record metadata.",
            "prohibited_in_v2_11c": "No brittle scraping, no table extraction, no rebuild.",
            "raw_preservation_policy": "Save raw HTML exactly as received.",
            "validation_owner": "v2.11D",
        },
        {
            "step_id": "06",
            "route_type": "fallback_html_page",
            "target": "symbols_traded_dxe",
            "url_or_discovery_rule": "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=dxe",
            "purpose": "Fallback acquisition if official CSV links are not sufficient.",
            "allowed_in_v2_11c": "Download raw HTML only and record metadata.",
            "prohibited_in_v2_11c": "No brittle scraping, no table extraction, no rebuild.",
            "raw_preservation_policy": "Save raw HTML exactly as received.",
            "validation_owner": "v2.11D",
        },
        {
            "step_id": "07",
            "route_type": "fallback_html_page",
            "target": "symbols_traded_trf",
            "url_or_discovery_rule": "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=trf",
            "purpose": "Fallback acquisition if official CSV links are not sufficient.",
            "allowed_in_v2_11c": "Download raw HTML only and record metadata.",
            "prohibited_in_v2_11c": "No brittle scraping, no table extraction, no rebuild.",
            "raw_preservation_policy": "Save raw HTML exactly as received.",
            "validation_owner": "v2.11D",
        },
        {
            "step_id": "08",
            "route_type": "semantic_caution",
            "target": "BXE_CXE_DXE_TRF_SIS_MIC_venue_semantics",
            "url_or_discovery_rule": "Derived from official files only; do not assume primary exchange semantics.",
            "purpose": "Prevent incorrect exchange+ticker assumptions before validation.",
            "allowed_in_v2_11c": "Record venue/MIC labels exactly as source exposes them.",
            "prohibited_in_v2_11c": "No mapping to primary listing exchange, no dedup logic, no key acceptance.",
            "raw_preservation_policy": "Do not mutate source fields.",
            "validation_owner": "v2.11D",
        },
    ]

    planned_download_rows = [
        {
            "sequence": "1",
            "family": "reference_data",
            "method": "GET",
            "url_or_rule": "https://www.cboe.com/europe/equities/support/reference_data/",
            "planned_raw_output": "outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/reference_data_page.html",
            "metadata_required": "url,status_code,content_type,bytes,sha256,fetched_at_utc",
            "notes": "Official discovery page. No data normalization.",
        },
        {
            "sequence": "2",
            "family": "live_symbols_csv",
            "method": "GET",
            "url_or_rule": "Discover official Live Symbols CSV links from reference_data_page.html",
            "planned_raw_output": "outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/live_symbols_*.csv",
            "metadata_required": "url,status_code,content_type,bytes,sha256,fetched_at_utc,source_link_text",
            "notes": "Preserve raw CSV exactly.",
        },
        {
            "sequence": "3",
            "family": "live_symbols_enhanced_csv",
            "method": "GET",
            "url_or_rule": "Discover official Live Symbols Enhanced CSV links from reference_data_page.html",
            "planned_raw_output": "outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/live_symbols_enhanced_*.csv",
            "metadata_required": "url,status_code,content_type,bytes,sha256,fetched_at_utc,source_link_text",
            "notes": "Validation later decides whether enhanced is preferred.",
        },
        {
            "sequence": "4",
            "family": "fallback_symbols_traded_html",
            "method": "GET",
            "url_or_rule": "CXE/BXE/DXE/TRF symbols_traded pages",
            "planned_raw_output": "outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/symbols_traded_*.html",
            "metadata_required": "url,status_code,content_type,bytes,sha256,fetched_at_utc,market_param",
            "notes": "Fallback raw HTML only. No brittle table scraping in acquisition.",
        },
    ]

    expected_output_rows = [
        {
            "phase": "v2.11C",
            "path": "scripts/cboe_europe_acquisition_v2_11c.py",
            "type": "script",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.11C",
            "path": "outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/",
            "type": "raw_directory",
            "required": "yes",
            "overwrite_policy": "new_directory_or_fail",
        },
        {
            "phase": "v2.11C",
            "path": "outputs/full_universe_source_acquisition/cboe_europe_download_manifest_v2_11c.json",
            "type": "manifest",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.11C",
            "path": "outputs/full_universe_source_acquisition/cboe_europe_download_manifest_v2_11c.csv",
            "type": "manifest",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.11C",
            "path": "outputs/full_universe_source_acquisition/cboe_europe_discovered_links_v2_11c.csv",
            "type": "discovery_manifest",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
        {
            "phase": "v2.11C",
            "path": "outputs/full_universe_source_acquisition/cboe_europe_acquisition_report_v2_11c.md",
            "type": "report",
            "required": "yes",
            "overwrite_policy": "must_not_overwrite_existing_file",
        },
    ]

    validation_questions = [
        "Does Cboe Europe expose stable official Live Symbols CSV files?",
        "Are CSV files available for BXE, CXE, DXE, TRF EU, TRF UK and/or SIS?",
        "Does enhanced CSV contain richer symbol/name/MIC/country/currency fields?",
        "How many rows exist before net-new filtering?",
        "How many MIC+ticker, venue+ticker, ISIN and exchange+ticker candidates are net-new against expanded_universe_v2_8e?",
        "Are rows ordinary shares, ETFs, funds, ETCs or mixed instruments?",
        "Can Cboe Europe rows be normalized conservatively without brittle scraping?",
        "Does Cboe Europe unlock the 15000-row first expansion threshold?",
        "Should Cboe Europe be source provider, candidate provider, enrichment, reference-only or deferred?",
    ]

    plan = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "CBOE_EUROPE_ACQUISITION_PLAN_READY",
        "readiness_score": 94,
        "decision": "PROCEED_TO_V2_11C_ACQUISITION_ONLY_AFTER_V2_11B_VALIDATION_AND_COMMIT",
        "generated_at_utc": generated_at_utc,
        "source_context": source_context,
        "hard_guards": hard_guards,
        "contract_for_v2_11c": contract_rows,
        "planned_downloads_for_v2_11c": planned_download_rows,
        "expected_outputs_for_v2_11c": expected_output_rows,
        "validation_handoff_to_v2_11d": validation_questions,
        "mic_venue_caution": [
            "BXE, CXE, DXE, TRF and SIS must be treated as venue/source semantics until validation.",
            "Do not assume Cboe venue equals primary listing exchange.",
            "Do not accept exchange+ticker keys without validation against MIC/venue/ISIN evidence.",
            "Preserve source MIC, venue, market and symbol fields exactly in acquisition.",
        ],
    }

    md = f"""# {VERSION} — {PHASE}

Status: **CBOE_EUROPE_ACQUISITION_PLAN_READY**

Phase type: **plan-only**

Readiness score: **94/100**

Decision: **PROCEED_TO_V2_11C_ACQUISITION_ONLY_AFTER_V2_11B_VALIDATION_AND_COMMIT**

Generated at UTC: `{generated_at_utc}`

## Confirmed previous phase

- v2.11A commit: `581fff8`
- v2.11A status: `CBOE_EUROPE_ROUTE_READY`
- v2.11A pushed to origin/main: yes

## Hard guards

- Network download performed: false
- Raw files downloaded: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false
- Rebuild allowed: false

## Current source context

- Current expanded rows: 9,200
- Rows needed for first expansion: 5,800
- Rows needed for full source: 40,800
- First expansion threshold: 15,000
- Full source threshold: 50,000
- Full 59k status: blocked until source complete and gate approved

## v2.11C controlled acquisition contract

v2.11C must be **acquisition-only**.

Allowed:

- Download Cboe Europe Reference Data page as raw HTML.
- Discover official Live Symbols CSV links from the Reference Data page.
- Discover official Live Symbols Enhanced CSV links from the Reference Data page.
- Download discovered official CSV files as raw files.
- Download CXE/BXE/DXE/TRF symbols_traded pages as fallback raw HTML.
- Record URL, status code, content type, byte size, SHA256 and fetch timestamp.
- Preserve raw files exactly as received.

Forbidden:

- No rebuild.
- No scoring.
- No OpenAI calls.
- No broker/API trading calls.
- No full 59k launch.
- No normalization.
- No net-new filtering.
- No brittle scraping.
- No issuer inference.
- No primary-exchange assumptions.
- No overwrite of active outputs.

## Cboe Europe route families

1. `cboe_europe_reference_data_page`
2. `live_symbols_csv`
3. `live_symbols_enhanced_csv`
4. `symbols_traded_cxe`
5. `symbols_traded_bxe`
6. `symbols_traded_dxe`
7. `symbols_traded_trf`
8. `BXE/CXE/DXE/TRF/SIS MIC and venue semantics caution`

## MIC / venue caution

BXE, CXE, DXE, TRF and SIS must be treated cautiously.

v2.11C may preserve the source fields, but must not decide whether those values represent:

- primary exchange,
- execution venue,
- reporting venue,
- book,
- MIC,
- market segment,
- listing market.

That decision belongs to v2.11D validation.

## Handoff questions for v2.11D

{chr(10).join(f"- {question}" for question in validation_questions)}

## Planned v2.11C outputs

{chr(10).join(f"- `{row['path']}`" for row in expected_output_rows)}

## v2.11B conclusion

Cboe Europe acquisition is ready to move to v2.11C only after this plan is validated and committed.

No source acquisition has been performed in v2.11B.
"""

    write_json(PLAN_JSON, plan)
    PLAN_MD.write_text(md, encoding="utf-8")

    write_csv(
        CONTRACT_CSV,
        contract_rows,
        [
            "step_id",
            "route_type",
            "target",
            "url_or_discovery_rule",
            "purpose",
            "allowed_in_v2_11c",
            "prohibited_in_v2_11c",
            "raw_preservation_policy",
            "validation_owner",
        ],
    )

    write_csv(
        PLANNED_DOWNLOADS_CSV,
        planned_download_rows,
        [
            "sequence",
            "family",
            "method",
            "url_or_rule",
            "planned_raw_output",
            "metadata_required",
            "notes",
        ],
    )

    write_csv(
        EXPECTED_OUTPUTS_CSV,
        expected_output_rows,
        [
            "phase",
            "path",
            "type",
            "required",
            "overwrite_policy",
        ],
    )

    print("v2.11B plan-only outputs generated successfully.")
    print(f"- {PLAN_JSON}")
    print(f"- {PLAN_MD}")
    print(f"- {CONTRACT_CSV}")
    print(f"- {PLANNED_DOWNLOADS_CSV}")
    print(f"- {EXPECTED_OUTPUTS_CSV}")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
