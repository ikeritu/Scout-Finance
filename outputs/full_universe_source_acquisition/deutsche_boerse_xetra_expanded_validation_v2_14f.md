# v2.14F - Deutsche Boerse Xetra Expanded Validation

Status: **DEUTSCHE_BOERSE_XETRA_EXPANDED_VALIDATION_PASSED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **validation-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `2026-07-09T21:52:51.612635+00:00`

## Decision

- Expanded validation passed: **true**
- Full source unlocked: **false**
- Full 59k: **blocked**
- Recommended next phase: **v2.14G - Deutsche Boerse Xetra Closure Report**

## Counts

- Expanded rows: 38287
- Xetra additions: 1424
- Xetra exclusions: 3645
- Expanded delta vs baseline: 1424
- Duplicate exchange+ticker keys: 0
- Xetra additions non-CS: 0
- Xetra additions blank ISIN: 0
- Xetra additions blank ticker: 0
- Rows needed after Xetra: 11713
- Source-to-50k after Xetra: 76.6%
- Critical failed checks: 0
- Warning failed checks: 0

## Provider breakdown

- cboe_europe_reference_data: 21154
- jpx_listed_securities: 3705
- nasdaq_trader_nasdaqlisted: 3244
- hkex_securities_list: 2804
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- deutsche_boerse_xetra_all_tradable_instruments: 1424
- cboe_listed_symbols: 1193

## Xetra exclusion reason counts

- excluded_non_common_equity_instrument_type_ETF: 3048
- excluded_non_common_equity_instrument_type_ETN: 382
- excluded_non_common_equity_instrument_type_ETC: 205
- already_in_baseline_by_isin: 9
- missing_ticker: 1

## Checks

- expanded_csv_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- additions_csv_exists: PASS (critical) — outputs\full_universe_source_acquisition\deutsche_boerse_xetra_rebuild_additions_v2_14e.csv
- exclusions_csv_exists: PASS (critical) — outputs\full_universe_source_acquisition\deutsche_boerse_xetra_rebuild_exclusions_v2_14e.csv
- rebuild_manifest_exists: PASS (critical) — outputs\full_universe_source_acquisition\deutsche_boerse_xetra_rebuild_manifest_v2_14e.json
- expanded_rows_expected: PASS (critical) — expanded_rows=38287; expected=38287
- xetra_additions_expected: PASS (critical) — additions=1424; expected=1424
- expanded_delta_expected: PASS (critical) — delta=1424
- xetra_additions_all_cs: PASS (critical) — non_cs_additions=0
- xetra_additions_have_isin: PASS (critical) — blank_isin=0
- xetra_additions_have_ticker: PASS (critical) — blank_ticker=0
- duplicate_exchange_ticker_keys_zero: PASS (critical) — duplicate_exchange_ticker_keys=0
- full_source_still_blocked: PASS (critical) — expanded_rows=38287; threshold=50000
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False
- no_scoring_openai_broker: PASS (critical) — scoring=False; openai=False; broker=False
- global_blank_isin_review: PASS (warning) — blank_isin=34091
- global_blank_ticker_review: PASS (warning) — blank_ticker=0
- global_blank_company_name_review: PASS (warning) — blank_company_name=1193

## Guards

- Network download performed in v2.14F: false
- Raw files downloaded in v2.14F: false
- Raw files modified after write: false
- Workbook/CSV parsed for validation: true
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase validates the v2.14E expanded source only. It does not rebuild, score, call OpenAI, call broker APIs or launch full 59k.
