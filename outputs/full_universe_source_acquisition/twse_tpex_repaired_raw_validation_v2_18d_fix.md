# v2.18D_FIX - TWSE + TPEx Repaired Raw Validation

Status: **TWSE_TPEX_REPAIRED_RAW_VALIDATION_COMPLETED_ROW_DATA_VALID_CANDIDATE_EXTRACTION_DRY_RUN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **repaired-raw-validation-only**

Generated at UTC: `2026-08-11T10:17:55.101857+00:00`

## Executive summary

v2.18D_FIX validates the repaired raw artifacts produced by v2.18C_FIX.

This is a local repaired-raw-validation-only phase. It does not perform network calls, endpoint calls, raw acquisition, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Validated candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv`
- Validated candidate rows: `40300`
- Final target candidates: `50000`
- Rows needed to 50k: `9700`
- Candidate completion: `80.6%`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Repaired raw validation summary

- Repair manifest rows: `6`
- Raw files exist: `6/6`
- Bytes match manifest: `6/6`
- SHA-256 match manifest: `6/6`
- Manifest row-data candidates: `2`
- Validated row-data candidates: `2`
- Ready-for-extraction sources: `2`
- Schema-ready sources: `2`
- TWSE ready sources: `2`
- TPEx still error sources: `2`
- Non-official selected downloads: `0`
- Critical failed checks: `0`

## File profile

- `twse_ssl_repair_twse_openapi_swagger` — TWSE — valid_support_html_artifact — format `html` — rows `0` — readiness `support_html_only_not_for_direct_extraction`
- `twse_ssl_repair_twse_listed_company_profile` — TWSE — validated_row_data_candidate — format `json_like` — rows `1094` — readiness `ready_for_candidate_extraction_dry_run`
- `twse_ssl_repair_twse_stock_day_all` — TWSE — validated_row_data_candidate — format `json_like` — rows `1378` — readiness `ready_for_candidate_extraction_dry_run`
- `twse_ssl_repair_twse_latest_listed_companies` — TWSE — valid_support_html_artifact — format `html` — rows `278` — readiness `support_html_only_not_for_direct_extraction`
- `tpex_openapi_swagger_json_repair` — TPEx — captured_error_payload — format `error_text` — rows `0` — readiness `tpex_still_not_ready_technical_error`
- `tpex_mainboard_daily_close_quotes_known_endpoint` — TPEx — captured_error_payload — format `error_text` — rows `0` — readiness `tpex_still_not_ready_technical_error`

## Schema profile

- `twse_ssl_repair_twse_openapi_swagger` — not_parse_ready — rows `0` — cols `0` — symbol `` — name ``
- `twse_ssl_repair_twse_listed_company_profile` — candidate_schema_ready — rows `1094` — cols `33` — symbol `公司代號` — name `公司名稱|公司簡稱`
- `twse_ssl_repair_twse_stock_day_all` — candidate_schema_ready — rows `1378` — cols `11` — symbol `Code` — name `Name`
- `twse_ssl_repair_twse_latest_listed_companies` — not_parse_ready — rows `278` — cols `0` — symbol `` — name ``
- `tpex_openapi_swagger_json_repair` — not_parse_ready — rows `0` — cols `0` — symbol `` — name ``
- `tpex_mainboard_daily_close_quotes_known_endpoint` — not_parse_ready — rows `0` — cols `0` — symbol `` — name ``

## Source diagnostics

- `twse_ssl_repair_twse_openapi_swagger` — ready `support_html_only_not_for_direct_extraction` — repair_still_required `False` — use_as_support_crosscheck_only
- `twse_ssl_repair_twse_listed_company_profile` — ready `ready_for_candidate_extraction_dry_run` — repair_still_required `False` — use_as_primary_source_in_v2_18e_dry_run
- `twse_ssl_repair_twse_stock_day_all` — ready `ready_for_candidate_extraction_dry_run` — repair_still_required `False` — use_as_primary_source_in_v2_18e_dry_run
- `twse_ssl_repair_twse_latest_listed_companies` — ready `support_html_only_not_for_direct_extraction` — repair_still_required `False` — use_as_support_crosscheck_only
- `tpex_openapi_swagger_json_repair` — ready `tpex_still_not_ready_technical_error` — repair_still_required `True` — keep_tpex_as_deferred_or repair_later_if_twse_delta_insufficient
- `tpex_mainboard_daily_close_quotes_known_endpoint` — ready `tpex_still_not_ready_technical_error` — repair_still_required `True` — keep_tpex_as_deferred_or repair_later_if_twse_delta_insufficient

## Next actions

- Phigh `TWSE` — proceed_to_candidate_extraction_dry_run — v2.18E - TWSE + TPEx Candidate Extraction Dry Run
- Pmedium `TPEx` — defer_or_repair_tpex_later — v2.18E - TWSE + TPEx Candidate Extraction Dry Run

## Checks

- v2_18c_fix_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_v2_18c_fix.json
- v2_18c_fix_status_expected: PASS (critical) — TWSE_TPEX_RAW_ACQUISITION_REPAIR_COMPLETED_ROW_DATA_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18d_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_validation_v2_18d.json
- v2_18d_status_expected: PASS (critical) — TWSE_TPEX_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- repair_manifest_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_manifest_v2_18c_fix.csv
- repair_decision_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_decision_v2_18c_fix.csv
- endpoint_discovery_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_endpoint_discovery_v2_18c_fix.csv
- repair_source_actions_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_source_actions_v2_18c_fix.csv
- previous_raw_diagnostics_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_validation_source_diagnostics_v2_18d.csv
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- validated_candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- validated_candidate_rows_expected: PASS (critical) — validated_candidate_rows=40300
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9700
- candidate_schema_matches_canonical: PASS (critical) — canonical_cols=33 candidate_cols=33
- repair_manifest_rows_present: PASS (critical) — repair_manifest_rows=6
- repair_raw_files_exist: PASS (critical) — 6/6
- repair_raw_bytes_match_manifest: PASS (critical) — 6/6
- repair_raw_sha256_match_manifest: PASS (critical) — 6/6
- manifest_row_data_candidates_preserved: PASS (critical) — manifest_row_data_count=2
- validated_row_data_candidates_detected: PASS (critical) — validated_row_data_count=2
- ready_for_extraction_sources_detected: PASS (critical) — ready_for_extraction_count=2
- twse_repaired_row_data_detected: PASS (critical) — twse_ready_count=2
- network_not_used_in_repaired_validation: PASS (critical) — network_download_performed=False
- raw_acquisition_not_performed: PASS (critical) — raw_acquisition_performed=False
- raw_files_not_modified: PASS (critical) — raw_files_modified=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- canonical_sha_unchanged: PASS (critical) — canonical sha unchanged
- network_scope_official_discovery_preserved: PASS (critical) — non_official_selected_downloads=0
- final_50k_gate_still_blocked: PASS (critical) — 40300 < 50000
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- tpex_still_requires_repair_or_deferral: PASS (warning) — tpex_still_error_count=2
- schema_ready_sources_detected: PASS (warning) — schema_ready_count=2

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw acquisition repair performed: false
- Repaired raw validation performed: true
- Raw files read: true
- Raw files written: false
- Raw files modified: false
- Repair manifest read: true
- File profile written: true
- Schema profile written: true
- Source diagnostics written: true
- Next actions written: true
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Final target 50k active: true
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Overwrite allowed: false

## Conclusion

v2.18D_FIX determines whether repaired TWSE/TPEx raw artifacts are valid enough for candidate extraction dry run.

## Recommended next phase

`v2.18E - TWSE + TPEx Candidate Extraction Dry Run`
