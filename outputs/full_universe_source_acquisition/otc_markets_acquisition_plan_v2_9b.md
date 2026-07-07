# Scout Finance ? v2.9B OTC Markets Acquisition Plan

- Phase: v2.9B
- Method: otc_markets_acquisition_plan_v1
- Created at: 2026-07-07T10:48:53+00:00
- Plan status: **OTC_MARKETS_ACQUISITION_PLAN_READY**
- Readiness score: **92/100**
- Plan decision: **OTC_MARKETS_CONTROLLED_ACQUISITION_APPROVED**
- Recommended next phase: **v2.9C ? OTC Markets Acquisition Real**

## Provider

- Provider ID: `otc_markets_stock_screener`
- Provider dir: `data/raw/source_providers/otc_markets_stock_screener`
- Primary route: `otc_markets_stock_screener_download_csv`
- Secondary route: `otc_markets_stock_screener_page_probe`

## Current state

- Current expanded universe: `data/raw/expanded_universe/expanded_universe_v2_8e.csv`
- Current expanded rows: 9200
- Current exclusions rows: 10056
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Rows needed first expansion: 5800
- Rows needed full source: 40800

## Planned routes for v2.9C

### 1. OTC Markets Stock Screener CSV download

- Route ID: `otc_markets_stock_screener_download_csv`
- Page URL: `https://www.otcmarkets.com/research/stock-screener`
- Download URL: `https://www.otcmarkets.com/research/stock-screener/api/downloadCSV?ce=true&sortField=volume&sortOrder=desc`
- Method: GET
- Expected content type: text/csv_or_octet_stream
- Expected value: HIGH
- Risk: MEDIUM
- Treatment: Primary route for v2.9C. Download raw CSV only, preserve exact bytes, then schema probe.

### 2. OTC Markets Stock Screener page probe

- Route ID: `otc_markets_stock_screener_page_probe`
- Page URL: `https://www.otcmarkets.com/research/stock-screener`
- Download URL: `https://www.otcmarkets.com/research/stock-screener`
- Method: GET
- Expected content type: text/html
- Expected value: MEDIUM
- Risk: LOW_MEDIUM
- Treatment: Secondary route for HTML/page metadata and possible alternative download discovery.

## Planned outputs for v2.9C

- provider_dir: `data/raw/source_providers/otc_markets_stock_screener`
- raw_page_html: `data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_page.html`
- raw_csv: `data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_raw.csv`
- schema_probe_csv: `outputs/full_universe_source_acquisition/otc_markets_schema_probe_v2_9c.csv`
- sample_csv: `outputs/full_universe_source_acquisition/otc_markets_sample_v2_9c.csv`
- acquisition_json: `outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.json`
- acquisition_md: `outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.md`

## Expected schema candidates

- symbol_candidates: symbol, ticker, security symbol, otc symbol
- name_candidates: security name, company name, name, issuer name
- market_tier_candidates: market, market tier, tier, otc market
- country_candidates: country, country of incorporation, domicile
- security_type_candidates: security type, type, instrument type

## Acquisition controls for v2.9C

- Network download allowed only for OTC Markets planned routes.
- Preserve raw HTML and raw CSV exactly.
- Report URL, status code, content type, size and SHA256 for every request.
- Do not normalize into expanded_universe during acquisition.
- Do not rebuild expanded_universe.
- Do not overwrite active MVP outputs.
- Do not execute scoring.
- Do not call OpenAI.
- Do not call broker APIs.
- Do not launch full 59k universe.
- Write schema probe and sample only.

## Validation contract for v2.9D

- Validate row count of OTC raw CSV.
- Detect symbol/ticker field.
- Detect company/security name field.
- Detect market tier if present.
- Detect country if present.
- Detect instrument/security type if present.
- Normalize candidates conservatively.
- Compute duplicate exchange+ticker keys inside OTC source.
- Compute net-new exchange+ticker keys against expanded_universe_v2_8e.
- Classify OTC rows as candidate-provider rows until post-rebuild validation.
- Decide whether OTC is usable as provider, enrichment source, reference-only or deferred.
- Confirm whether OTC can unlock 15000 rows.

## Decision gate

- Minimum net-new rows to consider rebuild: 5800

### Rebuild allowed if

- OTC CSV download succeeds.
- Schema has usable symbol/ticker field.
- Rows can be normalized to canonical schema.
- Net-new exchange+ticker rows are meaningful.
- Duplicate keys are controlled.
- Instrument semantics are acceptable or conservatively classified.

### Rebuild not allowed if

- No usable symbol/ticker field.
- CSV is blocked, empty, HTML disguised as CSV, or not reproducible.
- Schema cannot be interpreted without brittle scraping.
- Rows are not securities or are too ambiguous.
- Licensing/usage constraints make storage unsuitable.

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: false
- Active outputs overwritten: false
- Expanded universe rebuilt: false
- Plan only: true

## Positives

- v2.9A route artifact found: outputs/full_universe_source_acquisition/next_official_provider_route_v2_9a.json
- v2.9A route status accepted: NEXT_OFFICIAL_PROVIDER_ROUTE_READY
- v2.9A route decision accepted: OTC_MARKETS_SELECTED_AS_NEXT_PROVIDER_ROUTE
- Selected provider accepted: otc_markets_stock_screener
- Current source input available: data/raw/expanded_universe/expanded_universe_v2_8e.csv
- Current source input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv

## Blockers

- No blockers detected.

## Warnings

- OTC Markets may include mixed instruments: equities, ADRs, preferreds, funds, rights, warrants or international securities.
- OTC market tier and instrument semantics must be validated before any rebuild.
- Rows must be treated as candidate-provider rows until v2.9D validation confirms usability.
- Do not use OTC data downstream before validation and optional isolated rebuild.
- Full 59k remains blocked until source reaches at least 50000 rows.

## Recommendation

Proceed to v2.9C controlled OTC Markets acquisition. Do not rebuild until v2.9D validates schema and net-new coverage.

Important: v2.9B is plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.