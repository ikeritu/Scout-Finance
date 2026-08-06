# v2.17C - NSE India Raw Acquisition

Status: **NSE_INDIA_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED**

Phase type: **provider-raw-acquisition-only**

Generated at UTC: `2026-08-06T09:16:32.799137+00:00`

## Executive summary

NSE India raw acquisition completed.

This phase downloads landing pages and raw NSE source files only. It does not parse security rows, does not extract candidates, does not compare against the canonical dataset and does not rebuild or modify any expanded universe dataset.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completion: `76.57%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Raw acquisition summary

- Raw directory: `outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c`
- Manifest rows: `17`
- Downloaded artifacts: `16`
- Raw file artifacts: `14`
- Direct static downloads: `12`
- MII security downloads: `2`
- Critical failed checks: `0`

## Manifest

- `nse_home_session_seed` `landing_html` status=`downloaded_error_payload` bytes=`370` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_home_session_seed__landing_html.html`
- `nse_all_reports_landing` `landing_html` status=`downloaded` bytes=`588764` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_all_reports_landing__landing_html.html`
- `nse_securities_available_for_trading_landing` `landing_html` status=`downloaded` bytes=`1565158` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_securities_available_for_trading_landing__landing_html.html`
- `nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive` `mii_security_file_candidate` status=`downloaded` bytes=`1213427` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive__mii_security_file_candidate.csv.gz`
- `nse_all_reports_cm_mii_security_file_nse_listed` `mii_security_file_candidate` status=`downloaded` bytes=`1213427` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_all_reports_cm_mii_security_file_nse_listed__mii_security_file_candidate.csv.gz`
- `nse_securities_available_equity_segment` `raw_source_file` status=`downloaded` bytes=`169183` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_securities_available_equity_segment__raw_source_file.csv`
- `nse_securities_available_sme` `raw_source_file` status=`downloaded` bytes=`38817` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_securities_available_sme__raw_source_file.csv`
- `nse_idrs` `raw_source_file` status=`downloaded` bytes=`256` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_idrs__raw_source_file.csv`
- `nse_preference_shares` `raw_source_file` status=`downloaded` bytes=`609` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_preference_shares__raw_source_file.csv`
- `nse_warrants` `raw_source_file` status=`downloaded` bytes=`135` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_warrants__raw_source_file.csv`
- `nse_close_ended_mf` `raw_source_file` status=`downloaded` bytes=`13055` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_close_ended_mf__raw_source_file.csv`
- `nse_etfs` `raw_source_file` status=`downloaded` bytes=`27815` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_etfs__raw_source_file.csv`
- `nse_changes_company_names` `raw_source_file` status=`downloaded` bytes=`239693` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_changes_company_names__raw_source_file.csv`
- `nse_changes_symbols` `raw_source_file` status=`downloaded` bytes=`68434` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_changes_symbols__raw_source_file.csv`
- `nse_invits` `raw_source_file` status=`downloaded` bytes=`613` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_invits__raw_source_file.csv`
- `nse_reits` `raw_source_file` status=`downloaded` bytes=`482` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_reits__raw_source_file.csv`
- `nse_debt_instruments` `raw_source_file` status=`downloaded` bytes=`554225` path=`outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c\nse_debt_instruments__raw_source_file.csv`

## Source actions

- `nse_all_reports_landing` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_securities_available_for_trading_landing` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_all_reports_cm_mii_security_file_nse_listed` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_securities_available_equity_segment` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_securities_available_sme` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_idrs` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_preference_shares` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_warrants` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_close_ended_mf` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_etfs` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_changes_company_names` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_changes_symbols` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_invits` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_reits` attempted=`True` status=`downloaded` artifacts=`1`
- `nse_debt_instruments` attempted=`True` status=`downloaded` artifacts=`1`

## Checks

- v2_17b_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_acquisition_plan_v2_17b.json
- v2_17b_status_expected: PASS (critical) — NSE_INDIA_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_FULL_SOURCE_STILL_BLOCKED
- v2_17b_recommended_c: PASS (critical) — v2.17C - NSE India Raw Acquisition
- source_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_source_plan_v2_17b.csv
- action_plan_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_acquisition_actions_v2_17b.csv
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- canonical_rows_expected: PASS (critical) — canonical_rows=38287
- raw_dir_created: PASS (critical) — outputs\full_universe_source_acquisition\nse_raw_acquisition_v2_17c
- nse_landing_downloaded: PASS (critical) — all-reports landing
- securities_landing_downloaded: PASS (critical) — securities available landing
- direct_static_downloads_present: PASS (critical) — direct_static_downloads=12
- equity_segment_downloaded: PASS (critical) — EQUITY_L.csv
- sme_downloaded_or_attempted: PASS (warning) — SME_EQUITY_L.csv attempted
- mii_attempted: PASS (warning) — MII sources attempted
- mii_downloaded_if_discoverable: PASS (warning) — mii_downloads=2
- raw_file_artifacts_present: PASS (critical) — raw_file_artifacts=14
- full_source_still_blocked: PASS (critical) — 38287 < 50000
- network_used_as_allowed: PASS (critical) — network_download_performed=True
- raw_acquisition_performed: PASS (critical) — raw_acquisition_performed=True
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: true
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17B report read: true
- Source plan read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Raw acquisition performed: true
- Raw files downloaded: `True`
- Landing pages downloaded: true
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

v2.17C captures raw NSE India source artifacts and prepares them for v2.17D validation.

## Recommended next phase

`v2.17D - NSE India Raw Validation`
