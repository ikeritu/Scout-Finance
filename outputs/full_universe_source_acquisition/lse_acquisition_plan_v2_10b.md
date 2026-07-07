# Scout Finance ? v2.10B LSE Acquisition Plan

- Phase: v2.10B
- Method: lse_acquisition_plan_v1
- Created at: 2026-07-07T14:01:13+00:00
- Plan status: **LSE_ACQUISITION_PLAN_READY**
- Readiness score: **90/100**
- Plan decision: **LSE_CONTROLLED_ACQUISITION_APPROVED**
- Recommended next phase: **v2.10C ? LSE Acquisition Real**

## Provider

- Provider ID: `lse_issuers_and_instruments_reports`
- Provider dir: `data/raw/source_providers/lse_issuers_and_instruments_reports`
- Primary route: `lse_reports_page_probe`
- Fallback provider: `cboe_europe_reference_data`

## Current state

- Current expanded universe: `data/raw/expanded_universe/expanded_universe_v2_8e.csv`
- Current expanded rows: 9200
- Current exclusions rows: 10056
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Rows needed first expansion: 5800
- Rows needed full source: 40800

## Planned routes for v2.10C

### 1. LSE Reports page probe

- Route ID: `lse_reports_page_probe`
- URL: `https://www.londonstockexchange.com/reports`
- Method: GET
- Expected content type: text/html
- Network allowed in: v2.10C
- Expected value: HIGH
- Risk: LOW_MEDIUM
- Treatment: Download official Reports page HTML, preserve raw, discover issuer/instrument report links.

### 2. LSE Issuers reports tab/page probe

- Route ID: `lse_issuers_reports_tab_probe`
- URL: `https://www.londonstockexchange.com/reports?tab=issuers`
- Method: GET
- Expected content type: text/html
- Network allowed in: v2.10C
- Expected value: HIGH
- Risk: MEDIUM
- Treatment: Probe issuer-specific report route if tab URL resolves server-side or exposes embedded data.

### 3. LSE Instruments reports tab/page probe

- Route ID: `lse_instruments_reports_tab_probe`
- URL: `https://www.londonstockexchange.com/reports?tab=instruments`
- Method: GET
- Expected content type: text/html
- Network allowed in: v2.10C
- Expected value: HIGH
- Risk: MEDIUM
- Treatment: Probe instrument-specific report route if tab URL resolves server-side or exposes embedded data.

### 4. LSE Historical and analytics data products probe

- Route ID: `lse_historical_analytics_data_products_probe`
- URL: `https://www.londonstockexchange.com/equities-trading/market-data/historical-analytics-data-products`
- Method: GET
- Expected content type: text/html
- Network allowed in: v2.10C
- Expected value: MEDIUM
- Risk: MEDIUM
- Treatment: Reference route for Daily Tradeable Instruments Report or product documentation if public download route exists.

## Fallback routes

- Cboe Europe Equities Reference Data ? `https://www.cboe.com/europe/equities/support/reference_data/` ? FALLBACK_IF_LSE_BLOCKED

## Planned outputs for v2.10C

- provider_dir: `data/raw/source_providers/lse_issuers_and_instruments_reports`
- raw_reports_page_html: `data/raw/source_providers/lse_issuers_and_instruments_reports/lse_reports_page.html`
- raw_issuers_page_html: `data/raw/source_providers/lse_issuers_and_instruments_reports/lse_issuers_reports_page.html`
- raw_instruments_page_html: `data/raw/source_providers/lse_issuers_and_instruments_reports/lse_instruments_reports_page.html`
- raw_historical_analytics_page_html: `data/raw/source_providers/lse_issuers_and_instruments_reports/lse_historical_analytics_data_products_page.html`
- downloaded_report_candidates_dir: `data/raw/source_providers/lse_issuers_and_instruments_reports/report_candidates`
- acquisition_json: `outputs/full_universe_source_acquisition/lse_acquisition_real_v2_10c.json`
- acquisition_md: `outputs/full_universe_source_acquisition/lse_acquisition_real_v2_10c.md`
- discovered_links_csv: `outputs/full_universe_source_acquisition/lse_discovered_links_v2_10c.csv`
- schema_probe_csv: `outputs/full_universe_source_acquisition/lse_schema_probe_v2_10c.csv`
- sample_csv: `outputs/full_universe_source_acquisition/lse_sample_v2_10c.csv`

