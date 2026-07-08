# v2.12D — HKEX Validation

Status: **HKEX_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW_FULL_SOURCE_STILL_BLOCKED**

Phase type: **validation-only**

Generated at UTC: `2026-07-08T11:10:30.502323+00:00`

## Decision

- Rebuild allowed by validation: **True**
- Recommended next phase: **v2.12E — Rebuild Expanded Source With HKEX**
- Full 59k launched: **false**

## Selected sheet

- Sheet: `ListOfSecurities`
- XML path: `xl/worksheets/sheet1.xml`
- Header row index zero-based: 2
- Header score: 15
- Detected columns: `board_lot|category|currency|isin|name_of_securities|stock_code|subcategory`
- Candidate rows with stock code: 17589

## Counts

- Workbook sheets profiled: 1
- Candidate rows with stock code: 17589
- Candidate unique stock codes: 17589
- Candidate unique ISINs: 13962
- Equity candidate diagnostic only: 2804
- Non-ordinary or review required: 9190
- Unknown review required: 5595
- Stock code min length: 5
- Stock code max length: 5
- Possible leading-zero risk codes diagnostic: 0

## Baseline comparison

- baseline_expanded_path: outputs\full_universe_source_acquisition\expanded_universe_v2_11e.csv
- baseline_expanded_exists: True
- baseline_rows: 30354
- candidate_rows_with_stock_code: 17589
- candidate_unique_stock_codes: 17589
- candidate_unique_isins: 13962
- candidate_exchange_key_overlap_with_baseline: 0
- candidate_ticker_text_overlap_with_baseline_diagnostic_only: 0
- candidate_isin_overlap_with_baseline: 0
- diagnostic_not_in_baseline_by_exchange_key: 17589
- projected_rows_if_all_unique_hkex_codes_added: 47943
- full_source_unlocked_if_all_unique_hkex_codes_added: False
- rows_still_needed_after_hkex_projection: 2057
- possible_leading_zero_risk_codes_diagnostic: 0

## Critical checks

- manifest_exists: True
- raw_xlsx_exists: True
- raw_html_exists: True
- baseline_expanded_exists: True
- workbook_has_selected_sheet: True
- stock_code_column_detected: True
- name_column_detected: True
- candidate_rows_with_stock_code_gt_1000: True
- unique_stock_codes_gt_1000: True
- duplicate_exchange_ticker_keys_would_be_zero_if_exchange_hkex: True

## Hard guards

- phase_type: validation-only
- network_download_performed: False
- raw_files_modified: False
- workbook_parsed_for_validation: True
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

v2.12D validates raw HKEX acquisition only.

It does not create accepted rows, does not normalize into the expanded universe, does not perform final net-new filtering, does not rebuild, does not score, does not call OpenAI or broker APIs, and does not launch full 59k.

## Outputs

- `outputs\full_universe_source_acquisition\hkex_validation_v2_12d.json`
- `outputs\full_universe_source_acquisition\hkex_validation_report_v2_12d.md`
- `outputs\full_universe_source_acquisition\hkex_workbook_profile_v2_12d.csv`
- `outputs\full_universe_source_acquisition\hkex_security_category_profile_v2_12d.csv`
- `outputs\full_universe_source_acquisition\hkex_baseline_compare_v2_12d.csv`
- `outputs\full_universe_source_acquisition\hkex_validation_decision_v2_12d.csv`
- `outputs\full_universe_source_acquisition\hkex_candidate_preview_diagnostic_v2_12d.csv`
