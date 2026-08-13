# v2.21D_S — Singapore Rebuild + Validation Candidate

Status: **SINGAPORE_REBUILD_VALIDATION_CANDIDATE_COMPLETED_43066_ROWS_READY_FOR_PROMOTION_DECISION_NO_POINTER_UPDATE_SCORING_DEFERRED**

Phase type: **singapore-expanded-rebuild-validation-candidate**

Generated at UTC: `2026-08-13T07:49:21.982730+00:00`

## Executive summary

v2.21D_S builds and validates a Singapore-only expanded universe candidate from the v2.21C4S eligible candidates.

This phase creates a candidate dataset but does not promote it, does not update pointers, does not modify the operational base, does not run scoring, does not call OpenAI, does not call brokers, and does not launch full59k.

## Summary

- Rebuild decision: `SINGAPORE_REBUILD_CANDIDATE_43066_ROWS_VALIDATED_READY_FOR_PROMOTION_OR_FREEZE_DECISION`
- Approved for promotion decision: `True`
- Approved for pointer update: `False`
- Operational base rows: `42708`
- Operational base SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_21d_s_singapore_candidate.csv`
- Candidate rows: `43066`
- Candidate SHA256: `8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f`
- Singapore appended rows: `358`
- Remaining capacity after candidate: `1934`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Manifest

- `operational_base_input` — rows `42708` — SHA `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127` — input_only_unchanged
- `rollback_input` — rows `38287` — SHA `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f` — input_only_unchanged
- `v2_21c4s_schema_projection_input` — rows `358` — SHA `1c794dfa6649909baafbaf294ca71fef5a8d98edfddbae5ecb2d38eec077c891` — append_source
- `v2_21c4s_eligible_candidates_input` — rows `358` — SHA `7194894d4eb9f1ac4225427face49f16efc97c1450aa0a3e51889a8b53de74f5` — eligibility_audit_source
- `candidate_dataset_output` — rows `43066` — SHA `8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f` — candidate_only_not_promoted

## Checks

- v2_21c4s_status_expected: PASS (critical) — SINGAPORE_STRUCTURED_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_ELIGIBLE_CANDIDATES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED
- v2_21c4s_approved_for_singapore_rebuild_candidate: PASS (critical) — approved_for_singapore_rebuild_candidate=True
- v2_21c4s_global_v2_21d_not_approved: PASS (critical) — approved_for_global_v2_21d=False
- v2_21c4s_colombia_extraction_not_approved: PASS (critical) — approved_for_colombia_extraction=False
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- schema_projection_header_matches_operational_header: PASS (critical) — projection_columns=33;operational_columns=33
- schema_column_count_expected: PASS (critical) — columns=33
- projection_rows_expected: PASS (critical) — projection_rows=358
- eligible_rows_expected: PASS (critical) — eligible_rows=358
- eligible_rows_all_approved_for_rebuild_input: PASS (critical) — eligible_approved_count=358;eligible_rows=358
- eligible_rows_singapore_only: PASS (critical) — eligible_market_count=358;eligible_rows=358
- eligible_symbols_unique: PASS (critical) — duplicate_eligible_symbols=0
- eligible_names_unique_or_reviewable: PASS (warning) — duplicate_eligible_names=0
- eligible_isins_unique: PASS (critical) — duplicate_eligible_isins=0
- candidate_dataset_rows_expected: PASS (critical) — candidate_rows=43066;expected=43066
- candidate_dataset_rows_equal_base_plus_projection: PASS (critical) — candidate_rows=43066;base_plus_projection=43066
- candidate_dataset_above_quality_floor: PASS (critical) — candidate_rows=43066;floor=42000
- candidate_dataset_under_quality_ceiling: PASS (critical) — candidate_rows=43066;ceiling=45000
- remaining_capacity_non_negative: PASS (critical) — remaining_capacity_after_candidate=1934
- candidate_dataset_sha_created: PASS (critical) — 8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f
- appended_rows_country_confirmed: PASS (critical) — country_confirmed=358;projection_rows=358
- appended_rows_exchange_confirmed: PASS (critical) — exchange_confirmed=358;projection_rows=358
- appended_rows_mic_confirmed: PASS (critical) — mic_confirmed=358;projection_rows=358
- appended_rows_currency_confirmed: PASS (critical) — currency_confirmed=358;projection_rows=358
- operational_base_not_modified_after_candidate_build: PASS (critical) — operational_sha_after=892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_not_modified_after_candidate_build: PASS (critical) — rollback_sha_after=cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- expanded_rebuild_candidate_created: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21d_s_singapore_candidate.csv
- candidate_only_not_promoted: PASS (critical) — candidate dataset created; no active pointer update performed
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.21E_S - Singapore Promotion / Freeze Decision`

Secondary: `v2.21C3B - Colombia Regulatory Source Discovery`
