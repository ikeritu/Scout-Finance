# v2.19N — HKEX Candidate Extraction Dry Run

Status: **HKEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_EXTRACTED_CANONICAL_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **candidate-extraction-dry-run-only**

Generated at UTC: `2026-08-11T20:38:36.726126+00:00`

## Executive summary

v2.19N extracts HKEX candidates from the validated `ListOfSecurities.xlsx` source as a dry run.

This phase does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Extraction summary

- Source artifact: `hkex_repair_01_full_list_of_securities`
- Source file: `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\01_full_list_of_securities.xlsx`
- Source sheet: `ListOfSecurities`
- XLSX rows loaded: `17633`
- Header row number: `3`
- Mapped fields: `18`
- Candidate rows extracted: `17630`
- Rejected rows: `0`
- Unique stock codes: `17630`
- Duplicate stock-code count: `0`
- Critical failed checks: `0`

## Field mapping

- `stock_code` ← column `1` / `Stock Code`
- `name_of_securities` ← column `2` / `Name of Securities`
- `category` ← column `3` / `Category`
- `sub_category` ← column `4` / `Sub-Category`
- `board_lot` ← column `5` / `Board Lot`
- `isin` ← column `6` / `ISIN`
- `expiry_date` ← column `7` / `Expiry Date`
- `subject_to_stamp_duty` ← column `8` / `Subject to Stamp Duty`
- `shortsell_eligible` ← column `9` / `Shortsell Eligible`
- `cas_eligible` ← column `10` / `CAS Eligible`
- `vcm_eligible` ← column `11` / `VCM Eligible`
- `admitted_to_ccass` ← column `12` / `Admitted to CCASS`
- `debt_securities_board_lot_nominal` ← column `13` / `Debt Securities Board Lot (Nominal)`
- `debt_securities_investor_type` ← column `14` / `Debt Securities Investor Type`
- `pos_eligible` ← column `15` / `POS Eligible`
- `spread_table` ← column `16` / `Spread Table
1 = Part A
3 = Part B
5 = Part D
4 & 6 = Part E`
- `trading_currency` ← column `17` / `Trading Currency`
- `rmb_counter` ← column `18` / `RMB Counter`

## Instrument summary

- `debt_security`: `1330`
- `derivative_or_warrant`: `13081`
- `equity_like`: `2803`
- `fund_or_etp`: `361`
- `other_or_unclassified`: `39`
- `reit`: `14`
- `spac`: `2`

## Next actions

- Phigh `HKEX` — run_candidate_validation_against_canonical_dry_run — v2.19O - HKEX Candidate Validation Against Canonical Dry Run
- Phigh `HKEX` — separate_candidate_scope_flags — v2.19O - HKEX Candidate Validation Against Canonical Dry Run
- Phigh `50k` — preserve_quality_gate — v2.19O - HKEX Candidate Validation Against Canonical Dry Run

## Checks

- v2_19m_fix_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_repaired_raw_validation_v2_19m_fix.json
- v2_19m_fix_status_expected: PASS (critical) — HKEX_REPAIRED_RAW_VALIDATION_COMPLETED_PARSE_READY_EXTRACTION_DRY_RUN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- parse_readiness_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_repaired_raw_validation_parse_readiness_v2_19m_fix.csv
- sheet_schema_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_repaired_raw_validation_sheet_schema_v2_19m_fix.csv
- primary_parse_ready_in_prior_phase: PASS (critical) — hkex_repair_01_full_list_of_securities
- primary_raw_file_exists: PASS (critical) — outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\01_full_list_of_securities.xlsx
- primary_raw_file_sha_matches_manifest: PASS (critical) — 0cdb042847c03c3a57ee0d7efa105058a4ef2455500de5c26b503382a0c22259
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9004
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- primary_sheet_loaded: PASS (critical) — rows_loaded=17633; sheet=ListOfSecurities; path=xl/worksheets/sheet1.xml
- header_row_detected: PASS (critical) — header_row=3
- stock_code_field_mapped: PASS (critical) — {"admitted_to_ccass": 11, "board_lot": 4, "cas_eligible": 9, "category": 2, "debt_securities_board_lot_nominal": 12, "debt_securities_investor_type": 13, "expiry_date": 6, "isin": 5, "name_of_securities": 1, "pos_eligible": 14, "rmb_counter": 17, "shortsell_eligible": 8, "spread_table": 15, "stock_code": 0, "sub_category": 3, "subject_to_stamp_duty": 7, "trading_currency": 16, "vcm_eligible": 10}
- name_field_mapped: PASS (critical) — {"admitted_to_ccass": 11, "board_lot": 4, "cas_eligible": 9, "category": 2, "debt_securities_board_lot_nominal": 12, "debt_securities_investor_type": 13, "expiry_date": 6, "isin": 5, "name_of_securities": 1, "pos_eligible": 14, "rmb_counter": 17, "shortsell_eligible": 8, "spread_table": 15, "stock_code": 0, "sub_category": 3, "subject_to_stamp_duty": 7, "trading_currency": 16, "vcm_eligible": 10}
- candidate_rows_extracted: PASS (critical) — candidate_rows=17630
- unique_stock_codes_positive: PASS (critical) — unique_stock_codes=17630
- rejections_documented: PASS (warning) — rejections=0
- duplicates_documented: PASS (warning) — duplicate_stock_code_count=0
- candidate_output_dry_run_only: PASS (critical) — dry_run_only=True
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- network_not_used_by_extraction: PASS (critical) — network_download_performed=False
- candidate_extraction_performed: PASS (critical) — candidate_extraction_performed=True
- candidate_validation_against_canonical_not_performed: PASS (critical) — candidate_validation_against_canonical_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- expanded_validation_not_performed: PASS (critical) — expanded_validation_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Guards

- Network download performed: false
- Candidate extraction performed: true
- Candidate extraction dry run only: true
- Candidate validation against canonical performed: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `True`
- Expanded rebuild candidate performed: false
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

`v2.19O - HKEX Candidate Validation Against Canonical Dry Run`
