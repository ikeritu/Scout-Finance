# v2.13G - JPX Closure Report

Status: **JPX_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED**

Phase type: **closure-only**

Generated at UTC: `2026-07-08T20:54:25.179248+00:00`

## Final decision

- Source decision: **JPX_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE**
- Recommended next phase: **v2.14A - Next Provider Route For Remaining Full Source Gap**
- Full source unlocked: **false**
- Full 59k universe launched: **false**

## JPX final counts

- Baseline before JPX: 33158
- JPX rows added: 3705
- JPX rows excluded: 732
- Expanded rows after JPX: 36863
- Duplicate exchange+ticker keys: 0
- Critical failed checks: 0
- Warning failed checks: 0
- Full source threshold: 50000
- Rows needed after JPX: 13137

## Accepted JPX rows

- Prime Market (Domestic): 1551
- Growth Market(Domestic): 593
- Standard Market(Domestic): 1561

## Excluded JPX rows

- ETF_ETN_MARKET_SEGMENT_EXCLUDED: 468
- PRO_MARKET_REVIEW_EXCLUDED: 183
- NON_COMMON_EQUITY_REVIEW_EXCLUDED: 11
- FOREIGN_MARKET_SEGMENT_EXCLUDED: 5
- REIT_OR_FUND_MARKET_SEGMENT_EXCLUDED: 63
- MARKET_SEGMENT_NOT_IN_ALLOWLIST: 2

## Provider breakdown after JPX

- cboe_europe_reference_data: 21154
- jpx_listed_securities: 3705
- nasdaq_trader_nasdaqlisted: 3244
- hkex_securities_list: 2804
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- cboe_listed_symbols: 1193

## Critical checks

- v2_13d_validation_passed: True
- v2_13e_rebuild_completed: True
- v2_13f_validation_passed: True
- expanded_rows_match_expected: True
- duplicate_exchange_ticker_keys_zero: True
- critical_failed_checks_zero: True
- warning_failed_checks_zero: True
- full_source_unlocked_false: True
- full_59k_universe_not_launched: True

## Hard guards

- phase_type: closure-only
- network_download_performed: False
- raw_files_downloaded: False
- raw_files_modified: False
- workbook_or_csv_parsed: False
- normalization_performed: False
- net_new_filtering_performed: False
- expanded_universe_rebuilt: False
- scoring_recalculated: False
- openai_called: False
- broker_called: False
- full_59k_universe_launched: False
- overwrite_allowed: False

## Project percentages after v2.13G commit

- v2.13 JPX block: 100% completed / 0% pending
- Fuente real expandida: 93% completed / 7% pending
- Fuente real completa 50k-59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: 96% completed / 4% pending

## Closure summary

JPX is accepted as a conservative expanded-source provider.

The expanded universe increased from **33,158** to **36,863** rows.

The 50k full-source gate remains blocked because **13,137** additional rows are still needed.

Full 59k dry-run remains blocked until source is complete and an explicit gate is approved.

## Outputs

- `outputs\full_universe_source_acquisition\jpx_closure_report_v2_13g.json`
- `outputs\full_universe_source_acquisition\jpx_closure_report_v2_13g.md`
- `outputs\full_universe_source_acquisition\jpx_closure_decision_v2_13g.csv`
- `outputs\full_universe_source_acquisition\jpx_post_closure_roadmap_v2_13g.csv`
