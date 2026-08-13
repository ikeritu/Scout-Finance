# v2.21D_C — Colombia Conditional Build / Freeze

Status: **COLOMBIA_CONDITIONAL_BUILD_COMPLETED_CANDIDATE_CREATED_NO_PROMOTION_NO_POINTER_UPDATE_SCORING_DEFERRED**

Phase type: **colombia-conditional-build-freeze**

Generated at UTC: `2026-08-13T08:45:37.467587+00:00`

## Executive summary

v2.21D_C conditionally extracts Colombia candidates from official Superfinanciera/SIMEV/RNVE structured sources discovered in v2.21C3B.

This phase extracts, filters and deduplicates Colombia candidates. If eligible candidates exist, it builds a Colombia candidate dataset on top of the Singapore promoted artifact. It does not promote Colombia, does not modify the Singapore artifact, does not modify the previous operational base, does not update pointers, does not run scoring, does not call OpenAI, does not call brokers, and does not launch full59k.

## Summary

- Build decision: `COLOMBIA_CANDIDATE_CREATED_READY_FOR_PROMOTION_OR_FREEZE_DECISION`
- Candidate dataset created: `True`
- Approved for Colombia promotion decision: `True`
- Singapore promoted rows: `43066`
- Colombia raw rows seen: `36`
- Colombia accepted by quality: `27`
- Colombia eligible new candidates: `23`
- Colombia rejected candidates: `13`
- Colombia candidate rows: `43089`
- Colombia candidate SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`
- Remaining capacity: `1911`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Checks

- colombia_discovery_status_expected: PASS (critical) — COLOMBIA_REGULATORY_DISCOVERY_EXTRACTION_DECISION_COMPLETED_STRUCTURED_SOURCE_READY_EXTRACTION_APPROVED_NO_DATASET_CHANGES_SCORING_DEFERRED
- colombia_structured_extraction_approved: PASS (critical) — approved_for_colombia_structured_extraction=True
- singapore_promotion_status_expected: PASS (critical) — SINGAPORE_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- singapore_promoted_rows_expected: PASS (critical) — singapore_promoted_rows=43066
- singapore_promoted_sha_expected: PASS (critical) — 8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f
- schema_column_count_expected: PASS (critical) — columns=33
- structured_sources_available: PASS (critical) — structured_sources=8
- raw_candidate_rows_seen: PASS (critical) — raw_candidate_rows_seen=36
- raw_candidates_accepted_by_quality_available: PASS (warning) — raw_candidates_accepted_by_quality=27
- eligible_colombia_candidates_available: PASS (warning) — eligible_new_candidates=23
- candidate_dataset_created_if_eligible: PASS (critical) — candidate_dataset_created=True;eligible=23
- candidate_dataset_under_quality_ceiling: PASS (critical) — candidate_dataset_rows=43089;ceiling=45000
- candidate_dataset_above_quality_floor: PASS (critical) — candidate_dataset_rows=43089;floor=42000
- candidate_rows_equal_singapore_plus_eligible_if_created: PASS (critical) — candidate_rows=43089;base_plus_eligible=43089
- singapore_promoted_artifact_not_modified: PASS (critical) — Singapore promoted artifact SHA unchanged
- operational_base_not_modified: PASS (critical) — operational base SHA unchanged
- rollback_not_modified: PASS (critical) — rollback SHA unchanged
- candidate_dataset_not_promoted: PASS (critical) — colombia_candidate_dataset_promoted=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

`v2.21E_C - Colombia Promotion / Freeze Decision`
