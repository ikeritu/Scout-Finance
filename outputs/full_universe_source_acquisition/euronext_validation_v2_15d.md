# v2.15D - Euronext Validation

Status: **EURONEXT_VALIDATION_PASSED_CANDIDATES_DETECTED_REBUILD_STILL_BLOCKED**

Phase type: **validation-only**

Generated at UTC: `2026-07-10T22:27:01.038023+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Validation summary

- Raw files: 11
- Total raw bytes: 4001113
- Tables detected: 0
- Scripts detected: 0
- ISIN-like occurrences: 0
- Candidate endpoints: 1361
- Critical failed checks: 0
- Warning failed checks: 0

## Raw file diagnostics

- `euronext_advanced_reference_data.html` bytes=409557 tables=0 scripts=0 isin_like=0 endpoints=578
- `euronext_amsterdam_equities_list.html` bytes=342057 tables=0 scripts=0 isin_like=0 endpoints=398
- `euronext_brussels_equities_list.html` bytes=338285 tables=0 scripts=0 isin_like=0 endpoints=398
- `euronext_dublin_equities_list.html` bytes=296723 tables=0 scripts=0 isin_like=0 endpoints=399
- `euronext_lisbon_equities_list.html` bytes=313044 tables=0 scripts=0 isin_like=0 endpoints=398
- `euronext_live_all_equities.html` bytes=423012 tables=0 scripts=0 isin_like=0 endpoints=397
- `euronext_live_equities_overview.html` bytes=346293 tables=0 scripts=0 isin_like=0 endpoints=466
- `euronext_milan_equities_list.html` bytes=380685 tables=0 scripts=0 isin_like=0 endpoints=398
- `euronext_oslo_equities_list.html` bytes=350439 tables=0 scripts=0 isin_like=0 endpoints=399
- `euronext_paris_equities_list.html` bytes=385397 tables=0 scripts=0 isin_like=0 endpoints=399
- `euronext_static_reference_data.html` bytes=415621 tables=0 scripts=0 isin_like=0 endpoints=595

## Top candidate endpoints

- score=95 hints=euronext|instrument|instruments|json|live.euronext.com|stock url=https://live.euronext.com/en/instrumentSearch/searchJsonByMic?listMics&amp;instruType=Stock&amp;idBlockSearchBox=134
- score=85 hints=euronext|instrument|instruments|json|live.euronext.com url=https://live.euronext.com/en/instrumentSearch/searchJSON
- score=80 hints=data|euronext|instrument|instruments|stock|stocks url=https://athens.euronext.com/en/market-data/instruments/stocks?page=1
- score=75 hints=api|equity|euronext|live.euronext.com url=https://live.euronext.com/en/news/boursolive-2026-equity-markets-how-ai-reshaping-landscape
- score=60 hints=equities|equity|euronext|live.euronext.com url=https://live.euronext.com/en/products/equities/global-equity-market/list
- score=60 hints=equities|equity|euronext|live.euronext.com url=https://live.euronext.com/en/products/equities/equity-espresso
- score=60 hints=euronext|live.euronext.com|stock|stocks url=https://live.euronext.com/en/education/stocks
- score=60 hints=equities|equity|euronext|live.euronext.com url=https://live.euronext.com/en/markets/milan/equities/global-equity-market/list
- score=60 hints=euronext|live.euronext.com|stock|stocks url=https://live.euronext.com/en/news/what-difference-between-stocks-and-bonds
- score=60 hints=euronext|live.euronext.com|stock|stocks url=https://live.euronext.com/en/news/how-protect-stocks-if-market-goes-down
- score=60 hints=euronext|live.euronext.com|stock|stocks url=https://live.euronext.com/en/news/how-generate-income-stocks
- score=60 hints=euronext|live.euronext.com|stock|stocks url=https://live.euronext.com/en/news/how-invest-stocks
- score=60 hints=euronext|live.euronext.com|stock|stocks url=https://live.euronext.com/en/news/how-are-stocks-priced
- score=50 hints=equities|equity|euronext url=https://www.euronext.com/en/csd/oslo/equities-and-equity-certificates
- score=50 hints=equities|equity|euronext url=https://www.euronext.com/en/csd/oslo/equities-and-equity-certificates/shareholder-register
- score=50 hints=equities|equity|euronext url=https://www.euronext.com/en/csd/oslo/equities-and-equity-certificates/general-meetings
- score=50 hints=equities|equity|euronext url=https://www.euronext.com/en/csd/oslo/equities-and-equity-certificates/employee-share-savings
- score=50 hints=equities|equity|euronext url=https://www.euronext.com/en/csd/oslo/equities-and-equity-certificates/corporate-actions
- score=50 hints=equities|equity|euronext url=https://www.euronext.com/en/csd/oslo/equities-and-equity-certificates/registration
- score=50 hints=equities|equity|euronext url=https://www.euronext.com/en/csd/oslo/equities-and-equity-certificates/vps-issuer-services

## Checks

- raw_dir_exists: PASS (critical) - outputs\full_universe_source_acquisition\raw\euronext_v2_15c
- raw_files_present: PASS (critical) - raw_files=11
- acquisition_manifest_exists: PASS (critical) - outputs\full_universe_source_acquisition\euronext_raw_acquisition_manifest_v2_15c.json
- discovered_links_manifest_exists: PASS (critical) - outputs\full_universe_source_acquisition\euronext_discovered_links_v2_15c.json
- plan_exists: PASS (critical) - outputs\full_universe_source_acquisition\euronext_acquisition_plan_v2_15b.json
- downloads_ok_in_manifest: PASS (critical) - ok_count=11
- candidate_endpoints_detected: PASS (critical) - candidate_endpoints=1361
- source_candidate_usable_for_validation: PASS (critical) - usable=True
- full_source_still_blocked: PASS (critical) - current_rows=38287
- no_rebuild_or_scoring: PASS (critical) - rebuild=False; scoring=False; openai=False; broker=False; full59k=False
- tables_detected_review: PASS (warning) - tables=0
- isin_like_detected_review: PASS (warning) - isin_like=0

## Guards

- Network download performed in v2.15D: false
- Raw files downloaded in v2.15D: false
- Raw files modified after write: false
- Workbook/CSV parsed for validation: true
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

This phase validates raw Euronext acquisition artifacts and detects candidate endpoints/structure only.

It does not normalize securities, classify final instruments, filter net-new rows, rebuild the expanded universe, score equities, call OpenAI, call broker APIs or launch full 59k.

## Recommended next phase

`v2.15E - Euronext Expanded Rebuild Candidate Preparation`

Fallback if candidate endpoint quality is insufficient:

`v2.15D2 - Euronext Endpoint Discovery Validation`
