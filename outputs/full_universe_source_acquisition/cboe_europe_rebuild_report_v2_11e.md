# v2.11E — Rebuild Expanded Source With Cboe Europe

Status: **CBOE_EUROPE_REBUILD_COMPLETED**

Phase type: **rebuild-only**

Generated at UTC: `2026-07-08T08:17:54.038436+00:00`

## Hard guards

- Network download performed: false
- Raw files modified: false
- Normalization performed: true
- Net-new filtering performed: true
- Expanded universe rebuilt: true
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Inputs

- Baseline universe: `data\raw\expanded_universe\expanded_universe_v2_8e.csv`
- Validation decision: `outputs\full_universe_source_acquisition\cboe_europe_validation_decision_v2_11d.csv`
- Validation profile: `outputs\full_universe_source_acquisition\cboe_europe_csv_profile_v2_11d.csv`
- Raw dir: `outputs\full_universe_source_acquisition\raw\cboe_europe_v2_11c`

## Validation gate

- v2.11D decision: `CBOE_EUROPE_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW`
- Rebuild allowed by validation: `True`

## Rebuild summary

- Baseline rows: 9200
- Selected Cboe Europe CSV files: 6
- Candidate rows reviewed: 88243
- Cboe Europe rows added: 21154
- Exclusions: 67089
- New expanded rows: 30354
- Duplicate exchange+ticker keys: 0

## Thresholds

- First expansion threshold: 15000
- First expansion unlocked: True
- Full source threshold: 50000
- Full source unlocked: False

## Exclusion breakdown

- BASELINE_TICKER_ALREADY_PRESENT: 552
- DUPLICATE_CBOE_BATS_NAME: 66362
- NOT_LIVE: 175

## Important scope note

v2.11E creates a rebuilt expanded source candidate only.

It does not score, call OpenAI, call broker APIs, launch the full 59k universe, or validate final scoring readiness.

v2.11F must validate the rebuilt output before any downstream use.

## Outputs

- `outputs\full_universe_source_acquisition\expanded_universe_v2_11e.csv`
- `outputs\full_universe_source_acquisition\expanded_universe_exclusions_v2_11e.csv`
- `outputs\full_universe_source_acquisition\cboe_europe_normalized_candidates_v2_11e.csv`
- `outputs\full_universe_source_acquisition\cboe_europe_rebuild_report_v2_11e.json`
- `outputs\full_universe_source_acquisition\cboe_europe_rebuild_report_v2_11e.md`
