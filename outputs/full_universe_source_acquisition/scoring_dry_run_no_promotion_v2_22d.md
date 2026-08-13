# v2.22D — Scoring Dry Run / No Promotion

Status: **SCORING_DRY_RUN_NO_PROMOTION_COMPLETED_LOCAL_HEURISTIC_SCORES_CREATED_PROMOTION_DEFERRED**

Phase type: **scoring-dry-run-no-promotion**

Generated at UTC: `2026-08-13T11:15:17.686464+00:00`

## Executive summary

v2.22D creates a local deterministic scoring dry run using the current operational universe and the v2.22C2 exclusion overlay.

This phase does not promote scores and does not modify the canonical dataset.

## Inputs

Current dataset:

`outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv`

Rows: `43089`  
SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`

Classification overlay:

`outputs\full_universe_source_acquisition\residual_instrument_classification_review_classification_v2_22c2.csv`

Overlay rows: `9857`  
Excluded rows: `9591`

## Dry-run scoring output

`outputs\full_universe_source_acquisition\scoring_dry_run_no_promotion_scores_v2_22d.csv`

Scored rows: `33498`  
SHA256: `a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1`

## Score summary

- Min: `44.7`
- P25: `45.1`
- Median: `52.2`
- P75: `74.7667`
- Max: `87.2`
- Mean: `58.2468`

## Score distribution

- A_85_100: 1282 (3.8271%)
- B_70_84: 8980 (26.8076%)
- C_55_69: 6023 (17.9802%)
- D_40_54: 17213 (51.3852%)
- E_0_39: 0 (0.0%)

## Guardrails

- Dry-run scoring executed: `True`
- Approved for promotion: `False`
- Scoring promoted: `False`
- Production scoring authorized: `False`
- Canonical dataset modified: `False`
- Active canonical replaced: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

- classification_review_status_expected: PASS (critical) — RESIDUAL_INSTRUMENT_CLASSIFICATION_REVIEW_COMPLETED_FULL_DATASET_POLICY_OVERLAY_READY_FOR_SCORING_DRY_RUN_DECISION
- classification_review_approved_for_scoring_dry_run_decision: PASS (critical) — approved=True
- classification_review_not_approved_for_scoring_execution: PASS (critical) — approved_for_scoring_execution=False
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- previous_rows_expected: PASS (critical) — previous_rows=42708
- previous_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- classification_overlay_rows_expected: PASS (critical) — overlay_rows=9857;expected=9857
- excluded_rows_expected: PASS (critical) — excluded_rows=9591;expected=9591
- scorable_rows_expected: PASS (critical) — scorable_rows=33498;expected=33498
- excluded_plus_scorable_equals_current: PASS (critical) — excluded=9591;scorable=33498;current=43089
- score_output_created: PASS (critical) — outputs\full_universe_source_acquisition\scoring_dry_run_no_promotion_scores_v2_22d.csv
- score_output_rows_expected: PASS (critical) — score_rows=33498
- score_values_within_0_100: PASS (critical) — all_scores_between_0_and_100=True
- within_quality_floor: PASS (critical) — current_rows=43089;floor=42000
- within_quality_ceiling: PASS (critical) — current_rows=43089;ceiling=45000
- dry_run_scoring_executed: PASS (critical) — dry_run_scoring_executed=True
- production_scoring_not_authorized: PASS (critical) — production_scoring_authorized=False
- promotion_not_performed: PASS (critical) — scoring_promoted=False
- canonical_dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.22E - Scoring Promotion / Freeze Decision`

Secondary: `v2.22F - Repo Hygiene / Untracked Files Review`
