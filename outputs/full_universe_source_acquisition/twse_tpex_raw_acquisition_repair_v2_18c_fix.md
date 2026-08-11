# v2.18C_FIX - TWSE + TPEx Raw Acquisition Repair

Status: **TWSE_TPEX_RAW_ACQUISITION_REPAIR_COMPLETED_ROW_DATA_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **raw-acquisition-repair-only**

Generated at UTC: `2026-08-11T10:05:08.668888+00:00`

## Executive summary

v2.18C_FIX repairs raw acquisition for the TWSE + TPEx Taiwan route.

This phase performs network calls only for official TWSE/TPEx sources from v2.18B plus official TPEx Swagger/discovered official links. It writes repaired raw files, a repair manifest, endpoint discovery records, repair decisions and source actions.

It does not perform raw validation, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

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

## Repair summary

- Download attempts: `6`
- HTTP 200 count: `4`
- SSL fallback success count: `4`
- Row-data candidate count: `2`
- JSON-like count: `2`
- CSV-like count: `0`
- HTML count: `2`
- Error count: `2`
- Total bytes captured: `1847797`
- Endpoint discovery rows: `8`
- Critical failed checks: `0`

## Repair manifest summary

- `twse_ssl_repair_twse_openapi_swagger` — TWSE — downloaded_200 — HTTP `200` — format `html` — rows `0` — row_data `False`
- `twse_ssl_repair_twse_listed_company_profile` — TWSE — downloaded_200 — HTTP `200` — format `json_like` — rows `1094` — row_data `True`
- `twse_ssl_repair_twse_stock_day_all` — TWSE — downloaded_200 — HTTP `200` — format `json_like` — rows `1378` — row_data `True`
- `twse_ssl_repair_twse_latest_listed_companies` — TWSE — downloaded_200 — HTTP `200` — format `html` — rows `278` — row_data `False`
- `tpex_openapi_swagger_json_repair` — TPEx — network_error_payload_captured — HTTP `` — format `error_text` — rows `0` — row_data `False`
- `tpex_mainboard_daily_close_quotes_known_endpoint` — TPEx — network_error_payload_captured — HTTP `` — format `error_text` — rows `0` — row_data `False`

## Endpoint discovery

- `TPEx` — html_link_regex — selected `True` — https://www.tpex.org.tw/openapi/swagger.json
- `TPEx` — html_link_regex — selected `False` — https://fonts.googleapis.com
- `TPEx` — html_link_regex — selected `False` — https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@900&family=Noto+Serif+TC:wght@600;700&display=swap
- `TPEx` — html_link_regex — selected `False` — https://fonts.googleapis.com
- `TPEx` — html_link_regex — selected `False` — https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@900&family=Noto+Serif+TC:wght@600;700&display=swap
- `TPEx` — html_link_regex — selected `False` — https://fonts.googleapis.com
- `TPEx` — html_link_regex — selected `False` — https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@900&family=Noto+Serif+TC:wght@600;700&display=swap
- `TPEx` — html_link_regex — selected `True` — https://www.tpex.org.tw/openapi/swagger.json

## Checks

- v2_18d_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_validation_v2_18d.json
- v2_18d_status_expected: PASS (critical) — TWSE_TPEX_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18c_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c.json
- v2_18c_status_expected: PASS (critical) — TWSE_TPEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18d_diagnostics_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_validation_source_diagnostics_v2_18d.csv
- v2_18d_next_actions_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_validation_next_actions_v2_18d.csv
- source_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_source_plan_v2_18b.csv
- filter_policy_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_filter_policy_v2_18b.csv
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- validated_candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- validated_candidate_rows_expected: PASS (critical) — validated_candidate_rows=40300
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9700
- candidate_schema_matches_canonical: PASS (critical) — canonical_cols=33 candidate_cols=33
- repair_raw_directory_created: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_v2_18c_fix
- repair_download_attempts_performed: PASS (critical) — download_attempts=6
- repair_raw_artifacts_exist: PASS (critical) — raw_artifacts_exist=True
- repair_sha256_valid: PASS (critical) — raw_sha_valid=True
- network_used_in_repair_phase: PASS (critical) — network_download_performed=True
- network_scope_official_only: PASS (critical) — non_official_downloaded=0
- twse_ssl_repair_attempted: PASS (critical) — TWSE repair attempts present
- tpex_endpoint_discovery_attempted: PASS (critical) — TPEx swagger JSON attempted
- canonical_sha_unchanged: PASS (critical) — canonical sha unchanged
- raw_validation_not_performed: PASS (critical) — raw_validation_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- final_50k_gate_still_blocked: PASS (critical) — 40300 < 50000
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- row_data_candidate_captured: PASS (warning) — row_data_candidate_count=2
- twse_ssl_fallback_success: PASS (warning) — fallback_success_count=4
- tpex_discovered_endpoints_found: PASS (warning) — endpoint_discovery_rows=8

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Network scope: official sources and official endpoint discovery only
- Raw acquisition repair performed: true
- Raw files written: true
- Raw validation performed: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- v2.18D diagnostics read: true
- v2.18C manifest read: true
- Repair manifest written: true
- Endpoint discovery written: true
- Repair decision written: true
- Source actions written: true
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

v2.18C_FIX completes raw acquisition repair attempts and determines whether repaired raw validation can start.

## Recommended next phase

`v2.18D_FIX - TWSE + TPEx Repaired Raw Validation`
