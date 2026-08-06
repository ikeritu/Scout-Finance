# v2.17F - NSE India Candidate Validation Against Canonical Dry Run

Status: **NSE_INDIA_CANDIDATE_VALIDATION_AGAINST_CANONICAL_DRY_RUN_COMPLETED_NET_NEW_FOUND_REBUILD_CANDIDATE_READY_FULL_SOURCE_STILL_BLOCKED**

Phase type: **candidate-validation-against-canonical-dry-run-only**

Generated at UTC: `2026-08-06T13:40:37.600388+00:00`

## Executive summary

NSE India candidate validation against canonical completed as a dry run.

This phase reads the active canonical dataset and classifies NSE candidates from v2.17E as existing, possible existing, invalid, or potential net-new. It does not modify the canonical dataset, does not write any expanded rebuild candidate and does not apply net-new rows to the canonical source.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completion: `76.57%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Validation summary

- Canonical rows read: `38287`
- Candidate rows read: `11802`
- Classified candidates: `11802`
- Existing candidates: `0`
- Possible existing candidates: `7367`
- Potential net-new candidates: `4435`
- Potential net-new high: `2055`
- Potential net-new review: `2380`
- Internal duplicate groups: `3970`
- Internal duplicate rows marked: `7320`
- Invalid candidates: `0`
- Existing match rows: `47`
- Projected rows if all potential net-new promoted: `42722`
- Would reach full source threshold if all promoted: `False`
- Critical failed checks: `0`

## Source diagnostics

- `nse_all_reports_cm_mii_security_file_nse_listed` total=`9738` existing=`0` possible=`7358` net_new=`2380` invalid=`0`
- `nse_securities_available_equity_segment` total=`2064` existing=`0` possible=`9` net_new=`2055` invalid=`0`

## Checks

- v2_17e_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_candidate_extraction_dry_run_v2_17e.json
- v2_17e_status_expected: PASS (critical) — NSE_INDIA_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_CANONICAL_COMPARISON_STILL_BLOCKED
- v2_17e_recommended_f: PASS (critical) — v2.17F - NSE India Candidate Validation Against Canonical Dry Run
- v2_17e_candidates_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_candidate_extraction_candidates_v2_17e.csv
- v2_17e_exclusions_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_candidate_extraction_exclusions_v2_17e.csv
- v2_17e_source_diagnostics_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_candidate_extraction_source_diagnostics_v2_17e.csv
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- canonical_rows_expected: PASS (critical) — canonical_rows=38287
- canonical_symbol_index_available: PASS (critical) — symbol_base_keys=1424
- candidates_present: PASS (critical) — candidates=11802
- classified_all_candidates: PASS (critical) — classified=11802 candidates=11802
- classification_partition_ok: PASS (critical) — partition existing + possible + potential + invalid
- potential_net_new_or_existing_present: PASS (critical) — net_new=4435 existing=0 possible=7367
- existing_match_rows_consistent: PASS (warning) — existing_match_rows=47 existing_rows=0
- source_diagnostics_created: PASS (critical) — source_diagnostics=2
- full_source_still_blocked: PASS (critical) — 38287 < 50000
- network_not_used: PASS (critical) — network_download_performed=False
- canonical_dataset_read: PASS (critical) — canonical_dataset_read=True
- canonical_comparison_performed: PASS (critical) — canonical_comparison_performed=True
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- net_new_not_applied_to_canonical: PASS (critical) — net_new_filtering_applied_to_canonical=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- expanded_universe_not_rebuilt: PASS (critical) — expanded_universe_rebuilt_as_canonical=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17E report read: true
- Candidate rows read: true
- Exclusion rows read: true
- Canonical dataset read: true
- Canonical comparison performed: true
- Existing match classification performed: true
- Potential net-new classification performed: true
- Internal duplicate series guard performed: true
- Net-new filtering applied to candidates: true
- Net-new filtering applied to canonical: false
- Canonical dataset modified: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17F validates NSE India candidates against the canonical dataset in dry-run mode and prepares the route for rebuild candidate generation only if potential net-new rows are available.

## Recommended next phase

`v2.17G - NSE India Expanded Rebuild Candidate`
