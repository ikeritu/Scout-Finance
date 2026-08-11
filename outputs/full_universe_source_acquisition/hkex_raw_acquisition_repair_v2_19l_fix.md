# v2.19L_FIX — HKEX Raw Acquisition Repair

Status: **HKEX_RAW_ACQUISITION_REPAIR_COMPLETED_STRUCTURED_DOWNLOADS_CAPTURED_RAW_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **raw-acquisition-repair-only**

Generated at UTC: `2026-08-11T20:15:12.191181+00:00`

## Executive summary

v2.19L_FIX captures official HKEX structured downloads identified in v2.19M.

This phase performs raw acquisition repair only. It does not validate repaired raw artifacts for parse-readiness, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Repair summary

- Download candidate rows from v2.19M: `33`
- Selected downloads: `9`
- Artifacts written: `9`
- Raw files exist: `9`
- Header files exist: `9`
- Non-empty raw files: `9`
- HTTP success count: `9`
- HTTP error count: `0`
- Structured extension count: `9`
- Official scope violations: `0`
- Top primary Full List captured: `True`

## Manifest

- `hkex_repair_01_full_list_of_securities` — HTTP `200` — bytes `1382593` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\01_full_list_of_securities.xlsx`
- `hkex_repair_02_list_of_approved_spac_exchange_participants` — HTTP `200` — bytes `30720` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\02_list_of_approved_spac_exchange_participants.xls`
- `hkex_repair_03_secstkorder_xls` — HTTP `200` — bytes `427520` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\03_secstkorder_xls.xls`
- `hkex_repair_04_englishstk_xls` — HTTP `200` — bytes `434176` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\04_englishstk_xls.xls`
- `hkex_repair_05_list_of_vcm_securities_xls` — HTTP `200` — bytes `45568` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\05_list_of_vcm_securities_xls.xls`
- `hkex_repair_06_list_of_cas_securities_xls` — HTTP `200` — bytes `84992` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\06_list_of_cas_securities_xls.xls`
- `hkex_repair_07_isino_xls` — HTTP `200` — bytes `1883136` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\07_isino_xls.xls`
- `hkex_repair_08_isinsehk_xls` — HTTP `200` — bytes `1606656` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\08_isinsehk_xls.xls`
- `hkex_repair_09_list_of_dual_counter_securities` — HTTP `200` — bytes `19751` — `outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix\09_list_of_dual_counter_securities.xlsx`

## Next actions

- Phigh `HKEX` — run_repaired_raw_validation — v2.19M_FIX - HKEX Repaired Raw Validation
- Phigh `HKEX` — validate_list_of_securities_xlsx_parse_readiness — v2.19M_FIX - HKEX Repaired Raw Validation
- Phigh `50k` — preserve_quality_gate — v2.19M_FIX - HKEX Repaired Raw Validation

## Checks

- v2_19m_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_validation_v2_19m.json
- v2_19m_status_expected: PASS (critical) — HKEX_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- download_candidates_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_validation_official_download_candidates_v2_19m.csv
- download_candidates_available: PASS (critical) — download_candidate_rows=33
- selected_downloads_available: PASS (critical) — selected_downloads=9
- top_primary_full_list_selected: PASS (critical) — ListOfSecurities.xlsx selected
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9004
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- raw_repair_directory_exists: PASS (critical) — outputs\full_universe_source_acquisition\raw\hkex_v2_19l_fix
- repair_artifacts_written: PASS (critical) — artifacts_written=9; selected=9
- repair_raw_files_exist: PASS (critical) — raw_files_exist=9/9
- repair_header_files_exist: PASS (critical) — header_files_exist=9/9
- repair_raw_files_nonempty: PASS (critical) — nonempty_raw_count=9/9
- repair_http_success_documented: PASS (critical) — http_success_count=9; http_error_count=0
- repair_official_scope_no_violations: PASS (critical) — official_scope_violations=0
- repair_structured_files_captured: PASS (critical) — structured_extension_count=9
- top_primary_full_list_captured: PASS (critical) — top_primary_full_list_captured=True
- source_readiness_loaded: PASS (warning) — source_readiness_rows=5
- extraction_gate_loaded: PASS (warning) — extraction_gate_rows=6
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- network_used_by_repair_acquisition: PASS (critical) — network_download_performed=True
- raw_acquisition_repair_performed: PASS (critical) — raw_acquisition_repair_performed=True
- raw_validation_not_performed: PASS (critical) — raw_validation_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- next_phase_repaired_raw_validation: PASS (critical) — v2.19M_FIX - HKEX Repaired Raw Validation

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Raw acquisition repair performed: true
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

`v2.19M_FIX - HKEX Repaired Raw Validation`
