# Scout Finance ? v2.10A Next Provider Route

- Phase: v2.10A
- Method: next_provider_route_after_otc_v1
- Created at: 2026-07-07T13:34:55+00:00
- Route status: **NEXT_PROVIDER_ROUTE_READY**
- Readiness score: **90/100**
- Route decision: **LSE_SELECTED_AS_NEXT_PROVIDER_ROUTE**
- Selected provider: **lse_issuers_and_instruments_reports**
- Recommended next phase: **v2.10B ? LSE Acquisition Plan**

## Current state

- Current expanded universe: `data/raw/expanded_universe/expanded_universe_v2_8e.csv`
- Current exclusions: `data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv`
- Current expanded rows: 9200
- Current exclusions rows: 10056
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Rows needed first expansion: 5800
- Rows needed full source: 40800
- First expansion unlocked: False
- Full source unlocked: False

## Route candidates

### 1. London Stock Exchange ? Issuers and Instruments Reports

- Provider ID: `lse_issuers_and_instruments_reports`
- Source URL: `https://www.londonstockexchange.com/reports`
- Download candidate URL: ``
- Type: official_exchange_reports_route
- Expected value: HIGH_FOR_NON_US_EXPANSION
- Risk: MEDIUM
- Expected coverage: Potentially useful for UK and international instruments admitted to LSE markets, depending on available report exports.
- Why: After OTC produced only 25 net-new rows, the next route should target an official venue/reporting source with broader coverage than a small screener result.
- Planned treatment: v2.10B must inspect/report planned LSE acquisition routes without downloading. v2.10C may download only routes approved by v2.10B.
- Decision: **SELECTED_PRIMARY_ROUTE**

### 2. Cboe Europe Equities Reference Data

- Provider ID: `cboe_europe_reference_data`
- Source URL: `https://www.cboe.com/europe/equities/support/reference_data/`
- Download candidate URL: ``
- Type: official_european_reference_data_route
- Expected value: MEDIUM_TO_HIGH
- Risk: MEDIUM
- Expected coverage: Potentially useful for pan-European reference data if downloadable instruments files are exposed.
- Why: Official European exchange/operator source. Kept as fallback if LSE route is blocked or too dynamic.
- Planned treatment: Keep as fallback for v2.11A or switch route only if v2.10B blocks LSE.
- Decision: **FALLBACK_OFFICIAL_ROUTE**

### 3. DataHub NYSE Other Listings

- Provider ID: `datahub_nyse_other_listings`
- Source URL: `https://datahub.io/core/nyse-other-listings`
- Download candidate URL: ``
- Type: third_party_packaged_reference_route
- Expected value: LOW
- Risk: MEDIUM_HIGH
- Expected coverage: Likely overlap with existing Nasdaq Trader otherlisted data and may be too small.
- Why: Useful as reference or QA comparison, but not ideal as next primary provider because it is not the primary exchange source and likely overlaps.
- Planned treatment: Reference/QA only unless official routes fail.
- Decision: **REFERENCE_ONLY_FALLBACK**

### 4. Nasdaq Stock Screener Revisit

- Provider ID: `nasdaq_stock_screener_revisit`
- Source URL: `https://www.nasdaq.com/market-activity/stocks/screener`
- Download candidate URL: ``
- Type: official_or_semi_official_screener_review
- Expected value: LOW_TO_MEDIUM
- Risk: MEDIUM_HIGH
- Expected coverage: Likely overlaps with existing Nasdaq Trader and SEC sources.
- Why: Could enrich names/metadata, but less promising for large net-new expansion.
- Planned treatment: Keep deferred unless LSE and Cboe Europe fail.
- Decision: **DEFERRED_FALLBACK**

## Planned outputs for v2.10B

- provider_dir: `data/raw/source_providers/lse_issuers_and_instruments_reports`
- route_plan_json: `outputs/full_universe_source_acquisition/lse_acquisition_plan_v2_10b.json`
- route_plan_md: `outputs/full_universe_source_acquisition/lse_acquisition_plan_v2_10b.md`
- discovered_links_csv: `outputs/full_universe_source_acquisition/lse_discovered_links_v2_10b.csv`
- route_probe_csv: `outputs/full_universe_source_acquisition/lse_route_probe_v2_10b.csv`

## Planned controls

- v2.10B must be plan-only.
- No LSE download in v2.10A.
- No expanded_universe rebuild in v2.10A or v2.10B.
- No active MVP output overwrite.
- No scoring.
- No OpenAI.
- No broker calls.
- No full 59k launch.
- Prefer official downloadable CSV/XLS/XLSX/report files over dynamic page scraping.
- If LSE route is dynamic or blocked, close as blocked and switch to Cboe Europe route.

## Validation questions

- Does LSE expose a stable downloadable issuer/instrument report?
- What file format is available: CSV, XLS, XLSX, HTML table, ZIP, PDF?
- Does the report contain a usable symbol, issuer name, instrument type, market/segment and country?
- Does the report include ordinary shares, ETFs, funds, bonds or mixed instruments?
- Can rows be normalized to the canonical source schema without brittle scraping?
- How many rows are available before net-new filtering?
- How many exchange+ticker or MIC+ticker keys are net-new against expanded_universe_v2_8e?
- Does LSE unlock the 15000-row first expansion threshold?
- Should LSE be treated as source provider, candidate provider, enrichment, reference-only or deferred?

## Controls

- Network download performed: false
- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Active outputs overwritten: false
- Expanded universe rebuilt: false
- Plan only: true

## Positives

- v2.9G OTC closure artifact found: outputs/full_universe_source_acquisition/otc_markets_closure_report_v2_9g.json
- v2.9G closure status accepted: OTC_MARKETS_CLOSED_VALID_BUT_NOT_ENOUGH
- v2.9G closure decision accepted: OTC_MARKETS_CLOSED_REFERENCE_OR_ENRICHMENT_ONLY_NO_REBUILD
- Current source input available: data/raw/expanded_universe/expanded_universe_v2_8e.csv
- Current source input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv

## Blockers

- No blockers detected.

## Warnings

- Current expanded source remains below first expansion threshold: 9200 < 15000.
- Current expanded source remains below full-source threshold: 9200 < 50000.
- v2.10A is route-selection only; do not download LSE or Cboe Europe data in this phase.
- LSE may contain multiple report formats, archives or dynamic pages; v2.10B must define a controlled acquisition contract before network access.
- International venues may introduce non-US instruments, currencies, MICs and symbol semantics; classification must be conservative.

## Recommendation

Proceed to v2.10B LSE Acquisition Plan. Do not download or rebuild until the controlled acquisition contract is defined.

Important: v2.10A is route-selection plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.