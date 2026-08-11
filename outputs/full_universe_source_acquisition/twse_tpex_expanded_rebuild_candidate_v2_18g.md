# v2.18G - TWSE + TPEx Expanded Rebuild Candidate

Status: **TWSE_TPEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_40996_ROWS_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **expanded-rebuild-candidate-only**

Generated at UTC: `2026-08-11T12:50:04.302763+00:00`

## Executive summary

v2.18G rebuilds a new expanded candidate dataset by adding TWSE potential net-new rows from v2.18F to the validated NSE India candidate dataset.

This phase writes a new candidate file only. It does not replace the active canonical dataset, does not modify canonical, does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Base validated candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv`
- Base validated candidate rows: `40300`
- Expanded candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv`
- Expanded candidate rows: `40996`
- Final target candidates: `50000`
- Projected rows needed after TWSE: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Rebuild summary

- Base rows: `40300`
- Potential net-new rows from v2.18F: `696`
- Added rows: `696`
- Withheld rows: `0`
- Possible existing not auto-added: `379`
- Existing not auto-added: `0`
- Final rows: `40996`
- Schema columns: `33`
- Critical failed checks: `0`

## Schema

The expanded candidate dataset uses the exact base validated candidate header:

`ticker|company_name|exchange|country|source_provider|source_file|instrument_type|instrument_scope|classification_confidence|classification_reason|sector|industry|market_cap|raw_cik|raw_exchange|provider_precedence|merge_action|merge_reason|isin|currency|mic|source_version|source_url|hkex_category|hkex_subcategory|hkex_board_lot|provider|source_phase|symbol|security_name|instrument_id|product_assignment_group_description|asset_type`

## Next actions

- Phigh `TWSE` — validate_expanded_candidate — v2.18H - TWSE + TPEx Expanded Validation
- Pmedium `TWSE` — keep_possible_existing_excluded — v2.18H - TWSE + TPEx Expanded Validation
- Pmedium `50k` — plan_next_provider_after_twse_closure — v2.19A - Next Provider Route Selection

## Checks

- v2_18f_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_candidate_validation_against_canonical_dry_run_v2_18f.json
- v2_18f_status_expected: PASS (critical) — TWSE_TPEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_CANONICAL_BUCKETS_READY_FOR_EXPANDED_REBUILD_CANDIDATE_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18f_classification_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_candidate_validation_classification_v2_18f.csv
- active_canonical_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- base_validated_candidate_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- base_validated_rows_expected: PASS (critical) — base_rows=40300
- base_schema_columns_33: PASS (critical) — base_schema_columns=33
- v2_18f_candidates_validated_expected: PASS (critical) — candidates_validated=1075
- v2_18f_potential_net_new_expected: PASS (critical) — potential_net_new_count=696
- v2_18f_possible_existing_expected: PASS (critical) — possible_existing_count=379
- v2_18f_existing_expected: PASS (critical) — existing_count=0
- possible_existing_not_added: PASS (critical) — possible_existing_withheld_from_auto_add=379
- withheld_conflicts_zero: PASS (critical) — withheld_count=0
- added_count_expected: PASS (critical) — added_count=696
- final_rows_expected: PASS (critical) — final_rows=40996
- projected_rows_needed_after_twse_expected: PASS (critical) — projected_rows_needed_after_twse=9004
- added_candidate_ids_unique: PASS (critical) — added_candidate_ids=0 unique=0
- added_tickers_unique: PASS (critical) — added_tickers=696 unique=696
- added_symbols_unique: PASS (critical) — added_symbols=696 unique=696
- output_schema_matches_base_schema: PASS (critical) — expanded candidate is written with base header
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- base_validated_candidate_sha_unchanged: PASS (critical) — base validated candidate sha unchanged
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- expanded_rebuild_candidate_written: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv
- network_not_used: PASS (critical) — network_download_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: true
- Expanded rebuild candidate mode: candidate_only
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: true
- New expanded dataset path: `outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv`
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

`v2.18H - TWSE + TPEx Expanded Validation`
