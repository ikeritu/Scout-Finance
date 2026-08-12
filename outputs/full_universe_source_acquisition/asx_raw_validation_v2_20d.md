# v2.20D — ASX Raw Validation

Status: **ASX_RAW_VALIDATION_COMPLETED_REPAIR_RECOMMENDED_EXTRACTION_POSSIBLE_WITH_ISIN_XLS_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED**

Phase type: **raw-validation-only**

Generated at UTC: `2026-08-12T09:12:13.623848+00:00`

## Executive summary

v2.20D validates ASX raw files captured in v2.20C.

The raw set is considered ready for extraction dry run if required ASX pages exist, captured file hashes match the v2.20C manifest, the ISIN XLS is captured, and the ISIN XLS is a valid Excel container.

The legacy ASXListedCompanies CSV endpoint returned `404` and remains optional. Repair is recommended only if the ISIN XLS extraction dry run fails or yields too few clean candidates.

This phase performs raw validation only. It does not download new files, extract candidates, validate candidates against canonical, rebuild datasets, promote canonical, run scoring, call OpenAI, call brokers, run repo-wide renormalization or launch full59k.

## Validation summary

- Selected provider: `ASX`
- Manifest rows: `7`
- Attempts rows: `8`
- Required pages captured: `True`
- HTML required signals ready: `True`
- ISIN XLS captured: `True`
- ISIN XLS binary valid: `True`
- ISIN XLS optional parse ready: `True`
- Complete list legacy CSV captured: `False`
- Legacy CSV status: `404`
- Complete list route needs repair: `True`
- Last price CSV captured: `True`
- Last price CSV parseable: `True`
- Last price CSV rows: `4603`
- Parse ready for extraction: `True`
- Current HKEX validated candidate rows: `41392`
- Rows needed to 42k: `608`
- Rows needed to 45k: `3608`
- Critical failed checks: `0`
- Warning failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Source readiness

- `asx_required_pages` — `ready` — required_pages_captured=True;html_required_signal_ready=True
- `asx_isin_xls_direct` — `ready` — captured=True;binary_valid_excel_container=True;optional_parse_ready=True
- `asx_complete_list_legacy_csv` — `not_ready_optional` — captured=False;legacy_status=404
- `asx_last_known_closing_price_csv` — `ready_context_only` — captured=True;parseable=True;rows=4603

## XLS profile

- `asx_isin_xls_direct` — binary_valid `True` — optional_parse `parseable_with_pandas` — ``

## CSV profile

- `asx_discovered_last_known_closing_price_fy26` — rows `4603` — columns `6` — parseable `True`

## Checks

- v2_20c_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_quality_first_raw_acquisition_v2_20c.json
- v2_20c_status_expected: PASS (critical) — ASX_QUALITY_FIRST_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED
- v2_20c_next_phase_expected: PASS (critical) — v2.20D - ASX Raw Validation
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- hkex_validated_candidate_rows_expected: PASS (critical) — hkex_rows=41392
- active_canonical_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- current_candidate_sha_expected: PASS (critical) — 05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2
- hkex_validated_candidate_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- active_canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- current_candidate_sha_unchanged: PASS (critical) — current candidate sha unchanged
- hkex_candidate_sha_unchanged: PASS (critical) — HKEX candidate sha unchanged
- quality_floor_target_preserved: PASS (critical) — quality_floor=42000
- quality_ceiling_target_preserved: PASS (critical) — quality_ceiling=45000
- rows_needed_to_quality_floor_expected: PASS (critical) — rows_needed_to_42k=608
- rows_needed_to_quality_ceiling_expected: PASS (critical) — rows_needed_to_45k=3608
- rows_needed_to_50k_aspirational_expected: PASS (warning) — rows_needed_to_50k=8608
- raw_manifest_loaded: PASS (critical) — manifest_rows=7
- attempts_loaded: PASS (critical) — attempts=8
- all_manifest_files_exist: PASS (critical) — all_files_exist=True
- all_manifest_files_non_empty: PASS (critical) — all_files_non_empty=True
- all_manifest_sha_match: PASS (critical) — all_files_sha_match=True
- required_pages_captured: PASS (critical) — required_pages_captured=True
- market_statistics_page_captured: PASS (warning) — market_statistics_captured=True
- html_required_signals_ready: PASS (critical) — html_required_signal_ready=True
- isin_xls_captured: PASS (critical) — isin_xls_captured=True
- isin_xls_binary_valid: PASS (critical) — isin_xls_binary_valid=True
- isin_xls_optional_pandas_parse_ready: PASS (warning) — optional_parse_ready=True
- legacy_complete_list_csv_optional_404_documented: PASS (warning) — legacy_csv_status=404;captured=False
- last_price_csv_parseable_context_only: PASS (warning) — last_price_csv_parseable=True;rows=4603
- discovered_download_candidates_available: PASS (warning) — download_candidates=4
- parse_ready_for_extraction: PASS (critical) — parse_ready_for_extraction=True
- raw_validation_only: PASS (critical) — raw validation only
- network_download_not_performed: PASS (critical) — network_download_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- candidate_validation_not_performed: PASS (critical) — candidate_validation_against_canonical_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- expanded_validation_not_performed: PASS (critical) — expanded_validation_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- current_candidate_dataset_not_modified: PASS (critical) — current_candidate_dataset_modified=False
- hkex_candidate_dataset_not_modified: PASS (critical) — hkex_candidate_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Next actions

- Phigh `ASX` — open_asx_candidate_extraction_dry_run — v2.20E - ASX Candidate Extraction Dry Run
- Pmedium `ASX_complete_list` — defer_legacy_complete_list_repair_until_after_isin_extraction_yield — v2.20E - ASX Candidate Extraction Dry Run
- Phigh `quality_target` — preserve_42k_45k_operational_band — v2.20E - ASX Candidate Extraction Dry Run

## Guards

- Raw validation only: true
- Network download performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current candidate dataset modified: false
- HKEX validated candidate dataset modified: false
- Active canonical replaced: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20E - ASX Candidate Extraction Dry Run`
