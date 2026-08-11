# v2.19C_FIX - KRX Raw Acquisition Repair

Status: **KRX_RAW_ACQUISITION_REPAIR_COMPLETED_REPAIRED_RAW_FILES_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **raw-acquisition-repair-only**

Generated at UTC: `2026-08-11T16:15:55.682202+00:00`

## Executive summary

v2.19C_FIX repairs official KRX raw acquisition after v2.19D found no parse-ready primary artifacts.

This phase performs raw-acquisition repair only. It does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Repair summary

- v2.19D artifact rows: `7`
- v2.19D readiness rows: `4`
- v2.19D issue rows: `7`
- v2.19C manifest rows: `7`
- HTML signal rows: `1`
- HTML table probe rows: `1`
- HTML table probe possible: `False`
- Discovered URLs: `327`
- Discovered URLs selected for fetch: `2`
- Repair manifest rows: `18`
- Raw repair files written: `18`
- Official scope violations: `0`
- Captured rows: `13`
- HTTP 200 rows: `5`
- Structured rows: `1`
- Primary structured rows: `0`
- Critical failed checks: `0`

## Repair manifest

- `official_session_warmup_1` - captured - HTTP `200` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\warmup_1_global_krx_co_kr_d87b39d379.html`
- `official_session_warmup_2` - captured - HTTP `403` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\warmup_2_data_krx_co_kr_contents_MDC_MAIN_main_index_cmd_b6127483f5.html`
- `krx_global_listed_company_page_refetch` - captured - HTTP `200` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\krx_global_listed_company_page_refetch_global_krx_co_kr_contents_GLB_03_0308_0308010000_GLB0308010000_jsp_67f4d6ebd2.html`
- `krx_global_listed_company_page_locale_en` - captured - HTTP `200` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\krx_global_listed_company_page_locale_en_global_krx_co_kr_contents_GLB_03_0308_0308010000_GLB0308010000_jsp_c5214e5917.html`
- `krx_data_marketplace_information_download_guide` - captured - HTTP `403` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\krx_data_marketplace_information_download_guide_data_krx_co_kr_contents_MDC_INFO_informationController_MDCINFO002_cmd_5ced478fea.html`
- `krx_data_marketplace_main_page_ko` - captured - HTTP `403` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\krx_data_marketplace_main_page_ko_data_krx_co_kr_contents_MDC_MAIN_main_index_cmd_b6127483f5.html`
- `public_data_portal_krx_openapi_catalog_json` - captured - HTTP `200` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\public_data_portal_krx_openapi_catalog_json_www_data_go_kr_catalog_15094775_openapi_json_d6422db85d.json`
- `krx_data_marketplace_otp_mdcstat01901_all` - captured - HTTP `403` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\krx_data_marketplace_otp_mdcstat01901_all_data_krx_co_kr_comm_fileDn_GenerateOTP_generate_cmd_6d32e141c9.txt`
- `krx_data_marketplace_otp_mdcstat01901_stk` - captured - HTTP `403` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\krx_data_marketplace_otp_mdcstat01901_stk_data_krx_co_kr_comm_fileDn_GenerateOTP_generate_cmd_6d32e141c9.txt`
- `krx_data_marketplace_otp_mdcstat01901_ksq` - captured - HTTP `403` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\krx_data_marketplace_otp_mdcstat01901_ksq_data_krx_co_kr_comm_fileDn_GenerateOTP_generate_cmd_6d32e141c9.txt`
- `krx_data_marketplace_otp_mdcstat01901_knx` - captured - HTTP `403` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\krx_data_marketplace_otp_mdcstat01901_knx_data_krx_co_kr_comm_fileDn_GenerateOTP_generate_cmd_6d32e141c9.txt`
- `download_from_krx_data_marketplace_otp_mdcstat01901_all` - not_attempted_invalid_otp - HTTP `0` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\download_from_krx_data_marketplace_otp_mdcstat01901_all_data_krx_co_kr_comm_fileDn_download_csv_download_cmd_2f99414975.txt`
- `download_from_krx_data_marketplace_otp_mdcstat01901_stk` - not_attempted_invalid_otp - HTTP `0` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\download_from_krx_data_marketplace_otp_mdcstat01901_stk_data_krx_co_kr_comm_fileDn_download_csv_download_cmd_2f99414975.txt`
- `download_from_krx_data_marketplace_otp_mdcstat01901_ksq` - not_attempted_invalid_otp - HTTP `0` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\download_from_krx_data_marketplace_otp_mdcstat01901_ksq_data_krx_co_kr_comm_fileDn_download_csv_download_cmd_2f99414975.txt`
- `download_from_krx_data_marketplace_otp_mdcstat01901_knx` - not_attempted_invalid_otp - HTTP `0` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\download_from_krx_data_marketplace_otp_mdcstat01901_knx_data_krx_co_kr_comm_fileDn_download_csv_download_cmd_2f99414975.txt`
- `krx_global_discovered_official_url_1` - captured - HTTP `403` - `html_or_dynamic_page` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\discovered_1_data_krx_co_kr_contents_MDC_MAIN_main_index_cmd_cac008fa79.html`
- `krx_global_discovered_official_url_2` - captured - HTTP `200` - `csv_like` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\discovered_2_global_krx_co_kr_WEB_APP_webponent_grid_external_json2_min_js_f908cd57cd.js`
- `public_data_portal_krx_listed_stock_info_api_repair_sample` - not_attempted_missing_service_key - HTTP `0` - `binary_or_text_unknown` - `outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix\public_data_portal_krx_listed_stock_info_api_repair_not_attempted_missing_key_v2_19c_fix.txt`

## Source diagnostics

- `official_session_warmup` - attempts `2`, captured `2`, structured `0`, hints `html_or_dynamic_page`
- `krx_global_listed_company` - attempts `2`, captured `2`, structured `0`, hints `html_or_dynamic_page`
- `krx_data_marketplace_information` - attempts `1`, captured `1`, structured `0`, hints `html_or_dynamic_page`
- `krx_data_marketplace_all_listed_issues` - attempts `9`, captured `5`, structured `0`, hints `html_or_dynamic_page`
- `public_data_portal_krx_listed_stock_info` - attempts `2`, captured `1`, structured `0`, hints `binary_or_text_unknown|html_or_dynamic_page`
- `krx_global_discovered_official_url` - attempts `2`, captured `2`, structured `1`, hints `csv_like|html_or_dynamic_page`

## Next actions

- Phigh `KRX` - validate_repaired_raw_artifacts - v2.19D_FIX - KRX Repaired Raw Validation
- Phigh `KRX Global` - evaluate_html_table_probe - v2.19D_FIX - KRX Repaired Raw Validation
- Pmedium `KRX Data Marketplace` - evaluate_otp_and_csv_repair - v2.19D_FIX - KRX Repaired Raw Validation
- Pmedium `50k` - maintain_candidate_baseline - v2.19D_FIX - KRX Repaired Raw Validation

## Checks

- v2_19d_report_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_validation_v2_19d.json
- v2_19d_status_expected: PASS (critical) - KRX_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_19d_artifact_audit_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_validation_artifact_audit_v2_19d.csv
- v2_19d_source_readiness_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_validation_source_readiness_v2_19d.csv
- v2_19d_issue_audit_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_validation_issue_audit_v2_19d.csv
- v2_19c_manifest_exists: PASS (critical) - outputs\full_universe_source_acquisition\krx_raw_acquisition_manifest_v2_19c.csv
- v2_19d_repair_required: PASS (critical) - True
- active_canonical_rows_expected: PASS (critical) - active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) - current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) - rows_needed_to_50k=9004
- raw_repair_dir_created: PASS (critical) - outputs\full_universe_source_acquisition\raw\krx_v2_19c_fix
- html_probe_completed: PASS (critical) - html_signal_rows=1
- html_table_probe_written: PASS (warning) - html_table_probe_rows=1
- discovered_url_inventory_written: PASS (warning) - discovered_urls=327
- repair_manifest_rows_minimum: PASS (critical) - repair_manifest_rows=18
- raw_repair_files_written_minimum: PASS (critical) - raw_repair_files_written=18
- official_scope_only: PASS (critical) - official_scope_violations=0
- http_200_rows_present: PASS (warning) - http_200_rows=5
- structured_rows_present: PASS (warning) - structured_rows=1
- primary_structured_rows_present: FAIL (warning) - primary_structured_rows=0
- html_table_probe_possible: FAIL (warning) - html_table_probe_possible=False; rows=1
- canonical_sha_unchanged: PASS (critical) - active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) - current validated candidate sha unchanged
- canonical_dataset_not_modified: PASS (critical) - canonical_dataset_modified=False
- candidate_dataset_not_modified: PASS (critical) - candidate_dataset_modified=False
- raw_acquisition_repair_performed: PASS (critical) - raw_acquisition_repair_performed=True
- candidate_extraction_not_performed: PASS (critical) - candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) - canonical_comparison_performed=False
- expanded_rebuild_not_performed: PASS (critical) - expanded_rebuild_candidate_performed=False
- scoring_not_recalculated: PASS (critical) - scoring_recalculated=False
- openai_not_called: PASS (critical) - openai_called=False
- broker_not_called: PASS (critical) - broker_called=False
- full59k_not_launched: PASS (critical) - full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) - 40996 < 50000
- krx_repaired_raw_validation_next_needed: PASS (critical) - v2.19D_FIX - KRX Repaired Raw Validation

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Raw acquisition performed: false
- Raw acquisition repair performed: true
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

`v2.19D_FIX - KRX Repaired Raw Validation`
