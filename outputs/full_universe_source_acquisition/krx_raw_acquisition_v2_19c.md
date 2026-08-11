# v2.19C - KRX Raw Acquisition

Status: **KRX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **raw-acquisition-only**

Generated at UTC: `2026-08-11T15:44:13.574545+00:00`

## Executive summary

v2.19C captures official KRX/data.go.kr raw artifacts for the KRX route.

This phase performs raw acquisition only. It does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Raw acquisition summary

- Raw dir: `outputs\full_universe_source_acquisition\raw\krx_v2_19c`
- Source inventory rows: `4`
- Planned raw artifact rows: `4`
- Validation strategy rows: `7`
- Manifest rows: `7`
- Raw files written: `7`
- Official scope violations: `0`
- Captured rows: `5`
- Primary attempt rows: `4`
- Primary captured rows: `3`
- HTTP 200 rows: `2`
- Possible parse-ready rows: `0`
- Critical failed checks: `0`

## Manifest

- `krx_global_listed_company_page` — captured — HTTP `200` — `html_or_dynamic_page` — `outputs\full_universe_source_acquisition\raw\krx_v2_19c\krx_global_listed_company_page_v2_19c.html`
- `krx_data_marketplace_main_page` — captured — HTTP `403` — `html_or_dynamic_page` — `outputs\full_universe_source_acquisition\raw\krx_v2_19c\krx_data_marketplace_main_page_v2_19c.html`
- `krx_data_marketplace_all_listed_issues_otp_response` — captured — HTTP `403` — `html_or_dynamic_page` — `outputs\full_universe_source_acquisition\raw\krx_v2_19c\krx_data_marketplace_all_listed_issues_otp_response_v2_19c.txt`
- `krx_data_marketplace_all_listed_issues_download` — not_attempted_invalid_otp — HTTP `0` — `html_or_dynamic_page` — `outputs\full_universe_source_acquisition\raw\krx_v2_19c\krx_data_marketplace_all_listed_issues_download_not_attempted_v2_19c.txt`
- `public_data_portal_krx_listed_stock_info_page` — captured — HTTP `200` — `html_or_dynamic_page` — `outputs\full_universe_source_acquisition\raw\krx_v2_19c\public_data_portal_krx_listed_stock_info_page_v2_19c.html`
- `public_data_portal_krx_listed_stock_info_api_sample` — not_attempted_missing_service_key — HTTP `0` — `binary_or_text_unknown` — `outputs\full_universe_source_acquisition\raw\krx_v2_19c\public_data_portal_krx_listed_stock_info_api_not_attempted_missing_key_v2_19c.txt`
- `krx_open_api_data_feed_products_page` — captured — HTTP `403` — `html_or_dynamic_page` — `outputs\full_universe_source_acquisition\raw\krx_v2_19c\krx_open_api_data_feed_products_page_v2_19c.html`

## Source diagnostics

- `krx_global_listed_company` — attempts `1`, captured `1`, hints `html_or_dynamic_page`
- `krx_data_marketplace_all_listed_issues` — attempts `3`, captured `2`, hints `html_or_dynamic_page`
- `public_data_portal_krx_listed_stock_info` — attempts `2`, captured `1`, hints `binary_or_text_unknown|html_or_dynamic_page`
- `krx_open_api_data_feed_products` — attempts `1`, captured `1`, hints `html_or_dynamic_page`

## Next actions

- Phigh `KRX` — validate_raw_artifacts — v2.19D - KRX Raw Validation
- Phigh `KRX` — classify_parse_readiness — v2.19D - KRX Raw Validation
- Pmedium `50k` — maintain_candidate_baseline — v2.19D - KRX Raw Validation

## Checks

- v2_19b_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\krx_acquisition_plan_v2_19b.json
- v2_19b_status_expected: PASS (critical) — KRX_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_FOR_RAW_ACQUISITION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_19b_source_inventory_exists: PASS (critical) — outputs\full_universe_source_acquisition\krx_acquisition_plan_source_inventory_v2_19b.csv
- v2_19b_raw_artifacts_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\krx_acquisition_plan_raw_artifacts_v2_19b.csv
- v2_19b_validation_strategy_exists: PASS (critical) — outputs\full_universe_source_acquisition\krx_acquisition_plan_validation_strategy_v2_19b.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9004
- raw_dir_created: PASS (critical) — outputs\full_universe_source_acquisition\raw\krx_v2_19c
- manifest_rows_expected_minimum: PASS (critical) — manifest_rows=7
- raw_files_written_minimum: PASS (critical) — raw_files_written=7
- official_scope_only: PASS (critical) — official_scope_violations=0
- primary_sources_attempted: PASS (critical) — primary_attempt_rows=4
- primary_sources_captured: PASS (critical) — primary_captured_rows=3
- http_200_rows_present: PASS (warning) — http_200_rows=2
- possible_parse_ready_or_diagnostic_present: FAIL (warning) — possible_parse_ready_rows=0
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- candidate_dataset_not_modified: PASS (critical) — candidate_dataset_modified=False
- raw_acquisition_performed: PASS (critical) — raw_acquisition_performed=True
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- krx_raw_validation_next_needed: PASS (critical) — v2.19D - KRX Raw Validation

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Raw acquisition performed: true
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

`v2.19D - KRX Raw Validation`
