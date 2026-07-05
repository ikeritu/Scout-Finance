# Scout Finance ? v2.4A Controlled Provider Source Acquisition

- Phase: v2.4A
- Method: controlled_provider_source_acquisition_v1
- Created at: 2026-07-05T20:29:59+00:00
- Acquisition status: **PROVIDER_SOURCE_ACQUISITION_COMPLETED_WITH_WARNINGS**
- Readiness score: **85/100**
- Provider count: 2
- Total rows: 12957

## Controls

- Network download performed: true
- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Expanded source written: false

## Results

### nasdaq_trader_nasdaqlisted

- URL: https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt
- Raw path: `data/raw/source_providers/nasdaq_trader_nasdaqlisted/nasdaqlisted.txt`
- CSV path: `data/raw/source_providers/nasdaq_trader_nasdaqlisted/nasdaq_trader_nasdaqlisted.csv`
- Downloaded: True
- Converted: True
- Rows: 5537
- Columns: 8
- Ignored lines: 1

### nasdaq_trader_otherlisted

- URL: https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt
- Raw path: `data/raw/source_providers/nasdaq_trader_otherlisted/otherlisted.txt`
- CSV path: `data/raw/source_providers/nasdaq_trader_otherlisted/nasdaq_trader_otherlisted.csv`
- Downloaded: True
- Converted: True
- Rows: 7420
- Columns: 8
- Ignored lines: 1

## Positives

- nasdaq_trader_nasdaqlisted: Source downloaded.
- nasdaq_trader_nasdaqlisted: Pipe-delimited source converted to CSV.
- nasdaq_trader_otherlisted: Source downloaded.
- nasdaq_trader_otherlisted: Pipe-delimited source converted to CSV.

## Blockers

- No blockers detected.

## Warnings

- nasdaq_trader_nasdaqlisted: Ignored non-data lines: 1
- nasdaq_trader_otherlisted: Ignored non-data lines: 1

## Recommendation

Rerun v2.3E, then rerun v2.3F to validate local provider CSVs.