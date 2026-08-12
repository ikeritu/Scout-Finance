# v2.21C — Candidate Extraction + Dedup Dry Run

Status: **TARGETED_MARKET_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_NEW_CANDIDATES_READY_FOR_REBUILD_NO_DATASET_CHANGES_SCORING_DEFERRED**

Phase type: **targeted-market-candidate-extraction-dedup-dry-run**

Generated at UTC: `2026-08-12T21:55:35.445622+00:00`

## Executive summary

v2.21C performs a strict candidate extraction and dedup dry run for Colombia/BVC and Singapore/SGX using the raw sources captured in v2.21B.

This phase does not rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Extraction decision: `NEW_CANDIDATES_AVAILABLE_FOR_EXPANDED_REBUILD_CANDIDATE`
- Approved for next phase: `True`
- Operational base rows: `42708`
- Operational base SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Rollback rows: `38287`
- Rollback SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Successful raw sources: `4`
- Candidate attempts: `10`
- Accepted new candidates: `3`
- Rejected candidates: `7`
- Projected rows after addition: `42711`
- Remaining capacity after addition: `2289`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Source parser findings

- `BVC_OFFICIAL_ISSUERS_AND_PROSPECTUSES` — attempts `3` — status `CANDIDATES_FOUND` — tables `0` — next_data_objects `267`
- `BVC_RESULTS_AND_ISSUER_INFORMATION` — attempts `3` — status `CANDIDATES_FOUND` — tables `0` — next_data_objects `272`
- `SGX_SECURITIES_PRICES` — attempts `2` — status `CANDIDATES_FOUND` — tables `0` — next_data_objects `0`
- `SGX_CORPORATE_INFORMATION` — attempts `2` — status `CANDIDATES_FOUND` — tables `0` — next_data_objects `0`

## Dedup summary

- `COLOMBIA_BVC` — attempts `6` — accepted `1` — rejected `5` — ready `True`
- `SINGAPORE_SGX` — attempts `4` — accepted `2` — rejected `2` — ready `True`

## Checks

- v2_21b_status_expected: PASS (critical) — TARGETED_MARKET_ACQUISITION_RAW_VALIDATION_COMPLETED_COLOMBIA_SINGAPORE_RAW_SOURCES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED
- v2_21b_acquisition_decision_expected: PASS (critical) — RAW_SOURCES_AVAILABLE_FOR_CANDIDATE_EXTRACTION_DRY_RUN
- v2_21b_approved_for_next_phase: PASS (critical) — approved_for_next_phase=True
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- schema_column_count_expected: PASS (critical) — columns=33
- successful_raw_sources_available: PASS (critical) — successful_raw_sources=4
- candidate_extraction_attempted: PASS (critical) — candidate extraction attempted from v2.21B raw files
- dedup_dry_run_performed: PASS (critical) — dedup dry run performed against operational base
- new_candidates_extracted: PASS (warning) — accepted_new_candidates=3
- projected_rows_under_ceiling: PASS (critical) — projected_rows=42711;ceiling=45000
- operational_base_not_modified: PASS (critical) — operational base SHA unchanged
- candidate_output_is_dry_run_only: PASS (critical) — no rebuild/promotion/pointer update in v2.21C
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

`v2.21D - Expanded Rebuild Candidate`
