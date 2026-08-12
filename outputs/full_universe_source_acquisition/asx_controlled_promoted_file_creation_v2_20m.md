# v2.20M — ASX Controlled Promoted File Creation

Status: **ASX_CONTROLLED_PROMOTED_FILE_CREATION_COMPLETED_42708_ROWS_PROMOTED_FILE_CREATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED**

Phase type: **controlled-promoted-file-creation-only**

Generated at UTC: `2026-08-12T12:20:48.941146+00:00`

## Executive summary

v2.20M creates the versioned promoted canonical file from the validated ASX candidate.

Promotion source:

`outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv`

Promoted canonical file created:

`outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv`

This phase creates a versioned promoted file only. It does **not** overwrite `expanded_universe_v2_14e.csv`, does **not** update active pointers, does **not** recalculate scoring, does **not** call OpenAI, does **not** call brokers, and does **not** launch full59k.

## Creation summary

- Creation decision: `PROMOTED_FILE_CREATED_READY_FOR_VALIDATION`
- Copy performed: `True`
- Target existed before: `False`
- Target exists after: `True`
- Promotion source rows: `42708`
- Promotion source SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Promoted canonical rows: `42708`
- Promoted canonical SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Promoted rows match source: `True`
- Promoted SHA matches source: `True`
- Promoted schema matches source: `True`
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

