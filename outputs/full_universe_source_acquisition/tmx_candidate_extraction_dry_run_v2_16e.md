# v2.16E - TMX Candidate Extraction Dry Run

Status: **TMX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED**

Phase type: **candidate-extraction-dry-run-only**

Generated at UTC: `2026-08-05T11:21:46.906965+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Extraction summary

- v2.16C status: `TMX_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS_REBUILD_STILL_BLOCKED`
- v2.16D2 status: `TMX_CONTROLLED_ENDPOINT_PROBE_COMPLETED_NO_PROMISING_ENDPOINTS_REBUILD_STILL_BLOCKED`
- v2.16D2 recommended next phase: `v2.16E - TMX Candidate Extraction Dry Run`
- Manifest rows: `7`
- Raw files available: `4`
- HTML-like raw files: `4`
- Source diagnostics rows: `7`
- Candidate rows: `13`
- Exclusion rows: `1179`
- Method counts: `{'table_row': 1, 'json_object': 12}`
- Confidence counts: `{'low': 12, 'high': 1}`
- Source counts: `{'tmx_listed_company_directory': 1, 'tmx_money_recent_listings': 12}`
- Exclusion counts: `{'missing_name_for_json_object': 870, 'missing_symbol': 36, 'excluded_symbol_suffix_review': 157, 'invalid_symbol_format': 98, 'excluded_name_keyword:etf': 10, 'excluded_name_keyword:fund': 5, 'ambiguous_one_character_symbol_from_text': 2, 'text_exchange_name_starts_lowercase': 1}`
- Critical failed checks: `0`

## Source diagnostics

- `tmx_listed_company_directory` raw=True candidates=1 exclusions=4 methods anchor/json/table/text=0/4/1/0 title=`TMX TSX | TSXV | Listings | Listing With Us | Listed Company Directory`
- `tmx_equity_symbol_lookup` raw=False candidates=0 exclusions=0 methods anchor/json/table/text=0/0/0/0 title=``
- `tmx_tsxv_lcdb_search` raw=False candidates=0 exclusions=0 methods anchor/json/table/text=0/0/0/0 title=``
- `tmx_money_stocklists` raw=True candidates=0 exclusions=1144 methods anchor/json/table/text=0/1144/0/0 title=`Discover Top Ranked Stocks on TSX and TSX Venture Exchange | TMX Money Stocklist`
- `tmx_money_recent_listings` raw=True candidates=12 exclusions=27 methods anchor/json/table/text=0/39/0/0 title=`Recent Listings You May Have Missed | TMX Money Stocklist`
- `tmx_newsroom_equity_financing_statistics` raw=True candidates=0 exclusions=4 methods anchor/json/table/text=0/1/0/3 title=`TMX | Press Releases and Announcements`
- `tmx_datalinx_reference_data` raw=False candidates=0 exclusions=0 methods anchor/json/table/text=0/0/0/0 title=``

## Candidate preview

- `SYMBOL` `Company Name` exchange=`` confidence=low method=table_row source=`tmx_listed_company_directory`
- `ALCH` `Alchemy Labs Inc.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `AMAP` `Amapá Minerals Holdings Inc.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `ATOI` `Asiatel Outsourcing Inc.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `BUSH.P` `Bushido Capital Corp.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `CADY` `Cadillac Mines Corporation` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `AKT` `Akita Drilling Ltd.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `FSTV.P` `Falconstar Ventures Inc.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `INXS` `Goldinxs Mining Corp.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `NICE` `Ni-Co Energy Inc.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `OCAL` `OCAL Financial Inc.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `PCA` `Phoenix Metals Corp.` exchange=`` confidence=low method=json_object source=`tmx_money_recent_listings`
- `IRR` `Irruptive Metals Corp.` exchange=`TSXV` confidence=high method=json_object source=`tmx_money_recent_listings`

## Checks

- v2_16c_manifest_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_raw_acquisition_manifest_v2_16c.json
- v2_16c_manifest_csv_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_raw_acquisition_manifest_v2_16c.csv
- v2_16c_status_valid: PASS (critical) — TMX_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS_REBUILD_STILL_BLOCKED
- v2_16d2_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_controlled_endpoint_probe_v2_16d2.json
- v2_16d2_status_valid: PASS (critical) — TMX_CONTROLLED_ENDPOINT_PROBE_COMPLETED_NO_PROMISING_ENDPOINTS_REBUILD_STILL_BLOCKED
- v2_16d2_recommended_e: PASS (critical) — v2.16E - TMX Candidate Extraction Dry Run
- raw_files_available: PASS (critical) — raw_exists_count=4
- html_like_raw_files: PASS (critical) — html_like_count=4
- candidate_extraction_attempted: PASS (critical) — candidate_extraction_attempted=True
- candidate_rows_review: PASS (warning) — candidate_count=13
- exclusions_review: PASS (warning) — exclusion_count=1179
- canonical_dataset_not_read: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- canonical_dataset_not_modified: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- normalization_not_performed: PASS (critical) — global_normalization_performed=False
- net_new_filtering_not_performed: PASS (critical) — net_new_filtering_performed=False
- expanded_universe_not_rebuilt: PASS (critical) — expanded_universe_rebuilt=False
- network_not_used: PASS (critical) — network_download_performed=False
- endpoint_calls_not_performed: PASS (critical) — endpoint_calls_performed=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- full_source_still_blocked: PASS (critical) — 38287 < 50000

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw HTML local read performed: true
- Candidate extraction attempted: true
- Candidate rows extracted: true
- Security rows extracted: false
- Canonical dataset read: false
- Canonical dataset modified: false
- Canonical comparison performed: false
- Global normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX candidate extraction dry run completed.

This phase parses only local raw HTML files already versioned from v2.16C. It applies conservative filtering and moves weak symbol-only JSON fragments to exclusions/review. It performs no canonical comparison, no net-new filtering and no rebuild.

## Recommended next phase

`v2.16F - TMX Candidate Validation Against Canonical Dry Run`
