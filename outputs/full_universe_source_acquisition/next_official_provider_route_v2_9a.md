# Scout Finance ? v2.9A Next Official Provider Route

- Phase: v2.9A
- Method: next_official_provider_route_v1
- Created at: 2026-07-07T10:27:45+00:00
- Route status: **NEXT_OFFICIAL_PROVIDER_ROUTE_READY**
- Readiness score: **92/100**
- Route decision: **OTC_MARKETS_SELECTED_AS_NEXT_PROVIDER_ROUTE**
- Selected provider: **otc_markets_stock_screener**
- Recommended next phase: **v2.9B ? OTC Markets Acquisition Plan**

## Current state

- Current expanded universe: `data/raw/expanded_universe/expanded_universe_v2_8e.csv`
- Current expanded rows: 9200
- Current exclusions rows: 10056
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Rows needed first expansion: 5800
- Rows needed full source: 40800
- First expansion unlocked: False
- Full source unlocked: False

## Route candidates

### 1. OTC Markets Stock Screener

- Provider ID: `otc_markets_stock_screener`
- Source URL: `https://www.otcmarkets.com/research/stock-screener`
- Download candidate URL: `https://www.otcmarkets.com/research/stock-screener/api/downloadCSV?ce=true&sortField=volume&sortOrder=desc`
- Type: official_otc_markets_stock_screener_csv_candidate
- Expected value: HIGH_FOR_15000_THRESHOLD
- Risk: MEDIUM
- Expected coverage: Large OTC universe; may be enough to exceed 15000 if usable and net-new.
- Why: After Nasdaq Trader, SEC and Cboe, the remaining gap to 15000 is 5800 rows. OTC Markets has a broad official screener and download route candidate.
- Planned treatment: Plan controlled acquisition first. Preserve raw CSV. Validate schema and net-new exchange+ticker rows before any rebuild.
- Decision: **SELECTED_PRIMARY_ROUTE**

### 2. Nasdaq Stock Screener

- Provider ID: `nasdaq_stock_screener`
- Source URL: `https://www.nasdaq.com/market-activity/stocks/screener`
- Download candidate URL: ``
- Type: official_or_semi_official_nasdaq_screener_review
- Expected value: LOW_TO_MEDIUM
- Risk: MEDIUM_HIGH
- Expected coverage: May overlap heavily with Nasdaq Trader and SEC.
- Why: Could provide names/metadata but likely not enough net-new after existing Nasdaq/SEC routes.
- Planned treatment: Keep as fallback or enrichment route.
- Decision: **FALLBACK_ROUTE**

### 3. NYSE Deep JS Payload Review

- Provider ID: `nyse_deep_js_payload_review`
- Source URL: ``
- Download candidate URL: ``
- Type: deferred_deep_js_route
- Expected value: UNKNOWN
- Risk: HIGH
- Expected coverage: Unknown until deep JS payload route is solved.
- Why: Previously deferred because v2.5G required deep JS payload review.
- Planned treatment: Do not reopen until OTC route is resolved or explicitly prioritized.
- Decision: **DEFERRED_REQUIRES_DEEP_JS_PAYLOAD_REVIEW**

### 4. OpenFIGI / FIGI Symbology

- Provider ID: `openfigi_symbology`
- Source URL: `https://www.openfigi.com/`
- Download candidate URL: ``
- Type: identifier_enrichment_or_api_route
- Expected value: MEDIUM_FOR_ENRICHMENT_LOW_FOR_BULK_SOURCE
- Risk: MEDIUM_HIGH
- Expected coverage: Potentially useful for identifier enrichment, but bulk universe acquisition requires API and limits review.
- Why: Good candidate for enrichment, not necessarily the next bulk source provider.
- Planned treatment: Defer as enrichment route unless source expansion stalls.
- Decision: **REFERENCE_OR_ENRICHMENT_ROUTE_REQUIRES_API_CONSTRAINT_REVIEW**

## Planned outputs for v2.9B/v2.9C

- provider_dir: `data/raw/source_providers/otc_markets_stock_screener`
- route_plan_json: `outputs/full_universe_source_acquisition/otc_markets_acquisition_plan_v2_9b.json`
- route_plan_md: `outputs/full_universe_source_acquisition/otc_markets_acquisition_plan_v2_9b.md`
- raw_csv_target: `data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_raw.csv`
- schema_probe_csv: `outputs/full_universe_source_acquisition/otc_markets_schema_probe_v2_9c.csv`
- acquisition_json: `outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.json`
- acquisition_md: `outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.md`

## Planned controls

- v2.9B must be plan-only.
- v2.9C may download only OTC Markets route candidates selected in v2.9B.
- Preserve raw CSV exactly.
- Report URL, status code, content type, size and SHA256.
- Do not rebuild expanded_universe in acquisition phase.
- Do not overwrite active MVP outputs.
- Do not run scoring.
- Do not call OpenAI.
- Do not call broker APIs.
- Do not launch full 59k universe.
- Classify OTC rows conservatively until post-acquisition validation.

## Validation questions

- How many rows are available in OTC Markets CSV?
- Which columns are present?
- Is there a clear ticker/symbol field?
- Is there a company/security name field?
- Is market tier available: OTCQX, OTCQB, OTCID, Pink Limited, etc.?
- Is country available?
- How many exchange+ticker keys are net-new against expanded_universe_v2_8e?
- Are rows equities, ADRs, funds, preferreds, warrants, or mixed instruments?
- Can OTC Markets unlock 15000 rows safely?
- Should OTC Markets be primary source, candidate-provider source, enrichment source, or deferred?

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

- v2.8G Cboe closure artifact found: outputs/full_universe_source_acquisition/expanded_source_with_cboe_closure_report_v2_8g.json
- v2.8G closure status accepted: EXPANDED_SOURCE_WITH_CBOE_CLOSED_USEFUL_BUT_NOT_ENOUGH
- v2.8G closure decision accepted: CBOE_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH
- Current source input available: data/raw/expanded_universe/expanded_universe_v2_8e.csv
- Current source input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv

## Blockers

- No blockers detected.

## Warnings

- Current expanded source remains below first expansion threshold: 9200 < 15000
- Current expanded source remains below full-source threshold: 9200 < 50000
- OTC Markets route may include OTCQX, OTCQB, OTCID, Pink Limited, international ordinary shares, ADRs and other securities; classification must be conservative.
- OTC Markets CSV schema and licensing/usage constraints must be checked in v2.9B/v2.9C before rebuild.
- Do not mix OTC candidates into main universe until a dedicated validation phase confirms schema, net-new rows, and instrument semantics.

## Recommendation

Proceed to v2.9B with OTC Markets acquisition plan. Do not download or rebuild until v2.9B defines the controlled acquisition contract.

Important: v2.9A is route-selection plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.