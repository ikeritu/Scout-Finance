# v2.21C2 — Candidate Extraction False Positive Review

Status: **TARGETED_MARKET_CANDIDATE_FALSE_POSITIVE_REVIEW_COMPLETED_ACCEPTED_CANDIDATES_INVALIDATED_REBUILD_BLOCKED_SOURCE_DISCOVERY_REQUIRED**

Phase type: **targeted-market-candidate-extraction-false-positive-review**

Generated at UTC: `2026-08-12T22:15:25.121765+00:00`

## Executive summary

v2.21C2 reviews the accepted candidates from v2.21C and invalidates them as false positives.

This phase is audit-only. It does not rewrite v2.21C, does not re-run extraction, does not rebuild, does not promote, does not update pointers, does not run scoring, does not call OpenAI, does not call brokers, and does not launch full59k.

## Summary

- Review decision: `V2_21C_ACCEPTED_CANDIDATES_INVALIDATED_V2_21D_BLOCKED_V2_21C3_REQUIRED`
- Approved for v2.21C3: `True`
- Approved for v2.21D: `False`
- Operational base rows: `42708`
- Operational base SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Rollback rows: `38287`
- Rollback SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- v2.21C accepted candidates reviewed: `3`
- v2.21C accepted candidates invalidated: `3`
- Approved candidates after review: `0`
- Structured candidate sources: `0`
- Regex-only sources: `4`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Invalidated candidates

- `v2_21c_00001` — `COLOMBIA_BVC` — `GTM` / `KSZ85XQ8')` — `GOOGLE_TAG_MANAGER_TOKEN` — approved for rebuild `False`
- `v2_21c_00002` — `SINGAPORE_SGX` — `UA` / `Compatible` — `BROWSER_USER_AGENT_TOKEN` — approved for rebuild `False`
- `v2_21c_00003` — `SINGAPORE_SGX` — `5DY4G` / `LV8JN-2CLEK-T7VJU` — `HASH_OR_INTERNAL_BUILD_ID` — approved for rebuild `False`

## Source structure review

- `BVC_OFFICIAL_ISSUERS_AND_PROSPECTUSES` — structured `False` — regex_only `True` — status `regex_only_unreliable_for_rebuild`
- `BVC_RESULTS_AND_ISSUER_INFORMATION` — structured `False` — regex_only `True` — status `regex_only_unreliable_for_rebuild`
- `SGX_SECURITIES_PRICES` — structured `False` — regex_only `True` — status `regex_only_unreliable_for_rebuild`
- `SGX_CORPORATE_INFORMATION` — structured `False` — regex_only `True` — status `regex_only_unreliable_for_rebuild`

## Decision register

- `FP_REVIEW_001` — accepted `True` — Invalidate accepted candidates from v2.21C.
- `FP_REVIEW_002` — accepted `True` — Block v2.21D rebuild from current extraction output.
- `FP_REVIEW_003` — accepted `True` — Require official endpoint, API, CSV, XLS or structured downloadable listing.
- `FP_REVIEW_004` — accepted `True` — Preserve operational base and rollback.
- `FP_REVIEW_005` — accepted `True` — Keep scoring, OpenAI, broker and full59k deferred.

## Checks

- v2_21c_status_expected: PASS (critical) — TARGETED_MARKET_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_NEW_CANDIDATES_READY_FOR_REBUILD_NO_DATASET_CHANGES_SCORING_DEFERRED
- v2_21b_status_expected: PASS (critical) — TARGETED_MARKET_ACQUISITION_RAW_VALIDATION_COMPLETED_COLOMBIA_SINGAPORE_RAW_SOURCES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- schema_column_count_expected: PASS (critical) — columns=33
- v2_21c_extracted_candidates_loaded: PASS (critical) — extracted_candidates=3
- all_v2_21c_accepted_candidates_invalidated: PASS (critical) — invalidated=3;accepted_in_v2_21c=3
- no_candidates_approved_for_rebuild_after_review: PASS (critical) — approved_candidates_after_review=0
- structured_candidate_sources_not_available: PASS (warning) — structured_sources=0
- regex_only_sources_detected: PASS (warning) — regex_only_sources=4
- v2_21d_rebuild_blocked: PASS (critical) — v2.21D blocked until official structured candidates exist
- v2_21c3_source_discovery_required: PASS (critical) — official endpoint/downloadable listing discovery required
- operational_base_not_modified: PASS (critical) — operational base SHA unchanged
- false_positive_review_is_audit_only: PASS (critical) — no artifact rewrite; no history rewrite; no force push
- candidate_extraction_not_reexecuted: PASS (critical) — review uses v2.21C outputs only
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

`v2.21C3 - Official Endpoint / Downloadable Listing Discovery`
