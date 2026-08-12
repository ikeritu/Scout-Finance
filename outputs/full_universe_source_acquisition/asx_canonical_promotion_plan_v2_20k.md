# v2.20K — ASX Canonical Promotion Plan

Status: **ASX_CANONICAL_PROMOTION_PLAN_COMPLETED_DRY_RUN_READY_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED**

Phase type: **canonical-promotion-plan-only**

Generated at UTC: `2026-08-12T11:37:55.635103+00:00`

## Executive summary

v2.20K prepares the controlled canonical promotion plan for the validated ASX candidate.

Promotion source:

`outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv`

Planned promoted canonical dataset:

`outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv`

This phase is planning only. It does **not** copy, rename, overwrite, replace canonical, update pointers, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Plan summary

- Plan decision: `PROMOTION_PLAN_READY_FOR_DRY_RUN`
- Promotion source rows: `42708`
- Promotion source SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Active canonical rows: `38287`
- Active canonical SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Current validated candidate rows: `41392`
- ASX net-new rows vs current candidate: `1316`
- Uplift vs active canonical rows: `4421`
- Quality floor crossed: `True`
- Quality ceiling respected: `True`
- Rows above 42k floor: `708`
- Remaining capacity to 45k ceiling: `2292`
- Rows to 50k aspirational: `7292`
- Promotion strategy: `VERSIONED_CANONICAL_FILE_FIRST_WITH_EXPLICIT_POINTER_UPDATE_LATER`
- Canonical promotion performed: `False`
- Critical failed checks: `0`
- Warning failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Execution plan

- Step 1 `v2.20L` — dry_run_copy_plan: Simulate promotion from ASX validated candidate to planned promoted canonical path.
- Step 2 `v2.20L` — preflight_sha_and_row_controls: Validate source rows/SHA, current canonical rows/SHA, schema and target non-existence.
- Step 3 `v2.20M` — controlled_promoted_file_creation: Create versioned promoted canonical dataset from ASX validated candidate.
- Step 4 `v2.20N` — post_promotion_validation: Validate promoted canonical file rows/SHA/schema against ASX validated candidate.
- Step 5 `post-v2.20N` — explicit_active_pointer_decision: Decide whether app/scripts should reference the new promoted canonical file.

## Rollback plan

- `ROLLBACK_001` — active_canonical — Keep current active canonical as untouched rollback source.
- `ROLLBACK_002` — validated_asx_candidate — Treat ASX candidate as immutable source; regenerate promoted file from this only if needed.
- `ROLLBACK_003` — promotion_target — Delete or ignore promoted versioned file if validation fails; do not alter active canonical.

## Risk register

- `RISK_001` — Accidental overwrite of active canonical dataset — high — controlled_by_plan
- `RISK_002` — Promotion source drift — high — controlled_by_plan
- `RISK_003` — Operational references still point to old canonical after promoted file creation — medium — deferred_explicitly
- `RISK_004` — Chasing 50k volume after 42k target achieved — medium — controlled_by_plan
- `RISK_005` — Unexpected scoring or broker side effects — high — controlled_by_plan

## Checks

- v2_20g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_rebuild_candidate_v2_20g.json
- v2_20h_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_validation_v2_20h.json
- v2_20i_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_closure_report_v2_20i.json
- v2_20j_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_candidate_promotion_decision_gate_v2_20j.json
- v2_20g_status_expected: PASS (critical) — ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20h_status_expected: PASS (critical) — ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED
- v2_20i_status_expected: PASS (critical) — ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED
- v2_20j_status_expected: PASS (critical) — ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20j_next_phase_expected: PASS (critical) — v2.20K - ASX Canonical Promotion Plan
- v2_20j_promotion_decision_expected: PASS (critical) — PROMOTION_RECOMMENDED_READY_FOR_PLAN
- v2_20j_promotion_recommendation_expected: PASS (critical) — PREPARE_CANONICAL_PROMOTION_PLAN
- v2_20j_decision_gate_result_expected: PASS (critical) — APPROVE_PREPARATION_OF_CANONICAL_PROMOTION
- v2_20j_canonical_promotion_not_performed: PASS (critical) — canonical_promotion_performed=False
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
- quality_floor_crossed: PASS (critical) — asx_validated_rows=42708;floor=42000
- quality_ceiling_not_exceeded: PASS (critical) — asx_validated_rows=42708;ceiling=45000
- rows_above_quality_floor_expected: PASS (critical) — rows_above_floor=708
- remaining_capacity_to_quality_ceiling_expected: PASS (critical) — capacity_to_ceiling=2292
- rows_to_aspirational_50k_expected: PASS (warning) — rows_to_50k=7292
- planned_promotion_source_is_asx_candidate: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv
- planned_promotion_target_is_versioned_new_file: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv
- planned_target_does_not_exist_yet: PASS (warning) — target_exists=False
- promotion_plan_only: PASS (critical) — promotion plan only
- no_file_copy_performed: PASS (critical) — file_copy_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- canonical_promotion_not_performed: PASS (critical) — canonical_promotion_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Next actions

- Phigh `canonical` — run_asx_canonical_promotion_dry_run — v2.20L - ASX Canonical Promotion Dry Run
- Phigh `rollback` — verify_rollback_reference_before_execution — v2.20L - ASX Canonical Promotion Dry Run
- Pmedium `provider_expansion` — keep_provider_expansion_frozen_by_default — v2.20L - ASX Canonical Promotion Dry Run

## Guards

- Promotion plan only: true
- File copy performed: false
- File rename performed: false
- Canonical dataset modified: false
- Active canonical replaced: false
- Canonical promotion performed: false
- Planned promoted canonical dataset created: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20L - ASX Canonical Promotion Dry Run`
