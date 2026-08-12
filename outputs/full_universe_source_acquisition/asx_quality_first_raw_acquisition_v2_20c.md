# v2.20C — ASX Quality-First Raw Acquisition

Status: **ASX_QUALITY_FIRST_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED**

Phase type: **raw-acquisition-only**

Generated at UTC: `2026-08-12T08:49:33.914558+00:00`

## Executive summary

v2.20C captures ASX raw official sources for the quality-first route.

This phase performs raw acquisition only. It captures HTML pages and direct/download-discovered files where available. It does not extract candidate rows, does not validate candidates against canonical, does not rebuild a candidate dataset, does not promote any dataset to canonical, and does not run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

The current validated HKEX candidate dataset remains **41,392** rows. The operational target band remains **42,000–45,000**. Only **608** clean net-new rows are needed to cross 42k.

## Acquisition summary

- Selected provider: `ASX`
- Raw directory: `outputs\full_universe_source_acquisition\raw\asx_v2_20c`
- Attempts total: `8`
- Successful attempts: `7`
- Failed attempts: `1`
- Required failed attempts: `0`
- Manifest rows: `7`
- Captured pages: `5`
- Captured downloads: `2`
- Captured CSV files: `1`
- Captured XLS/XLSX files: `1`
- Discovered links: `60`
- Discovered download candidates: `4`
- Legacy CSV status: `404`
- Critical failed checks: `0`
- Warning failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Raw manifest

- `asx_indices_page` — `200` — `192384` bytes — `outputs\full_universe_source_acquisition\raw\asx_v2_20c\pages\asx_indices_page.html`
- `asx_company_directory_page` — `200` — `136144` bytes — `outputs\full_universe_source_acquisition\raw\asx_v2_20c\pages\asx_company_directory_page.html`
- `asx_isin_services_page` — `200` — `143035` bytes — `outputs\full_universe_source_acquisition\raw\asx_v2_20c\pages\asx_isin_services_page.html`
- `asx_codes_and_descriptors_page` — `200` — `161332` bytes — `outputs\full_universe_source_acquisition\raw\asx_v2_20c\pages\asx_codes_and_descriptors_page.html`
- `asx_market_statistics_page` — `200` — `179374` bytes — `outputs\full_universe_source_acquisition\raw\asx_v2_20c\pages\asx_market_statistics_page.html`
- `asx_isin_xls_direct` — `200` — `1985024` bytes — `outputs\full_universe_source_acquisition\raw\asx_v2_20c\downloads\asx_isin_xls_direct.xls`
- `asx_discovered_last_known_closing_price_fy26` — `200` — `326441` bytes — `outputs\full_universe_source_acquisition\raw\asx_v2_20c\downloads\asx_discovered_last_known_closing_price_fy26.csv`

## Attempts

- `asx_indices_page` — OK — status `200` — 
- `asx_company_directory_page` — OK — status `200` — 
- `asx_isin_services_page` — OK — status `200` — 
- `asx_codes_and_descriptors_page` — OK — status `200` — 
- `asx_market_statistics_page` — OK — status `200` — 
- `asx_isin_xls_direct` — OK — status `200` — 
- `asx_listed_companies_legacy_csv` — FAIL — status `404` — HTTP Error 404: 
- `asx_discovered_last_known_closing_price_fy26` — OK — status `200` — 

## Checks

- v2_20b_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_quality_first_acquisition_plan_v2_20b.json
- v2_20b_status_expected: PASS (critical) — ASX_QUALITY_FIRST_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_RAW_ACQUISITION_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED
- v2_20b_next_phase_expected: PASS (critical) — v2.20C - ASX Quality-First Raw Acquisition
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
- required_pages_captured: PASS (critical) — required_failed=0
- official_pages_captured_count: PASS (critical) — captured_pages=5
- raw_manifest_non_empty: PASS (critical) — manifest_rows=7
- attempts_recorded: PASS (critical) — attempts=8
- discovered_links_recorded: PASS (warning) — discovered_links=60
- discovered_download_candidates_recorded: PASS (warning) — download_candidates=4
- structured_download_captured: PASS (warning) — captured_downloads=2
- csv_or_xls_captured: PASS (warning) — csv=1;xls=1
- legacy_csv_failure_non_critical: PASS (warning) — legacy_csv_status=404
- raw_acquisition_only: PASS (critical) — raw acquisition only
- network_download_performed: PASS (critical) — network_attempts=8
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

- Phigh `ASX` — run_asx_raw_validation — v2.20D - ASX Raw Validation
- Pmedium `ASX_download_repair` — repair_complete_list_csv_route_if_needed — v2.20D - ASX Raw Validation
- Phigh `quality_target` — preserve_42k_45k_operational_band — v2.20D - ASX Raw Validation

## Guards

- Raw acquisition only: true
- Network download performed: true
- Raw validation performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current candidate dataset modified: false
- HKEX candidate dataset modified: false
- Active canonical replaced: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20D - ASX Raw Validation`
