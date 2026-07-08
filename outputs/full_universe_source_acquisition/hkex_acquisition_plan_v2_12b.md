# v2.12B — HKEX Acquisition Plan

Status: **HKEX_ACQUISITION_PLAN_READY**

Phase type: **plan-only**

Selected provider: **hkex_securities_list**

Decision: **PROCEED_TO_V2_12C_HKEX_ACQUISITION_ONLY_AFTER_V2_12B_VALIDATION_AND_COMMIT**

Generated at UTC: `2026-07-08T10:21:50.800428+00:00`

## Confirmed previous phase

- v2.12A route decision: `HKEX_SELECTED_AS_NEXT_PROVIDER_ROUTE`
- v2.12A commit: `9856571`
- Selected route: `hkex_securities_list`

## Current state

- Current expanded rows: 30354
- Full source threshold: 50000
- Rows needed for full source: 19646
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

- 01 `hkex_list_of_securities_xlsx_en` — official_direct_file — Acquire official HKEX List of Securities file as raw bytes.
- 02 `hkex_securities_lists_page` — official_landing_page — Acquire official Securities Lists page for provenance and fallback link discovery.
- 03 `hkex_list_of_securities_xlsx_zh` — optional_official_fallback_file — Optional fallback/provenance file if English XLSX acquisition fails or schema comparison is needed.
- 04 `hkex_security_category_and_stock_code_semantics` — semantic_caution — Prevent incorrect inclusion of ETFs, REITs, warrants, debt, derivatives, structured products or non-equity instruments.
- 05 `hkex_stock_code_format` — identifier_caution — Avoid losing leading zeros and avoid ticker-key collisions.

## Validation questions for v2.12D

- Q01: Does HKEX ListOfSecurities.xlsx remain directly downloadable?
- Q02: Which workbook sheet contains the actual securities table?
- Q03: Does the workbook contain stock code, name of securities, category, sub-category, board lot, currency and ISIN?
- Q04: How many rows exist before filtering?
- Q05: How many rows are ordinary equities versus ETFs, REITs, warrants, debt, derivatives or other instruments?
- Q06: How many candidate identifiers are net-new against expanded_universe_v2_11e?
- Q07: Can HKEX rows be normalized conservatively without brittle scraping?
- Q08: Does HKEX materially reduce the 19,646-row gap to 50k?
- Q09: Should HKEX be source provider, candidate provider, enrichment, reference-only or deferred?

## Planned v2.12C outputs

- `scripts/hkex_acquisition_v2_12c.py`
- `outputs/full_universe_source_acquisition/raw/hkex_v2_12c/`
- `outputs/full_universe_source_acquisition/hkex_download_manifest_v2_12c.json`
- `outputs/full_universe_source_acquisition/hkex_download_manifest_v2_12c.csv`
- `outputs/full_universe_source_acquisition/hkex_discovered_links_v2_12c.csv`
- `outputs/full_universe_source_acquisition/hkex_acquisition_report_v2_12c.md`

## Important caution

HKEX stock codes must be preserved as text because leading zeros are significant.

HKEX security categories must not be accepted blindly. ETFs, REITs, warrants, debt instruments, derivatives and structured products need conservative review in v2.12D.

## Project percentages

- v2.12B HKEX Acquisition Plan: 100% completed / 0% pending after commit
- Fuente real expandida: 88% completed / 12% pending
- Fuente real completa 50k–59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: 94% completed / 6% pending

## Recommended next phase

**v2.12C — HKEX Acquisition Real**

Only after v2.12B outputs are validated, committed and pushed.
