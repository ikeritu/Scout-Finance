# v2.20B — ASX Quality-First Acquisition Plan

Status: **ASX_QUALITY_FIRST_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_RAW_ACQUISITION_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED**

Phase type: **acquisition-plan-only**

Generated at UTC: `2026-08-12T08:12:00.079573+00:00`

## Executive summary

v2.20B defines the ASX quality-first acquisition plan.

The project now operates with a **42,000–45,000** quality-first target band. The current HKEX validated candidate dataset has **41,392** rows, so ASX only needs **608** clean net-new rows to cross the 42k floor and **3,608** clean net-new rows to reach the 45k ceiling.

50k remains aspirational only. ASX must not be used to add low-quality rows, warrants, options, debt, rights, structured products, duplicated fund-like instruments or speculative illiquid microcaps merely to increase row count.

This phase is an acquisition plan only. It does not download ASX files, does not extract candidates, does not validate candidates against canonical, does not rebuild a candidate dataset, does not promote any dataset to canonical, and does not run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Plan summary

- Selected provider: `ASX`
- HKEX validated candidate rows: `41392`
- Operational target floor: `42000`
- Operational target ceiling: `45000`
- Aspirational target: `50000`
- Rows needed to 42k: `608`
- Rows needed to 45k: `3608`
- Rows needed to 50k aspirational: `8608`
- Primary source: `asx_listed_companies_page`
- Identifier enrichment source: `asx_isin_directory`
- Scope reference: `asx_codes_and_descriptors`
- Critical failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Official source plan

- P1 `asx_listed_companies_page` — official_asx_page_with_csv_download — https://www.asx.com.au/markets/trade-our-cash-market/overview/indices
- P2 `asx_isin_directory` — official_asx_excel_download — https://www.asx.com.au/markets/market-resources/isin-services
- P3 `asx_codes_and_descriptors` — official_asx_reference_page — https://www.asx.com.au/markets/market-resources/asx-codes-and-descriptors
- P4 `asx_market_statistics` — official_asx_statistics_page — https://www.asx.com.au/about/market-statistics
- P5 `asx_legacy_csv_candidate` — legacy_direct_csv_candidate — https://www.asx.com.au/asx/research/ASXListedCompanies.csv

## Scope rules

- `ASX_INCLUDE_001` — include `ordinary_equity` — include ordinary listed company shares where code/name/descriptor supports equity scope
- `ASX_INCLUDE_002` — include_conditional `a_reit` — include liquid A-REITs if clearly listed equity-like vehicles
- `ASX_INCLUDE_003` — include_conditional `listed_investment_company_or_trust` — include only if it behaves as listed equity and passes duplicate/instrument checks
- `ASX_EXCLUDE_001` — exclude `warrants` — exclude warrants by default
- `ASX_EXCLUDE_002` — exclude `exchange_traded_options` — exclude options by default
- `ASX_EXCLUDE_003` — exclude `debt_interest_rate_securities_notes_hybrids` — exclude debt, notes, interest-rate securities and hybrids by default
- `ASX_EXCLUDE_004` — exclude `rights_secondary_issues_partly_paid` — exclude rights, special settlement, partly paid and other secondary issues by default
- `ASX_EXCLUDE_005` — exclude `etf_managed_fund_structured_product` — exclude ETFs, managed funds and structured products by default
- `ASX_EXCLUDE_006` — exclude_or_flag `illiquid_speculative_microcap` — exclude or flag speculative/illiquid microcaps where source allows

## Expected yield scenarios

- `conservative_quality_floor` — mid `608` clean net-new — may_cross_42k_if_mid_case
- `base_quality_case` — mid `1200` clean net-new — crosses_42k_and_moves_toward_45k
- `strong_quality_case` — mid `2500` clean net-new — could_reach_or_approach_45k
- `bad_yield_case` — mid `249` clean net-new — does_not_justify_long_route_unless_quality_exceptional

## Roadmap

