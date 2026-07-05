# Scout Finance ? v2.4C Expanded Source Validation Real

- Phase: v2.4C
- Method: expanded_source_validation_real_v1
- Created at: 2026-07-05T21:12:47+00:00
- Validation status: **EXPANDED_SOURCE_REAL_VALIDATION_PARTIAL_BELOW_TARGET_WITH_WARNINGS**
- Readiness score: **70/100**
- Full source gate: **FULL_SOURCE_BLOCKED_BELOW_FIRST_EXPANSION_TARGET**
- Row count: 5648
- Exclusions count: 7309
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

## Schema validation

- Missing required columns: []
- Missing optional columns: []
- Empty tickers: 0
- Empty company names: 0
- Empty exchanges: 0
- Empty countries: 0
- Duplicate exchange+ticker keys: 0
- Invalid scope values: 0
- Invalid instrument type values: 0
- Invalid confidence values: 0

## Exchange counts

- NASDAQ: 3244
- NYSE: 2122
- NYSE American: 265
- NYSE Arca: 13
- Cboe BZX: 4

## Provider counts

- nasdaq_trader_nasdaqlisted: 3244
- nasdaq_trader_otherlisted: 2404

## Scope counts

- IN_SCOPE: 5578
- IN_SCOPE_ADR: 70

## Type counts

- COMMON_STOCK: 5578
- ADR: 70

## Positives

- v2.4B builder artifact found: outputs/full_universe_source_acquisition/expanded_source_builder_real_v2_4b.json
- v2.4B builder status usable: EXPANDED_SOURCE_BUILD_PARTIAL_BELOW_TARGET_WITH_WARNINGS
- Expanded source CSV readable: data/raw/expanded_universe/expanded_universe_v2_4b.csv
- Exclusions CSV readable: data/raw/expanded_universe/expanded_universe_exclusions_v2_4b.csv
- All required canonical columns are present.
- All optional canonical columns are present.
- No empty ticker values detected.
- No empty exchange values detected.
- No empty country values detected.
- No empty company names detected.
- No duplicate exchange+ticker keys detected.
- All instrument_scope values are valid.
- All instrument_type values are valid.
- All classification_confidence values are valid.

## Blockers

- No blockers detected.

## Warnings

- Expanded source below first expansion target: 5648 < 15000
- Expanded source below full-source threshold: 5648 < 50000

## Recommendation

Expanded source is structurally valid but does not unlock full 59k. Repeat v2.2C/v2.2E only as partial expanded-source validation.

Important: v2.4C validates the isolated expanded source only. It does not execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.