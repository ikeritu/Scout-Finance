# v2.20N — ASX Promoted Canonical Validation

Status: **ASX_PROMOTED_CANONICAL_VALIDATION_COMPLETED_42708_ROWS_PROMOTED_FILE_VALIDATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED**

Phase type: **promoted-canonical-validation-only**

Generated at UTC: `2026-08-12T14:36:40.131569+00:00`

## Executive summary

v2.20N validates the promoted canonical file created in v2.20M.

Promoted canonical file:

`outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv`

Promotion source:

`outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv`

The promoted file is validated against source rows, SHA and schema. This phase does **not** create files, copy files, rename files, overwrite canonical, update active pointers, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Validation summary

- Validation decision: `PROMOTED_CANONICAL_VALIDATED_READY_FOR_POINTER_DECISION_GATE`
- Promoted canonical rows: `42708`
- Promoted canonical SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Promotion source rows: `42708`
- Promotion source SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Promoted rows match source: `True`
- Promoted SHA matches source: `True`
- Promoted schema matches source: `True`
- Promoted schema matches active canonical: `True`
- Schema column count: `33`
- Active canonical rows: `38287`
- Active canonical SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Active canonical replaced: `False`
- Active pointer updated: `False`
- ASX net-new rows vs current candidate: `1316`
- Uplift vs active canonical rows: `4421`
- Quality floor crossed: `True`
- Quality ceiling respected: `True`
- Rows above 42k floor: `708`
- Remaining capacity to 45k ceiling: `2292`
- Rows to 50k aspirational: `7292`
- Critical failed checks: `0`
- Warning failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Artifact manifest

