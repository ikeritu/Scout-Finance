# v2.15F2 - Euronext Extraction Strategy Revision

Status: **EURONEXT_EXTRACTION_STRATEGY_REVISION_ENDPOINT_PROBE_RECOMMENDED_REBUILD_STILL_BLOCKED**

Phase type: **strategy-revision-only**

Generated at UTC: `2026-08-04T09:56:24.587428+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Revision summary

- Raw files available: 11
- v2.15F extraction quality: `low`
- v2.15F deduped candidates: 7
- v2.15F unique ISINs: 7
- v2.15F table-based candidates: 0
- v2.15F context-only candidates: 7
- Public HTML failed as rebuild source: `True`
- Source strategy rows: 1361
- Allowed source strategy rows: 254
- Candidate endpoints from v2.15D: 1361
- Endpoint probe plan rows: 1184
- Executable probe rows: 95
- Critical failed checks: 0

## Decisions

- `public_html_rebuild_path`: **reject_for_rebuild** — Do not proceed from public HTML tables to expanded universe rebuild. Evidence: `dry_quality=low; table_based_count=0; context_only_count=7; unique_isins=7`
- `context_only_candidates`: **keep_as_evidence_only** — Context-only ISINs are not sufficient for net-new filtering or canonical integration. Evidence: `deduped_candidates=7; quality=low; source_kind=isin_context`
- `endpoint_probe_path`: **prepare_controlled_probe** — Next phase may probe candidate endpoints for metadata only; no rebuild allowed. Evidence: `executable_probe_rows=95; total_probe_rows=1184`
- `full_source_gate`: **remain_blocked** — Full source and full59k remain blocked. Evidence: `current_rows=38287; threshold=50000; rows_needed=11713`

## Top executable endpoint probes

- probe=fe79497e18312c5a type=live_listing_dynamic_probe priority=2 score=60 url=https://live.euronext.com/en/markets/milan/equities/global-equity-market/list
- probe=1121ea764807f970 type=live_listing_dynamic_probe priority=2 score=60 url=https://live.euronext.com/en/products/equities/global-equity-market/list
- probe=5695ef8ac07a90eb type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/de/markets/amsterdam/equities/list?page=0
- probe=4953adaee04eeaeb type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/de/markets/brussels/equities/list?page=0
- probe=5bcd8a2fdd8549b7 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/de/markets/dublin/equities/list?page=0
- probe=c937db948d3dc07c type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/de/markets/lisbon/equities/list?page=0
- probe=f53265b310760355 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/de/markets/milan/equities/list?page=0
- probe=75646fb3750c1d29 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/de/markets/oslo/equities/list?page=0
- probe=93d06c459f738e1d type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/de/markets/paris/equities/list?page=0
- probe=5990df11ae33d87d type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/de/products/equities/list
- probe=2a56bcc391f114c4 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/amsterdam/equities/list
- probe=99b68ed6622d9f72 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/amsterdam/equities/list?page=0
- probe=d232c172541aa1f5 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/brussels/equities/access/list
- probe=aec547e74e6987a3 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/brussels/equities/euronext/list
- probe=626d32fd14de1117 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/brussels/equities/expert/list
- probe=d36227b0b8b4f395 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/brussels/equities/growth/list
- probe=9e196949e8903ae0 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/brussels/equities/list
- probe=dbccb4f4b83c224f type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/brussels/equities/list?page=0
- probe=b5bf5e0bfdd4a2a4 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/dublin/equities/access/list
- probe=82f01ad5400bae67 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/dublin/equities/euronext/list
- probe=a164d98b0c7c267b type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/dublin/equities/growth/list
- probe=14a2d67425f79904 type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/dublin/equities/list
- probe=24aad6fd4c8ab2ce type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/dublin/equities/list?page=0
- probe=cc2a04fc7b8b701e type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/lisbon/equities/access/list
- probe=532a51d82c4044ce type=live_listing_dynamic_probe priority=2 score=35 url=https://live.euronext.com/en/markets/lisbon/equities/euronext/list

## Checks

- v2_15f_dry_run_exists: PASS (critical) - outputs\full_universe_source_acquisition\euronext_candidate_extraction_dry_run_v2_15f.json
- v2_15f_dry_run_completed: PASS (critical) - EURONEXT_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_LOW_QUALITY_REBUILD_STILL_BLOCKED
- v2_15f_low_quality_confirmed: PASS (warning) - extraction_quality=low
- public_html_failed_as_rebuild_source: PASS (warning) - table_based_count=0; context_only_count=7
- source_strategy_available: PASS (critical) - source_strategy_rows=1361
- candidate_endpoints_available: PASS (critical) - candidate_endpoints=1361
- probe_plan_generated: PASS (critical) - probe_plan_rows=1184
- executable_probe_rows_available: PASS (warning) - executable_probe_rows=95
- canonical_dataset_not_read: PASS (critical) - outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- canonical_dataset_not_modified: PASS (critical) - outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- no_net_new_filtering: PASS (critical) - net_new_filtering=False
- no_expanded_universe_rebuild: PASS (critical) - expanded_universe_rebuilt=False
- full_source_still_blocked: PASS (critical) - current_rows=38287

## Guards

- Network download performed in v2.15F2: false
- Endpoint probe executed: false
- Raw files downloaded in v2.15F2: false
- Raw files modified after write: false
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

## Important note

This phase revises the Euronext extraction strategy only.

It does not execute endpoint probes, does not download new files, does not read or modify the canonical expanded universe, does not calculate definitive net-new rows, does not normalize securities, does not rebuild the expanded universe, does not score equities, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Recommended next phase

`v2.15F3 - Euronext Controlled Endpoint Probe`
