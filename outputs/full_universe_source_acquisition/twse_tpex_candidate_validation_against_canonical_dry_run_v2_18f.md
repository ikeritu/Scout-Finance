# v2.18F - TWSE + TPEx Candidate Validation Against Canonical Dry Run

Status: **TWSE_TPEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_CANONICAL_BUCKETS_READY_FOR_EXPANDED_REBUILD_CANDIDATE_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **candidate-validation-against-canonical-dry-run-only**

Generated at UTC: `2026-08-11T12:17:10.082230+00:00`

## Executive summary

v2.18F validates TWSE + TPEx extracted candidates against the active canonical dataset in dry-run mode.

This phase reads canonical only for comparison. It does not write an expanded candidate dataset, does not modify canonical, does not replace the active canonical, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Validated candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv`
- Validated candidate rows: `40300`
- Final target candidates: `50000`
- Rows needed before TWSE: `9700`
- Projected candidate rows if all net-new are added: `40996`
- Projected rows needed after TWSE: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

- Candidates validated: `1075`
- Existing: `0`
- Possible existing: `379`
- Potential net-new: `696`
- Net-new count: `696`
- Review required: `379`
- Match evidence rows: `382`
- Critical failed checks: `0`

## Bucket summary

- `existing`: 0 (0.0%)
- `possible_existing`: 379 (35.2558%)
- `potential_net_new`: 696 (64.7442%)

## Canonical detection profile

- Symbol columns: `ticker|symbol`
- Name columns: `company_name|security_name`
- Provider columns: `source_provider|provider_precedence|provider`
- Exchange columns: `exchange|raw_exchange|mic`
- Country columns: `country`
- Symbol index keys: `37545`
- Name index keys: `24807`

## Next actions

- Phigh `TWSE` — proceed_to_expanded_rebuild_candidate — v2.18G - TWSE + TPEx Expanded Rebuild Candidate
- Pmedium `TWSE` — track_possible_existing_as_non_net_new — v2.18G - TWSE + TPEx Expanded Rebuild Candidate

## Checks

- v2_18e_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_candidate_extraction_dry_run_v2_18e.json
- v2_18e_status_expected: PASS (critical) — TWSE_TPEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_TWSE_CANDIDATES_READY_FOR_CANONICAL_VALIDATION_DRY_RUN_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18e_candidates_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_candidate_extraction_candidates_v2_18e.csv
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- validated_candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- validated_candidate_rows_expected: PASS (critical) — validated_candidate_rows=40300
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9700
- candidate_count_matches_v2_18e_report: PASS (critical) — candidates_csv=1075 report=1075
- candidate_ids_unique: PASS (critical) — candidate_id uniqueness preserved
- candidate_symbols_unique: PASS (critical) — candidate symbol uniqueness preserved
- canonical_symbol_columns_detected: PASS (warning) — symbol_cols=ticker|symbol
- canonical_name_columns_detected: PASS (warning) — name_cols=company_name|security_name
- canonical_symbol_column_detection_not_overbroad: PASS (critical) — symbol_cols_count=2 symbol_cols=ticker|symbol
- canonical_name_column_detection_not_overbroad: PASS (critical) — name_cols_count=2 name_cols=company_name|security_name
- canonical_validation_classified_all_candidates: PASS (critical) — classified=1075 candidates=1075
- bucket_counts_sum_to_candidates: PASS (critical) — bucket_sum=1075 candidates=1075
- potential_net_new_tracked: PASS (critical) — potential_net_new_count=696
- match_evidence_generated_or_no_matches: PASS (critical) — match_evidence_rows=382
- canonical_sha_unchanged: PASS (critical) — canonical sha unchanged
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- expanded_candidate_not_written: PASS (critical) — new_expanded_dataset_written=False
- candidate_validation_dry_run_only: PASS (critical) — candidate_validation_against_canonical_dry_run_only=True
- network_not_used: PASS (critical) — network_download_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- potential_net_new_positive: PASS (warning) — potential_net_new_count=696
- possible_existing_tracked: PASS (warning) — possible_existing_count=379
- review_required_tracked: PASS (warning) — review_required_count=379

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: true
- Candidate validation mode: dry_run_only
- Canonical dataset read: true
- Canonical comparison performed: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`v2.18G - TWSE + TPEx Expanded Rebuild Candidate`
