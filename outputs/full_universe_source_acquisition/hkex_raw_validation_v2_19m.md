# v2.19M — HKEX Raw Validation

Status: **HKEX_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **raw-validation-only**

Generated at UTC: `2026-08-11T20:02:57.722982+00:00`

## Executive summary

v2.19M validates the HKEX/HKEXnews raw artifacts captured in v2.19L.

This phase performs raw validation only. It does not download data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

- Manifest rows: `5`
- Artifact audit rows: `5`
- Artifacts exist: `5/5`
- Headers exist: `5/5`
- Bytes match: `5/5`
- SHA256 match: `5/5`
- Official scope violations: `0`
- Candidate ready count: `0`
- Primary candidate ready count: `0`
- Extraction allowed count: `0`
- Official download candidate count: `33`
- High priority download candidate count: `24`
- Critical issue count: `0`
- Warning issue count: `2`
- Extraction ready: `False`
- Repair required: `True`
- Route blocked before extraction: `False`

## Source readiness

- `hkex_securities_lists_page` — primary_page_captured_not_direct_parse_ready — candidate_ready `False` — primary `False`
- `hkex_equities_page` — primary_page_captured_not_direct_parse_ready — candidate_ready `False` — primary `False`
- `hkex_newly_listed_securities_page` — supporting_reference_captured_not_candidate_ready — candidate_ready `False` — primary `False`
- `hkex_market_search_listing_result_page` — supporting_reference_captured_not_candidate_ready — candidate_ready `False` — primary `False`
- `hkexnews_index_page` — supporting_reference_captured_not_candidate_ready — candidate_ready `False` — primary `False`

## Top official download candidates

- score `100` — `Full List of Securities` — `https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx`
- score `95` — `List of Approved SPAC Exchange Participants` — `https://www.hkex.com.hk/-/media/HKEX-Market/Products/Securities/Equities/SPAC/List-of-Approved-SPAC-EP.xls`
- score `70` — `List of Dual Counter Securities` — `https://www.hkex.com.hk/-/media/HKEX-Market/Services/Trading/Securities/Securities-Lists/Dual_Counter_Security_List.xlsx`
- score `70` — `` — `https://www.hkex.com.hk/-/media/HKEX-Market/Services/Trading/Securities/Securities-Lists/Redirect_List-of-Closing-Auction-Session-(CAS)-Securities/list-of-cas-securities.xls`
- score `70` — `` — `https://www.hkex.com.hk/-/media/HKEX-Market/Services/Trading/Securities/Securities-Lists/Redirect_List-of-Volatility-Control-Mechanism-(VCM)-Securities/list-of-vcm-securities.xls`
- score `70` — `` — `https://www.hkex.com.hk/-/media/HKEX-Market/Services/Trading/Securities/Securities-Lists/ISINs-assigned-by-HKEX/isinsehk.xls`
- score `70` — `` — `https://www.hkex.com.hk/-/media/HKEX-Market/Services/Trading/Securities/Securities-Lists/ISINs-assigned-by-Other-Numbering-Agencies/isino.xls`
- score `70` — `` — `https://www.hkex.com.hk/-/media/HKEX-Market/Services/Trading/Securities/Securities-Lists/Securities-Using-Standard-Transfer-Form-(including-GEM)-By-Stock-Code-Order/secstkorder.xls`
- score `70` — `` — `https://www.hkex.com.hk/-/media/HKEX-Market/Services/Trading/Securities/Securities-Lists/Securities-Using-Standard-Transfer-Form-(including-GEM)-By-English-Stock-Short-Name-Order/englishstk.xls`
- score `45` — `Equities` — `https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en`
- score `45` — `Equities` — `https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities?sc_lang=en`
- score `45` — `ZJ INNOLIGHT` — `https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities/Equities-Quote?sym=3308&sc_lang=en`
- score `45` — `SUNCORP TECH` — `https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities/Equities-Quote?sym=2903&sc_lang=en`
- score `45` — `NASN TECH` — `https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities/Equities-Quote?sym=2261&sc_lang=en`
- score `45` — `BRIGHTSTAR TECH` — `https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities/Equities-Quote?sym=8577&sc_lang=en`
- score `45` — `STAPLED SECURITIES` — `https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en#collapse2`
- score `45` — `SPAC Shares and SPAC Warrants` — `https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en#collapse3`
- score `45` — `List of SPAC Warrants` — `https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities?sc_lang=en&subcat=6`
- score `45` — `List of SPAC Shares` — `https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities?sc_lang=en&subcat=5`
- score `45` — `HKD-RMB Dual Counter Securities` — `https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en#collapse0`
- score `45` — `Equity Warrants` — `https://www.hkex.com.hk/Products/Securities/Equities/Equity-Warrants?sc_lang=en`
- score `45` — `DEPOSITARY RECEIPTS` — `https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en#collapse1`
- score `45` — `` — `https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en#`
- score `45` — `` — `https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en#hkex_page_header`
- score `20` — `Securities Lists` — `https://www.hkex.com.hk/Services/Trading/Securities/Securities-Lists?sc_lang=en`

