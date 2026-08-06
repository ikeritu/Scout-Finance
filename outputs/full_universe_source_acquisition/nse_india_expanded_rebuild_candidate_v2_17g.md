# v2.17G - NSE India Expanded Rebuild Candidate

Status: **NSE_INDIA_EXPANDED_REBUILD_CANDIDATE_COMPLETED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED**

Phase type: **expanded-rebuild-candidate-only**

Generated at UTC: `2026-08-06T14:09:41.891669+00:00`

## Executive summary

NSE India expanded rebuild candidate created.

This phase writes a candidate expanded universe dataset by appending v2.17F potential net-new rows to the active canonical dataset schema. It does not replace or modify the active canonical dataset.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Full source threshold: `50000`
- Rows needed before NSE candidate: `11713`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Rebuild candidate summary

- Potential net-new rows raw: `4435`
- Potential net-new rows unique before promotion policy: `4435`
- Deferred by safe promotion policy: `2422`
- Potential net-new rows promoted: `2013`
- Rows added to candidate dataset: `2013`
- Expanded candidate rows: `40300`
- Rows needed after candidate dataset: `9700`
- Completion after candidate: `80.6%`
- Would reach full source threshold: `False`
- Canonical SHA before: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Canonical SHA after: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Expanded candidate SHA: `a6d93e89c2c26ae49bde7aa923ec42c385a4885602bcafa7a0bdfc50f2801ac6`
- Critical failed checks: `0`

## Artifacts

- Expanded candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv`
- Delta rows: `outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_delta_rows_v2_17g.csv`
- Promotions: `outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_promotions_v2_17g.csv`
- Schema mapping: `outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_schema_mapping_v2_17g.csv`
- JSON report: `outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_v2_17g.json`

## Checks

- v2_17f_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_candidate_validation_against_canonical_dry_run_v2_17f.json
- v2_17f_status_expected: PASS (critical) — NSE_INDIA_CANDIDATE_VALIDATION_AGAINST_CANONICAL_DRY_RUN_COMPLETED_NET_NEW_FOUND_REBUILD_CANDIDATE_READY_FULL_SOURCE_STILL_BLOCKED
- v2_17f_recommended_g: PASS (critical) — v2.17G - NSE India Expanded Rebuild Candidate
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- canonical_rows_expected: PASS (critical) — canonical_rows=38287
- canonical_header_present: PASS (critical) — columns=33
- potential_net_new_rows_present: PASS (critical) — raw_potential=4435
- safe_promotable_rows_present: PASS (critical) — safe_promotable_rows=2013
- promotion_policy_deferred_rows_recorded: PASS (warning) — deferred_rows=2422
- rows_added_matches_unique_potential: PASS (critical) — rows_added=2013 unique_potential=2013
- expanded_rows_projected: PASS (critical) — projected=40300
- expanded_candidate_written: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- delta_rows_written: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_delta_rows_v2_17g.csv
- promotions_written: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_promotions_v2_17g.csv
- schema_mapping_written: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_schema_mapping_v2_17g.csv
- expanded_dataset_schema_matches_canonical: PASS (critical) — same header used for canonical + appended rows
- symbol_column_mapped: PASS (critical) — symbol_col=symbol
- name_column_mapped: PASS (critical) — name_col=company_name
- canonical_sha_unchanged: PASS (critical) — canonical sha unchanged
- full_source_still_blocked: PASS (critical) — 40300 < 50000
- network_not_used: PASS (critical) — network_download_performed=False
- canonical_dataset_read: PASS (critical) — canonical_dataset_read=True
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- expanded_candidate_dataset_written: PASS (critical) — new_expanded_candidate_dataset_written=True
- expanded_universe_not_rebuilt_as_canonical: PASS (critical) — expanded_universe_rebuilt_as_canonical=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17F report read: true
- Potential net-new rows read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- New expanded candidate dataset written: true
- Delta rows written: true
- Promotions written: true
- Schema mapping written: true
- Safe promotion policy applied: true
- Deferred review rows not promoted: `2422`
- Net-new rows applied to candidate dataset: true
- Net-new rows applied to canonical: false
- Expanded universe rebuilt as canonical: false
- Active canonical replaced: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17G creates the NSE India expanded rebuild candidate and prepares validation in v2.17H.

## Recommended next phase

`v2.17H - NSE India Expanded Validation`
