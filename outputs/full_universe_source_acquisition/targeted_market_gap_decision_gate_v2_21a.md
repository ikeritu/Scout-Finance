# v2.21A — Colombia + Singapore Targeted Expansion Gate

Status: **TARGETED_MARKET_GAP_DECISION_GATE_COMPLETED_COLOMBIA_SINGAPORE_APPROVED_FOR_PLANNING_42708_ROWS_NO_DATA_CHANGES_SCORING_DEFERRED**

Phase type: **targeted-market-gap-decision-gate-only**

Generated at UTC: `2026-08-12T21:35:00.478195+00:00`

## Executive summary

v2.21A opens a narrow targeted market-gap decision gate for Colombia and Singapore.

It does not acquire data, edit files, replace canonical, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Gate summary

- Gate decision: `COLOMBIA_SINGAPORE_TARGETED_EXPANSION_APPROVED_FOR_ACQUISITION_AND_RAW_VALIDATION`
- Approved for next phase: `True`
- Operational base dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_20m_asx_promoted.csv`
- Operational base rows: `42708`
- Operational base SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Rollback dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Rollback rows: `38287`
- Rollback SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Remaining capacity to 45k ceiling: `2292`
- Target markets: `Colombia/BVC`, `Singapore/SGX`
- Provider expansion scope: `targeted_only`
- Scoring authorized: `False`
- OpenAI authorized: `False`
- Broker authorized: `False`
- full59k: `DEPRECATED_DEFERRED`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Target markets

- `COLOMBIA_BVC` — present `False` — approved `True` — User-requested missing market; small targeted LatAm expansion.
- `SINGAPORE_SGX` — present `False` — approved `True` — User-requested missing market; high-quality Asian developed market coverage.

## Source candidates

- `BVC_OFFICIAL_ISSUERS_AND_PROSPECTUSES` — provider `BVC` — planned for `v2.21B`
- `BVC_RESULTS_AND_ISSUER_INFORMATION` — provider `BVC` — planned for `v2.21B`
- `SGX_SECURITIES_PRICES` — provider `SGX` — planned for `v2.21B`
- `SGX_CORPORATE_INFORMATION` — provider `SGX` — planned for `v2.21B`

## Decision register

- `TARGET_GAP_001` — accepted `True` — Approve Colombia + Singapore targeted expansion planning.
- `TARGET_GAP_002` — accepted `True` — Keep expansion narrow.
- `TARGET_GAP_003` — accepted `True` — Do not authorize scoring.
- `TARGET_GAP_004` — accepted `True` — Keep full59k deprecated/deferred.
- `TARGET_GAP_005` — accepted `True` — Preserve ASX operational base and v2_14e rollback.

## Checks

- v2_20t_status_expected: PASS (critical) — ASX_FINAL_PROMOTION_CLOSURE_REPORT_COMPLETED_OPERATIONAL_BASE_RECOGNIZED_42708_ROWS_ROLLBACK_AVAILABLE_SCORING_DEFERRED_FULL59K_DEPRECATED
- v2_20t_closure_decision_expected: PASS (critical) — ASX_PROMOTION_CLOSED_PROMOTED_CANONICAL_RECOGNIZED_AS_OPERATIONAL_BASE_SCORING_DEFERRED
- v2_20t_asx_promotion_closed: PASS (critical) — asx_promotion_closed=True
- v2_20t_scoring_deferred: PASS (critical) — scoring_authorized=False
- v2_20t_provider_expansion_was_frozen_before_new_gate: PASS (critical) — provider_expansion_frozen=True
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- schema_column_count_expected: PASS (critical) — columns=33
- required_country_column_present: PASS (critical) — country column present
- required_exchange_column_present: PASS (critical) — exchange column present
- required_mic_column_present: PASS (critical) — mic column present
- required_currency_column_present: PASS (critical) — currency column present
- operational_floor_already_achieved: PASS (critical) — rows=42708;floor=42000
- operational_ceiling_capacity_available: PASS (critical) — remaining_capacity=2292
- remaining_capacity_at_least_100_rows: PASS (warning) — remaining_capacity=2292
- target_market_gap_confirmed::COLOMBIA_BVC: PASS (warning) — country_hits=0;exchange_hits=0;mic_hits=0;currency_hits=0
- target_market_gap_confirmed::SINGAPORE_SGX: PASS (warning) — country_hits=0;exchange_hits=0;mic_hits=0;currency_hits=0
- decision_gate_only: PASS (critical) — targeted market gap decision gate only
- network_download_not_performed: PASS (critical) — network_download_performed=False
- raw_acquisition_not_performed: PASS (critical) — raw_acquisition_performed=False
- file_edit_not_performed: PASS (critical) — file_edit_performed=False
- file_copy_not_performed: PASS (critical) — file_copy_performed=False
- file_rename_not_performed: PASS (critical) — file_rename_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

`v2.21B - Colombia/BVC + Singapore/SGX Acquisition & Raw Validation`