## Extraction gate

- `artifact_integrity`: PASS (critical) — critical_issue_count=0; artifacts=5/5; bytes=5/5; sha256=5/5
- `official_scope`: PASS (critical) — official_scope_violations=0
- `primary_candidate_ready_present`: NOT PASS (warning) — primary_candidate_ready_count=0
- `structured_extraction_allowed`: NOT PASS (warning) — extraction_allowed_count=0
- `official_download_candidates_available`: PASS (warning) — official_download_candidate_count=33; high_priority=24
- `extraction_ready`: NOT PASS (warning) — extraction_ready=False; repair_required=True; route_blocked_before_extraction=False

## Next actions

- Phigh `HKEX` — capture_official_download_candidates — v2.19L_FIX - HKEX Raw Acquisition Repair
- Phigh `HKEX` — prioritize_xls_xlsx_full_list_equities_links — v2.19L_FIX - HKEX Raw Acquisition Repair
- Phigh `50k` — preserve_quality_gate — v2.19L_FIX - HKEX Raw Acquisition Repair

## Checks

- v2_19l_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_v2_19l.json
- v2_19l_status_expected: PASS (critical) — HKEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- manifest_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_manifest_v2_19l.csv
- source_diagnostics_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_source_diagnostics_v2_19l.csv
- discovered_links_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_discovered_links_v2_19l.csv
- html_signals_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_html_signals_v2_19l.csv
- artifact_index_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_artifact_index_v2_19l.csv
- manifest_rows_expected: PASS (critical) — manifest_rows=5
- artifact_index_rows_expected: PASS (critical) — artifact_index_rows=5
- source_inventory_loaded: PASS (critical) — source_inventory_rows=5
- validation_strategy_loaded: PASS (critical) — validation_strategy_rows=5
- filtering_policy_loaded: PASS (critical) — filtering_policy_rows=4
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9004
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- artifact_integrity_no_critical_issues: PASS (critical) — critical_issue_count=0
- raw_files_exist: PASS (critical) — raw_files_exist=5/5
- headers_exist: PASS (critical) — headers_exist=5/5
- bytes_match: PASS (critical) — bytes_match=5/5
- sha256_match: PASS (critical) — sha256_match=5/5
- official_scope_no_violations: PASS (critical) — official_scope_violations=0
- source_readiness_rows_expected: PASS (critical) — source_readiness_rows=5
- candidate_ready_count_documented: PASS (warning) — candidate_ready_count=0
- primary_candidate_ready_count_documented: PASS (warning) — primary_candidate_ready_count=0
- official_download_candidates_documented: PASS (warning) — official_download_candidate_count=33
- repair_required_or_extraction_ready_or_blocked: PASS (critical) — extraction_ready=False; repair_required=True; route_blocked=False
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- network_not_used_by_raw_validation: PASS (critical) — network_download_performed=False
- raw_files_read: PASS (critical) — raw_files_read=True
- raw_files_written_false: PASS (critical) — raw_files_written=False
- raw_validation_performed: PASS (critical) — raw_validation_performed=True
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw validation performed: true
- Raw files read: true
- Raw files written: false
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

`v2.19L_FIX - HKEX Raw Acquisition Repair`
