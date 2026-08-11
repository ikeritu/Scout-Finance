# v2.19M_FIX — HKEX Repaired Raw Validation

Status: **HKEX_REPAIRED_RAW_VALIDATION_COMPLETED_PARSE_READY_EXTRACTION_DRY_RUN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **repaired-raw-validation-only**

Generated at UTC: `2026-08-11T20:27:16.075536+00:00`

## Executive summary

v2.19M_FIX validates the repaired HKEX structured raw files captured in v2.19L_FIX.

This phase performs repaired raw validation only. It reads repaired raw files and inspects workbook/container structure. It does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

- Manifest rows: `9`
- Artifact audit rows: `9`
- Raw files exist: `9/9`
- Headers exist: `9/9`
- Non-empty raw files: `9/9`
- Bytes match: `9/9`
- SHA256 match: `9/9`
- HTTP success: `9/9`
- Official scope violations: `0`
- XLSX valid count: `2`
- XLS OLE valid count: `7`
- Primary parse-ready count: `1`
- Extraction dry-run allowed count: `1`
- Top primary parse-ready: `True`
- Top primary parseable stock-code rows: `17630`
- Critical issue count: `0`
- Warning issue count: `0`

## Workbook inventory

- `hkex_repair_01_full_list_of_securities` — ext `.xlsx` — sheets `1` — primary rows `17630`
- `hkex_repair_02_list_of_approved_spac_exchange_participants` — ext `.xls` — sheets `0` — primary rows `0`
- `hkex_repair_03_secstkorder_xls` — ext `.xls` — sheets `0` — primary rows `0`
- `hkex_repair_04_englishstk_xls` — ext `.xls` — sheets `0` — primary rows `0`
- `hkex_repair_05_list_of_vcm_securities_xls` — ext `.xls` — sheets `0` — primary rows `0`
- `hkex_repair_06_list_of_cas_securities_xls` — ext `.xls` — sheets `0` — primary rows `0`
- `hkex_repair_07_isino_xls` — ext `.xls` — sheets `0` — primary rows `0`
- `hkex_repair_08_isinsehk_xls` — ext `.xls` — sheets `0` — primary rows `0`
- `hkex_repair_09_list_of_dual_counter_securities` — ext `.xlsx` — sheets `1` — primary rows `14`

## Parse readiness

- `hkex_repair_01_full_list_of_securities` — primary_parse_ready_for_candidate_extraction_dry_run — extraction_allowed `True` — rows `17630`
- `hkex_repair_02_list_of_approved_spac_exchange_participants` — supporting_structured_file_validated — extraction_allowed `False` — rows `0`
- `hkex_repair_03_secstkorder_xls` — supporting_structured_file_validated — extraction_allowed `False` — rows `0`
- `hkex_repair_04_englishstk_xls` — supporting_structured_file_validated — extraction_allowed `False` — rows `0`
- `hkex_repair_05_list_of_vcm_securities_xls` — supporting_structured_file_validated — extraction_allowed `False` — rows `0`
- `hkex_repair_06_list_of_cas_securities_xls` — supporting_structured_file_validated — extraction_allowed `False` — rows `0`
- `hkex_repair_07_isino_xls` — supporting_structured_file_validated — extraction_allowed `False` — rows `0`
- `hkex_repair_08_isinsehk_xls` — supporting_structured_file_validated — extraction_allowed `False` — rows `0`
- `hkex_repair_09_list_of_dual_counter_securities` — supporting_structured_file_validated — extraction_allowed `False` — rows `14`

## Next actions

- Phigh `HKEX` — run_candidate_extraction_dry_run — v2.19N - HKEX Candidate Extraction Dry Run
- Phigh `HKEX` — extract_from_primary_full_list_only_first — v2.19N - HKEX Candidate Extraction Dry Run
- Phigh `50k` — preserve_quality_gate — v2.19N - HKEX Candidate Extraction Dry Run

## Checks

- v2_19l_fix_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_repair_v2_19l_fix.json
- v2_19l_fix_status_expected: PASS (critical) — HKEX_RAW_ACQUISITION_REPAIR_COMPLETED_STRUCTURED_DOWNLOADS_CAPTURED_RAW_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- repair_manifest_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_repair_manifest_v2_19l_fix.csv
- repair_manifest_rows_expected: PASS (critical) — manifest_rows=9
- repair_artifact_index_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_repair_artifact_index_v2_19l_fix.csv
- repair_artifact_index_rows_expected: PASS (critical) — artifact_index_rows=9
- repair_source_diagnostics_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_repair_source_diagnostics_v2_19l_fix.csv
- repair_selected_downloads_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_raw_acquisition_repair_selected_downloads_v2_19l_fix.csv
- repair_selected_downloads_rows_expected: PASS (critical) — selected_download_rows=9
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9004
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- artifact_audit_rows_expected: PASS (critical) — artifact_audit_rows=9
- raw_files_exist: PASS (critical) — raw_files_exist=9/9
- headers_exist: PASS (critical) — headers_exist=9/9
- raw_files_nonempty: PASS (critical) — nonempty_raw_count=9/9
- bytes_match: PASS (critical) — bytes_match=9/9
- sha256_match: PASS (critical) — sha256_match=9/9
- http_success: PASS (critical) — http_success=9/9
- official_scope_no_violations: PASS (critical) — official_scope_violations=0
- xlsx_valid_count_documented: PASS (critical) — xlsx_valid_count=2
- xls_ole_valid_count_documented: PASS (warning) — xls_ole_valid_count=7
- top_primary_full_list_parse_ready: PASS (critical) — top_primary_parse_ready=True; stock_rows=17630
- primary_parse_ready_count_positive: PASS (critical) — primary_parse_ready_count=1
- extraction_dry_run_allowed_count_positive: PASS (critical) — extraction_dry_run_allowed_count=1
- support_structured_valid_count_documented: PASS (warning) — support_structured_valid_count=8
- critical_issue_count_zero: PASS (critical) — critical_issue_count=0
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000
- network_not_used_by_repaired_raw_validation: PASS (critical) — network_download_performed=False
- raw_files_read: PASS (critical) — raw_files_read=True
- raw_files_written_false: PASS (critical) — raw_files_written=False
- repaired_raw_validation_performed: PASS (critical) — repaired_raw_validation_performed=True
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
- Repaired raw validation performed: true
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

`v2.19N - HKEX Candidate Extraction Dry Run`