- `promotion_source_asx_candidate` — `outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv` — rows `42708` — SHA `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- `promoted_canonical_versioned_file` — `outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv` — rows `42708` — SHA `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- `active_canonical_rollback_reference` — `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv` — rows `38287` — SHA `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- `current_validated_candidate_reference` — `outputs\full_universe_source_acquisition\expanded_universe_candidate_hkex_v2_19p.csv` — rows `41392` — SHA `3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c`

## Copy controls

- `COPY_001` — target_absent_before_creation: PASS — outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv
- `COPY_002` — copyfile_executed: PASS — outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv -> outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv
- `COPY_003` — target_exists_after_creation: PASS — outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv
- `COPY_004` — target_sha_matches_source: PASS — target=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127;source=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- `COPY_005` — target_rows_match_source: PASS — target=42708;source=42708
- `COPY_006` — target_schema_matches_source: PASS — columns=33

## Rollback controls

- `ROLLBACK_001` — active_canonical — AVAILABLE_UNCHANGED — Continue to use active canonical v2_14e if promoted file validation fails.
- `ROLLBACK_002` — asx_validated_candidate — AVAILABLE_UNCHANGED — Regenerate promoted file from this exact source if needed.
- `ROLLBACK_003` — promoted_canonical_file — CREATED_NEEDS_POST_VALIDATION — Delete or ignore promoted file if v2.20N validation fails; do not update pointers.

## Checks

- v2_20g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_rebuild_candidate_v2_20g.json
- v2_20h_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_validation_v2_20h.json
- v2_20i_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_closure_report_v2_20i.json
- v2_20j_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_candidate_promotion_decision_gate_v2_20j.json
- v2_20k_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_canonical_promotion_plan_v2_20k.json
- v2_20l_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_canonical_promotion_dry_run_v2_20l.json
- v2_20g_status_expected: PASS (critical) — ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20h_status_expected: PASS (critical) — ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED
- v2_20i_status_expected: PASS (critical) — ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED
- v2_20j_status_expected: PASS (critical) — ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20k_status_expected: PASS (critical) — ASX_CANONICAL_PROMOTION_PLAN_COMPLETED_DRY_RUN_READY_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20l_status_expected: PASS (critical) — ASX_CANONICAL_PROMOTION_DRY_RUN_COMPLETED_PROMOTION_EXECUTION_READY_42708_ROWS_CANONICAL_UNCHANGED_PROMOTED_FILE_NOT_CREATED_FULL59K_DEPRECATED
- v2_20l_next_phase_expected: PASS (critical) — v2.20M - ASX Controlled Promoted File Creation
- v2_20l_dry_run_decision_expected: PASS (critical) — PROMOTION_DRY_RUN_PASSED_EXECUTION_READY
- v2_20l_promoted_file_not_created: PASS (critical) — promoted_file_created=False
- v2_20l_active_pointer_not_updated: PASS (critical) — active_pointer_updated=False
- source_candidate_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv
- active_canonical_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- promoted_target_absent_before_creation: PASS (critical) — target_exists_before=False
- active_canonical_rows_expected_before: PASS (critical) — active_canonical_rows=38287
- pre_hkex_current_candidate_rows_expected_before: PASS (critical) — pre_hkex_rows=40996
- current_validated_candidate_rows_expected_before: PASS (critical) — current_validated_rows=41392
- asx_validated_candidate_rows_expected_before: PASS (critical) — asx_validated_rows=42708
- active_canonical_sha_expected_before: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- pre_hkex_current_candidate_sha_expected_before: PASS (critical) — 05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2
- current_validated_candidate_sha_expected_before: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- asx_validated_candidate_sha_expected_before: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- schema_column_count_expected_before: PASS (critical) — asx_columns=33
- schema_matches_active_canonical_before: PASS (critical) — schema_matches_active_canonical=True
- schema_matches_current_candidate_before: PASS (critical) — schema_matches_current_candidate=True
- copy_performed: PASS (critical) — copy_performed=True
- promoted_target_exists_after_creation: PASS (critical) — target_exists_after=True
- promoted_rows_expected: PASS (critical) — promoted_rows=42708
- promoted_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- promoted_rows_match_source: PASS (critical) — promoted=42708;source=42708
- promoted_sha_matches_source: PASS (critical) — promoted=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127;source=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- promoted_schema_matches_source: PASS (critical) — schema_matches_source=True
- promoted_column_count_expected: PASS (critical) — promoted_columns=33
- active_canonical_rows_unchanged: PASS (critical) — before=38287;after=38287
- pre_hkex_current_candidate_rows_unchanged: PASS (critical) — before=40996;after=40996
- current_validated_candidate_rows_unchanged: PASS (critical) — before=41392;after=41392
- asx_validated_candidate_rows_unchanged: PASS (critical) — before=42708;after=42708
- active_canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- pre_hkex_current_candidate_sha_unchanged: PASS (critical) — pre-HKEX current candidate sha unchanged
- current_validated_candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- asx_validated_candidate_sha_unchanged: PASS (critical) — ASX validated candidate sha unchanged
- asx_net_new_rows_expected: PASS (critical) — asx_net_new_rows=1316
- uplift_vs_active_canonical_expected: PASS (critical) — uplift_vs_active_canonical=4421
- quality_floor_crossed: PASS (critical) — promoted_rows=42708;floor=42000
- quality_ceiling_not_exceeded: PASS (critical) — promoted_rows=42708;ceiling=45000
- rows_above_quality_floor_expected: PASS (critical) — rows_above_floor=708
- remaining_capacity_to_quality_ceiling_expected: PASS (critical) — capacity_to_ceiling=2292
- rows_to_aspirational_50k_expected: PASS (warning) — rows_to_50k=7292
- controlled_file_creation_only: PASS (critical) — controlled promoted file creation only
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- active_pointer_not_updated: PASS (critical) — active_pointer_updated=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Next actions

- Phigh `validation` — validate_promoted_canonical_file — v2.20N - ASX Promoted Canonical Validation
- Phigh `pointer` — keep_active_pointer_unchanged — post-v2.20N explicit pointer phase
- Phigh `rollback` — preserve_v2_14e_as_rollback_reference — v2.20N - ASX Promoted Canonical Validation

## Guards

- Controlled promoted file creation only: true
- File copy performed: True
- File rename performed: false
- Promoted file created: True
- Promoted file matches source SHA: True
- Promoted file matches source rows: True
- Promoted file schema matches source: True
- Canonical dataset modified: false
- Active canonical replaced: false
- Active pointer updated: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20N - ASX Promoted Canonical Validation`
