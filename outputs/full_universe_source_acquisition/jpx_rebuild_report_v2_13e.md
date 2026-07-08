# v2.13E - Rebuild Expanded Source With JPX

Status: **JPX_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **rebuild-only**

Generated at UTC: `2026-07-08T19:09:39.987929+00:00`

## Decision

- Baseline rows: 33158
- JPX source rows reviewed: 4437
- JPX rows added: 3705
- JPX rows excluded: 732
- Expanded rows: 36863
- Duplicate exchange+ticker keys: 0
- Full source threshold: 50000
- Full source unlocked: False
- Rows needed after JPX: 13137
- Full 59k universe launched: false
- Recommended next phase: **v2.13F - Validate Expanded Source With JPX**

## Accepted JPX rows by market segment

- Standard Market(Domestic): 1561
- Prime Market (Domestic): 1551
- Growth Market(Domestic): 593

## Excluded JPX rows by reason

- ETF_ETN_MARKET_SEGMENT_EXCLUDED: 468
- PRO_MARKET_REVIEW_EXCLUDED: 183
- REIT_OR_FUND_MARKET_SEGMENT_EXCLUDED: 63
- NON_COMMON_EQUITY_REVIEW_EXCLUDED: 11
- FOREIGN_MARKET_SEGMENT_EXCLUDED: 5
- MARKET_SEGMENT_NOT_IN_ALLOWLIST: 2

## Provider breakdown

- cboe_europe_reference_data: 21154
- jpx_listed_securities: 3705
- nasdaq_trader_nasdaqlisted: 3244
- hkex_securities_list: 2804
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- cboe_listed_symbols: 1193

## Critical checks

- v2_13d_rebuild_allowed: True
- baseline_rows_match_expected: True
- accepted_rows_gt_zero: True
- expanded_rows_equals_baseline_plus_added: True
- duplicate_exchange_ticker_keys_zero: True
- full_59k_universe_not_launched: True

## Hard guards

- phase_type: rebuild-only
- network_download_performed: False
- raw_files_modified: False
- normalization_performed: True
- net_new_filtering_performed: True
- expanded_universe_rebuilt: True
- scoring_recalculated: False
- openai_called: False
- broker_called: False
- full_59k_universe_launched: False
- overwrite_allowed: False

## Scope note

v2.13E is rebuild-only.

It appends only conservative JPX domestic Prime/Standard/Growth equity candidates.

It does not download anything, does not score, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Outputs

- `outputs\full_universe_source_acquisition\expanded_universe_v2_13e.csv`
- `outputs\full_universe_source_acquisition\jpx_rebuild_summary_v2_13e.json`
- `outputs\full_universe_source_acquisition\jpx_rebuild_report_v2_13e.md`
- `outputs\full_universe_source_acquisition\jpx_accepted_rows_v2_13e.csv`
- `outputs\full_universe_source_acquisition\jpx_excluded_rows_v2_13e.csv`
- `outputs\full_universe_source_acquisition\provider_breakdown_v2_13e.csv`
- `outputs\full_universe_source_acquisition\jpx_rebuild_decision_v2_13e.csv`
