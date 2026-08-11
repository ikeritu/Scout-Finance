# v2.19D_FIX - KRX Repaired Raw Validation

Status: **KRX_REPAIRED_RAW_VALIDATION_COMPLETED_NO_PARSE_READY_SOURCE_ROUTE_BLOCKED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **repaired-raw-validation-only**

Generated at UTC: `2026-08-11T16:27:30.313198+00:00`

## Executive summary

v2.19D_FIX validates the repaired KRX raw artifacts from v2.19C_FIX.

This phase is repaired-raw-validation only. It does not download new data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Repaired raw validation summary

- Repair manifest rows: `18`
- Repair source diagnostics rows: `6`
- HTML signal rows: `1`
- Discovered URL rows: `327`
- Selected discovered URLs: `2`
- Table probe rows: `1`
- Artifact audit rows: `18`
- Artifacts exist: `18/18`
- Bytes match: `18/18`
- SHA256 match: `18/18`
- Official scope violations: `0`
- Structured artifacts: `1`
- Candidate-ready artifacts: `0`
- Primary candidate-ready artifacts: `0`
- Supporting candidate-ready artifacts: `0`
- Critical issues: `0`
- Warning issues: `18`
- Extraction ready: `False`
- KRX route blocked before extraction: `True`
- Critical failed checks: `0`

## Artifact audit

- `official_session_warmup_1` - exists `True`, bytes `True`, sha `True`, readiness `reference_or_warmup_not_candidate_ready`, extraction `False`
- `official_session_warmup_2` - exists `True`, bytes `True`, sha `True`, readiness `http_or_diagnostic_payload_not_candidate_ready`, extraction `False`
- `krx_global_listed_company_page_refetch` - exists `True`, bytes `True`, sha `True`, readiness `reference_or_warmup_not_candidate_ready`, extraction `False`
- `krx_global_listed_company_page_locale_en` - exists `True`, bytes `True`, sha `True`, readiness `reference_or_warmup_not_candidate_ready`, extraction `False`
- `krx_data_marketplace_information_download_guide` - exists `True`, bytes `True`, sha `True`, readiness `http_or_diagnostic_payload_not_candidate_ready`, extraction `False`
- `krx_data_marketplace_main_page_ko` - exists `True`, bytes `True`, sha `True`, readiness `http_or_diagnostic_payload_not_candidate_ready`, extraction `False`
- `public_data_portal_krx_openapi_catalog_json` - exists `True`, bytes `True`, sha `True`, readiness `reference_or_warmup_not_candidate_ready`, extraction `False`
- `krx_data_marketplace_otp_mdcstat01901_all` - exists `True`, bytes `True`, sha `True`, readiness `http_or_diagnostic_payload_not_candidate_ready`, extraction `False`
- `krx_data_marketplace_otp_mdcstat01901_stk` - exists `True`, bytes `True`, sha `True`, readiness `http_or_diagnostic_payload_not_candidate_ready`, extraction `False`
- `krx_data_marketplace_otp_mdcstat01901_ksq` - exists `True`, bytes `True`, sha `True`, readiness `http_or_diagnostic_payload_not_candidate_ready`, extraction `False`
- `krx_data_marketplace_otp_mdcstat01901_knx` - exists `True`, bytes `True`, sha `True`, readiness `http_or_diagnostic_payload_not_candidate_ready`, extraction `False`
- `download_from_krx_data_marketplace_otp_mdcstat01901_all` - exists `True`, bytes `True`, sha `True`, readiness `invalid_otp_not_candidate_ready`, extraction `False`
- `download_from_krx_data_marketplace_otp_mdcstat01901_stk` - exists `True`, bytes `True`, sha `True`, readiness `invalid_otp_not_candidate_ready`, extraction `False`
- `download_from_krx_data_marketplace_otp_mdcstat01901_ksq` - exists `True`, bytes `True`, sha `True`, readiness `invalid_otp_not_candidate_ready`, extraction `False`
- `download_from_krx_data_marketplace_otp_mdcstat01901_knx` - exists `True`, bytes `True`, sha `True`, readiness `invalid_otp_not_candidate_ready`, extraction `False`
- `krx_global_discovered_official_url_1` - exists `True`, bytes `True`, sha `True`, readiness `http_or_diagnostic_payload_not_candidate_ready`, extraction `False`
- `krx_global_discovered_official_url_2` - exists `True`, bytes `True`, sha `True`, readiness `structured_reference_not_candidate_ready`, extraction `False`
- `public_data_portal_krx_listed_stock_info_api_repair_sample` - exists `True`, bytes `True`, sha `True`, readiness `optional_api_missing_key_not_candidate_ready`, extraction `False`

