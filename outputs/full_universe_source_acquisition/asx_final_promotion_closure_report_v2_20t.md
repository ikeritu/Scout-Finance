# v2.20T — Final ASX Promotion Closure Report

Status: **ASX_FINAL_PROMOTION_CLOSURE_REPORT_COMPLETED_OPERATIONAL_BASE_RECOGNIZED_42708_ROWS_ROLLBACK_AVAILABLE_SCORING_DEFERRED_FULL59K_DEPRECATED**

Phase type: **final-asx-promotion-closure-report-only**

Generated at UTC: `2026-08-12T15:43:39.061510+00:00`

## Executive summary

v2.20T closes the ASX promotion path.

The promoted canonical is recognized as the operational base, while the previous v2_14e canonical remains preserved as rollback.

This phase does **not** edit files, replace canonical, copy files, rename files, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Closure summary

- Closure decision: `ASX_PROMOTION_CLOSED_PROMOTED_CANONICAL_RECOGNIZED_AS_OPERATIONAL_BASE_SCORING_DEFERRED`
- ASX promotion closed: `True`
- Operational base dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv`
- Operational base rows: `42708`
- Operational base SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Rollback dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Rollback rows: `38287`
- Rollback SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Controlled pointer files validated: `3`
- Controlled pointer files with old refs: `0`
- Controlled pointer files with new refs: `3`
- Quality floor crossed: `True`
- Quality ceiling respected: `True`
- Provider expansion frozen: `True`
- Scoring authorized: `False`
- OpenAI authorized: `False`
- Broker authorized: `False`
- full59k: `DEPRECATED_DEFERRED`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Roadmap closure

- `v2.20A` — Quality-First Target Reset and Provider Selection: closed — Quality-first route reset; ASX selected.
- `v2.20B` — ASX Quality-First Acquisition Plan: closed — ASX acquisition route planned.
- `v2.20C` — ASX Quality-First Raw Acquisition: closed — ASX raw acquisition completed.
- `v2.20D` — ASX Raw Validation: closed — ASX raw data validated.
- `v2.20E` — ASX Candidate Extraction Dry Run: closed — Candidate extraction dry run completed.
- `v2.20F` — ASX Candidate Validation Against Current Candidate Dry Run: closed — ASX candidate validated against current candidate path.
- `v2.20G` — ASX Expanded Rebuild Candidate: closed — Expanded rebuild candidate created.
- `v2.20H` — ASX Expanded Validation: closed — Expanded validation completed.
- `v2.20I` — ASX Closure Report: closed — Provider closure report completed.
- `v2.20J` — ASX Candidate Promotion Decision Gate: closed — Promotion decision approved.
- `v2.20K` — ASX Canonical Promotion Plan: closed — Canonical promotion planned.
- `v2.20L` — ASX Canonical Promotion Dry Run: closed — Promotion dry run passed.
- `v2.20M` — ASX Controlled Promoted File Creation: closed — Promoted file created.
- `v2.20N` — ASX Promoted Canonical Validation: closed — Promoted canonical validated.
- `v2.20O` — ASX Active Pointer Decision Gate: closed — Pointer update plan approved.
- `v2.20P` — ASX Active Pointer Update Plan: closed — Three active pointer candidates identified.
- `v2.20Q` — ASX Controlled Active Pointer Update: closed — Three controlled pointer files updated.
- `v2.20R` — ASX Active Pointer Update Validation: closed — Pointer update validated.
- `v2.20S` — Post-Pointer Operational Readiness Gate: closed — Operational base ready for final closure.
- `v2.20T` — Final ASX Promotion Closure Report: closed_if_this_report_passes — Final closure report for ASX promotion.

## Pointer controls

- `outputs/audit/documentation_canonical_dataset_path_v2_14i.json` — validated `True` — old_refs `0` — new_refs `1`
- `outputs/audit/eol_guard_v2_14k.json` — validated `True` — old_refs `0` — new_refs `1`
- `tests/test_expanded_universe_post_closure_v2_14j.py` — validated `True` — old_refs `0` — new_refs `1`

## Decision register

- `ASX_CLOSURE_001` — accepted `True` — Close ASX promotion path.
- `ASX_CLOSURE_002` — accepted `True` — Recognize promoted canonical as operational base.
- `ASX_CLOSURE_003` — accepted `True` — Preserve v2_14e as rollback.
- `ASX_CLOSURE_004` — accepted `True` — Freeze provider expansion by default.
- `ASX_CLOSURE_005` — accepted `True` — Defer scoring/OpenAI/broker.
- `ASX_CLOSURE_006` — accepted `True` — Keep full59k deprecated/deferred.

## Scoring deferral

- `SCORING_DEFERRAL_001` — scoring: authorized `False` — Deferred
- `SCORING_DEFERRAL_002` — openai: authorized `False` — Deferred
- `SCORING_DEFERRAL_003` — broker: authorized `False` — Deferred
- `SCORING_DEFERRAL_004` — full59k: authorized `False` — Deprecated/deferred

## Checks

- v2_20m_status_expected: PASS (critical) — ASX_CONTROLLED_PROMOTED_FILE_CREATION_COMPLETED_42708_ROWS_PROMOTED_FILE_CREATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED
- v2_20n_status_expected: PASS (critical) — ASX_PROMOTED_CANONICAL_VALIDATION_COMPLETED_42708_ROWS_PROMOTED_FILE_VALIDATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED
- v2_20o_status_expected: PASS (critical) — ASX_ACTIVE_POINTER_DECISION_GATE_COMPLETED_POINTER_UPDATE_PLAN_APPROVED_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED
- v2_20p_status_expected: PASS (critical) — ASX_ACTIVE_POINTER_UPDATE_PLAN_COMPLETED_POINTER_UPDATE_READY_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED
- v2_20q_status_expected: PASS (critical) — ASX_CONTROLLED_ACTIVE_POINTER_UPDATE_COMPLETED_3_FILES_UPDATED_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20r_status_expected: PASS (critical) — ASX_ACTIVE_POINTER_UPDATE_VALIDATION_COMPLETED_3_FILES_VALIDATED_42708_ROWS_POINTERS_ACTIVE_ROLLBACK_AVAILABLE_FULL59K_DEPRECATED
- v2_20s_status_expected: PASS (critical) — ASX_POST_POINTER_OPERATIONAL_READINESS_GATE_COMPLETED_OPERATIONAL_BASE_READY_42708_ROWS_ROLLBACK_AVAILABLE_SCORING_NOT_AUTHORIZED_FULL59K_DEPRECATED
- v2_20s_next_phase_expected: PASS (critical) — v2.20T - Final ASX Promotion Closure Report
- v2_20s_readiness_decision_expected: PASS (critical) — PROMOTED_CANONICAL_OPERATIONAL_BASE_READY_FOR_FINAL_CLOSURE
- v2_20s_operational_base_ready: PASS (critical) — operational_base_ready=True
- v2_20s_provider_expansion_frozen: PASS (critical) — provider_expansion_frozen=True
- v2_20s_scoring_not_authorized: PASS (critical) — scoring_authorized=False
- v2_20s_openai_not_authorized: PASS (critical) — openai_authorized=False
- v2_20s_broker_not_authorized: PASS (critical) — broker_authorized=False
- v2_20s_full59k_deferred: PASS (critical) — full59k=DEPRECATED_DEFERRED
- promoted_rows_expected: PASS (critical) — promoted_rows=42708
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- asx_rows_expected: PASS (critical) — asx_rows=42708
- current_rows_expected: PASS (critical) — current_rows=41392
- promoted_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- asx_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- current_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- promoted_matches_asx_rows: PASS (critical) — promoted=42708;asx=42708
- promoted_matches_asx_sha: PASS (critical) — promoted=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127;asx=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- promoted_schema_matches_rollback: PASS (critical) — promoted_columns=33;rollback_columns=33
- promoted_schema_matches_asx: PASS (critical) — promoted_columns=33;asx_columns=33
- promoted_schema_matches_current_candidate: PASS (critical) — promoted_columns=33;current_columns=33
- schema_column_count_expected: PASS (critical) — promoted_columns=33
- quality_floor_crossed: PASS (critical) — rows=42708;floor=42000
- quality_ceiling_not_exceeded: PASS (critical) — rows=42708;ceiling=45000
- pointer_file_exists::outputs/audit/documentation_canonical_dataset_path_v2_14i.json: PASS (critical) — outputs\audit\documentation_canonical_dataset_path_v2_14i.json
- pointer_file_no_old_refs::outputs/audit/documentation_canonical_dataset_path_v2_14i.json: PASS (critical) — old_refs=0
- pointer_file_has_new_ref::outputs/audit/documentation_canonical_dataset_path_v2_14i.json: PASS (critical) — new_refs=1
- pointer_file_validated::outputs/audit/documentation_canonical_dataset_path_v2_14i.json: PASS (critical) — validated=True
- pointer_file_exists::outputs/audit/eol_guard_v2_14k.json: PASS (critical) — outputs\audit\eol_guard_v2_14k.json
- pointer_file_no_old_refs::outputs/audit/eol_guard_v2_14k.json: PASS (critical) — old_refs=0
- pointer_file_has_new_ref::outputs/audit/eol_guard_v2_14k.json: PASS (critical) — new_refs=1
- pointer_file_validated::outputs/audit/eol_guard_v2_14k.json: PASS (critical) — validated=True
- pointer_file_exists::tests/test_expanded_universe_post_closure_v2_14j.py: PASS (critical) — tests\test_expanded_universe_post_closure_v2_14j.py
- pointer_file_no_old_refs::tests/test_expanded_universe_post_closure_v2_14j.py: PASS (critical) — old_refs=0
- pointer_file_has_new_ref::tests/test_expanded_universe_post_closure_v2_14j.py: PASS (critical) — new_refs=1
- pointer_file_validated::tests/test_expanded_universe_post_closure_v2_14j.py: PASS (critical) — validated=True
- pointer_files_validated_expected: PASS (critical) — pointer_files_validated=3
- pointer_files_with_old_refs_expected_zero: PASS (critical) — pointer_files_with_old_refs=0
- pointer_files_with_new_refs_expected_three: PASS (critical) — pointer_files_with_new_refs=3
- closure_report_only: PASS (critical) — final ASX promotion closure report only
- file_edit_not_performed: PASS (critical) — file_edit_performed=False
- file_copy_not_performed: PASS (critical) — file_copy_performed=False
- file_rename_not_performed: PASS (critical) — file_rename_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- promoted_dataset_not_modified: PASS (critical) — promoted_canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- provider_expansion_not_authorized: PASS (critical) — provider_expansion_authorized=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

`v2.21A - Post-ASX Explicit Scoring Decision Gate`
