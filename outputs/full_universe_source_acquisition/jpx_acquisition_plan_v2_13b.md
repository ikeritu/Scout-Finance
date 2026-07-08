# v2.13B - JPX Acquisition Plan

Status: **JPX_ACQUISITION_PLAN_READY**

Phase type: **plan-only**

Selected provider: **jpx_listed_securities_csv**

Decision: **PROCEED_TO_V2_13C_JPX_ACQUISITION_ONLY_AFTER_V2_13B_VALIDATION_AND_COMMIT**

Generated at UTC: `2026-07-08T13:51:59.269092+00:00`

## Confirmed previous phase

- v2.13A route decision: `JPX_SELECTED_AS_NEXT_PROVIDER_ROUTE`
- v2.13A commit: `642de26`
- Selected route: `jpx_listed_securities_csv`

## Current state

- Current expanded rows: 33158
- Full source threshold: 50000
- Rows needed for full source: 16842
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

- 01 `jpxdata_portal_catalog` — official_data_portal_catalog — Acquire JPX official data portal page for provenance and discovery of listed securities dataset.
- 02 `jpx_list_of_tse_listed_issues_catalog_entry` — official_client_portal_catalog_entry — Acquire official catalog entry/search surface where List of TSE-listed Issues is listed as free monthly Excel data.
- 03 `jpx_list_of_tse_listed_issues_workbook` — official_dataset_download_candidate — Acquire official listed issues file as raw bytes if a direct official download link is discovered in v2.13C.
- 04 `jpx_listed_company_search` — official_fallback_search_page — Acquire official listed company search page as fallback/provenance if the data portal route is dynamic or blocked.
- 05 `jpx_security_type_and_market_segment_semantics` — semantic_caution — Prevent inclusion of ETFs, REITs, funds, preferred securities, foreign stocks or other non-common-equity instruments without review.
- 06 `jpx_local_code_format` — identifier_caution — Avoid numeric conversion and preserve leading zeros or special suffixes if present.

## Validation questions for v2.13D

- Q01: Does JPX expose a directly downloadable List of TSE-listed Issues file from official pages?
- Q02: Is the downloaded file Excel, CSV or another structured format?
- Q03: Which sheet/table contains the listed securities table?
- Q04: Does the dataset contain local code, company name, market segment, security type, industry and ISIN?
- Q05: How many rows exist before filtering?
- Q06: How many rows are ordinary listed companies versus ETFs, REITs, preferred securities, funds, foreign stocks or other instruments?
- Q07: How many candidate identifiers are net-new against expanded_universe_v2_12e?
- Q08: Can JPX rows be normalized conservatively without brittle scraping?
- Q09: Does JPX materially reduce the 16,842-row gap to 50k?
- Q10: Should JPX be source provider, candidate provider, enrichment, reference-only or deferred?

## Planned v2.13C outputs

- `scripts/jpx_acquisition_v2_13c.py`
- `outputs/full_universe_source_acquisition/raw/jpx_v2_13c/`
- `outputs/full_universe_source_acquisition/jpx_download_manifest_v2_13c.json`
- `outputs/full_universe_source_acquisition/jpx_download_manifest_v2_13c.csv`
- `outputs/full_universe_source_acquisition/jpx_discovered_links_v2_13c.csv`
- `outputs/full_universe_source_acquisition/jpx_acquisition_report_v2_13c.md`

## Important cautions

JPX local security codes must be preserved as text.

JPX market segment and security type must not be accepted blindly. ETFs, REITs, preferred securities, funds, foreign stocks and other non-common-equity instruments need conservative review in v2.13D.

## Project percentages

- v2.13B JPX Acquisition Plan: 100% completed / 0% pending after commit
- Fuente real expandida: 91% completed / 9% pending
- Fuente real completa 50k-59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: 95% completed / 5% pending

## Recommended next phase

**v2.13C - JPX Acquisition Real**

Only after v2.13B outputs are validated, committed and pushed.
