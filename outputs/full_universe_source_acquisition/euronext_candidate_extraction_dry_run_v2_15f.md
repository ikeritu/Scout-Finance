# v2.15F - Euronext Candidate Extraction Dry Run

Status: **EURONEXT_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_LOW_QUALITY_REBUILD_STILL_BLOCKED**

Phase type: **dry-run-only**

Generated at UTC: `2026-08-04T09:27:42.514021+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Dry-run summary

- Raw files reviewed: 11
- Strategy rows from v2.15E: 1361
- Allowed strategy rows from v2.15E: 254
- Table candidates from v2.15E: 11
- Raw extracted candidates before dedupe: 27
- Deduped extracted candidates: 7
- Unique ISINs: 7
- Quality bucket counts: `{'low': 7}`
- Source kind counts: `{'isin_context': 7}`
- Extraction quality: `low`
- Critical failed checks: 0

## Quality by raw file

- `euronext_advanced_reference_data.html` tables=0 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0
- `euronext_amsterdam_equities_list.html` tables=1 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0
- `euronext_brussels_equities_list.html` tables=1 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0
- `euronext_dublin_equities_list.html` tables=1 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0
- `euronext_lisbon_equities_list.html` tables=1 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0
- `euronext_live_all_equities.html` tables=1 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0
- `euronext_live_equities_overview.html` tables=3 table_candidates=0 context_candidates=27 total=27 high=0 medium=0 low=27
- `euronext_milan_equities_list.html` tables=1 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0
- `euronext_oslo_equities_list.html` tables=1 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0
- `euronext_paris_equities_list.html` tables=1 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0
- `euronext_static_reference_data.html` tables=0 table_candidates=0 context_candidates=0 total=0 high=0 medium=0 low=0

## Top candidates

- `BE0389555039` source=isin_context quality=low confidence=45 file=`euronext_live_equities_overview.html` name=`` symbol=``
- `FR0003500008` source=isin_context quality=low confidence=45 file=`euronext_live_equities_overview.html` name=`` symbol=``
- `FR0014005WN0` source=isin_context quality=low confidence=45 file=`euronext_live_equities_overview.html` name=`` symbol=``
- `IE00B0500264` source=isin_context quality=low confidence=45 file=`euronext_live_equities_overview.html` name=`` symbol=``
- `NL0000000107` source=isin_context quality=low confidence=45 file=`euronext_live_equities_overview.html` name=`` symbol=``
- `NO0007035327` source=isin_context quality=low confidence=45 file=`euronext_live_equities_overview.html` name=`` symbol=``
- `PTING0200002` source=isin_context quality=low confidence=45 file=`euronext_live_equities_overview.html` name=`` symbol=``

## Checks

- v2_15e_prep_exists: PASS (critical) - outputs\full_universe_source_acquisition\euronext_rebuild_candidate_prep_v2_15e.json
- raw_files_available: PASS (critical) - raw_files=11
- table_candidates_available: PASS (warning) - table_candidates=11
- source_strategy_available: PASS (critical) - strategy_rows=1361
- allowed_strategy_rows_review: PASS (warning) - allowed_strategy_rows=254
- dry_run_candidates_extracted: PASS (critical) - deduped_candidates=7
- unique_isins_detected: PASS (critical) - unique_isins=7
- canonical_dataset_not_modified: PASS (critical) - outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- no_net_new_filtering: PASS (critical) - net_new_filtering=False
- no_expanded_universe_rebuild: PASS (critical) - expanded_universe_rebuilt=False
- full_source_still_blocked: PASS (critical) - current_rows=38287
- medium_or_high_candidates_review: FAIL (warning) - medium_or_high_candidates=0
- table_based_candidates_review: FAIL (warning) - table_based_candidates=0
- context_only_not_enough_for_rebuild: FAIL (warning) - context_only_candidates=7; table_based_candidates=0

## Guards

- Network download performed in v2.15F: false
- Raw files downloaded in v2.15F: false
- Raw files modified after write: false
- Raw HTML parsed for dry run: true
- Candidate rows extracted to dry-run CSV: true
- Canonical dataset read: false
- Canonical dataset modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase extracts provisional raw candidates only.

It does not read or modify the canonical expanded universe, does not calculate definitive net-new rows, does not normalize securities, does not rebuild the expanded universe, does not score equities, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Recommended next phase

`v2.15F2 - Euronext Extraction Strategy Revision`
