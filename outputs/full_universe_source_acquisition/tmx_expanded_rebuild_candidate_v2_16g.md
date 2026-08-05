# v2.16G - TMX Expanded Rebuild Candidate

Status: **TMX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_ADD1_FULL_SOURCE_STILL_BLOCKED**

Phase type: **expanded-rebuild-candidate-only**

Generated at UTC: `2026-08-05T20:17:18.044859+00:00`

## Current state

- Canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Canonical rows before: `38287`
- Candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_tmx_v2_16g.csv`
- Candidate rows after: `38288`
- Additions: `1`
- Full source threshold: `50000`
- Rows needed before: `11713`
- Rows needed after candidate: `11712`
- Source-to-50k before: `76.6%`
- Source-to-50k after candidate: `76.58%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Schema mapping

- Symbol column: `ticker`
- Name column: `company_name`
- Exchange column: `exchange`
- Source column: `source_provider`
- Country column: `country`
- Currency column: `currency`
- Field count: `33`

## Additions

- `IRR` `Irruptive Metals Corp.` exchange=`TSXV` confidence=`high` reason=`symbol_absent_from_canonical_high_confidence` row_index=`38288`

## Checks

- v2_16f_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_candidate_validation_against_canonical_v2_16f.json
- v2_16f_rows_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_candidate_validation_rows_v2_16f.csv
- v2_16f_status_valid: PASS (critical) — TMX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_REBUILD_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED
- v2_16f_recommended_g: PASS (critical) — v2.16G - TMX Expanded Rebuild Candidate
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- canonical_rows_expected: PASS (critical) — canonical_rows=38287 expected=38287
- canonical_symbol_column_detected: PASS (critical) — symbol_col=ticker
- canonical_name_column_detected: PASS (critical) — name_col=company_name
- canonical_exchange_column_detected: PASS (warning) — exchange_col=exchange
- selected_rebuild_candidates_loaded: PASS (critical) — selected=1
- additions_created: PASS (critical) — additions=1
- expected_single_tmx_addition: PASS (critical) — additions=1
- candidate_dataset_rows_expected: PASS (critical) — candidate_rows=38288 expected=38288
- candidate_dataset_written: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_tmx_v2_16g.csv
- additions_csv_written: PASS (critical) — outputs\full_universe_source_acquisition\tmx_expanded_rebuild_candidate_additions_v2_16g.csv
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- new_expanded_candidate_dataset_written: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_tmx_v2_16g.csv
- canonical_replacement_not_performed: PASS (critical) — expanded_universe_v2_14e.csv untouched
- full_source_still_blocked: PASS (critical) — 38288 < 50000
- network_not_used: PASS (critical) — network_download_performed=False
- endpoint_calls_not_performed: PASS (critical) — endpoint_calls_performed=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Candidate validation rows read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- New expanded candidate dataset written: true
- Canonical replacement performed: false
- Net-new filtering applied to canonical: false
- Expanded universe rebuilt as canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

TMX expanded rebuild candidate generated.

This phase creates a separate candidate dataset by appending the v2.16F recommended rebuild candidate row to a copy of the canonical expanded universe. It does not modify the canonical dataset and does not unblock full source.

## Recommended next phase

`v2.16H - TMX Expanded Validation`
