# v2.13F - Validate Expanded Source With JPX

Status: **JPX_EXPANDED_VALIDATION_PASSED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **validation-only**

Generated at UTC: `2026-07-08T20:38:54.149599+00:00`

## Decision

- Recommended next phase: **v2.13G - JPX Closure Report**
- Full source unlocked: **False**
- Full 59k universe launched: **false**

## Counts

- Baseline rows: 33158
- Expanded rows: 36863
- Expanded delta: 3705
- JPX provider rows: 3705
- Accepted JPX rows: 3705
- Excluded JPX rows: 732
- Duplicate exchange+ticker keys: 0
- JPX blank ticker: 0
- JPX blank exchange: 0
- JPX blank company name: 0
- Full source threshold: 50000
- Rows needed after JPX: 13137
- Critical failed checks: 0
- Warning failed checks: 0

## Provider breakdown

- cboe_europe_reference_data: 21154
- jpx_listed_securities: 3705
- nasdaq_trader_nasdaqlisted: 3244
- hkex_securities_list: 2804
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- cboe_listed_symbols: 1193

## JPX market segment breakdown

- Market segment field not present in expanded schema.

## Checks

- baseline_file_exists: True — expected `True`, actual `True`
- expanded_file_exists: True — expected `True`, actual `True`
- schema_matches_baseline: True — expected `True`, actual `True`
- baseline_rows_match_expected: True — expected `33158`, actual `33158`
- expanded_rows_match_expected: True — expected `36863`, actual `36863`
- expanded_delta_equals_expected_jpx_added: True — expected `3705`, actual `3705`
- accepted_jpx_rows_match_expected: True — expected `3705`, actual `3705`
- excluded_jpx_rows_match_expected: True — expected `732`, actual `732`
- jpx_provider_rows_match_expected: True — expected `3705`, actual `3705`
- duplicate_exchange_ticker_keys_zero: True — expected `0`, actual `0`
- jpx_blank_ticker_zero: True — expected `0`, actual `0`
- jpx_blank_exchange_zero: True — expected `0`, actual `0`
- jpx_blank_company_zero: True — expected `0`, actual `0`
- jpx_exchange_is_jpx: True — expected `0`, actual `0`
- full_source_unlocked_false: True — expected `False`, actual `False`
- rows_needed_after_jpx_expected: True — expected `13137`, actual `13137`
- full_59k_universe_not_launched: True — expected `False`, actual `False`
- rebuild_status_is_expected: True — expected `JPX_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED`, actual `JPX_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED`
- rebuild_json_expanded_rows_matches_validation: True — expected `36863`, actual `36863`
- rebuild_json_jpx_added_matches_validation: True — expected `3705`, actual `3705`

## Hard guards

- phase_type: validation-only
- network_download_performed: False
- raw_files_modified: False
- normalization_performed: False
- net_new_filtering_performed: False
- expanded_universe_rebuilt: False
- scoring_recalculated: False
- openai_called: False
- broker_called: False
- full_59k_universe_launched: False
- overwrite_allowed: False

## Scope note

v2.13F is validation-only.

It does not download anything, does not modify raw files, does not normalize, does not rebuild, does not score, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Outputs

- `outputs\full_universe_source_acquisition\jpx_expanded_validation_v2_13f.json`
- `outputs\full_universe_source_acquisition\jpx_expanded_validation_report_v2_13f.md`
- `outputs\full_universe_source_acquisition\jpx_expanded_validation_checks_v2_13f.csv`
- `outputs\full_universe_source_acquisition\provider_breakdown_validation_v2_13f.csv`
- `outputs\full_universe_source_acquisition\jpx_duplicate_exchange_ticker_keys_v2_13f.csv`
- `outputs\full_universe_source_acquisition\jpx_rows_sample_v2_13f.csv`
- `outputs\full_universe_source_acquisition\jpx_blank_field_diagnostics_v2_13f.csv`
