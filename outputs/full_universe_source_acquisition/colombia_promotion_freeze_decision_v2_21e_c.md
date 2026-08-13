# v2.21E_C — Colombia Promotion / Freeze Decision

Status: **COLOMBIA_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED**

Phase type: **colombia-promotion-freeze-decision**

Generated at UTC: `2026-08-13T08:54:59.223348+00:00`

## Executive summary

v2.21E_C makes the Colombia promotion/freeze decision.

The v2.21D_C Colombia candidate is promoted as a controlled artifact after final validation. The previous operational base remains unchanged, the Singapore promoted artifact remains unchanged, no active pointer file is modified, no scoring is run, no OpenAI call is made, no broker call is made, and full59k remains deprecated/deferred.

## Summary

- Promotion decision: `COLOMBIA_PROMOTED_ARTIFACT_READY_FOR_FINAL_V2_21_CLOSURE`
- Approved as promoted artifact: `True`
- Approved for final v2.21 closure: `True`
- Active pointer update performed: `False`
- Colombia promoted dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_21e_c_colombia_promoted.csv`
- Colombia promoted rows: `43089`
- Colombia promoted SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`
- Colombia appended rows: `23`
- Remaining capacity: `1911`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Manifest

- `previous_operational_base_input` — rows `42708` — SHA `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127` — input_only_unchanged
- `rollback_input` — rows `38287` — SHA `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f` — input_only_unchanged
- `singapore_promoted_input` — rows `43066` — SHA `8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f` — input_only_unchanged
- `colombia_candidate_input` — rows `43089` — SHA `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707` — promotion_candidate_input_unchanged
- `colombia_promoted_dataset_output` — rows `43089` — SHA `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707` — promoted_artifact_not_active_pointer_update
- `colombia_pointer_manifest_output` — rows `1` — SHA `efc769917133d4dfca1c0d5ffadb22684ceb04f7d0860c4d5ba49bd4eeccbe29` — promotion_pointer_manifest_no_existing_pointer_modified

## Decision register

- `COLOMBIA_PROMOTION_001` — accepted `True` — Promote Colombia candidate as v2.21E_C promoted artifact.
- `COLOMBIA_PROMOTION_002` — accepted `True` — Do not update active pointer in v2.21E_C.
- `COLOMBIA_PROMOTION_003` — accepted `True` — Preserve Singapore promoted artifact unchanged.
- `COLOMBIA_PROMOTION_004` — accepted `True` — Keep scoring/OpenAI/broker/full59k deferred.

## Checks

- colombia_build_status_expected: PASS (critical) — COLOMBIA_CONDITIONAL_BUILD_COMPLETED_CANDIDATE_CREATED_NO_PROMOTION_NO_POINTER_UPDATE_SCORING_DEFERRED
- colombia_build_approved_for_promotion_decision: PASS (critical) — approved_for_colombia_promotion_decision=True
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- singapore_promoted_rows_expected: PASS (critical) — singapore_promoted_rows=43066
- singapore_promoted_sha_expected: PASS (critical) — 8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f
- colombia_candidate_rows_expected: PASS (critical) — colombia_candidate_rows=43089
- colombia_candidate_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- header_matches_singapore_promoted: PASS (critical) — candidate_columns=33;singapore_columns=33
- schema_column_count_expected: PASS (critical) — candidate_columns=33;operational_columns=33
- eligible_rows_expected: PASS (critical) — eligible_count=23
- eligible_rows_all_approved: PASS (critical) — eligible_approved_count=23;eligible_count=23
- eligible_country_context_expected: PASS (critical) — eligible_country_count=23;eligible_count=23
- eligible_exchange_context_expected: PASS (critical) — eligible_exchange_count=23;eligible_count=23
- eligible_mic_context_expected: PASS (critical) — eligible_mic_count=23;eligible_count=23
- eligible_currency_context_expected: PASS (critical) — eligible_currency_count=23;eligible_count=23
- appended_rows_expected: PASS (critical) — appended_rows=23
- appended_rows_country_confirmed: PASS (critical) — country_confirmed=23
- appended_rows_country_code_confirmed_or_not_required: PASS (critical) — country_code_confirmed=23;country_code_columns=0
- appended_rows_exchange_confirmed: PASS (critical) — exchange_confirmed=23
- appended_rows_mic_confirmed: PASS (critical) — mic_confirmed=23
- appended_rows_currency_confirmed: PASS (critical) — currency_confirmed=23
- promoted_dataset_rows_expected: PASS (critical) — promoted_rows=43089
- promoted_dataset_sha_matches_candidate: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- promoted_dataset_under_quality_ceiling: PASS (critical) — promoted_rows=43089;ceiling=45000
- promoted_dataset_above_quality_floor: PASS (critical) — promoted_rows=43089;floor=42000
- remaining_capacity_non_negative: PASS (critical) — remaining_capacity=1911
- pointer_manifest_created: PASS (critical) — outputs\full_universe_source_acquisition\colombia_promotion_freeze_decision_pointer_manifest_v2_21e_c.json
- operational_base_not_modified: PASS (critical) — operational_sha_after=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_not_modified: PASS (critical) — rollback_sha_after=cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- singapore_promoted_artifact_not_modified: PASS (critical) — singapore_promoted_sha_after=8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f
- colombia_candidate_input_not_modified: PASS (critical) — colombia_candidate_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

`v2.21G - Final v2.21 Closure Report`
