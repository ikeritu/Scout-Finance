# Scout Finance ? v2.3F Expanded Source Validation

- Phase: v2.3F
- Method: expanded_source_validation_v1
- Created at: 2026-07-05T20:30:14+00:00
- Validation status: **EXPANDED_SOURCE_VALIDATION_READY_WITH_WARNINGS**
- Readiness score: **70/100**
- Provider files found: 2
- Valid provider files: 2
- Total rows: 12957
- Target first expansion rows: 15000
- Minimum full source rows: 50000

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: false
- Active outputs overwritten: false
- Expanded source written: false

## Provider results

### nasdaq_trader_nasdaqlisted

- Status: PROVIDER_FILE_VALID
- Path: `data/raw/source_providers/nasdaq_trader_nasdaqlisted/nasdaq_trader_nasdaqlisted.csv`
- Rows: 5537
- Columns: 8
- Ticker-like column: Symbol
- Empty tickers: 0
- Duplicate tickers: 0
- Unique tickers: 5537

### nasdaq_trader_otherlisted

- Status: PROVIDER_FILE_VALID
- Path: `data/raw/source_providers/nasdaq_trader_otherlisted/nasdaq_trader_otherlisted.csv`
- Rows: 7420
- Columns: 8
- Ticker-like column: ACT Symbol
- Empty tickers: 0
- Duplicate tickers: 0
- Unique tickers: 7420

## Positives

- v2.3E builder artifact found: outputs/full_universe_source_acquisition/expanded_source_builder_skeleton_v2_3e.json
- v2.3E builder status usable: EXPANDED_SOURCE_BUILDER_SKELETON_READY
- Provider scan CSV found: outputs/full_universe_source_acquisition/expanded_source_builder_provider_scan_v2_3e.csv
- Local provider CSV files found: 2

## Blockers

- No blockers detected.

## Warnings

- Expanded source rows below first expansion target: 12957 < 15000

## Recommendation

Proceed according to validation status. Do not run full 59k unless full-source gate is later unlocked.

Important: v2.3F is validation only. It does not download data, execute scoring, call OpenAI, call a broker, write an expanded source, or launch full 59k.