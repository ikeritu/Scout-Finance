# v2.19L — HKEX Raw Acquisition

Status: **HKEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **raw-acquisition-only**

Generated at UTC: `2026-08-11T18:35:23.438397+00:00`

## Executive summary

v2.19L captures official HKEX/HKEXnews raw artifacts planned in v2.19K.

This phase performs raw acquisition only. It does not validate raw artifacts for parse-readiness, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Acquisition summary

- Source inventory rows: `5`
- Raw artifact plan rows: `5`
- Artifacts written: `5`
- Raw files exist: `5`
- Header files exist: `5`
- Non-empty raw files: `5`
- HTTP success count: `5`
- HTTP error count: `0`
- Official scope violations: `0`
- Discovered links: `1028`
- Official discovered links: `919`
- Candidate-related links: `381`
- Download-like links: `15`
- HTML signal rows: `95`
- HTML signals present: `53`

## Manifest

- `hkex_securities_lists_page` — HTTP `200` — bytes `398508` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l\01_hkex_securities_lists_page.html`
- `hkex_equities_page` — HTTP `200` — bytes `457338` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l\02_hkex_equities_page.html`
- `hkex_newly_listed_securities_page` — HTTP `200` — bytes `257012` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l\03_hkex_newly_listed_securities_page.html`
- `hkex_market_search_listing_result_page` — HTTP `200` — bytes `378551` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l\04_hkex_market_search_listing_result_page.html`
- `hkexnews_index_page` — HTTP `200` — bytes `9169` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l\05_hkexnews_index_page.htm`

## Source diagnostics

- `hkex_securities_lists_page` — anchors `205` — scripts `43` — tables `8` — downloads `8`
- `hkex_equities_page` — anchors `267` — scripts `42` — tables `9` — downloads `7`
- `hkex_newly_listed_securities_page` — anchors `197` — scripts `43` — tables `10` — downloads `0`
- `hkex_market_search_listing_result_page` — anchors `163` — scripts `43` — tables `9` — downloads `0`
- `hkexnews_index_page` — anchors `5` — scripts `16` — tables `0` — downloads `0`

## Next actions

- Phigh `HKEX` — run_hkex_raw_validation — v2.19M - HKEX Raw Validation
- Phigh `HKEX` — review_discovered_links_for_official_download_candidates — v2.19M - HKEX Raw Validation
- Phigh `50k` — preserve_quality_gate — v2.19M - HKEX Raw Validation

## Checks

- v2_19k_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_acquisition_plan_v2_19k.json
- v2_19k_status_expected: PASS (critical) — HKEX_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_FOR_RAW_ACQUISITION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- source_inventory_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_acquisition_plan_source_inventory_v2_19k.csv
- raw_artifact_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_acquisition_plan_raw_artifacts_v2_19k.csv
- source_inventory_rows_expected: PASS (critical) — source_inventory_rows=5
- raw_artifact_plan_rows_expected: PASS (critical) — raw_artifact_plan_rows=5
- validation_strategy_loaded: PASS (critical) — validation_strategy_rows=5
- filtering_policy_loaded: PASS (critical) — filtering_policy_rows=4
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9004
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- raw_directory_exists: PASS (critical) — outputs\full_universe_source_acquisition\raw\hkex_v2_19l
- planned_artifacts_written: PASS (critical) — artifacts_written=5; planned=5
- raw_files_exist: PASS (critical) — raw_files_exist=5/5
- header_files_exist: PASS (critical) — header_files_exist=5/5
- raw_files_nonempty: PASS (critical) — nonempty_raw_count=5/5
- official_scope_no_violations: PASS (critical) — official_scope_violations=0
- http_success_documented: PASS (warning) — http_success_count=5; http_error_count=0
- discovered_links_documented: PASS (warning) — discovered_links_count=1028
- candidate_related_links_documented: PASS (warning) — candidate_related_links_count=381
- download_like_links_documented: PASS (warning) — download_like_links_count=15
- html_signals_documented: PASS (warning) — html_signal_present_count=53
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- network_used_by_raw_acquisition: PASS (critical) — network_download_performed=True
- raw_acquisition_performed: PASS (critical) — raw_acquisition_performed=True
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- next_phase_hkex_raw_validation: PASS (critical) — v2.19M - HKEX Raw Validation

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Raw acquisition performed: true
- Raw validation performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`v2.19M - HKEX Raw Validation`
