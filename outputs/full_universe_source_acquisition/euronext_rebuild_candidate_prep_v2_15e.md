# v2.15E - Euronext Expanded Rebuild Candidate Preparation

Status: **EURONEXT_REBUILD_CANDIDATE_PREP_PASSED_REBUILD_STILL_BLOCKED**

Phase type: **candidate-preparation-only**

Generated at UTC: `2026-08-04T08:16:45.200436+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Preparation summary

- Raw files reviewed: 11
- Raw diagnostic rows: 11
- Candidate endpoints from v2.15D: 1361
- Source strategy rows: 1361
- HTML table candidates: 11
- Usable table candidates, medium/high: 8
- Allowed next phase endpoints: 254
- Extraction route: `hybrid_endpoint_then_html_table_fallback`
- Critical failed checks: 0

## Minimal target fields for later extraction

- ISIN
- Ticker or symbol
- Name, issuer or company
- Market or exchange
- Currency optional

## Top table candidates

- `euronext_amsterdam_equities_list.html` table=0 rows=1 cols=7 score=226 suitability=high hits=isin|symbol|name|market
- `euronext_brussels_equities_list.html` table=0 rows=1 cols=7 score=226 suitability=high hits=isin|symbol|name|market
- `euronext_dublin_equities_list.html` table=0 rows=1 cols=7 score=226 suitability=high hits=isin|symbol|name|market
- `euronext_lisbon_equities_list.html` table=0 rows=1 cols=7 score=226 suitability=high hits=isin|symbol|name|market
- `euronext_live_all_equities.html` table=0 rows=1 cols=7 score=226 suitability=high hits=isin|symbol|name|market
- `euronext_milan_equities_list.html` table=0 rows=1 cols=7 score=226 suitability=high hits=isin|symbol|name|market
- `euronext_oslo_equities_list.html` table=0 rows=1 cols=7 score=226 suitability=high hits=isin|symbol|name|market
- `euronext_paris_equities_list.html` table=0 rows=1 cols=7 score=226 suitability=high hits=isin|symbol|name|market
- `euronext_live_equities_overview.html` table=1 rows=8 cols=3 score=88 suitability=low hits=name|instrument
- `euronext_live_equities_overview.html` table=0 rows=20 cols=2 score=70 suitability=low hits=shares
- `euronext_live_equities_overview.html` table=2 rows=5 cols=2 score=15 suitability=low hits=

## Top source strategy rows

- priority=2 score=60 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/products/equities/global-equity-market/list
- priority=2 score=60 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/products/equities/equity-espresso
- priority=2 score=60 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/markets/milan/equities/global-equity-market/list
- priority=2 score=50 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/products/equity-derivatives/news
- priority=2 score=50 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/products/equity-derivatives/esg-derivatives
- priority=2 score=50 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/products/equity-derivatives/sector-index-derivatives
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/markets/amsterdam/equities/list
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/markets/amsterdam/equities/list?page=0
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/fr/markets/amsterdam/equities/list?page=0
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/nb/markets/amsterdam/equities/list?page=0
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/nl/markets/amsterdam/equities/list?page=0
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/pt/markets/amsterdam/equities/list?page=0
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/de/markets/amsterdam/equities/list?page=0
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/it/markets/amsterdam/equities/list?page=0
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/markets/brussels/equities/list
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/markets/dublin/equities/list
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/markets/lisbon/equities/list
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/markets/milan/equities/list
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/markets/oslo/equities/list
- priority=2 score=35 use=possible_public_equity_listing_route_next_phase risk=medium url=https://live.euronext.com/en/markets/paris/equities/list

## Checks

- v2_15d_validation_exists: PASS (critical) - outputs\full_universe_source_acquisition\euronext_validation_v2_15d.json
- v2_15d_validation_passed_or_available: PASS (critical) - EURONEXT_VALIDATION_PASSED_CANDIDATES_DETECTED_REBUILD_STILL_BLOCKED
- raw_files_available: PASS (critical) - raw_files=11
- candidate_endpoints_available: PASS (critical) - candidate_endpoints=1361
- source_strategy_generated: PASS (critical) - strategy_rows=1361
- rebuild_still_blocked: PASS (critical) - current_rows=38287
- no_canonical_dataset_write: PASS (critical) - outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- no_net_new_filtering: PASS (critical) - net_new_filtering=False
- no_expanded_universe_rebuild: PASS (critical) - expanded_universe_rebuilt=False
- usable_table_candidates_review: PASS (warning) - usable_table_candidates=8

## Guards

- Network download performed in v2.15E: false
- Raw files downloaded in v2.15E: false
- Raw files modified after write: false
- Raw HTML parsed for candidate preparation: true
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Canonical dataset modified: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase prepares the rebuild candidate strategy only.

It does not normalize securities, classify final instruments, filter net-new rows, rebuild the expanded universe, score equities, call OpenAI, call broker APIs or launch full 59k.

## Recommended next phase

`v2.15F - Euronext Candidate Extraction Dry Run`
