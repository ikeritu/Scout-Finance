# v2.16C - TMX Raw Acquisition

Status: **TMX_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS_REBUILD_STILL_BLOCKED**

Phase type: **raw-acquisition-only**

Generated at UTC: `2026-08-04T22:26:53.757645+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Raw acquisition summary

- Plan artifact: `outputs\full_universe_source_acquisition\tmx_acquisition_plan_v2_16b.json`
- Source candidates artifact: `outputs\full_universe_source_acquisition\tmx_source_candidates_v2_16b.csv`
- Raw directory: `outputs\full_universe_source_acquisition\raw\tmx_v2_16c`
- Source candidates: `7`
- Download allowed sources: `6`
- Download attempted: `6`
- Raw files written: `4`
- HTTP OK count: `4`
- Skipped sources: `1`
- Paid/controlled sources skipped: `1`
- Error count: `2`
- Bytes total: `440295`
- Critical failed checks: `0`

## Source actions

- `tmx_listed_company_directory` — action=`download_landing_response_only` allowed=True reason=`allowed_public_planned_source`
- `tmx_equity_symbol_lookup` — action=`download_landing_response_only` allowed=True reason=`allowed_public_planned_source`
- `tmx_tsxv_lcdb_search` — action=`download_landing_response_only` allowed=True reason=`allowed_public_planned_source`
- `tmx_money_stocklists` — action=`download_landing_response_only` allowed=True reason=`allowed_public_planned_source`
- `tmx_money_recent_listings` — action=`download_landing_response_only` allowed=True reason=`allowed_public_planned_source`
- `tmx_newsroom_equity_financing_statistics` — action=`download_landing_response_only` allowed=True reason=`allowed_public_planned_source`
- `tmx_datalinx_reference_data` — action=`skip` allowed=False reason=`paid_or_controlled_source_not_downloaded`

## Manifest

- `tmx_listed_company_directory` attempted=True ok=True status=200 bytes=69545 raw=`outputs\full_universe_source_acquisition\raw\tmx_v2_16c\01_tmx_listed_company_directory.raw` skipped=``
- `tmx_equity_symbol_lookup` attempted=True ok=False status= bytes=0 raw=`` skipped=``
- `tmx_tsxv_lcdb_search` attempted=True ok=False status= bytes=0 raw=`` skipped=``
- `tmx_money_stocklists` attempted=True ok=True status=200 bytes=180958 raw=`outputs\full_universe_source_acquisition\raw\tmx_v2_16c\04_tmx_money_stocklists.raw` skipped=``
- `tmx_money_recent_listings` attempted=True ok=True status=200 bytes=121028 raw=`outputs\full_universe_source_acquisition\raw\tmx_v2_16c\05_tmx_money_recent_listings.raw` skipped=``
- `tmx_newsroom_equity_financing_statistics` attempted=True ok=True status=200 bytes=68764 raw=`outputs\full_universe_source_acquisition\raw\tmx_v2_16c\06_tmx_newsroom_equity_financing_statistics.raw` skipped=``
- `tmx_datalinx_reference_data` attempted=False ok=False status= bytes=0 raw=`` skipped=`paid_or_controlled_source_not_downloaded`

## Checks

- v2_16b_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_acquisition_plan_v2_16b.json
- v2_16b_source_candidates_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_source_candidates_v2_16b.csv
- v2_16b_status_valid: PASS (critical) — TMX_ACQUISITION_PLAN_CREATED_NO_DOWNLOADS_PERFORMED_FULL_SOURCE_BLOCKED
- v2_16b_recommended_v2_16c: PASS (critical) — v2.16C - TMX Raw Acquisition
- raw_dir_created: PASS (critical) — outputs\full_universe_source_acquisition\raw\tmx_v2_16c
- source_candidates_loaded: PASS (critical) — sources=7
- public_sources_attempted: PASS (critical) — attempted=6
- raw_files_written: PASS (critical) — raw_files_written=4
- controller_timeouts_review: PASS (warning) — controller_errors_or_timeouts=2
- at_least_one_http_ok: PASS (warning) — ok_count=4
- paid_controlled_source_skipped: PASS (critical) — paid_skipped_count=1
- errors_review: FAIL (warning) — error_count=2
- current_rows_unchanged: PASS (critical) — current_rows=38287
- rows_needed_unchanged: PASS (critical) — rows_needed=11713
- full_source_still_blocked: PASS (critical) — 38287 < 50000
- canonical_dataset_not_read: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- canonical_dataset_not_modified: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- no_parsing: PASS (critical) — parsing_performed=False
- no_security_extraction: PASS (critical) — security_rows_extracted=False
- no_normalization: PASS (critical) — normalization_performed=False
- no_net_new_filtering: PASS (critical) — net_new_filtering=False
- no_expanded_universe_rebuild: PASS (critical) — expanded_universe_rebuilt=False

## Guards

- Network download performed in v2.16C: true
- Raw files downloaded: true
- Raw files modified after write: false
- Landing responses only: true
- Query sweep performed: false
- Paid or controlled data accessed: false
- Parsing performed: false
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

TMX raw acquisition completed as landing-response acquisition only.

This phase downloaded planned public TMX/TSX/TSXV landing responses and wrote raw files plus manifest metadata. It did not parse securities, extract candidates, normalize instruments, read or modify the canonical expanded universe, calculate net-new rows, rebuild the universe, score equities, call OpenAI, call broker APIs or launch full59k.

## Recommended next phase

`v2.16D - TMX Validation`