- `promotion_source_asx_candidate` — `outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv` — exists `True` — rows `42708` — SHA `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- `promoted_canonical_versioned_file` — `outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv` — exists `True` — rows `42708` — SHA `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- `active_canonical_rollback_reference` — `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv` — exists `True` — rows `38287` — SHA `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- `current_validated_candidate_reference` — `outputs\full_universe_source_acquisition\expanded_universe_candidate_hkex_v2_19p.csv` — exists `True` — rows `41392` — SHA `3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c`

## SHA controls

- `SHA_001` — promoted_canonical: PASS — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- `SHA_002` — asx_source: PASS — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- `SHA_003` — active_canonical: PASS — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- `SHA_004` — promoted_vs_asx_source: PASS — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127

## Schema controls

- `SCHEMA_001` — promoted_canonical — columns `33` — matches ASX `True`
- `SCHEMA_002` — asx_source — columns `33` — matches ASX `True`
- `SCHEMA_003` — active_canonical — columns `33` — matches ASX `True`

## Content controls

- `CONTENT_001` — promoted_rows_match_source: PASS — promoted=42708;source=42708
- `CONTENT_002` — promoted_sha_match_source: PASS — promoted=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127;source=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- `CONTENT_003` — promoted_schema_match_source: PASS — promoted_columns=33;source_columns=33
- `CONTENT_004` — quality_floor_and_ceiling: PASS — rows=42708;floor=42000;ceiling=45000

## Activation gate

- `ACTIVATION_001` — promoted_file_validated: PASS — critical_failed_checks=0;warning_failed_checks=0
- `ACTIVATION_002` — active_canonical_still_rollback: PASS — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- `ACTIVATION_003` — pointer_update_not_yet_performed: PASS — active_pointer_updated=False
- `ACTIVATION_004` — next_phase_must_be_decision_gate: PASS — v2.20O - ASX Active Pointer Decision Gate

## Checks

- v2_20g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_rebuild_candidate_v2_20g.json
- v2_20h_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_validation_v2_20h.json
- v2_20i_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_closure_report_v2_20i.json
- v2_20j_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_candidate_promotion_decision_gate_v2_20j.json
- v2_20k_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_canonical_promotion_plan_v2_20k.json
- v2_20l_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_canonical_promotion_dry_run_v2_20l.json
- v2_20m_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_controlled_promoted_file_creation_v2_20m.json
- v2_20g_status_expected: PASS (critical) — ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20h_status_expected: PASS (critical) — ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED
- v2_20i_status_expected: PASS (critical) — ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED
- v2_20j_status_expected: PASS (critical) — ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20k_status_expected: PASS (critical) — ASX_CANONICAL_PROMOTION_PLAN_COMPLETED_DRY_RUN_READY_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20l_status_expected: PASS (critical) — ASX_CANONICAL_PROMOTION_DRY_RUN_COMPLETED_PROMOTION_EXECUTION_READY_42708_ROWS_CANONICAL_UNCHANGED_PROMOTED_FILE_NOT_CREATED_FULL59K_DEPRECATED
- v2_20m_status_expected: PASS (critical) — ASX_CONTROLLED_PROMOTED_FILE_CREATION_COMPLETED_42708_ROWS_PROMOTED_FILE_CREATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED
- v2_20m_next_phase_expected: PASS (critical) — v2.20N - ASX Promoted Canonical Validation
- v2_20m_creation_decision_expected: PASS (critical) — PROMOTED_FILE_CREATED_READY_FOR_VALIDATION
- v2_20m_copy_performed: PASS (critical) — copy_performed=True
- v2_20m_active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- v2_20m_active_pointer_not_updated: PASS (critical) — active_pointer_updated=False
- active_canonical_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- current_validated_candidate_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_hkex_v2_19p.csv
- asx_validated_candidate_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv
- promoted_canonical_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_validated_rows=41392
- asx_validated_candidate_rows_expected: PASS (critical) — asx_validated_rows=42708
- promoted_canonical_rows_expected: PASS (critical) — promoted_rows=42708
- active_canonical_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- current_validated_candidate_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- asx_validated_candidate_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- promoted_canonical_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- promoted_matches_asx_rows: PASS (critical) — promoted=42708;asx=42708
- promoted_matches_asx_sha: PASS (critical) — promoted=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127;asx=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- promoted_matches_asx_schema: PASS (critical) — matches=True
- promoted_matches_active_schema: PASS (critical) — matches=True
- promoted_matches_current_schema: PASS (critical) — matches=True
- promoted_column_count_expected: PASS (critical) — promoted_columns=33
- active_canonical_sha_unchanged_during_validation: PASS (critical) — active canonical SHA unchanged
- current_validated_candidate_sha_unchanged_during_validation: PASS (critical) — current candidate SHA unchanged
- asx_validated_candidate_sha_unchanged_during_validation: PASS (critical) — ASX candidate SHA unchanged
- promoted_canonical_sha_unchanged_during_validation: PASS (critical) — promoted canonical SHA unchanged
- asx_net_new_rows_expected: PASS (critical) — asx_net_new_rows=1316
- uplift_vs_active_canonical_expected: PASS (critical) — uplift_vs_active_canonical=4421
- quality_floor_crossed: PASS (critical) — promoted_rows=42708;floor=42000
- quality_ceiling_not_exceeded: PASS (critical) — promoted_rows=42708;ceiling=45000
- rows_above_quality_floor_expected: PASS (critical) — rows_above_floor=708
- remaining_capacity_to_quality_ceiling_expected: PASS (critical) — capacity_to_ceiling=2292
- rows_to_aspirational_50k_expected: PASS (warning) — rows_to_50k=7292
- validation_only: PASS (critical) — promoted canonical validation only
- file_copy_not_performed: PASS (critical) — file_copy_performed=False
- file_rename_not_performed: PASS (critical) — file_rename_performed=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- active_pointer_not_updated: PASS (critical) — active_pointer_updated=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Next actions

- Phigh `pointer` — run_active_pointer_decision_gate — v2.20O - ASX Active Pointer Decision Gate
- Phigh `rollback` — preserve_active_canonical_rollback_reference — v2.20O - ASX Active Pointer Decision Gate
- Pmedium `quality` — keep_provider_expansion_frozen — v2.20O - ASX Active Pointer Decision Gate

## Guards

- Promoted canonical validation only: true
- File copy performed: false
- File rename performed: false
- Promoted file created in this phase: false
- Promoted file exists: True
- Promoted file validated: True
- Canonical dataset modified: false
- Active canonical replaced: false
- Active pointer updated: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20O - ASX Active Pointer Decision Gate`
