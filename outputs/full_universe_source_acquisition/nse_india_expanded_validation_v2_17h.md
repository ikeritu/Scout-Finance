# v2.17H - NSE India Expanded Validation

Status: **NSE_INDIA_EXPANDED_VALIDATION_COMPLETED_CANDIDATE_VALID_CLOSURE_READY_FULL_SOURCE_STILL_BLOCKED**

Phase type: **expanded-candidate-validation-only**

Generated at UTC: `2026-08-06T14:33:06.576452+00:00`

## Executive summary

NSE India expanded candidate validation completed.

This phase validates the v2.17G expanded candidate dataset. It confirms schema consistency, append integrity, safe promotion policy compliance, canonical SHA stability and full-source gate status. It does not modify or replace the active canonical dataset.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Expanded candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv`
- Expanded candidate rows: `40300`
- Delta rows: `2013`
- Full source threshold: `50000`
- Rows needed after candidate: `9700`
- Completion after candidate: `80.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Expanded validation summary

- Canonical rows: `38287`
- Delta rows: `2013`
- Promotions: `2013`
- Expanded candidate rows: `40300`
- Canonical prefix matches: `38287/38287`
- Delta tail matches: `2013/2013`
- Promotion policy failures: `0`
- Duplicate delta rows: `0`
- Duplicate promotion candidate IDs: `0`
- Source counts: `{'nse_securities_available_equity_segment': 2013}`
- Series counts: `{'EQ': 2013}`
- Confidence counts: `{'high': 2013}`
- Policy counts: `{'include_safe_high_confidence_equity_segment_eq_only_in_candidate_dataset': 2013}`
- Canonical SHA before: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Canonical SHA after: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Expanded candidate SHA: `a6d93e89c2c26ae49bde7aa923ec42c385a4885602bcafa7a0bdfc50f2801ac6`
- Critical failed checks: `0`

## Checks

- v2_17g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_v2_17g.json
- v2_17g_status_expected: PASS (critical) — NSE_INDIA_EXPANDED_REBUILD_CANDIDATE_COMPLETED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED
- v2_17g_recommended_h: PASS (critical) — v2.17H - NSE India Expanded Validation
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- expanded_candidate_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- delta_rows_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_delta_rows_v2_17g.csv
- promotions_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_promotions_v2_17g.csv
- schema_mapping_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_expanded_rebuild_candidate_schema_mapping_v2_17g.csv
- canonical_rows_expected: PASS (critical) — canonical_rows=38287
- headers_match_canonical_expanded: PASS (critical) — canonical_cols=33 expanded_cols=33
- headers_match_canonical_delta: PASS (critical) — canonical_cols=33 delta_cols=33
- expanded_rows_equal_canonical_plus_delta: PASS (critical) — expanded=40300 canonical=38287 delta=2013
- delta_rows_equal_promotions: PASS (critical) — delta=2013 promotions=2013
- canonical_prefix_fully_matches: PASS (critical) — matched=38287/38287
- delta_tail_fully_matches: PASS (critical) — matched=2013/2013
- canonical_sha_unchanged: PASS (critical) — canonical sha unchanged
- promotion_policy_qa_all_passed: PASS (critical) — failures=0
- safe_source_only: PASS (critical) — source_counts={'nse_securities_available_equity_segment': 2013}
- eq_series_only: PASS (critical) — series_counts={'EQ': 2013}
- high_confidence_only: PASS (critical) — confidence_counts={'high': 2013}
- safe_policy_only: PASS (critical) — policy_counts={'include_safe_high_confidence_equity_segment_eq_only_in_candidate_dataset': 2013}
- potential_net_new_high_only: PASS (critical) — net_new_bucket_counts={'potential_net_new_high': 2013}
- no_duplicate_delta_rows: PASS (critical) — duplicate_delta_rows=0
- no_duplicate_promotion_candidate_ids: PASS (critical) — duplicate_promotion_candidate_ids=0
- expanded_candidate_has_growth: PASS (critical) — delta_rows=2013
- full_source_still_blocked: PASS (critical) — 40300 < 50000
- network_not_used: PASS (critical) — network_download_performed=False
- canonical_dataset_read: PASS (critical) — canonical_dataset_read=True
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- expanded_candidate_validated: PASS (critical) — expanded_candidate_validated=True
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17G report read: true
- Canonical dataset read: true
- Expanded candidate dataset read: true
- Delta rows read: true
- Promotions read: true
- Schema mapping read: true
- Expanded candidate validated: true
- Promotion policy validated: true
- Safe promotion policy enforced: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Active canonical replaced: false
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

v2.17H validates the NSE India expanded rebuild candidate and prepares the NSE India closure report.

## Recommended next phase

`v2.17I - NSE India Closure Report`
