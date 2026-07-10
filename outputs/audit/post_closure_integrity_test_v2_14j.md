# v2.14J - Post-Closure Integrity Test

Status: **POST_CLOSURE_INTEGRITY_TEST_PASSED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **test-only**

Canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`

## Counts

- Rows: 38287
- Rows needed to 50k: 11713
- Source-to-50k: 76.6%
- Duplicate exchange+ticker keys: 0
- Blank ticker: 0
- Blank exchange: 0
- Blank provider: 0
- Blank company_name: 1193
- Blank ISIN: 34091

## Provider breakdown

- nasdaq_trader_nasdaqlisted: 3244
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- cboe_listed_symbols: 1193
- cboe_europe_reference_data: 21154
- hkex_securities_list: 2804
- jpx_listed_securities: 3705
- deutsche_boerse_xetra_all_tradable_instruments: 1424

## Checks

- canonical_dataset_exists: PASS (critical) - outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- validation_json_exists: PASS (critical) - outputs\full_universe_source_acquisition\deutsche_boerse_xetra_expanded_validation_v2_14f.json
- closure_json_exists: PASS (critical) - outputs\full_universe_source_acquisition\deutsche_boerse_xetra_closure_report_v2_14g.json
- row_count_expected: PASS (critical) - rows=38287; expected=38287
- rows_needed_expected: PASS (critical) - rows_needed=11713; expected=11713
- source_to_50k_expected: PASS (critical) - source_to_50k=76.6; expected=76.6
- ticker_column_found: PASS (critical) - ticker_col=ticker
- exchange_column_found: PASS (critical) - exchange_col=exchange
- provider_column_found: PASS (critical) - provider_col=source_provider
- company_column_found: PASS (warning) - company_col=company_name
- isin_column_found: PASS (warning) - isin_col=isin
- blank_ticker_zero: PASS (critical) - blank_ticker=0
- blank_exchange_zero: PASS (critical) - blank_exchange=0
- blank_provider_zero: PASS (critical) - blank_provider=0
- duplicate_exchange_ticker_zero: PASS (critical) - duplicate_exchange_ticker_keys=0
- provider_breakdown_exact: PASS (critical) - provider_counts={'nasdaq_trader_nasdaqlisted': 3244, 'nasdaq_trader_otherlisted': 2404, 'sec_company_tickers_exchange': 2359, 'cboe_listed_symbols': 1193, 'cboe_europe_reference_data': 21154, 'hkex_securities_list': 2804, 'jpx_listed_securities': 3705, 'deutsche_boerse_xetra_all_tradable_instruments': 1424}
- xetra_provider_count_expected: PASS (critical) - xetra_count=1424
- full_source_still_blocked: PASS (critical) - rows=38287; threshold=50000
- closure_status_expected: PASS (critical) - closure_status=DEUTSCHE_BOERSE_XETRA_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED
- validation_status_expected: PASS (critical) - validation_status=DEUTSCHE_BOERSE_XETRA_EXPANDED_VALIDATION_PASSED_FULL_SOURCE_STILL_BLOCKED
- global_blank_company_name_review: PASS (warning) - blank_company_name=1193
- global_blank_isin_review: PASS (warning) - blank_isin=34091
- no_scoring_openai_broker_full59k: PASS (critical) - scoring=False; openai=False; broker=False; full59k=False

## Guards

- Network download performed: false
- Raw files downloaded: false
- Raw files modified after write: false
- Workbook/CSV parsed for test: true
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Recommended next phase

`v2.14K - .gitattributes / EOL Guard`

Alternative:

`v2.15A - Next Provider Route For Remaining Full Source Gap`
