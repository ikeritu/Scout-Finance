# v2.22C_REVIEW — Pre-Scoring Quality Findings Review

Status: **PRE_SCORING_QUALITY_FINDINGS_REVIEW_COMPLETED_RESIDUAL_REVIEW_REQUIRED_SCORING_DRY_RUN_DEFERRED**

Phase type: **pre-scoring-quality-findings-review**

Generated at UTC: `2026-08-13T10:41:15.090308+00:00`

## Executive summary

v2.22C_REVIEW classifies the quality findings from v2.22C.

No scoring is executed.

## Key results

- Current dataset rows: `43089`
- Current dataset SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`
- New rows vs previous base: `381`
- Singapore new rows: `358`
- Colombia new rows: `23`
- Full-row duplicate extra rows: `0`
- Primary-key duplicate finding classification: weak-key false positive
- Original instrument flags classification: broad substring scan overflagged
- Refined residual instrument review required: `9591`

## Scoring status

Approved for scoring dry run decision: `True`

Approved for scoring execution: `False`

Scoring executed: `False`

## Checks

- audit_status_expected: PASS (critical) — PRE_SCORING_DATA_QUALITY_AUDIT_COMPLETED_REVIEW_FINDINGS_DOCUMENTED_SCORING_DRY_RUN_DEFERRED
- audit_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- previous_rows_expected: PASS (critical) — previous_rows=42708
- previous_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- headers_consistent_current_previous: PASS (critical) — current_columns=33;previous_columns=33
- headers_consistent_current_rollback: PASS (critical) — current_columns=33;rollback_columns=33
- new_rows_total_expected: PASS (critical) — new_rows=381
- new_rows_singapore_expected: PASS (critical) — singapore=358
- new_rows_colombia_expected: PASS (critical) — colombia=23
- full_row_duplicates_zero: PASS (critical) — extra_rows=0;groups=0
- primary_key_duplicates_classified_non_blocking: PASS (critical) — weak_key_false_positive=True
- original_instrument_flags_classified_as_overbroad: PASS (critical) — broad_substring_scan_overflagged=True
- refined_instrument_residual_documented: PASS (warning) — residual_review_required=9591
- within_quality_floor: PASS (critical) — current_rows=43089;floor=42000
- within_quality_ceiling: PASS (critical) — current_rows=43089;ceiling=45000
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- scoring_not_executed: PASS (critical) — scoring_executed=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False

## Recommended next phase

Primary: `v2.22C2 - Residual Instrument Classification Review`

Secondary: `v2.22D - Scoring Dry Run / No Promotion`
