# v2.16D - TMX Validation

Status: **TMX_VALIDATION_COMPLETED_ENDPOINT_SEEDS_DETECTED_REBUILD_STILL_BLOCKED**

Phase type: **raw-validation-only**

Generated at UTC: `2026-08-05T08:09:04.720442+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Validation summary

- v2.16C status: `TMX_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS_REBUILD_STILL_BLOCKED`
- v2.16C recommended next phase: `v2.16D - TMX Validation`
- Manifest rows: `7`
- Raw files available: `4`
- HTML-like raw files: `4`
- Diagnostic rows: `7`
- Marker rows: `44`
- Endpoint seed rows: `873`
- Future probe allowed count: `170`
- High/medium quality count: `4`
- Quality counts: `{'high': 4, 'none': 3}`
- Recommended route counts: `{'controlled_endpoint_probe_recommended': 4, 'no_raw_file': 3}`
- Table count total: `1`
- Script count total: `43`
- Link count total: `773`
- Critical failed checks: `0`

## Raw diagnostics

- `tmx_listed_company_directory` raw=True html=True quality=high route=`controlled_endpoint_probe_recommended` endpoints=463 tables=1 scripts=9 links=377 title=`TMX TSX | TSXV | Listings | Listing With Us | Listed Company Directory`
- `tmx_equity_symbol_lookup` raw=False html=False quality=none route=`no_raw_file` endpoints=0 tables=0 scripts=0 links=0 title=``
- `tmx_tsxv_lcdb_search` raw=False html=False quality=none route=`no_raw_file` endpoints=0 tables=0 scripts=0 links=0 title=``
- `tmx_money_stocklists` raw=True html=True quality=high route=`controlled_endpoint_probe_recommended` endpoints=63 tables=0 scripts=11 links=2 title=`Discover Top Ranked Stocks on TSX and TSX Venture Exchange | TMX Money Stocklist`
- `tmx_money_recent_listings` raw=True html=True quality=high route=`controlled_endpoint_probe_recommended` endpoints=73 tables=0 scripts=17 links=6 title=`Recent Listings You May Have Missed | TMX Money Stocklist`
- `tmx_newsroom_equity_financing_statistics` raw=True html=True quality=high route=`controlled_endpoint_probe_recommended` endpoints=274 tables=0 scripts=6 links=388 title=`TMX | Press Releases and Announcements`
- `tmx_datalinx_reference_data` raw=False html=False quality=none route=`no_raw_file` endpoints=0 tables=0 scripts=0 links=0 title=``

## Top endpoint seeds

- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://cdn-cookieyes.com/client_data/aaef49d96429078d7fb3f7c6/script.js`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://7867ffbbe876435a846fe0266e167d23.js.ubembed.com`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/assets/application/js/common.1784907896.min.js`
- `tmx_listed_company_directory` signal=medium allowed=False hits=`quote` url=`https://qmod.quotemedia.com/js/qmodLoader.js`
- `tmx_listed_company_directory` signal=medium allowed=True hits=`search|tsx` url=`https://www.tmx.com/tmxes/tmxes.js?lang=en&nocss&container=tmxes-search-container-mobile&index=tsx`
- `tmx_listed_company_directory` signal=medium allowed=True hits=`company|listed|tsx` url=`https://www.tsx.com/en/listings/listing-with-us/listed-company-directory`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/assets/application/img/touch-icon-iphone.1718215393.png`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/assets/application/img/touch-icon-ipad.1718215393.png`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/assets/application/img/touch-icon-iphone4.1718215393.png`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/assets/application/img/touch-icon-android.1718215393.png`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/favicon.ico`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`http://microformats.org/profile/hcalendar`
- `tmx_listed_company_directory` signal=high allowed=False hits=`api` url=`https://fonts.googleapis.com`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://fonts.gstatic.com`
- `tmx_listed_company_directory` signal=high allowed=False hits=`api` url=`https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/assets/application/css/style.1761950993.min.css`
- `tmx_listed_company_directory` signal=medium allowed=True hits=`company` url=`https://www.tsx.com/assets/application/css/company-directory.1742857456.min.css`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/en`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/en/listings`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/en/listings/listing-with-us`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/en/listings/listing-with-us/listing-guides`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/en/listings/listing-with-us/sector-and-product-profiles`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/en/listings/listing-with-us/sector-and-product-profiles/latin-america`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/en/listings/listing-with-us/sector-and-product-profiles/latin-america-portuguese`
- `tmx_listed_company_directory` signal=none allowed=False hits=`` url=`https://www.tsx.com/en/listings/listing-with-us/sector-and-product-profiles/technology`

## Checks

- v2_16c_manifest_json_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_raw_acquisition_manifest_v2_16c.json
- v2_16c_manifest_csv_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_raw_acquisition_manifest_v2_16c.csv
- v2_16c_source_actions_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_raw_acquisition_source_actions_v2_16c.csv
- v2_16c_status_valid: PASS (critical) — TMX_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS_REBUILD_STILL_BLOCKED
- raw_dir_exists: PASS (critical) — outputs\full_universe_source_acquisition\raw\tmx_v2_16c
- manifest_rows_loaded: PASS (critical) — manifest_rows=7
- raw_files_available_for_validation: PASS (critical) — raw_exists_count=4
- html_like_raw_files: PASS (critical) — html_like_count=4
- structural_diagnostics_generated: PASS (critical) — diagnostics=7
- endpoint_seeds_detected_review: PASS (warning) — endpoint_seeds=873
- future_probe_allowed_review: PASS (warning) — future_probe_allowed=170
- high_or_medium_quality_review: PASS (warning) — high_or_medium_quality=4
- table_or_script_or_link_structure_review: PASS (warning) — tables=1; scripts=43; links=773
- current_rows_unchanged: PASS (critical) — current_rows=38287
- rows_needed_unchanged: PASS (critical) — rows_needed=11713
- full_source_still_blocked: PASS (critical) — 38287 < 50000
- network_not_used_in_validation: PASS (critical) — network_download_performed=False
- raw_files_not_modified_after_validation: PASS (critical) — raw_files_modified_after_write=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- endpoint_calls_not_performed: PASS (critical) — endpoint_calls_performed=False
- security_rows_not_extracted: PASS (critical) — security_rows_extracted=False
- candidate_rows_not_extracted: PASS (critical) — candidate_rows_extracted=False
- canonical_dataset_not_read: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- canonical_dataset_not_modified: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- normalization_not_performed: PASS (critical) — normalization_performed=False
- net_new_filtering_not_performed: PASS (critical) — net_new_filtering_performed=False
- expanded_universe_not_rebuilt: PASS (critical) — expanded_universe_rebuilt=False

## Guards

- Network download performed in v2.16D: false
- New raw files downloaded in v2.16D: false
- Raw files modified after write: false
- Raw HTML structural inspection performed: true
- Endpoint seed detection performed: true
- Endpoint calls performed: false
- Query sweep performed: false
- Security rows extracted: false
- Candidate rows extracted: false
- Canonical dataset read: false
- Canonical dataset modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX validation completed as raw structural validation only.

This phase reads the v2.16C manifest and raw files, validates local HTML structure, counts useful markers and records potential endpoint seeds for a future controlled phase. It performs no network access, no downloads, no endpoint calls, no query sweep, no security extraction, no candidate extraction, no canonical dataset read/write, no normalization, no net-new filtering and no rebuild.

## Recommended next phase

`v2.16D2 - TMX Controlled Endpoint Probe`
