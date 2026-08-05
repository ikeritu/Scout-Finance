# v2.16H - TMX Expanded Validation

Status: **TMX_EXPANDED_VALIDATION_COMPLETED_CANDIDATE_ADD1_VALID_CANONICAL_STILL_UNCHANGED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **expanded-candidate-validation-only**

Generated at UTC: `2026-08-05T21:01:24.384062+00:00`

## Current state

- Canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_tmx_v2_16g.csv`
- Canonical rows: `38287`
- Candidate rows: `38288`
- Delta: `1`
- Full source threshold: `50000`
- Rows needed after candidate: `11712`
- Source-to-50k after candidate: `76.58%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Validation summary

- v2.16G status: `TMX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_ADD1_FULL_SOURCE_STILL_BLOCKED`
- v2.16G recommended next phase: `v2.16H - TMX Expanded Validation`
- Fieldnames match: `True`
- Symbol column: `ticker`
- Exchange column: `exchange`
- Name column: `company_name`
- Canonical prefix mismatch count: `0`
- Canonical expected key count: `0`
- Candidate expected key count: `1`
- Appended rows: `1`
- Appended expected key count: `1`
- Expected candidate names: `['Irruptive Metals Corp.']`
- Critical failed checks: `0`

## Validated addition

- `IRR` `Irruptive Metals Corp.` exchange=`TSXV`

## Checks

- v2_16g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_expanded_rebuild_candidate_v2_16g.json
- v2_16g_additions_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_expanded_rebuild_candidate_additions_v2_16g.csv
- v2_16g_audit_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_expanded_rebuild_candidate_row_audit_v2_16g.csv
- v2_16g_status_valid: PASS (critical) — TMX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_ADD1_FULL_SOURCE_STILL_BLOCKED
- v2_16g_recommended_h: PASS (critical) — v2.16H - TMX Expanded Validation
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_tmx_v2_16g.csv
- fieldnames_match: PASS (critical) — canonical_fields=33 candidate_fields=33
- symbol_column_detected: PASS (critical) — symbol_col=ticker
- exchange_column_detected: PASS (critical) — exchange_col=exchange
- name_column_detected: PASS (critical) — name_col=company_name
- canonical_rows_expected: PASS (critical) — canonical_rows=38287 expected=38287
- candidate_rows_expected: PASS (critical) — candidate_rows=38288 expected=38288
- delta_expected_plus_one: PASS (critical) — delta=1 expected=1
- additions_count_expected_one: PASS (critical) — additions=1
- audit_rows_present: PASS (critical) — audit_rows=1
- canonical_prefix_unchanged_in_candidate: PASS (critical) — prefix_mismatch_count=0; examples=[]
- canonical_expected_key_absent: PASS (critical) — ('IRR', 'TSXV') canonical_count=0
- candidate_expected_key_present_once: PASS (critical) — ('IRR', 'TSXV') candidate_count=1
- appended_expected_key_present_once: PASS (critical) — ('IRR', 'TSXV') appended_count=1
- appended_rows_count_expected_one: PASS (critical) — appended_rows=1
- expected_name_present: PASS (critical) — names=['Irruptive Metals Corp.']
- full_source_still_blocked: PASS (critical) — 38288 < 50000
- canonical_dataset_not_modified_by_phase: PASS (critical) — canonical_dataset_modified=False
- candidate_not_promoted_to_canonical: PASS (critical) — canonical_replacement_performed=False
- network_not_used: PASS (critical) — network_download_performed=False
- endpoint_calls_not_performed: PASS (critical) — endpoint_calls_performed=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.16G report read: true
- v2.16G additions read: true
- Canonical dataset read: true
- Candidate dataset read: true
- Candidate dataset validated: true
- Canonical dataset modified: false
- Canonical replacement performed: false
- Candidate promoted to canonical: false
- Expanded universe rebuilt as canonical: false
- New expanded dataset written: false
- Net-new filtering applied to canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

TMX expanded candidate validation completed.

The v2.16G candidate dataset is validated as a separate candidate artifact with one additional TMX row. The canonical dataset remains the active canonical dataset and is not replaced in this phase.

## Recommended next phase

`v2.16I - TMX Closure Report`
