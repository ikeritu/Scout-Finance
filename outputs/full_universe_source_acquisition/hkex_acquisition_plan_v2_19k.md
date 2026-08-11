# v2.19K — HKEX Acquisition Plan

Status: **HKEX_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_FOR_RAW_ACQUISITION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **acquisition-plan-only**

Generated at UTC: `2026-08-11T18:04:26.751101+00:00`

## Executive summary

v2.19K prepares the HKEX acquisition plan after HKEX was selected in v2.19J.

This phase is plan-only. It does not download data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Plan summary

- Selected route: `HKEX_HONG_KONG_EXCHANGE`
- Provider: `HKEX`
- Market: `Hong Kong`
- Source inventory rows: `5`
- Raw artifacts planned: `5`
- Validation strategy rows: `5`
- Filtering policy rows: `4`
- Risk register rows: `4`
- Expected gross rows band: `2500-3500`
- Expected net-new band: `1500-2500`

## Source inventory

- `hkex_securities_lists` — primary_candidate_source — `https://www.hkex.com.hk/Services/Trading/Securities/Securities-Lists?sc_lang=en`
- `hkex_equities` — primary_or_crosscheck_source — `https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en`
- `hkex_newly_listed_securities` — supporting_or_crosscheck_source — `https://www.hkex.com.hk/Services/Trading/Securities/Trading-News/Newly-Listed-Securities?sc_lang=en`
- `hkex_market_search_listing_result` — supporting_or_probe_source — `https://www.hkex.com.hk/Global/HKEX-Market-Search-Listing-Result?sc_lang=en`
- `hkexnews_issuer_search` — issuer_reference_source — `https://www.hkexnews.hk/index.htm`

## Validation strategy

- `HKEX_VAL_001` — critical — Every planned raw artifact must exist, have byte count > 0, and have recorded sha256.
- `HKEX_VAL_002` — critical — All captured artifacts must resolve to hkex.com.hk or hkexnews.hk official hosts.
- `HKEX_VAL_003` — critical — At least one primary/crosscheck artifact must contain parse-ready stock code and issuer/security name rows.
- `HKEX_VAL_004` — warning — Raw validation must identify whether the source mixes equities with warrants, CBBCs, debt, ETFs, REITs, unit trusts or structured products.
- `HKEX_VAL_005` — critical — No HKEX rows may be appended until candidate extraction and validation against canonical are complete.

## Filtering policy

- `HKEX_FILTER_001` — include — Include ordinary equity/listed company securities only when stock code and issuer/security name are present.
- `HKEX_FILTER_002` — exclude — Exclude warrants, CBBCs, derivative warrants, debt securities, ETFs, REITs, unit trusts, structured products and similar non-operating-company instruments unless explicitly approved later.
- `HKEX_FILTER_003` — review — Review multiple counters, RMB/HKD dual counters, share classes and duplicate issuer codes before net-new append.
- `HKEX_FILTER_004` — dedupe — Canonical duplicate checks must compare stock code, ticker variants, issuer name normalization and ISIN when available.

## Next actions

- Phigh `HKEX` — run_hkex_raw_acquisition — v2.19L - HKEX Raw Acquisition
- Phigh `HKEX` — capture_source_pages_before_linked_files — v2.19L - HKEX Raw Acquisition
- Phigh `50k` — preserve_quality_gate — v2.19L - HKEX Raw Acquisition

## Checks

- v2_19j_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\next_provider_route_selection_after_krx_v2_19j.json
- v2_19j_status_expected: PASS (critical) — NEXT_PROVIDER_ROUTE_SELECTION_AFTER_KRX_COMPLETED_HKEX_SELECTED_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- selected_route_csv_exists: PASS (critical) — outputs\full_universe_source_acquisition\next_provider_route_selection_after_krx_selected_route_v2_19j.csv
- decision_matrix_csv_exists: PASS (critical) — outputs\full_universe_source_acquisition\next_provider_route_selection_after_krx_decision_matrix_v2_19j.csv
- selected_route_is_hkex: PASS (critical) — HKEX_HONG_KONG_EXCHANGE
- selected_provider_is_hkex: PASS (critical) — HKEX
- v2_19j_recommended_next_phase_hkex: PASS (critical) — v2.19K - HKEX Acquisition Plan
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9004
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- source_inventory_minimum: PASS (critical) — sources=5
- primary_source_present: PASS (critical) — primary_candidate_source present
- all_sources_official_scope: PASS (critical) — all planned urls hkex/hkexnews official
- raw_artifact_plan_rows_match_sources: PASS (critical) — raw_artifact_plan_rows=5
- validation_strategy_present: PASS (critical) — validation_strategy_rows=5
- filtering_policy_present: PASS (critical) — filtering_policy_rows=4
- risk_register_present: PASS (warning) — risk_register_rows=4
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- network_not_used_by_plan: PASS (critical) — network_download_performed=False
- raw_acquisition_not_performed: PASS (critical) — raw_acquisition_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- next_phase_hkex_raw_acquisition: PASS (critical) — v2.19L - HKEX Raw Acquisition

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Acquisition plan performed: true
- Raw acquisition performed: false
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

`v2.19L - HKEX Raw Acquisition`