## Expected schema candidates

- symbol_candidates: symbol, ticker, tidm, sedol, isin, instrument code, epic
- name_candidates: issuer name, company name, security name, instrument name, name
- market_candidates: market, segment, trading service, market segment, admission market
- instrument_type_candidates: instrument type, security type, type, sector, asset class
- country_candidates: country, country of incorporation, domicile, issuer country
- currency_candidates: currency, trading currency, price currency
- isin_candidates: isin, isin code

## Acquisition controls for v2.10C

- Network download allowed only for planned LSE routes.
- Preserve every raw HTML/report file exactly.
- Report URL, status code, content type, size and SHA256 for every request.
- Discover candidate links only from official LSE pages downloaded in v2.10C.
- Download only official CSV/XLS/XLSX/ZIP/JSON report candidates discovered from LSE pages.
- Do not normalize into expanded_universe during acquisition.
- Do not rebuild expanded_universe.
- Do not overwrite active MVP outputs.
- Do not execute scoring.
- Do not call OpenAI.
- Do not call broker APIs.
- Do not launch full 59k universe.

## Validation contract for v2.10D

- Validate whether LSE produced any downloadable report file usable for source expansion.
- Detect row count and schema for each downloaded candidate file.
- Detect usable identifier fields: TIDM/ticker, ISIN, SEDOL, issuer name, market/segment and instrument type.
- Avoid treating ISIN-only rows as ticker-ready unless a market symbol is present.
- Normalize candidates conservatively with source_provider=lse_issuers_and_instruments_reports.
- Compute duplicate keys inside LSE candidate source.
- Compute net-new candidate rows against expanded_universe_v2_8e.
- Decide whether LSE is usable for isolated rebuild, reference/enrichment only, or blocked.
- Confirm whether LSE can unlock the 15000-row first expansion threshold.

## Decision gate

- Minimum net-new rows to consider rebuild: 5800
- Fallback if blocked: Switch to v2.11A Cboe Europe Reference Data Route or close LSE as blocked.

### Rebuild allowed if

- At least one official LSE report file is downloaded successfully.
- Schema has usable symbol/ticker or safely mappable market identifier.
- Rows can be normalized to canonical schema without brittle scraping.
- Net-new rows are meaningful enough to justify rebuild.
- Duplicate keys are controlled.
- Instrument semantics are acceptable or conservatively classified.

### Rebuild not allowed if

- LSE page is fully dynamic and exposes no stable report/download path.
- Only PDFs or non-tabular documents are available.
- No usable symbol/ticker/identifier field is available.
- Rows are too ambiguous or mixed without safe classification.
- Licensing/usage constraints make storage unsuitable.
- Net-new rows are far below threshold.

## Outputs

- Planned links CSV: `outputs/full_universe_source_acquisition/lse_discovered_links_v2_10b.csv`
- Route probe CSV: `outputs/full_universe_source_acquisition/lse_route_probe_v2_10b.csv`
- Plan JSON: `outputs/full_universe_source_acquisition/lse_acquisition_plan_v2_10b.json`
- Plan report: `outputs/full_universe_source_acquisition/lse_acquisition_plan_v2_10b.md`

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

- v2.10A route artifact found: outputs/full_universe_source_acquisition/next_provider_route_v2_10a.json
- v2.10A route status accepted: NEXT_PROVIDER_ROUTE_READY
- v2.10A route decision accepted: LSE_SELECTED_AS_NEXT_PROVIDER_ROUTE
- Selected provider accepted: lse_issuers_and_instruments_reports
- Current source input available: data/raw/expanded_universe/expanded_universe_v2_8e.csv
- Current source input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv

## Blockers

- No blockers detected.

## Warnings

- LSE reports may be dynamic and may require route discovery in v2.10C.
- Prefer stable official report downloads over brittle scraping.
- LSE may include mixed instruments: shares, ETFs, funds, bonds, warrants or other securities.
- MIC, currency, segment and country semantics must be preserved conservatively.
- Full 59k remains blocked until source reaches at least 50000 rows.

## Recommendation

Proceed to v2.10C controlled LSE acquisition. Do not rebuild until v2.10D validates schema and net-new coverage.

Important: v2.10B is plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.