# v2.18D - TWSE + TPEx Raw Validation

Status: **TWSE_TPEX_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **raw-validation-only**

Generated at UTC: `2026-08-11T09:38:49.031667+00:00`

## Executive summary

v2.18D validates the TWSE + TPEx raw artifacts captured in v2.18C.

This is a local raw-validation-only phase. It does not perform network calls, endpoint calls, raw acquisition, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

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

## Raw validation summary

- Manifest rows: `9`
- Raw files exist: `9/9`
- Bytes match manifest: `9/9`
- SHA-256 match manifest: `9/9`
- HTTP 200 sources: `5`
- Network error sources: `4`
- TWSE technical error sources: `4`
- TPEx HTTP 200 sources: `5`
- Primary candidate sources: `2`
- Parse-ready primary candidate sources: `0`
- HTML landing primary sources: `1`
- Repair required count: `5`
- Critical failed checks: `0`

## File profile

- `twse_openapi_swagger` — TWSE — technical_acquisition_error_captured — error_text — readiness `not_ready_technical_acquisition_error`
- `twse_listed_company_profile` — TWSE — technical_acquisition_error_captured — json_like — readiness `not_ready_technical_acquisition_error`
- `twse_stock_day_all` — TWSE — technical_acquisition_error_captured — json_like — readiness `not_ready_technical_acquisition_error`
- `twse_latest_listed_companies` — TWSE — technical_acquisition_error_captured — error_text — readiness `not_ready_technical_acquisition_error`
- `tpex_openapi_swagger` — TPEx — valid_catalog_raw_artifact — html — readiness `catalog_only_not_for_direct_extraction`
- `tpex_daily_stock_quotes` — TPEx — html_landing_page_not_row_data — html — readiness `not_ready_html_landing_page_or_dynamic_download`
- `tpex_stock_pricing_page` — TPEx — support_html_artifact — html — readiness `support_source_html_only`
- `tpex_mainboard_applicant_companies` — TPEx — valid_review_only_raw_artifact — html — readiness `review_only_not_safe_for_auto_extraction`
- `tpex_gisa_company` — TPEx — valid_review_only_raw_artifact — html — readiness `review_only_not_safe_for_auto_extraction`

## Source diagnostics

- `twse_openapi_swagger` — repair_required `True` — not_ready_technical_acquisition_error — repair_acquisition_client_or_source_access_before_extraction
- `twse_listed_company_profile` — repair_required `True` — not_ready_technical_acquisition_error — repair_acquisition_client_or_source_access_before_extraction
- `twse_stock_day_all` — repair_required `True` — not_ready_technical_acquisition_error — repair_acquisition_client_or_source_access_before_extraction
- `twse_latest_listed_companies` — repair_required `True` — not_ready_technical_acquisition_error — repair_acquisition_client_or_source_access_before_extraction
- `tpex_openapi_swagger` — repair_required `False` — catalog_only_not_for_direct_extraction — use_catalog_only_for_endpoint_discovery_if_needed
- `tpex_daily_stock_quotes` — repair_required `True` — not_ready_html_landing_page_or_dynamic_download — resolve_static_csv_json_endpoint_or parse page links in a repair phase
- `tpex_stock_pricing_page` — repair_required `False` — support_source_html_only — use only as crosscheck after primary row-data exists
- `tpex_mainboard_applicant_companies` — repair_required `False` — review_only_not_safe_for_auto_extraction — keep_as_diagnostic_or_future_route
- `tpex_gisa_company` — repair_required `False` — review_only_not_safe_for_auto_extraction — keep_as_diagnostic_or_future_route

## Next actions

- Phigh `TWSE` — repair_ssl_or_client_acquisition_for_twse_sources — v2.18C_FIX - TWSE + TPEx Raw Acquisition Repair
- Phigh `TPEx` — resolve_static_csv_or_json_endpoint_from_html_landing_page — v2.18C_FIX - TWSE + TPEx Raw Acquisition Repair

## Checks

- v2_18c_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c.json
- v2_18c_status_expected: PASS (critical) — TWSE_TPEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18c_manifest_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_manifest_v2_18c.csv
- v2_18c_source_actions_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_source_actions_v2_18c.csv
- raw_directory_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c
- source_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_source_plan_v2_18b.csv
- filter_policy_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_filter_policy_v2_18b.csv
- schema_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_candidate_schema_plan_v2_18b.csv
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- validated_candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- validated_candidate_rows_expected: PASS (critical) — validated_candidate_rows=40300
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9700
- candidate_schema_matches_canonical: PASS (critical) — canonical_cols=33 candidate_cols=33
- manifest_rows_expected: PASS (critical) — manifest_rows=9
- source_actions_present: PASS (critical) — source_actions=12
- raw_files_exist: PASS (critical) — 9/9
- raw_bytes_match_manifest: PASS (critical) — 9/9
- raw_sha256_match_manifest: PASS (critical) — 9/9
- raw_artifacts_profiled: PASS (critical) — file_profile_rows=9
- http_200_or_error_captured: PASS (critical) — http_200=5 network_error=4
- canonical_sha_unchanged: PASS (critical) — canonical sha unchanged
- network_not_used_in_validation: PASS (critical) — network_download_performed=False
- raw_files_not_modified: PASS (critical) — raw_files_modified=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- final_50k_gate_still_blocked: PASS (critical) — 40300 < 50000
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- twse_ssl_errors_detected_and_captured: PASS (warning) — twse_error_sources=4
- tpex_http_200_sources_detected: PASS (warning) — tpex_http_200_sources=5
- primary_candidate_sources_parse_ready: FAIL (warning) — parse_ready_primary_sources=0/2
- repair_required_before_extraction: PASS (warning) — repair_required_count=5

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw validation performed: true
- Raw files read: true
- Raw files written: false
- Raw files modified: false
- Manifest read: true
- File profile written: true
- Source diagnostics written: true
- Format profile written: true
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

v2.18D validates the raw artifacts and determines whether candidate extraction can proceed or whether acquisition repair is required first.

## Recommended next phase

`v2.18C_FIX - TWSE + TPEx Raw Acquisition Repair`
