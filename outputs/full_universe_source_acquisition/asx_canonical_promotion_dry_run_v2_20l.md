# v2.20L — ASX Canonical Promotion Dry Run

Status: **ASX_CANONICAL_PROMOTION_DRY_RUN_COMPLETED_PROMOTION_EXECUTION_READY_42708_ROWS_CANONICAL_UNCHANGED_PROMOTED_FILE_NOT_CREATED_FULL59K_DEPRECATED**

Phase type: **canonical-promotion-dry-run-only**

Generated at UTC: `2026-08-12T12:05:53.699956+00:00`

## Executive summary

v2.20L performs a dry run for canonical promotion of the validated ASX candidate.

Promotion source:

`outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv`

Planned promoted canonical dataset:

`outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv`

This phase is dry-run only. It does **not** copy, rename, overwrite, create the promoted CSV, replace canonical, update active pointers, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Dry-run summary

- Dry-run decision: `PROMOTION_DRY_RUN_PASSED_EXECUTION_READY`
- Promotion source rows: `42708`
- Promotion source SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Active canonical rows: `38287`
- Active canonical SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Planned promoted target exists before dry run: `False`
- Planned promoted target exists after dry run: `False`
- Current validated candidate rows: `41392`
- ASX net-new rows vs current candidate: `1316`
- Uplift vs active canonical rows: `4421`
- Schema column count: `33`
- Schema matches active canonical: `True`
- Schema matches current candidate: `True`
- Quality floor crossed: `True`
- Quality ceiling respected: `True`
- Rows above 42k floor: `708`
- Remaining capacity to 45k ceiling: `2292`
- Rows to 50k aspirational: `7292`
- Canonical promotion performed: `False`
- Promoted file created: `False`
- Active pointer updated: `False`
- Critical failed checks: `0`
- Warning failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Preflight

- `PREFLIGHT_001` — source_candidate_exists: PASS — outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv
- `PREFLIGHT_002` — active_canonical_exists: PASS — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- `PREFLIGHT_003` — planned_target_absent: PASS — outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv
- `PREFLIGHT_004` — promotion_source_rows_expected: PASS — rows=42708
- `PREFLIGHT_005` — promotion_source_sha_expected: PASS — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- `PREFLIGHT_006` — schema_compatible: PASS — active=True;current=True

## SHA controls

- `active_canonical` — rows `38287` — matched `True`
- `current_validated_candidate` — rows `41392` — matched `True`
- `asx_validated_candidate` — rows `42708` — matched `True`
- `planned_promoted_canonical` — rows `` — matched `True`

## Schema controls

- `active_canonical` — columns `33` — matches ASX `True`
- `current_validated_candidate` — columns `33` — matches ASX `True`
- `asx_validated_candidate` — columns `33` — matches ASX `True`

## Rollback controls

- `ROLLBACK_001` — active_canonical — AVAILABLE_UNCHANGED
- `ROLLBACK_002` — asx_validated_candidate — AVAILABLE_UNCHANGED
- `ROLLBACK_003` — planned_promoted_target — NOT_CREATED_AS_EXPECTED

## Checks

- v2_20g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_rebuild_candidate_v2_20g.json
- v2_20h_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_validation_v2_20h.json
- v2_20i_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_closure_report_v2_20i.json
- v2_20j_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_candidate_promotion_decision_gate_v2_20j.json
- v2_20k_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_canonical_promotion_plan_v2_20k.json
- v2_20g_status_expected: PASS (critical) — ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20h_status_expected: PASS (critical) — ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED
- v2_20i_status_expected: PASS (critical) — ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED
- v2_20j_status_expected: PASS (critical) — ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20k_status_expected: PASS (critical) — ASX_CANONICAL_PROMOTION_PLAN_COMPLETED_DRY_RUN_READY_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20k_next_phase_expected: PASS (critical) — v2.20L - ASX Canonical Promotion Dry Run
- v2_20k_plan_decision_expected: PASS (critical) — PROMOTION_PLAN_READY_FOR_DRY_RUN
- v2_20k_promotion_source_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv
- v2_20k_planned_target_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv
- v2_20k_canonical_promotion_not_performed: PASS (critical) — canonical_promotion_performed=False
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- pre_hkex_current_candidate_rows_expected: PASS (critical) — pre_hkex_rows=40996
- current_validated_candidate_rows_expected: PASS (critical) — current_validated_rows=41392
- asx_validated_candidate_rows_expected: PASS (critical) — asx_validated_rows=42708
- asx_net_new_rows_expected: PASS (critical) — asx_net_new_rows=1316
- uplift_vs_active_canonical_expected: PASS (critical) — uplift_vs_active_canonical=4421
- active_canonical_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- pre_hkex_current_candidate_sha_expected: PASS (critical) — 05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2
- current_validated_candidate_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- asx_validated_candidate_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- active_canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- pre_hkex_current_candidate_sha_unchanged: PASS (critical) — pre-HKEX current candidate sha unchanged
- current_validated_candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- asx_validated_candidate_sha_unchanged: PASS (critical) — ASX validated candidate sha unchanged
- schema_column_count_expected: PASS (critical) — asx_columns=33
- schema_matches_active_canonical: PASS (critical) — schema_matches_active_canonical=True
- schema_matches_current_candidate: PASS (critical) — schema_matches_current_candidate=True
- quality_floor_crossed: PASS (critical) — asx_validated_rows=42708;floor=42000
- quality_ceiling_not_exceeded: PASS (critical) — asx_validated_rows=42708;ceiling=45000
- rows_above_quality_floor_expected: PASS (critical) — rows_above_floor=708
- remaining_capacity_to_quality_ceiling_expected: PASS (critical) — capacity_to_ceiling=2292
- rows_to_aspirational_50k_expected: PASS (warning) — rows_to_50k=7292
- planned_target_absent_before_dry_run: PASS (critical) — target_exists_before=False
- planned_target_absent_after_dry_run: PASS (critical) — target_exists_after=False
- dry_run_only: PASS (critical) — dry run only
- file_copy_not_performed: PASS (critical) — file_copy_performed=False
- file_rename_not_performed: PASS (critical) — file_rename_performed=False
- promoted_file_not_created: PASS (critical) — target_exists_after=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- canonical_promotion_not_performed: PASS (critical) — canonical_promotion_performed=False
- active_pointer_not_updated: PASS (critical) — active_pointer_updated=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Next actions

- Phigh `canonical` — create_versioned_asx_promoted_file — v2.20M - ASX Controlled Promoted File Creation
- Phigh `validation` — validate_promoted_file_after_creation — v2.20N - ASX Promoted Canonical Validation
- Phigh `pointer` — defer_active_pointer_update — post-v2.20N explicit pointer phase

## Guards

- Canonical promotion dry run only: true
- File copy performed: false
- File rename performed: false
- Promoted file created: false
- Canonical dataset modified: false
- Active canonical replaced: false
- Canonical promotion performed: false
- Active pointer updated: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20M - ASX Controlled Promoted File Creation`
