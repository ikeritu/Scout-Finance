# v2.13D - JPX Validation

Status: **JPX_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW_FULL_SOURCE_STILL_BLOCKED**

Phase type: **validation-only**

Generated at UTC: `2026-07-08T14:47:29.478837+00:00`

## Decision

- Rebuild allowed by validation: **True**
- Recommended next phase: **v2.13E - Rebuild Expanded Source With JPX**
- Full 59k launched: **false**

## Selected dataset

- File: `001_jpx_dataset_candidate_jpx_discovered_workbook_candidate.xls`
- Sheet/table: `Sheet1`
- Parser: `xlrd`
- Header row index zero-based: 0
- Header score: 14
- Detected columns: `company_name|date|industry|local_code|market_segment`
- Candidate rows with local code: 4437

## Counts

- Dataset files found: 2
- Workbook sheets/tables profiled: 2
- Candidate rows with local code: 4437
- Candidate unique local codes: 4437
- Candidate unique ISINs: 0
- Equity candidate diagnostic only: 3711
- Non-ordinary or review required: 542
- Unknown review required: 184
- Local code min length: 4
- Local code max length: 5
- Possible leading-zero risk codes diagnostic: 0

## Baseline comparison

- baseline_expanded_path: outputs\full_universe_source_acquisition\expanded_universe_v2_12e.csv
- baseline_expanded_exists: True
- baseline_rows: 33158
- dataset_files_found: 2
- workbook_sheets_or_tables_profiled: 2
- selected_file_name: 001_jpx_dataset_candidate_jpx_discovered_workbook_candidate.xls
- selected_sheet_name: Sheet1
- candidate_rows_with_local_code: 4437
- candidate_unique_local_codes: 4437
- candidate_unique_isins: 0
- candidate_exchange_key_overlap_with_baseline: 0
- candidate_ticker_text_overlap_with_baseline_diagnostic_only: 0
- candidate_isin_overlap_with_baseline: 0
- diagnostic_not_in_baseline_by_exchange_key: 4437
- projected_rows_if_all_unique_jpx_codes_added: 37595
- full_source_unlocked_if_all_unique_jpx_codes_added: False
- rows_still_needed_after_jpx_projection: 12405
- possible_leading_zero_risk_codes_diagnostic: 0

## Critical checks

- manifest_exists: True
- baseline_expanded_exists: True
- dataset_files_found: True
- workbook_profiled: True
- selected_sheet_or_table_found: True
- local_code_column_detected: True
- company_name_column_detected: True
- candidate_rows_with_local_code_gt_1000: True
- unique_local_codes_gt_1000: True
- duplicate_exchange_ticker_keys_would_be_zero_if_exchange_jpx: True

## Hard guards

- phase_type: validation-only
- network_download_performed: False
- raw_files_modified: False
- workbook_or_csv_parsed_for_validation: True
- normalization_performed: False
- net_new_filtering_performed: False
- diagnostic_baseline_compare_performed: True
- expanded_universe_rebuilt: False
- scoring_recalculated: False
- openai_called: False
- broker_called: False
- full_59k_universe_launched: False
- overwrite_allowed: False

## Scope note

v2.13D validates raw JPX acquisition only.

It does not create accepted rows, does not normalize into the expanded universe, does not perform final net-new filtering, does not rebuild, does not score, does not call OpenAI or broker APIs, and does not launch full 59k.

## Outputs

- `outputs\full_universe_source_acquisition\jpx_validation_v2_13d.json`
- `outputs\full_universe_source_acquisition\jpx_validation_report_v2_13d.md`
- `outputs\full_universe_source_acquisition\jpx_workbook_profile_v2_13d.csv`
- `outputs\full_universe_source_acquisition\jpx_security_category_profile_v2_13d.csv`
- `outputs\full_universe_source_acquisition\jpx_baseline_compare_v2_13d.csv`
- `outputs\full_universe_source_acquisition\jpx_validation_decision_v2_13d.csv`
- `outputs\full_universe_source_acquisition\jpx_candidate_preview_diagnostic_v2_13d.csv`
