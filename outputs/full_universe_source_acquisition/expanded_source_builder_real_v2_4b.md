# Scout Finance ? v2.4B Expanded Source Builder Real

- Phase: v2.4B
- Method: expanded_source_builder_real_v1
- Created at: 2026-07-05T20:53:19+00:00
- Builder status: **EXPANDED_SOURCE_BUILD_PARTIAL_BELOW_TARGET_WITH_WARNINGS**
- Readiness score: **70/100**
- Raw rows: 12957
- Included rows: 5648
- Excluded rows: 7309
- Global duplicate exclusions: 0

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: false
- Expanded source written: true
- Active outputs overwritten: false

## Outputs

- expanded_source_csv: `data/raw/expanded_universe/expanded_universe_v2_4b.csv`
- exclusion_csv: `data/raw/expanded_universe/expanded_universe_exclusions_v2_4b.csv`
- breakdown_csv: `outputs/full_universe_source_acquisition/expanded_source_builder_real_breakdown_v2_4b.csv`

## Provider summaries

### nasdaq_trader_nasdaqlisted

- Raw rows: 5537
- Included rows: 3244
- Excluded rows: 2293
- Duplicate rows removed: 0

### nasdaq_trader_otherlisted

- Raw rows: 7420
- Included rows: 2404
- Excluded rows: 5016
- Duplicate rows removed: 0

## Exchange counts

- NASDAQ: 3244
- NYSE: 2122
- NYSE American: 265
- NYSE Arca: 13
- Cboe BZX: 4

## Instrument scope counts

- IN_SCOPE: 5578
- IN_SCOPE_ADR: 70

## Instrument type counts

- COMMON_STOCK: 5578
- ADR: 70

## Positives

- v2.4A acquisition artifact found: outputs/full_universe_source_acquisition/provider_source_acquisition_v2_4a.json
- v2.4A acquisition status usable: PROVIDER_SOURCE_ACQUISITION_COMPLETED_WITH_WARNINGS
- nasdaq_trader_nasdaqlisted: Provider source file readable.
- nasdaq_trader_otherlisted: Provider source file readable.

## Blockers

- No blockers detected.

## Warnings

- Expanded universe below first expansion target: 5648 < 15000
- Expanded universe below full-source threshold: 5648 < 50000

## Recommendation

Proceed to v2.4C expanded source validation real. Do not run scoring or full 59k.

Important: v2.4B builds an isolated expanded source only. It does not execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.