# v2.18C - TWSE + TPEx Raw Acquisition

Status: **TWSE_TPEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **raw-acquisition-only**

Generated at UTC: `2026-08-11T09:20:50.377302+00:00`

## Executive summary

v2.18C performs raw acquisition for the TWSE + TPEx Taiwan route.

This phase performs network calls only for official sources listed in the v2.18B source plan. It writes raw files, a raw acquisition manifest and source actions. It does not perform raw validation, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

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

## Raw acquisition summary

- Planned sources: `9`
- Included sources: `9`
- Download attempts: `9`
- HTTP 200 count: `5`
- HTTP error count: `0`
- Network error count: `4`
- Error payload count: `4`
- Total bytes captured: `39704`
- Raw directory: `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c`
- Manifest CSV: `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_manifest_v2_18c.csv`
- Source actions CSV: `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_source_actions_v2_18c.csv`
- Critical failed checks: `0`

## Manifest summary

- `twse_openapi_swagger` — network_error_payload_captured — HTTP `` — bytes `120` — `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c\01_twse_openapi_swagger_network_error_payload_captured.html`
- `twse_listed_company_profile` — network_error_payload_captured — HTTP `` — bytes `120` — `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c\02_twse_listed_company_profile_network_error_payload_captured.json`
- `twse_stock_day_all` — network_error_payload_captured — HTTP `` — bytes `120` — `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c\03_twse_stock_day_all_network_error_payload_captured.json`
- `twse_latest_listed_companies` — network_error_payload_captured — HTTP `` — bytes `120` — `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c\04_twse_latest_listed_companies_network_error_payload_captured.html`
- `tpex_openapi_swagger` — downloaded_200 — HTTP `200` — bytes `3030` — `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c\05_tpex_openapi_swagger_200.html`
- `tpex_daily_stock_quotes` — downloaded_200 — HTTP `200` — bytes `11041` — `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c\06_tpex_daily_stock_quotes_200.csv`
- `tpex_stock_pricing_page` — downloaded_200 — HTTP `200` — bytes `11038` — `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c\07_tpex_stock_pricing_page_200.csv`
- `tpex_mainboard_applicant_companies` — downloaded_200 — HTTP `200` — bytes `11085` — `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c\08_tpex_mainboard_applicant_companies_200.csv`
- `tpex_gisa_company` — downloaded_200 — HTTP `200` — bytes `3030` — `outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c\09_tpex_gisa_company_200.html`

## Checks

- v2_18b_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_acquisition_plan_v2_18b.json
- v2_18b_status_expected: PASS (critical) — TWSE_TPEX_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- source_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_source_plan_v2_18b.csv
- actions_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_acquisition_actions_v2_18b.csv
- filter_policy_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_filter_policy_v2_18b.csv
- schema_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_candidate_schema_plan_v2_18b.csv
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- validated_candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- validated_candidate_rows_expected: PASS (critical) — validated_candidate_rows=40300
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9700
- candidate_schema_matches_canonical: PASS (critical) — canonical_cols=33 candidate_cols=33
- included_sources_expected: PASS (critical) — included_sources=9
- manifest_rows_match_included_sources: PASS (critical) — manifest_rows=9 included_sources=9
- raw_directory_created: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_v2_18c
- raw_artifacts_exist: PASS (critical) — raw_artifacts_exist=True
- raw_bytes_captured: PASS (critical) — total_bytes=39704
- download_attempts_performed: PASS (critical) — attempted=9
- network_used_in_allowed_phase: PASS (critical) — network_download_performed=True
- http_status_preserved: PASS (critical) — http_status recorded in manifest
- sha256_recorded: PASS (critical) — sha256 recorded for every raw artifact
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

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Network scope: official sources from v2.18B source plan only
- Raw acquisition performed: true
- Raw files written: true
- Raw validation performed: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- Source plan read: true
- Filter policy read: true
- Schema plan read: true
- Raw manifest written: true
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

v2.18C captures raw TWSE + TPEx source artifacts and prepares raw validation in v2.18D.

## Recommended next phase

`v2.18D - TWSE + TPEx Raw Validation`
