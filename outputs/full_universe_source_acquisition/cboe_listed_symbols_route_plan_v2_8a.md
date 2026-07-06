# Scout Finance ? v2.8A Cboe Listed Symbols Route Plan

- Phase: v2.8A
- Method: cboe_listed_symbols_route_plan_v1
- Created at: 2026-07-06T20:43:11+00:00
- Plan status: **CBOE_LISTED_SYMBOLS_ROUTE_PLAN_READY**
- Readiness score: **90/100**
- Recommended next phase: **v2.8B ? Cboe Listed Symbols Acquisition Real**

## Current state

- Current expanded universe: `data/raw/expanded_universe/expanded_universe_v2_7b.csv`
- Current expanded rows: 8007
- Current exclusions rows: 10056
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Rows needed first expansion: 6993
- Rows needed full source: 41993

## Route candidates

### 1. Cboe U.S. Equities Listed Symbols

- Route ID: `cboe_us_equities_listed_symbols`
- Source URL: `https://www.cboe.com/us/equities/market_statistics/listed_symbols/`
- Type: official_cboe_listed_symbols
- Expected download options: CSV, XML
- Expected value: MEDIUM
- Risk: MEDIUM
- Why: Official Cboe listed-symbol page. Most relevant if it provides securities actually listed on Cboe.
- Planned treatment: Acquire raw CSV/XML in isolated provider folder, normalize only after schema detection, then validate net new rows against expanded_universe_v2_7b.

### 2. Cboe U.S. Equities Symbols Traded

- Route ID: `cboe_us_equities_symbols_traded`
- Source URL: `https://www.cboe.com/us/equities/market_statistics/symbols_traded/`
- Type: official_cboe_symbols_traded_reference
- Expected download options: CSV, XML
- Expected value: LOW_TO_MEDIUM
- Risk: MEDIUM
- Why: Official Cboe symbols-traded reference page. Useful for reference coverage, but may include symbols traded on Cboe rather than listed by Cboe.
- Planned treatment: Acquire only as secondary/reference route unless listed-symbols route fails or has insufficient schema.

## Planned outputs for v2.8B

- provider_dir: `data/raw/source_providers/cboe_listed_symbols`
- raw_listed_symbols_file: `data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.csv`
- raw_symbols_traded_file: `data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_raw.csv`
- normalized_csv: `data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_normalized.csv`
- acquisition_json: `outputs/full_universe_source_acquisition/cboe_listed_symbols_acquisition_real_v2_8b.json`
- acquisition_md: `outputs/full_universe_source_acquisition/cboe_listed_symbols_acquisition_real_v2_8b.md`
- schema_probe_csv: `outputs/full_universe_source_acquisition/cboe_listed_symbols_schema_probe_v2_8b.csv`

## Expected normalized columns

- `ticker`
- `company_name`
- `exchange`
- `country`
- `source_provider`
- `source_file`
- `instrument_type`
- `instrument_scope`
- `classification_confidence`
- `classification_reason`
- `sector`
- `industry`
- `market_cap`
- `raw_symbol`
- `raw_name`
- `raw_exchange`
- `raw_listing_market`

## Acquisition controls for v2.8B

- No OpenAI.
- No broker.
- No scoring recalculation.
- No full 59k universe launch.
- No active output overwrite.
- No expanded_universe rebuild.
- Network download allowed only for Cboe official route candidates.
- Raw files must be preserved.
- Normalized CSV is written only if schema is detected confidently.
- All downloaded URLs, status codes, sizes and SHA256 hashes must be reported.

## Validation questions for v2.8C

- How many rows are present in each raw Cboe route?
- Which fields are available in CSV/XML?
- Does listed_symbols differ from symbols_traded?
- How many exchange+ticker keys are net new against expanded_universe_v2_7b?
- Are rows true listed securities or merely tradable symbols?
- Should Cboe be used as a primary provider, enrichment source, or be deferred?

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

- v2.7D SEC closure artifact found: outputs/full_universe_source_acquisition/expanded_source_with_sec_closure_report_v2_7d.json
- v2.7D closure status accepted: EXPANDED_SOURCE_WITH_SEC_CLOSED_USEFUL_BUT_NOT_ENOUGH
- v2.7D closure decision accepted: SEC_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH
- Required current source file available: data/raw/expanded_universe/expanded_universe_v2_7b.csv
- Required current source file available: data/raw/expanded_universe/expanded_universe_exclusions_v2_7b.csv

## Blockers

- No blockers detected.

## Warnings

- Cboe route may add limited rows because current universe already includes Cboe BZX rows from Nasdaq Trader otherlisted.
- Cboe Listed Symbols may be narrower than Symbols Traded; v2.8B should preserve raw files and report row/schema before any rebuild.
- Full 59k remains blocked until enough additional official provider rows are validated.

## Recommendation

Proceed to v2.8B with controlled acquisition of Cboe official CSV/XML routes. Do not rebuild until v2.8C validates net new coverage.

Important: v2.8A is plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.