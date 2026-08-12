# v2.21C4S — Singapore Structured Candidate Extraction + Dedup Dry Run

Status: **SINGAPORE_STRUCTURED_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_ELIGIBLE_CANDIDATES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED**

Phase type: **targeted-market-singapore-structured-candidate-extraction-dedup-dry-run**

Generated at UTC: `2026-08-12T22:58:45.079701+00:00`

## Executive summary

v2.21C4S performs a Singapore-only structured candidate extraction and dedup dry run from SGX structured JSON endpoints validated in v2.21C3 and approved by v2.21C3_REVIEW.

This phase does not include Colombia. Colombia remains on the separate v2.21C3B regulatory discovery path.

This phase does not rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Extraction decision: `SINGAPORE_ELIGIBLE_CANDIDATES_READY_FOR_EXPANDED_REBUILD_CANDIDATE`
- Approved for Singapore rebuild candidate: `True`
- Approved for global v2.21D: `False`
- Operational base rows: `42708`
- Operational base SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Rollback rows: `38287`
- Rollback SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Structured SGX endpoints used: `2`
- Raw candidates extracted: `1554`
- Eligible new candidates: `358`
- Rejected candidates: `1196`
- Projected rows after addition: `43066`
- Remaining capacity after addition: `1934`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Source endpoints

- `SGX_SECURITIES_V1_1_JSON_MINIMAL` — records `1278` — selected `True`
- `SGX_SECURITIES_V1_1_JSON_EXTENDED` — records `1278` — selected `True`

## Dedup summary

- `SINGAPORE_SGX` — raw `1554` — eligible `358` — rejected `1196` — projected rows `43066`

## Checks

- v2_21c3_status_expected: PASS (critical) — TARGETED_MARKET_OFFICIAL_ENDPOINT_DISCOVERY_COMPLETED_PARTIAL_STRUCTURED_ENDPOINTS_FOUND_REVIEW_REQUIRED
- v2_21c3_review_status_expected: PASS (critical) — TARGETED_MARKET_MISSING_ENDPOINT_REVIEW_COMPLETED_SPLIT_ROUTE_APPROVED_SGX_READY_COLOMBIA_REGULATORY_DISCOVERY_REQUIRED
- singapore_structured_extraction_approved: PASS (critical) — approved_for_singapore_structured_extraction=True
- colombia_not_in_scope: PASS (critical) — Colombia remains discovery-only and is not extracted in v2.21C4S.
- global_v2_21c4_not_approved: PASS (critical) — approved_for_global_v2_21c4=False
- v2_21d_not_approved: PASS (critical) — approved_for_v2_21d=False
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- schema_column_count_expected: PASS (critical) — columns=33
- structured_sgx_endpoints_available: PASS (critical) — structured_sgx_endpoints=2
- raw_candidates_extracted: PASS (critical) — raw_candidates=1554
- eligible_candidates_available: PASS (warning) — eligible_candidates=358
- projected_rows_under_quality_ceiling: PASS (critical) — projected_rows=43066;ceiling=45000
- capacity_remaining_non_negative: PASS (critical) — remaining_capacity_after_addition=1934
- operational_base_not_modified: PASS (critical) — operational base SHA unchanged
- rollback_not_modified: PASS (critical) — rollback SHA unchanged
- singapore_only_scope: PASS (critical) — all candidate rows are Singapore/SGX scoped
- regex_only_candidate_acceptance_not_allowed: PASS (critical) — only structured JSON endpoint objects are parsed
- dedup_dry_run_performed: PASS (critical) — dedup dry run performed against operational base
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.21D_S - Singapore Expanded Rebuild Candidate`

Secondary: `v2.21C3B - Colombia Regulatory Source Discovery`
