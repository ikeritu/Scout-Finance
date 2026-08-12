# v2.21B — Colombia/BVC + Singapore/SGX Acquisition & Raw Validation

Status: **TARGETED_MARKET_ACQUISITION_RAW_VALIDATION_COMPLETED_COLOMBIA_SINGAPORE_RAW_SOURCES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED**

Phase type: **targeted-market-raw-acquisition-and-validation**

Generated at UTC: `2026-08-12T21:44:26.441015+00:00`

## Executive summary

v2.21B performs controlled raw acquisition and validation for Colombia/BVC and Singapore/SGX.

This phase captures raw official source material only. It does not extract candidates, deduplicate, rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Acquisition decision: `RAW_SOURCES_AVAILABLE_FOR_CANDIDATE_EXTRACTION_DRY_RUN`
- Approved for next phase: `True`
- Operational base rows: `42708`
- Operational base SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Rollback rows: `38287`
- Rollback SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Remaining capacity to 45k ceiling: `2292`
- Sources attempted: `4`
- Sources successful: `4`
- Raw directory: `outputs\full_universe_source_acquisition\raw_targeted_markets_v2_21b`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Source fetches

- `BVC_OFFICIAL_ISSUERS_AND_PROSPECTUSES` — success `True` — status `200` — bytes `38628` — `PASS`
- `BVC_RESULTS_AND_ISSUER_INFORMATION` — success `True` — status `200` — bytes `38872` — `PASS`
- `SGX_SECURITIES_PRICES` — success `True` — status `200` — bytes `14859` — `PASS`
- `SGX_CORPORATE_INFORMATION` — success `True` — status `200` — bytes `14860` — `PASS`

## Market readiness

- `COLOMBIA_BVC` — ready `True` — successes `2` — failed `0`
- `SINGAPORE_SGX` — ready `True` — successes `2` — failed `0`

## Checks

- v2_21a_status_expected: PASS (critical) — TARGETED_MARKET_GAP_DECISION_GATE_COMPLETED_COLOMBIA_SINGAPORE_APPROVED_FOR_PLANNING_42708_ROWS_NO_DATA_CHANGES_SCORING_DEFERRED
- v2_21a_gate_decision_expected: PASS (critical) — COLOMBIA_SINGAPORE_TARGETED_EXPANSION_APPROVED_FOR_ACQUISITION_AND_RAW_VALIDATION
- v2_21a_approved_for_next_phase: PASS (critical) — approved_for_next_phase=True
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- schema_column_count_expected: PASS (critical) — columns=33
- operational_floor_preserved: PASS (critical) — rows=42708;floor=42000
- operational_ceiling_preserved: PASS (critical) — rows=42708;ceiling=45000
- raw_source_available::COLOMBIA_BVC: PASS (critical) — success_count=2;failed_count=0;total_raw_bytes=77500
- primary_source_available::COLOMBIA_BVC: PASS (warning) — primary_success_count=1
- raw_source_available::SINGAPORE_SGX: PASS (critical) — success_count=2;failed_count=0;total_raw_bytes=29719
- primary_source_available::SINGAPORE_SGX: PASS (warning) — primary_success_count=1
- at_least_two_sources_successful: PASS (warning) — successful_sources=4;total_sources=4
- raw_files_registered: PASS (critical) — raw_file_rows=8
- raw_acquisition_performed: PASS (critical) — official raw source fetches attempted
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- dedup_not_performed: PASS (critical) — dedup_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

`v2.21C - Candidate Extraction + Dedup Dry Run`
