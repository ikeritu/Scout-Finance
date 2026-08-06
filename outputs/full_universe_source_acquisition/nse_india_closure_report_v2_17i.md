# v2.17I - NSE India Closure Report

Status: **NSE_INDIA_CLOSURE_COMPLETED_VALIDATED_CANDIDATE_RETAINED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **provider-closure-report-only**

Generated at UTC: `2026-08-06T14:44:11.550838+00:00`

## Executive summary

NSE India provider route is closed.

The route produced a validated expanded candidate dataset but did not replace or modify the active canonical dataset. The safe NSE India delta contains `2013` rows, taking the candidate dataset to `40300` rows. The full-source threshold remains blocked because the candidate is still below `50000` rows.

## Final provider result

- Provider: `NSE India`
- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Validated candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv`
- Validated candidate rows: `40300`
- Safe delta rows: `2013`
- Rows needed after candidate: `9700`
- Candidate completion toward 50k: `80.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`
- Active canonical replaced: `false`
- Canonical SHA before: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Canonical SHA after: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`

## Phase ledger

- `v2.17B`: PASS — `NSE_INDIA_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_FULL_SOURCE_STILL_BLOCKED`
- `v2.17C`: PASS — `NSE_INDIA_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED`
- `v2.17D`: PASS — `NSE_INDIA_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_CANDIDATE_EXTRACTION_READY_FULL_SOURCE_STILL_BLOCKED`
- `v2.17E`: PASS — `NSE_INDIA_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_CANONICAL_COMPARISON_STILL_BLOCKED`
- `v2.17F`: PASS — `NSE_INDIA_CANDIDATE_VALIDATION_AGAINST_CANONICAL_DRY_RUN_COMPLETED_NET_NEW_FOUND_REBUILD_CANDIDATE_READY_FULL_SOURCE_STILL_BLOCKED`
- `v2.17G`: PASS — `NSE_INDIA_EXPANDED_REBUILD_CANDIDATE_COMPLETED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED`
- `v2.17H`: PASS — `NSE_INDIA_EXPANDED_VALIDATION_COMPLETED_CANDIDATE_VALID_CLOSURE_READY_FULL_SOURCE_STILL_BLOCKED`

## Closure checks

- all_phase_reports_exist: PASS (critical) — v2.17B-H JSON reports
- all_phase_reports_pass_closure_assessment: PASS (critical) — {'v2.17B': 'PASS', 'v2.17C': 'PASS', 'v2.17D': 'PASS', 'v2.17E': 'PASS', 'v2.17F': 'PASS', 'v2.17G': 'PASS', 'v2.17H': 'PASS'}
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- canonical_rows_expected: PASS (critical) — canonical_rows=38287
- canonical_sha_unchanged: PASS (critical) — canonical sha unchanged during closure
- expanded_candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- expanded_candidate_rows_expected: PASS (critical) — candidate_rows=40300
- safe_delta_rows_expected: PASS (critical) — delta_rows=2013
- delta_rows_equal_promotions: PASS (critical) — delta=2013 promotions=2013
- candidate_schema_matches_canonical: PASS (critical) — canonical_cols=33 candidate_cols=33
- h_report_status_expected: PASS (critical) — NSE_INDIA_EXPANDED_VALIDATION_COMPLETED_CANDIDATE_VALID_CLOSURE_READY_FULL_SOURCE_STILL_BLOCKED
- h_report_recommends_closure: PASS (critical) — v2.17I - NSE India Closure Report
- promotion_policy_qa_rows_expected: PASS (critical) — promotion_policy_qa_rows=2013
- delta_integrity_rows_present: PASS (critical) — delta_integrity_rows=5
- schema_mapping_rows_present: PASS (critical) — schema_mapping_rows=33
- full_source_still_blocked: PASS (critical) — 40300 < 50000
- rows_needed_after_candidate_expected: PASS (critical) — rows_needed_after_candidate=9700
- network_not_used: PASS (critical) — network_download_performed=False
- canonical_dataset_read: PASS (critical) — canonical_dataset_read=True
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- expanded_universe_not_rebuilt_as_canonical: PASS (critical) — expanded_universe_rebuilt_as_canonical=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guard summary

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Phase reports v2.17B-H read: true
- Canonical dataset read: true
- Candidate dataset read: true
- Closure report written: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Validated candidate retained: true
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Closure decision

NSE India is closed as a successful provider route that created and validated a conservative candidate expansion. It should remain as a validated candidate dataset until a separately controlled promotion decision is opened.

## Next steps

- P1: Select next provider route after NSE India closure — `v2.18A - Next Provider Route Selection` — TWSE + TPEx Taiwan
- P2: Keep NSE India candidate dataset as validated candidate only — `No active canonical replacement in v2.17I` — NSE India
- P3: Reserve quick-win provider route — `Fallback after v2.18A if needed` — ASX Australia

## Recommended next phase

`v2.18A - Next Provider Route Selection`

## Recommended next provider candidate

`TWSE + TPEx Taiwan`

## Reserve provider candidate

`ASX Australia`
