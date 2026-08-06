# v2.17D - NSE India Raw Validation

Status: **NSE_INDIA_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_CANDIDATE_EXTRACTION_READY_FULL_SOURCE_STILL_BLOCKED**

Phase type: **provider-raw-validation-only**

Generated at UTC: `2026-08-06T09:35:34.720303+00:00`

## Executive summary

NSE India raw validation completed.

This phase validates local raw files captured in v2.17C. It checks file existence, bytes, SHA-256, gzip decompression, CSV parseability, headers and row counts. It does not extract candidate securities, does not compare against the canonical dataset and does not modify or rebuild any expanded universe dataset.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completion: `76.57%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Raw validation summary

- Raw directory: `outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c`
- Manifest rows: `17`
- File profiles: `17`
- Schema profiles: `14`
- Source diagnostics: `17`
- Valid raw CSV files: `14`
- Plain CSV files: `12`
- Gzip CSV files: `2`
- Landing files: `3`
- Equity segment rows: `2397`
- MII valid files: `2`
- Duplicate SHA groups: `1`
- Critical failed checks: `0`

## File profiles

- `nse_home_session_seed` `landing_html` bucket=`landing_saved` rows=`0` cols=`0` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_home_session_seed__landing_html.html`
- `nse_all_reports_landing` `landing_html` bucket=`landing_saved` rows=`0` cols=`0` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_all_reports_landing__landing_html.html`
- `nse_securities_available_for_trading_landing` `landing_html` bucket=`landing_saved` rows=`0` cols=`0` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_securities_available_for_trading_landing__landing_html.html`
- `nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive` `mii_security_file_candidate` bucket=`valid_raw_csv` rows=`36243` cols=`120` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive__mii_security_file_candidate.csv.gz`
- `nse_all_reports_cm_mii_security_file_nse_listed` `mii_security_file_candidate` bucket=`valid_raw_csv` rows=`36243` cols=`120` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_all_reports_cm_mii_security_file_nse_listed__mii_security_file_candidate.csv.gz`
- `nse_securities_available_equity_segment` `raw_source_file` bucket=`valid_raw_csv` rows=`2397` cols=`8` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_securities_available_equity_segment__raw_source_file.csv`
- `nse_securities_available_sme` `raw_source_file` bucket=`valid_raw_csv` rows=`560` cols=`8` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_securities_available_sme__raw_source_file.csv`
- `nse_idrs` `raw_source_file` bucket=`valid_raw_csv` rows=`4` cols=`8` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_idrs__raw_source_file.csv`
- `nse_preference_shares` `raw_source_file` bucket=`valid_raw_csv` rows=`4` cols=`15` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_preference_shares__raw_source_file.csv`
- `nse_warrants` `raw_source_file` bucket=`valid_raw_csv` rows=`1` cols=`6` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_warrants__raw_source_file.csv`
- `nse_close_ended_mf` `raw_source_file` bucket=`valid_raw_csv` rows=`119` cols=`8` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_close_ended_mf__raw_source_file.csv`
- `nse_etfs` `raw_source_file` bucket=`valid_raw_csv` rows=`341` cols=`7` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_etfs__raw_source_file.csv`
- `nse_changes_company_names` `raw_source_file` bucket=`valid_raw_csv` rows=`2321` cols=`4` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_changes_company_names__raw_source_file.csv`
- `nse_changes_symbols` `raw_source_file` bucket=`valid_raw_csv` rows=`1053` cols=`4` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_changes_symbols__raw_source_file.csv`
- `nse_invits` `raw_source_file` bucket=`valid_raw_csv` rows=`7` cols=`8` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_invits__raw_source_file.csv`
- `nse_reits` `raw_source_file` bucket=`valid_raw_csv` rows=`5` cols=`8` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_reits__raw_source_file.csv`
- `nse_debt_instruments` `raw_source_file` bucket=`valid_raw_csv` rows=`6066` cols=`15` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_debt_instruments__raw_source_file.csv`

## Source diagnostics

- `nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive` bucket=`valid_raw_source` csv_ok=`1` rows=`36243`
- `nse_all_reports_cm_mii_security_file_nse_listed` bucket=`valid_raw_source` csv_ok=`1` rows=`36243`
- `nse_all_reports_landing` bucket=`landing_or_html_only` csv_ok=`0` rows=`0`
- `nse_changes_company_names` bucket=`valid_raw_source` csv_ok=`1` rows=`2321`
- `nse_changes_symbols` bucket=`valid_raw_source` csv_ok=`1` rows=`1053`
- `nse_close_ended_mf` bucket=`valid_raw_source` csv_ok=`1` rows=`119`
- `nse_debt_instruments` bucket=`valid_raw_source` csv_ok=`1` rows=`6066`
- `nse_etfs` bucket=`valid_raw_source` csv_ok=`1` rows=`341`
- `nse_home_session_seed` bucket=`landing_or_html_only` csv_ok=`0` rows=`0`
- `nse_idrs` bucket=`valid_raw_source` csv_ok=`1` rows=`4`
- `nse_invits` bucket=`valid_raw_source` csv_ok=`1` rows=`7`
- `nse_preference_shares` bucket=`valid_raw_source` csv_ok=`1` rows=`4`
- `nse_reits` bucket=`valid_raw_source` csv_ok=`1` rows=`5`
- `nse_securities_available_equity_segment` bucket=`valid_raw_source` csv_ok=`1` rows=`2397`
- `nse_securities_available_for_trading_landing` bucket=`landing_or_html_only` csv_ok=`0` rows=`0`
- `nse_securities_available_sme` bucket=`valid_raw_source` csv_ok=`1` rows=`560`
- `nse_warrants` bucket=`valid_raw_source` csv_ok=`1` rows=`1`