## Source readiness

- `krx_data_marketplace_all_listed_issues` - status `diagnostic_or_http_error_only`, candidate-ready `0`, primary-ready `0`
- `krx_data_marketplace_information` - status `diagnostic_or_http_error_only`, candidate-ready `0`, primary-ready `0`
- `krx_global_discovered_official_url` - status `diagnostic_or_http_error_only`, candidate-ready `0`, primary-ready `0`
- `krx_global_listed_company` - status `captured_not_candidate_ready`, candidate-ready `0`, primary-ready `0`
- `official_session_warmup` - status `diagnostic_or_http_error_only`, candidate-ready `0`, primary-ready `0`
- `public_data_portal_krx_listed_stock_info` - status `captured_not_candidate_ready`, candidate-ready `0`, primary-ready `0`

## Issues

- warning `reference_or_warmup_not_candidate_ready` / `official_session_warmup` / `official_session_warmup_1` - Artifact is reference, warmup, script or discovered-page evidence, not candidate row data.
- warning `http_or_diagnostic_payload_not_candidate_ready` / `official_session_warmup` / `official_session_warmup_2` - Artifact is an HTTP/error/diagnostic payload, not candidate row data.
- warning `reference_or_warmup_not_candidate_ready` / `krx_global_listed_company` / `krx_global_listed_company_page_refetch` - Artifact is reference, warmup, script or discovered-page evidence, not candidate row data.
- warning `reference_or_warmup_not_candidate_ready` / `krx_global_listed_company` / `krx_global_listed_company_page_locale_en` - Artifact is reference, warmup, script or discovered-page evidence, not candidate row data.
- warning `http_or_diagnostic_payload_not_candidate_ready` / `krx_data_marketplace_information` / `krx_data_marketplace_information_download_guide` - Artifact is an HTTP/error/diagnostic payload, not candidate row data.
- warning `http_or_diagnostic_payload_not_candidate_ready` / `krx_data_marketplace_all_listed_issues` / `krx_data_marketplace_main_page_ko` - Artifact is an HTTP/error/diagnostic payload, not candidate row data.
- warning `reference_or_warmup_not_candidate_ready` / `public_data_portal_krx_listed_stock_info` / `public_data_portal_krx_openapi_catalog_json` - Artifact is reference, warmup, script or discovered-page evidence, not candidate row data.
- warning `http_or_diagnostic_payload_not_candidate_ready` / `krx_data_marketplace_all_listed_issues` / `krx_data_marketplace_otp_mdcstat01901_all` - Artifact is an HTTP/error/diagnostic payload, not candidate row data.
- warning `http_or_diagnostic_payload_not_candidate_ready` / `krx_data_marketplace_all_listed_issues` / `krx_data_marketplace_otp_mdcstat01901_stk` - Artifact is an HTTP/error/diagnostic payload, not candidate row data.
- warning `http_or_diagnostic_payload_not_candidate_ready` / `krx_data_marketplace_all_listed_issues` / `krx_data_marketplace_otp_mdcstat01901_ksq` - Artifact is an HTTP/error/diagnostic payload, not candidate row data.
- warning `http_or_diagnostic_payload_not_candidate_ready` / `krx_data_marketplace_all_listed_issues` / `krx_data_marketplace_otp_mdcstat01901_knx` - Artifact is an HTTP/error/diagnostic payload, not candidate row data.
- warning `invalid_otp_not_candidate_ready` / `krx_data_marketplace_all_listed_issues` / `download_from_krx_data_marketplace_otp_mdcstat01901_all` - CSV download was not attempted because OTP was invalid.
- warning `invalid_otp_not_candidate_ready` / `krx_data_marketplace_all_listed_issues` / `download_from_krx_data_marketplace_otp_mdcstat01901_stk` - CSV download was not attempted because OTP was invalid.
- warning `invalid_otp_not_candidate_ready` / `krx_data_marketplace_all_listed_issues` / `download_from_krx_data_marketplace_otp_mdcstat01901_ksq` - CSV download was not attempted because OTP was invalid.
- warning `invalid_otp_not_candidate_ready` / `krx_data_marketplace_all_listed_issues` / `download_from_krx_data_marketplace_otp_mdcstat01901_knx` - CSV download was not attempted because OTP was invalid.
- warning `http_or_diagnostic_payload_not_candidate_ready` / `krx_global_discovered_official_url` / `krx_global_discovered_official_url_1` - Artifact is an HTTP/error/diagnostic payload, not candidate row data.
- warning `structured_reference_not_candidate_ready` / `krx_global_discovered_official_url` / `krx_global_discovered_official_url_2` - Structured artifact appears to be reference/catalog/script data, not listed-company rows.
- warning `optional_api_missing_key_not_candidate_ready` / `public_data_portal_krx_listed_stock_info` / `public_data_portal_krx_listed_stock_info_api_repair_sample` - Optional data.go.kr API was not attempted because the service key is missing.