- `v2.20A` — Quality-First Target Reset and Provider Selection: `closed`
- `v2.20B` — ASX Quality-First Acquisition Plan: `generated_by_this_phase`
- `v2.20C` — ASX Quality-First Raw Acquisition: `next`
- `v2.20D` — ASX Raw Validation: `planned`
- `v2.20E` — ASX Candidate Extraction Dry Run: `planned_if_raw_ready`
- `v2.20F` — ASX Candidate Validation Against Current Candidate Dry Run: `planned_if_extraction_ready`
- `v2.20G` — ASX Expanded Rebuild Candidate: `conditional`
- `v2.20H` — ASX Expanded Validation: `conditional`
- `v2.20I` — ASX Closure Report: `conditional`

## Next actions

- Phigh `ASX` — open_asx_quality_first_raw_acquisition — v2.20C - ASX Quality-First Raw Acquisition
- Phigh `quality_target` — preserve_42k_45k_operational_band — v2.20C - ASX Quality-First Raw Acquisition
- Pmedium `fallback` — keep_tmx_tsx_only_as_backup — post-ASX closure or ASX block

## Checks

- v2_20a_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\quality_first_target_reset_provider_selection_v2_20a.json
- v2_20a_status_expected: PASS (critical) — QUALITY_FIRST_TARGET_RESET_COMPLETED_42K_45K_OPERATIONAL_ASX_SELECTED_50K_ASPIRATIONAL_FULL59K_DEPRECATED
- v2_20a_selected_provider_asx: PASS (critical) — ASX
- v2_20a_next_phase_expected: PASS (critical) — v2.20B - ASX Quality-First Acquisition Plan
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- hkex_validated_candidate_rows_expected: PASS (critical) — hkex_rows=41392
- active_canonical_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- current_candidate_sha_expected: PASS (critical) — 05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2
- hkex_validated_candidate_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- active_canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- current_candidate_sha_unchanged: PASS (critical) — current candidate sha unchanged
- hkex_candidate_sha_unchanged: PASS (critical) — HKEX candidate sha unchanged
- quality_floor_target_preserved: PASS (critical) — quality_floor=42000
- quality_ceiling_target_preserved: PASS (critical) — quality_ceiling=45000
- rows_needed_to_quality_floor_expected: PASS (critical) — rows_needed_to_42k=608
- rows_needed_to_quality_ceiling_expected: PASS (critical) — rows_needed_to_45k=3608
- rows_needed_to_50k_aspirational_expected: PASS (warning) — rows_needed_to_50k=8608
- official_sources_defined: PASS (critical) — sources=5
- primary_asx_source_defined: PASS (critical) — asx_listed_companies_page
- isin_enrichment_source_defined: PASS (critical) — asx_isin_directory
- scope_rules_defined: PASS (critical) — scope_rules=9
- exclude_derivatives_debt_structured_products: PASS (critical) — critical exclusions present
- yield_scenarios_defined: PASS (critical) — yield_scenarios=4
- next_phase_raw_acquisition: PASS (critical) — v2.20C - ASX Quality-First Raw Acquisition
- acquisition_plan_only: PASS (critical) — acquisition plan only
- network_download_not_performed: PASS (critical) — network_download_performed=False
- raw_acquisition_not_performed: PASS (critical) — raw_acquisition_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- candidate_validation_not_performed: PASS (critical) — candidate_validation_against_canonical_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- expanded_validation_not_performed: PASS (critical) — expanded_validation_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- current_candidate_dataset_not_modified: PASS (critical) — current_candidate_dataset_modified=False
- hkex_candidate_dataset_not_modified: PASS (critical) — hkex_candidate_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Guards

- Acquisition plan only: true
- Selected provider: `ASX`
- Network download performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current candidate dataset modified: false
- HKEX validated candidate dataset modified: false
- Active canonical replaced: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false

## Recommended next phase

`v2.20C - ASX Quality-First Raw Acquisition`
