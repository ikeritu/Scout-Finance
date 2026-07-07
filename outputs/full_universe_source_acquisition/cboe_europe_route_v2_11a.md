# Scout Finance ? v2.11A Cboe Europe Route

- Phase: v2.11A
- Method: cboe_europe_route_plan_v1
- Created at: 2026-07-07T22:08:30+00:00
- Route status: **CBOE_EUROPE_ROUTE_READY**
- Readiness score: **92/100**
- Route decision: **CBOE_EUROPE_SELECTED_AS_NEXT_PROVIDER_ROUTE**
- Recommended next phase: **v2.11B ? Cboe Europe Acquisition Plan**

## Provider

- Provider ID: `cboe_europe_reference_data`
- Provider dir: `data/raw/source_providers/cboe_europe_reference_data`
- Primary route: `cboe_europe_reference_data_page_probe`
- Preferred files: `Live Symbols CSV`, `Live Symbols Enhanced CSV`
- Markets/services to probe: BXE, CXE, DXE, TRF EU, TRF UK, SIS

## Current state

- Current expanded rows: 9200
- Current exclusions rows: 10056
- Rows needed first expansion: 5800
- Rows needed full source: 40800

## Route candidates

### 1. Cboe Europe Reference Data page

- Route ID: `cboe_europe_reference_data_page_probe`
- URL: `https://www.cboe.com/europe/equities/support/reference_data/`
- Method: GET
- Expected content type: text/html
- Expected value: HIGH
- Risk: LOW_MEDIUM
- Network allowed in: v2.11B/v2.11C
- Treatment: Discover official Live Symbols CSV and Live Symbols Enhanced CSV links from the Cboe Europe Reference Data page.

### 2. Cboe Europe Live Symbols CSV files

- Route ID: `cboe_europe_live_symbols_csv`
- URL: `DISCOVER_FROM_REFERENCE_DATA_PAGE`
- Method: GET
- Expected content type: text/csv
- Expected value: HIGH
- Risk: LOW
- Network allowed in: v2.11C
- Treatment: Download only discovered official CSV files for BXE/CXE/DXE/TRF EU/TRF UK/SIS if present.

### 3. Cboe Europe Live Symbols Enhanced CSV files

- Route ID: `cboe_europe_live_symbols_enhanced_csv`
- URL: `DISCOVER_FROM_REFERENCE_DATA_PAGE`
- Method: GET
- Expected content type: text/csv
- Expected value: HIGH
- Risk: LOW
- Network allowed in: v2.11C
- Treatment: Prefer enhanced CSV if schema includes richer fields for symbol, name, currency, MIC, country, supported services or asset classification.

### 4. Cboe Europe Symbols Traded pages

- Route ID: `cboe_europe_symbols_traded_pages`
- URL: `CXE/BXE/DXE/TRF symbols_traded pages`
- Method: GET
- Expected content type: text/html
- Expected value: MEDIUM
- Risk: MEDIUM
- Network allowed in: v2.11C
- Treatment: Fallback page probe only if Reference Data page does not expose direct CSV files.

## Planned symbol pages

- CXE: `https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=cxe` -> `data/raw/source_providers/cboe_europe_reference_data/cboe_europe_cxe_symbols_traded_page.html`
- BXE: `https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=bxe` -> `data/raw/source_providers/cboe_europe_reference_data/cboe_europe_bxe_symbols_traded_page.html`
- DXE: `https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=dxe` -> `data/raw/source_providers/cboe_europe_reference_data/cboe_europe_dxe_symbols_traded_page.html`
- TRF: `https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=trf` -> `data/raw/source_providers/cboe_europe_reference_data/cboe_europe_trf_symbols_traded_page.html`

## Expected schema candidates

- symbol: symbol, bats_name, ticker, instrument, isin
- issuer_name: company, company_name, name, issuer, security_name
- market: market, exchange, book, venue, mic, primary_market
- asset_class: asset_class, asset type, security_type, instrument_type
- currency: currency, trading_currency, price_currency
- country: country, country_of_incorporation, domicile
- isin: isin, isin_code

## Validation questions

- Does Cboe Europe expose stable official Live Symbols CSV files?
- Are CSV files available for BXE, CXE, DXE, TRF EU, TRF UK and/or SIS?
- Does enhanced CSV contain richer symbol/name/MIC/country/currency fields?
- How many rows exist before net-new filtering?
- How many exchange+ticker or MIC+ticker keys are net-new against expanded_universe_v2_8e?
- Are rows ordinary shares, ETFs, funds, ETCs or mixed instruments?
- Can Cboe Europe rows be normalized conservatively without brittle scraping?
- Does Cboe Europe unlock the 15000-row first expansion threshold?
- Should Cboe Europe be source provider, candidate provider, enrichment, reference-only or deferred?

## Decision gate

- Minimum net-new rows to consider rebuild: 5800
- Rebuild allowed only after v2.11D validates schema, duplicate control and net-new rows.
- Full 59k remains blocked until source reaches at least 50000 rows.

## Outputs

- Route candidates CSV: `outputs/full_universe_source_acquisition/cboe_europe_route_candidates_v2_11a.csv`
- Planned outputs CSV: `outputs/full_universe_source_acquisition/cboe_europe_planned_outputs_v2_11a.csv`
- Route JSON: `outputs/full_universe_source_acquisition/cboe_europe_route_v2_11a.json`
- Route report: `outputs/full_universe_source_acquisition/cboe_europe_route_v2_11a.md`

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
- Route selection only: true

## Positives

- v2.10G LSE closure artifact found: outputs/full_universe_source_acquisition/lse_closure_report_v2_10g.json
- v2.10G closure status accepted: LSE_CLOSED_ACCESSIBLE_BUT_NOT_USABLE_FOR_REBUILD
- v2.10G closure decision accepted: LSE_CLOSED_NO_REBUILD_FALLBACK_REQUIRED
- v2.10G recommended next phase accepted: v2.11A ? Cboe Europe Route
- Current source input available: data/raw/expanded_universe/expanded_universe_v2_8e.csv
- Current source input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv

## Blockers

- No blockers detected.

## Warnings

- v2.11A is route-selection only; no Cboe Europe data is downloaded in this phase.
- Cboe Europe may include non-US symbols, multiple venues, MIC semantics and duplicate instruments across books.
- European symbol semantics must not be merged blindly with US tickers.
- Rows from TRF/APA/reporting routes may need separate classification from lit order book symbols.
- Full 59k remains blocked until source reaches at least 50000 rows.

## Recommendation

Proceed to v2.11B Cboe Europe Acquisition Plan. Do not download until controlled acquisition contract is defined.

Important: v2.11A is route-selection only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.