## Checks

- v2_17c_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_raw_acquisition_v2_17c.json
- v2_17c_status_expected: PASS (critical) — NSE_INDIA_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED
- v2_17c_recommended_d: PASS (critical) — v2.17D - NSE India Raw Validation
- manifest_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_raw_acquisition_manifest_v2_17c.csv
- source_actions_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_raw_acquisition_source_actions_v2_17c.csv
- raw_dir_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- canonical_rows_expected: PASS (critical) — canonical_rows=38287
- manifest_rows_present: PASS (critical) — manifest_rows=17
- file_profiles_generated: PASS (critical) — file_profiles=17 manifest_rows=17
- valid_raw_csv_files_present: PASS (critical) — valid_raw_csv=14
- plain_csv_sources_present: PASS (critical) — plain_csv=12
- mii_gzip_sources_present: PASS (critical) — gzip_csv=2
- equity_segment_valid_csv: PASS (critical) — equity_profile={'artifact_id': 'bb8abac71c641905', 'source_id': 'nse_securities_available_equity_segment', 'artifact_type': 'raw_source_file', 'local_path': 'outputs\\full_universe_source_acquisition\\nse_raw_acquisition_v2_17c\\nse_securities_available_equity_segment__raw_source_file.csv', 'exists': True, 'download_status': 'downloaded', 'http_status': '200', 'content_type': 'text/csv', 'extension': '.csv', 'manifest_bytes': 169183, 'actual_bytes': 169183, 'manifest_sha256': 'd0147081b02000ecdea8398e42304d1f2051ef0ef62f14f1e004b456654676f9', 'actual_sha256': 'd0147081b02000ecdea8398e42304d1f2051ef0ef62f14f1e004b456654676f9', 'sha256_matches': True, 'gzip_magic_manifest': False, 'gzip_magic_actual': False, 'gzip_decompress_attempted': False, 'gzip_decompress_ok': False, 'raw_kind': 'csv', 'csv_parse_attempted': True, 'csv_parse_ok': True, 'csv_delimiter': ',', 'csv_row_count': 2397, 'csv_column_count': 8, 'columns_preview': 'SYMBOL | NAME OF COMPANY | SERIES | DATE OF LISTING | PAID UP VALUE | MARKET LOT | ISIN NUMBER | FACE VALUE', 'validation_bucket': 'valid_raw_csv', 'issues': ''}
- mii_sources_valid_or_reviewable: PASS (critical) — mii_valid=2
- critical_sources_valid: PASS (critical) — valid_critical_sources=['nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive', 'nse_all_reports_cm_mii_security_file_nse_listed', 'nse_debt_instruments', 'nse_etfs', 'nse_invits', 'nse_reits', 'nse_securities_available_equity_segment', 'nse_securities_available_sme']
- exclusion_reference_sources_valid: PASS (critical) — exclusion_valid=['nse_close_ended_mf', 'nse_debt_instruments', 'nse_etfs', 'nse_idrs', 'nse_invits', 'nse_preference_shares', 'nse_reits', 'nse_warrants']
- schema_profiles_created: PASS (critical) — schema_profiles=14
- sha256_all_local_files_match_manifest: PASS (critical) — all existing files match manifest sha256
- landing_pages_available: PASS (critical) — landing_profiles=3
- duplicate_sha_review: PASS (warning) — duplicate_sha_groups=1
- full_source_still_blocked: PASS (critical) — 38287 < 50000
- network_not_used: PASS (critical) — network_download_performed=False
- endpoint_calls_not_performed: PASS (critical) — endpoint_calls_performed=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- raw_validation_performed: PASS (critical) — raw_validation_performed=True
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- security_rows_not_extracted: PASS (critical) — security_rows_extracted=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17C report read: true
- Manifest read: true
- Raw files read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Raw validation performed: true
- Format validation performed: true
- Gzip validation performed: true
- CSV header validation performed: true
- Candidate extraction performed: false
- Security rows extracted: false
- Canonical comparison performed: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Net-new filtering applied to canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17D validates the NSE India raw acquisition artifacts and prepares the route for candidate extraction dry run in v2.17E.

## Recommended next phase

`v2.17E - NSE India Candidate Extraction Dry Run`