## Extraction gate

- `artifact_integrity`: PASS - exists=18/18; bytes=18/18; sha256=18/18
- `official_scope`: PASS - official_scope_violations=0
- `primary_candidate_data`: FAIL - primary_candidate_ready_count=0
- `extraction_ready`: FAIL - extraction_ready=False
- `krx_route_blocked_before_extraction`: PASS - blocked=True; candidate_ready_count=0; primary_candidate_ready_count=0

## Next actions

- Phigh `KRX` - close_krx_route_or_extract_if_gate_passed - v2.19I - KRX Closure Report
- Phigh `KRX` - document_repair_limitations - v2.19I - KRX Closure Report
- Phigh `50k` - select_next_provider_route_if_krx_blocked - next provider route selection after KRX closure

## Checks

- v2_19c_fix_report_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_acquisition_repair_v2_19c_fix.json
- v2_19c_fix_status_expected: PASS (critical) - KRX_RAW_ACQUISITION_REPAIR_COMPLETED_REPAIRED_RAW_FILES_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_19c_fix_manifest_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_acquisition_repair_manifest_v2_19c_fix.csv
- v2_19c_fix_source_diagnostics_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_acquisition_repair_source_diagnostics_v2_19c_fix.csv
- raw_repair_dir_exists: PASS (critical) - outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix
- repair_manifest_rows_expected: PASS (critical) - repair_manifest_rows=18
- all_repair_artifacts_exist: PASS (critical) - artifacts_exist=18/18
- all_repair_bytes_match: PASS (critical) - bytes_match=18/18
- all_repair_sha256_match: PASS (critical) - sha256_match=18/18
- official_scope_only: PASS (critical) - official_scope_violations=0
- artifact_critical_issues_zero: PASS (critical) - critical_issue_count=0
- active_canonical_rows_expected: PASS (critical) - active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) - current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) - rows_needed_to_50k=9004
- canonical_sha_unchanged: PASS (critical) - active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) - current validated candidate sha unchanged
- html_signal_inventory_available: PASS (warning) - html_signal_rows=1
- discovered_url_inventory_available: PASS (warning) - discovered_urls=327
- selected_discovered_urls_documented: PASS (warning) - selected_discovered_count=2
- html_table_probe_not_sufficient: PASS (warning) - html_table_rows=1; html_signal_table_rows=1
- structured_artifacts_present: PASS (warning) - structured_artifact_count=1
- primary_candidate_ready_present: FAIL (warning) - primary_candidate_ready_count=0
- extraction_ready: FAIL (warning) - extraction_ready=False
- krx_route_blocked_before_extraction: PASS (warning) - krx_route_blocked_before_extraction=True
- raw_files_read_only: PASS (critical) - raw_files_written=False
- network_not_used_by_repaired_validation: PASS (critical) - network_download_performed=False
- candidate_extraction_not_performed: PASS (critical) - candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) - canonical_comparison_performed=False
- expanded_rebuild_not_performed: PASS (critical) - expanded_rebuild_candidate_performed=False
- scoring_not_recalculated: PASS (critical) - scoring_recalculated=False
- openai_not_called: PASS (critical) - openai_called=False
- broker_not_called: PASS (critical) - broker_called=False
- full59k_not_launched: PASS (critical) - full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) - 40996 < 50000

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw acquisition repair performed: false
- Repaired raw validation performed: true
- Raw files read: true
- Raw files written: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
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

`v2.19I - KRX Closure Report`
