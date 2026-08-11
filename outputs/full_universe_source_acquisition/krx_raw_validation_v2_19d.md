# v2.19D - KRX Raw Validation

Status: **KRX_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **raw-validation-only**

Generated at UTC: `2026-08-11T15:58:06.662217+00:00`

## Executive summary

v2.19D validates the raw KRX artifacts captured in v2.19C.

This phase is validation-only. It does not download new data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Raw validation summary

- Manifest rows: `7`
- Source diagnostics rows: `4`
- Artifact audit rows: `7`
- Artifacts exist: `7/7`
- Bytes match: `7/7`
- SHA256 match: `7/7`
- Parse-ready artifacts: `0`
- Primary parse-ready artifacts: `0`
- Critical issues: `0`
- Warning issues: `7`
- Extraction ready: `False`
- Repair required: `True`
- Critical failed checks: `0`

## Artifact audit

- `krx_global_listed_company_page` - exists `True`, bytes `True`, sha `True`, readiness `html_table_probe_required`
- `krx_data_marketplace_main_page` - exists `True`, bytes `True`, sha `True`, readiness `not_parse_ready_http_403`
- `krx_data_marketplace_all_listed_issues_otp_response` - exists `True`, bytes `True`, sha `True`, readiness `not_parse_ready_http_403`
- `krx_data_marketplace_all_listed_issues_download` - exists `True`, bytes `True`, sha `True`, readiness `not_parse_ready_invalid_otp`
- `public_data_portal_krx_listed_stock_info_page` - exists `True`, bytes `True`, sha `True`, readiness `html_or_dynamic_not_parse_ready`
- `public_data_portal_krx_listed_stock_info_api_sample` - exists `True`, bytes `True`, sha `True`, readiness `optional_api_not_attempted_missing_key`
- `krx_open_api_data_feed_products_page` - exists `True`, bytes `True`, sha `True`, readiness `not_parse_ready_http_403`

## Source readiness

- `krx_data_marketplace_all_listed_issues` - status `blocked_http_403_or_invalid_otp_repair_required`, parse-ready `0`, warnings `3`
- `krx_global_listed_company` - status `captured_html_repair_or_probe_required`, parse-ready `0`, warnings `1`
- `krx_open_api_data_feed_products` - status `reference_only_not_parse_ready`, parse-ready `0`, warnings `1`
- `public_data_portal_krx_listed_stock_info` - status `metadata_captured_api_key_optional`, parse-ready `0`, warnings `2`

## Issues

- warning `html_table_probe_required` / `krx_global_listed_company` / `krx_global_listed_company_page` - KRX Global HTML may contain table-like content, but extraction must not start before a dedicated parser/probe phase.
- warning `not_parse_ready_http_403` / `krx_data_marketplace_all_listed_issues` / `krx_data_marketplace_main_page` - Official source returned HTTP 403 and was captured as diagnostic evidence.
- warning `not_parse_ready_http_403` / `krx_data_marketplace_all_listed_issues` / `krx_data_marketplace_all_listed_issues_otp_response` - Official source returned HTTP 403 and was captured as diagnostic evidence.
- warning `not_parse_ready_invalid_otp` / `krx_data_marketplace_all_listed_issues` / `krx_data_marketplace_all_listed_issues_download` - KRX CSV download was not attempted because OTP token was invalid.
- warning `html_or_dynamic_not_parse_ready` / `public_data_portal_krx_listed_stock_info` / `public_data_portal_krx_listed_stock_info_page` - HTML/dynamic page captured but not considered direct candidate source.
- warning `optional_api_not_attempted_missing_key` / `public_data_portal_krx_listed_stock_info` / `public_data_portal_krx_listed_stock_info_api_sample` - Optional data.go.kr API was not attempted because DATA_GO_KR_SERVICE_KEY is missing.
- warning `not_parse_ready_http_403` / `krx_open_api_data_feed_products` / `krx_open_api_data_feed_products_page` - Official source returned HTTP 403 and was captured as diagnostic evidence.

## Next actions

- Phigh `KRX` - repair_official_raw_acquisition - v2.19C_FIX - KRX Raw Acquisition Repair
- Phigh `KRX Global` - inspect_html_download_flow - v2.19C_FIX - KRX Raw Acquisition Repair
- Phigh `KRX Data Marketplace` - repair_403_otp_flow - v2.19C_FIX - KRX Raw Acquisition Repair
- Pmedium `data.go.kr` - optionally_configure_service_key - v2.19C_FIX - KRX Raw Acquisition Repair

## Checks

- v2_19c_report_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_acquisition_v2_19c.json
- v2_19c_status_expected: PASS (critical) - KRX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_19c_manifest_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_acquisition_manifest_v2_19c.csv
- v2_19c_source_diagnostics_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_acquisition_source_diagnostics_v2_19c.csv
- raw_dir_exists: PASS (critical) - outputs\full_universe_source_acquisition\raw\krx_v2_19c
- manifest_rows_expected: PASS (critical) - manifest_rows=7
- all_manifest_artifacts_exist: PASS (critical) - artifacts_exist=7/7
- all_manifest_bytes_match: PASS (critical) - bytes_match=7/7
- all_manifest_sha256_match: PASS (critical) - sha256_match=7/7
- artifact_critical_issues_zero: PASS (critical) - critical_issue_count=0
- active_canonical_rows_expected: PASS (critical) - active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) - current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) - rows_needed_to_50k=9004
- canonical_sha_unchanged: PASS (critical) - active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) - current validated candidate sha unchanged
- raw_files_read_only: PASS (critical) - raw_files_written=False
- network_not_used_by_validation: PASS (critical) - network_download_performed=False
- candidate_extraction_not_performed: PASS (critical) - candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) - canonical_comparison_performed=False
- expanded_rebuild_not_performed: PASS (critical) - expanded_rebuild_candidate_performed=False
- scoring_not_recalculated: PASS (critical) - scoring_recalculated=False
- openai_not_called: PASS (critical) - openai_called=False
- broker_not_called: PASS (critical) - broker_called=False
- full59k_not_launched: PASS (critical) - full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) - 40996 < 50000
- parse_ready_artifacts_present: FAIL (warning) - parse_ready_count=0
- primary_parse_ready_artifacts_present: FAIL (warning) - primary_parse_ready_count=0
- repair_required_before_extraction: PASS (warning) - repair_required=True; extraction_ready=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw validation performed: true
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

`v2.19C_FIX - KRX Raw Acquisition Repair`
