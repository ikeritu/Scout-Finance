# v2.20E — ASX Candidate Extraction Dry Run

Status: **ASX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_EXTRACTED_VALIDATION_DRY_RUN_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED**

Phase type: **candidate-extraction-dry-run-only**

Generated at UTC: `2026-08-12T09:27:11.258448+00:00`

## Executive summary

v2.20E performs an ASX candidate extraction dry run from the validated ASX raw files.

The primary source is the official ASX ISIN XLS captured in v2.20C and validated in v2.20D. The ASX last-known-closing-price CSV is used only as context/enrichment, not as the primary universe source.

This phase extracts and classifies ASX rows into include, exclude and review buckets. It does **not** validate against the current candidate dataset, does **not** append rows, does **not** rebuild an expanded candidate, does **not** promote canonical, and does **not** run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

Gross included ASX rows are not net-new rows. v2.20F must perform duplicate/net-new validation against the current HKEX validated candidate before any rebuild is considered.

## Extraction summary

- Selected provider: `ASX`
- Source file: `outputs\full_universe_source_acquisition\raw\asx_v2_20c\downloads\asx_isin_xls_direct.xls`
- Context file: `outputs\full_universe_source_acquisition\raw\asx_v2_20c\downloads\asx_discovered_last_known_closing_price_fy26.csv`
- Sheets loaded: `1`
- Sheet profiles: `1`
- Context codes: `4602`
- Extracted rows total: `14409`
- Included rows: `1921`
- Excluded rows: `12488`
- Review rows: `0`
- Duplicate ASX codes: `1`
- Duplicate ISINs: `0`
- Context matched rows: `4491`
- Included rows with context match: `1808`
- Current HKEX validated candidate rows: `41392`
- Rows needed to 42k: `608`
- Rows needed to 45k: `3608`
- Included rows cover 42k gap before duplicate validation: `True`
- Critical failed checks: `0`
- Warning failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Sheet profile

- `ISIN` — status `parseable` — rows `14409` — code `asx_code` — isin `isin_code` — name `company_name`

## Scope summary

- `a_reit_equity_like` / `include_conditional`: `17`
- `excluded_non_core_instrument` / `exclude`: `10706`
- `listed_investment_vehicle_conditional` / `include_conditional`: `7`
- `missing_code` / `exclude`: `1`
- `missing_identity` / `exclude`: `1`
- `non_standard_asx_code_length` / `exclude`: `1780`
- `ordinary_equity` / `include_candidate`: `1771`
- `ordinary_or_equity_like_unclassified` / `include_candidate`: `126`

## Checks

- v2_20d_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_raw_validation_v2_20d.json
- v2_20d_status_expected: PASS (critical) — ASX_RAW_VALIDATION_COMPLETED_REPAIR_RECOMMENDED_EXTRACTION_POSSIBLE_WITH_ISIN_XLS_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED
- v2_20d_next_phase_expected: PASS (critical) — v2.20E - ASX Candidate Extraction Dry Run
- v2_20d_parse_ready_for_extraction: PASS (critical) — True
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
- asx_isin_xls_exists: PASS (critical) — outputs\full_universe_source_acquisition\raw\asx_v2_20c\downloads\asx_isin_xls_direct.xls
- asx_isin_xls_non_empty: PASS (critical) — bytes=1985024
- asx_context_csv_exists: PASS (warning) — outputs\full_universe_source_acquisition\raw\asx_v2_20c\downloads\asx_discovered_last_known_closing_price_fy26.csv
- excel_sheets_loaded: PASS (critical) — sheets=1
- sheet_profile_created: PASS (critical) — sheet_profiles=1
- extracted_rows_non_empty: PASS (critical) — extracted_rows=14409
- included_rows_non_empty: PASS (critical) — included_rows=1921
- included_rows_at_least_quality_floor_gap: PASS (warning) — included_rows=1921;needed_to_42k=608
- asx_code_extracted: PASS (critical) — at least one ASX code extracted
- isin_extracted: PASS (critical) — at least one ISIN extracted
- context_match_available: PASS (warning) — context_matches=4491
- duplicates_documented: PASS (warning) — duplicate_rows=1
- candidate_extraction_dry_run_only: PASS (critical) — candidate extraction dry run only
- network_download_not_performed: PASS (critical) — network_download_performed=False
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

- Phigh `ASX` — run_asx_candidate_validation_against_current_candidate_dry_run — v2.20F - ASX Candidate Validation Against Current Candidate Dry Run
- Phigh `ASX_scope` — preserve_scope_filters_in_validation — v2.20F - ASX Candidate Validation Against Current Candidate Dry Run
- Phigh `quality_target` — validate_net_new_rows_before_rebuild — v2.20F - ASX Candidate Validation Against Current Candidate Dry Run

## Guards

- Candidate extraction dry run only: true
- Network download performed: false
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

`v2.20F - ASX Candidate Validation Against Current Candidate Dry Run`
