# v2.18I - TWSE + TPEx Closure Report

Status: **TWSE_TPEX_CLOSURE_COMPLETED_40996_CANDIDATES_NEXT_PROVIDER_SELECTION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **closure-report-only**

Generated at UTC: `2026-08-11T14:48:23.069919+00:00`

## Executive summary

v2.18I formally closes the TWSE + TPEx route.

The route is a partial success: TWSE contributed validated net-new candidates, while TPEx remains deferred or repair-later. The route does not reach the 50k target, so the next required step is a new provider route selection.

This phase is closure/report-only. It does not write a new expanded candidate dataset, does not replace the active canonical dataset, does not modify canonical, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Closure result

- Route: `TWSE + TPEx Taiwan`
- Route result: `partial_success_twse_only`
- TWSE status: `completed_used`
- TPEx status: `deferred_or_repair_later`
- Active canonical rows: `38287`
- Base NSE candidate rows: `40300`
- TWSE candidates extracted: `1075`
- TWSE potential net-new: `696`
- TWSE possible-existing not added: `379`
- TWSE existing not added: `0`
- TWSE added rows: `696`
- TWSE withheld rows: `0`
- Final TWSE + TPEx candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed after TWSE: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`
- Critical failed checks: `0`

## Metric summary

- active_canonical_rows: `38287` / expected `38287` rows
- base_nse_candidate_rows: `40300` / expected `40300` rows
- twse_candidates_extracted: `1075` / expected `1075` candidates
- twse_potential_net_new: `696` / expected `696` candidates
- twse_possible_existing_not_added: `379` / expected `379` candidates
- twse_existing_not_added: `0` / expected `0` candidates
- twse_added_rows: `696` / expected `696` rows
- twse_withheld_rows: `0` / expected `0` rows
- twse_tpex_expanded_candidate_rows: `40996` / expected `40996` rows
- schema_columns: `33` / expected `33` columns
- final_target_candidates: `50000` / expected `50000` rows
- rows_needed_after_twse: `9004` / expected `9004` rows

## Phase ledger

- `v2.18A` — 50k Target Route Selection — TWSE + TPEx selected as next route; full59k deprecated/deferred
- `v2.18B` — TWSE + TPEx Acquisition Plan — official-source acquisition plan
- `v2.18C` — TWSE + TPEx Raw Acquisition — raw acquisition attempted; repair required
- `v2.18D` — TWSE + TPEx Raw Validation — raw files validated; repair required
- `v2.18C_FIX` — TWSE + TPEx Raw Acquisition Repair — TWSE row-data captured; TPEx deferred
- `v2.18D_FIX` — TWSE + TPEx Repaired Raw Validation — 2 TWSE row-data sources ready for extraction
- `v2.18E` — TWSE + TPEx Candidate Extraction Dry Run — 1075 TWSE candidates extracted; DR and non-common-equity excluded
- `v2.18F` — TWSE + TPEx Candidate Validation Against Canonical Dry Run — 696 potential net-new; 379 possible existing
- `v2.18G` — TWSE + TPEx Expanded Rebuild Candidate — candidate rebuilt with 40996 rows
- `v2.18H` — TWSE + TPEx Expanded Validation — expanded candidate validated with 40996 rows
- `v2.18I` — TWSE + TPEx Closure Report — formal closure and next-provider handoff

## Source status

- `TWSE listed company profile` — completed_used — used for v2.18E extraction and v2.18G candidate rebuild
- `TWSE stock day all` — completed_used — supporting source only
- `TPEx` — deferred_or_repair_later — do not block TWSE closure; revisit in a future provider/repair route if needed
- `full59k` — deprecated_deferred_not_active — keep 50k target route only

## Next actions

- Phigh `50k` — start_next_provider_route_selection — v2.19A - Next Provider Route Selection
- Pmedium `TPEx` — defer_or_repair_later — v2.19A - Next Provider Route Selection
- Pmedium `candidate_dataset` — preserve_twse_tpex_candidate_as_validated_candidate — v2.19A - Next Provider Route Selection

## Checks

- v2_18e_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_candidate_extraction_dry_run_v2_18e.json
- v2_18f_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_candidate_validation_against_canonical_dry_run_v2_18f.json
- v2_18g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_expanded_rebuild_candidate_v2_18g.json
- v2_18h_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_expanded_validation_v2_18h.json
- v2_18e_status_expected: PASS (critical) — TWSE_TPEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_TWSE_CANDIDATES_READY_FOR_CANONICAL_VALIDATION_DRY_RUN_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18f_status_expected: PASS (critical) — TWSE_TPEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_CANONICAL_BUCKETS_READY_FOR_EXPANDED_REBUILD_CANDIDATE_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18g_status_expected: PASS (critical) — TWSE_TPEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_40996_ROWS_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18h_status_expected: PASS (critical) — TWSE_TPEX_EXPANDED_VALIDATION_COMPLETED_40996_ROWS_VALIDATED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- base_nse_rows_expected: PASS (critical) — base_rows=40300
- expanded_candidate_rows_expected: PASS (critical) — expanded_rows=40996
- row_increment_expected: PASS (critical) — row_increment=696
- schema_columns_expected: PASS (critical) — schema_columns=33
- schema_equal_base_expanded: PASS (critical) — base header equals expanded header
- twse_candidates_extracted_expected: PASS (critical) — extracted_candidates=1075
- twse_potential_net_new_expected: PASS (critical) — potential_net_new=696
- twse_possible_existing_expected: PASS (critical) — possible_existing=379
- twse_existing_expected: PASS (critical) — existing=0
- twse_added_rows_expected: PASS (critical) — added_rows=696
- twse_withheld_rows_expected: PASS (critical) — withheld_rows=0
- rows_needed_after_twse_expected: PASS (critical) — rows_needed_after_twse=9004
- v2_18h_critical_failed_checks_zero: PASS (critical) — v2_18h_critical_failed_checks=0
- row_audit_all_passed: PASS (critical) — v2.18H row audit all passed
- symbol_audit_all_passed: PASS (critical) — v2.18H symbol audit all passed
- schema_profile_rows_expected: PASS (critical) — schema_profile_rows=33
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- base_candidate_sha_unchanged: PASS (critical) — base candidate sha unchanged
- expanded_candidate_sha_unchanged: PASS (critical) — expanded candidate sha unchanged
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- no_new_expanded_dataset_written: PASS (critical) — new_expanded_dataset_written=False
- closure_report_only: PASS (critical) — phase_type=closure-report-only
- network_not_used: PASS (critical) — network_download_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- full59k_deprecated_deferred: PASS (critical) — full59k=DEPRECATED_DEFERRED
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- next_provider_needed: PASS (critical) — rows_needed_after_twse=9004

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Closure report performed: true
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`v2.19A - Next Provider Route Selection`
