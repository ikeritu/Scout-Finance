# v2.11F - Validate Expanded Source With Cboe Europe

Status: **CBOE_EUROPE_EXPANDED_VALIDATION_COMPLETED**

Phase type: **validation-only**

Generated at UTC: `2026-07-08T08:33:21.861203+00:00`

## Hard guards

- Network download performed: false
- Raw files modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Inputs

- Expanded universe: `outputs\full_universe_source_acquisition\expanded_universe_v2_11e.csv`
- Candidates: `outputs\full_universe_source_acquisition\cboe_europe_normalized_candidates_v2_11e.csv`
- Exclusions: `outputs\full_universe_source_acquisition\expanded_universe_exclusions_v2_11e.csv`
- Rebuild report: `outputs\full_universe_source_acquisition\cboe_europe_rebuild_report_v2_11e.json`

## Counts

- Expected baseline rows from v2.11E: 9200
- Expected Cboe rows added from v2.11E: 21154
- Expected expanded rows from v2.11E: 30354
- Actual expanded rows: 30354
- Actual Cboe rows detected: 21154
- Accepted candidate rows: 21154
- Actual exclusion rows: 67089
- Duplicate exchange+ticker keys: 0
- Duplicate exchange+ticker rows: 0

## Thresholds

- First expansion threshold: 15000
- First expansion unlocked: True
- Full source threshold: 50000
- Full source unlocked: False
- Rows still needed for full source: 19646

## Provider breakdown

- cboe_europe_reference_data: 21154
- cboe_listed_symbols: 1193
- nasdaq_trader_nasdaqlisted: 3244
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359

## Failed checks

- blank_company_name_rows: expected `0`, actual `1193`, severity=warning

## Decision

- Decision: **CBOE_EUROPE_EXPANDED_SOURCE_VALIDATED_FIRST_EXPANSION_READY**
- Validation passed: **True**
- Recommended next phase: **v2.11G_CBOE_EUROPE_CLOSURE_REPORT**

## Important scope note

v2.11F validates the rebuilt expanded source only.

It does not rebuild, score, call OpenAI, call broker APIs, or launch the full 59k universe.

## Outputs

- `outputs\full_universe_source_acquisition\cboe_europe_expanded_validation_v2_11f.json`
- `outputs\full_universe_source_acquisition\cboe_europe_expanded_validation_report_v2_11f.md`
- `outputs\full_universe_source_acquisition\cboe_europe_expanded_integrity_checks_v2_11f.csv`
- `outputs\full_universe_source_acquisition\cboe_europe_provider_breakdown_v2_11f.csv`
- `outputs\full_universe_source_acquisition\cboe_europe_column_quality_v2_11f.csv`
