# v2.18E - TWSE + TPEx Candidate Extraction Dry Run

Status: **TWSE_TPEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_TWSE_CANDIDATES_READY_FOR_CANONICAL_VALIDATION_DRY_RUN_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **candidate-extraction-dry-run-only**

Generated at UTC: `2026-08-11T11:44:10.974518+00:00`

## Executive summary

v2.18E performs a TWSE + TPEx candidate extraction dry run.

This phase uses the repaired TWSE listed company profile JSON as the primary source and TWSE stock day all JSON as crosscheck. TPEx remains deferred/support because v2.18D_FIX confirmed TPEx still has technical acquisition errors.

This is a dry-run-only phase. It does not read the canonical dataset, does not compare against canonical, does not write an expanded candidate dataset, does not modify canonical, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Validated candidate rows: `40300`
- Final target candidates: `50000`
- Rows needed to 50k: `9700`
- Candidate completion: `80.6%`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Extraction summary

- Primary source: `twse_ssl_repair_twse_listed_company_profile`
- Crosscheck source: `twse_ssl_repair_twse_stock_day_all`
- Primary rows: `1094`
- Crosscheck rows: `1378`
- Candidates emitted: `1075`
- Exclusions emitted: `19`
- Unique candidate IDs: `1075`
- Duplicate candidate IDs: `0`
- Unique symbols: `1075`
- Duplicate symbols: `0`
- Review required candidates: `1`
- Crosscheck found: `1074`
- Crosscheck missing: `1`
- Critical failed checks: `0`

## Confidence buckets

- high: 1074
- medium: 1
- medium_review: 0

## Field mapping

- Primary symbol: `公司代號`
- Primary name: `公司名稱`
- Primary short name: `公司簡稱`
- Primary industry: `產業別`
- Primary listing date: `上市日期`
- Crosscheck symbol: `Code`
- Crosscheck name: `Name`
- ISIN: not available in source

## Checks

- v2_18d_fix_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_repaired_raw_validation_v2_18d_fix.json
- v2_18d_fix_status_expected: PASS (critical) — TWSE_TPEX_REPAIRED_RAW_VALIDATION_COMPLETED_ROW_DATA_VALID_CANDIDATE_EXTRACTION_DRY_RUN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_18c_fix_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_v2_18c_fix.json
- v2_18c_fix_status_expected: PASS (critical) — TWSE_TPEX_RAW_ACQUISITION_REPAIR_COMPLETED_ROW_DATA_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- repair_manifest_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_manifest_v2_18c_fix.csv
- primary_source_manifest_present: PASS (critical) — twse_ssl_repair_twse_listed_company_profile
- crosscheck_source_manifest_present: PASS (critical) — twse_ssl_repair_twse_stock_day_all
- primary_raw_artifact_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_v2_18c_fix\twse_ssl_repair_twse_listed_company_profile_200.json
- crosscheck_raw_artifact_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_raw_acquisition_repair_v2_18c_fix\twse_ssl_repair_twse_stock_day_all_200.json
- primary_raw_sha_unchanged: PASS (critical) — primary raw sha unchanged
- crosscheck_raw_sha_unchanged: PASS (critical) — crosscheck raw sha unchanged
- primary_json_list_parsed: PASS (critical) — primary_rows=1094
- crosscheck_json_list_parsed: PASS (critical) — crosscheck_rows=1378
- primary_rows_expected_minimum: PASS (critical) — primary_rows=1094
- crosscheck_rows_expected_minimum: PASS (critical) — crosscheck_rows=1378
- candidates_emitted: PASS (critical) — candidates_count=1075
- candidate_ids_unique: PASS (critical) — duplicate_candidate_ids=0
- candidate_symbols_unique: PASS (critical) — duplicate_symbols=0
- no_canonical_comparison_performed: PASS (critical) — canonical_comparison_performed=False
- canonical_dataset_not_read: PASS (critical) — canonical_dataset_read=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- candidate_extraction_dry_run_only: PASS (critical) — candidate_extraction_dry_run_only=True
- network_not_used: PASS (critical) — network_download_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) — 40300 < 50000
- crosscheck_coverage_positive: PASS (warning) — crosscheck_found_count=1074
- high_confidence_candidates_positive: PASS (warning) — high_confidence_count=1074
- review_required_candidates_tracked: PASS (warning) — review_required_count=1

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw acquisition repair performed: false
- Raw validation performed: false
- Repaired raw validation performed: false
- Candidate extraction performed: true
- Candidate extraction mode: dry_run_only
- Canonical dataset read: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Candidate validation against canonical performed: false
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

`v2.18F - TWSE + TPEx Candidate Validation Against Canonical Dry Run`
