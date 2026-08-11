# v2.19B - KRX Korea Exchange Acquisition Plan

Status: **KRX_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_FOR_RAW_ACQUISITION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **acquisition-plan-only**

Generated at UTC: `2026-08-11T15:28:22.191450+00:00`

## Executive summary

v2.19B defines the KRX Korea Exchange acquisition plan after v2.19A selected KRX as the next official provider route.

This phase is acquisition-plan-only. It does not download raw data, does not call endpoints, does not extract candidates, does not rebuild an expanded dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Current validated candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Intermediate quality target: `45,000-47,500`
- Stretch target: `50,000`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Route context

- Selected route from v2.19A: `KRX_KOREA_EXCHANGE`
- Planned route name: `KRX - Korea Exchange Official Listed Securities Route`
- Source inventory count: `4`
- Primary sources count: `2`
- Supporting sources count: `1`
- Raw artifacts planned: `4`
- Instrument filters planned: `5`
- Validation steps planned: `7`
- Critical failed checks: `0`

## Source inventory

- P1 `krx_global_listed_company` - Global KRX Listed Company - selected_primary - https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp
- P2 `krx_data_marketplace_all_listed_issues` - KRX Data Marketplace - All Listed Issues - selected_primary_or_crosscheck - https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en
- P3 `public_data_portal_krx_listed_stock_info` - KRX Listed Stock Information OpenAPI - selected_supporting - https://www.data.go.kr/en/data/15094775/openapi.do
- P4 `krx_open_api_data_feed_products` - KRX Open API Data Feed Products - reference_only - https://openapi.krx.co.kr/contents/OPP/DATA/OPPDATA002.jsp

## Raw artifacts planned for v2.19C

- `krx_global_listed_company_raw` from `krx_global_listed_company` -> `outputs/full_universe_source_acquisition/raw/krx_v2_19c/krx_global_listed_company_raw.*`
- `krx_data_marketplace_all_listed_issues_raw` from `krx_data_marketplace_all_listed_issues` -> `outputs/full_universe_source_acquisition/raw/krx_v2_19c/krx_data_marketplace_all_listed_issues_raw.*`
- `public_data_portal_krx_listed_stock_info_raw` from `public_data_portal_krx_listed_stock_info` -> `outputs/full_universe_source_acquisition/raw/krx_v2_19c/public_data_portal_krx_listed_stock_info_raw.*`
- `krx_raw_acquisition_manifest` from `all` -> `outputs/full_universe_source_acquisition/krx_raw_acquisition_manifest_v2_19c.csv`

## Instrument filters

- `keep_common_operating_company_equity` - keep_candidate - Keep ordinary listed operating-company equities after source schema confirms instrument group.
- `include_krx_equity_markets_with_review` - market_scope - Capture KOSPI, KOSDAQ and KONEX in raw; later classify liquidity/review flags before auto-add.
- `exclude_etf_etn_elw_fund_bond_derivative` - exclude - Exclude ETF, ETN, ELW, funds, bonds, derivatives, warrants and structured products.
- `preferred_spac_reit_rights_review` - exclude_or_review - Exclude preferred/preference shares by default; review SPAC, REIT, rights and special-purpose vehicles.
- `symbol_isin_name_dedupe` - dedupe - Use KRX short code, ISIN, company name, English/Korean name and market as dedupe evidence against canonical.

## Validation strategy

- `v2.19C` - KRX Raw Acquisition - official domains only; raw files or error payloads captured; manifest written; no candidate extraction
- `v2.19D` - KRX Raw Validation - at least one primary KRX source parse-ready for candidate extraction
- `v2.19E` - KRX Candidate Extraction Dry Run - candidate-shaped rows, no duplicate KRX identifiers, instrument filters applied
- `v2.19F` - KRX Candidate Validation Against Canonical Dry Run - do not auto-add possible_existing; count only high-confidence potential_net_new
- `v2.19G` - KRX Expanded Rebuild Candidate - schema preserved, current candidate unchanged, canonical unchanged
- `v2.19H` - KRX Expanded Validation - no critical failed checks; no symbol conflicts; 50k gate status explicit
- `v2.19I` - KRX Closure Report - document rows added and remaining to 50k

## Next actions

- Phigh `KRX` - perform_raw_acquisition - v2.19C - KRX Raw Acquisition
- Phigh `KRX` - capture_manifest_and_error_payloads - v2.19C - KRX Raw Acquisition
- Pmedium `50k` - maintain_quality_target - v2.19C - KRX Raw Acquisition

## Checks

- v2_19a_report_exists: PASS (critical) - outputs\full_universe_source_acquisition\next_provider_route_selection_v2_19a.json
- v2_19a_status_expected: PASS (critical) - NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_KRX_SELECTED_ACQUISITION_PLAN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_19a_selected_route_expected: PASS (critical) - selected_route_id=KRX_KOREA_EXCHANGE
- v2_19a_selected_route_csv_exists: PASS (critical) - outputs\full_universe_source_acquisition\next_provider_selected_route_v2_19a.csv
- v2_19a_route_candidates_csv_exists: PASS (critical) - outputs\full_universe_source_acquisition\next_provider_route_candidates_v2_19a.csv
- selected_route_csv_has_one_row: PASS (critical) - selected_route_rows=1
- route_candidates_csv_has_expected_rows: PASS (critical) - route_candidate_rows=5
- active_canonical_exists: PASS (critical) - outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- current_validated_candidate_exists: PASS (critical) - outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv
- active_canonical_rows_expected: PASS (critical) - active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) - current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) - rows_needed_to_50k=9004
- source_inventory_minimum_count: PASS (critical) - source_inventory=4
- primary_sources_available: PASS (critical) - primary_sources=2
- supporting_source_available: PASS (warning) - supporting_sources=1
- raw_artifact_plan_available: PASS (critical) - raw_artifacts_planned=4
- instrument_filters_available: PASS (critical) - instrument_filters=5
- validation_strategy_available: PASS (critical) - validation_steps=7
- official_sources_only: PASS (critical) - all planned URLs are KRX or data.go.kr official sources
- no_full59k_source: PASS (critical) - full59k absent from source inventory
- canonical_sha_unchanged: PASS (critical) - active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) - current validated candidate sha unchanged
- canonical_dataset_not_modified: PASS (critical) - canonical_dataset_modified=False
- candidate_dataset_not_modified: PASS (critical) - candidate_dataset_modified=False
- plan_only_no_raw_download: PASS (critical) - raw_acquisition_performed=False
- plan_only_no_candidate_extraction: PASS (critical) - candidate_extraction_performed=False
- plan_only_no_expanded_rebuild: PASS (critical) - expanded_rebuild_candidate_performed=False
- network_not_used_by_script: PASS (critical) - network_download_performed=False
- scoring_not_recalculated: PASS (critical) - scoring_recalculated=False
- openai_not_called: PASS (critical) - openai_called=False
- broker_not_called: PASS (critical) - broker_called=False
- full59k_not_launched: PASS (critical) - full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) - 40996 < 50000
- krx_raw_acquisition_next_needed: PASS (critical) - v2.19C - KRX Raw Acquisition

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Acquisition plan performed: true
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Current candidate dataset read: true
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
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

`v2.19C - KRX Raw Acquisition`
