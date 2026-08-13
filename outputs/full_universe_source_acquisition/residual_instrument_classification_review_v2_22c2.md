# v2.22C2 — Residual Instrument Classification Review

Status: **RESIDUAL_INSTRUMENT_CLASSIFICATION_REVIEW_COMPLETED_FULL_DATASET_POLICY_OVERLAY_READY_FOR_SCORING_DRY_RUN_DECISION**

Phase type: **residual-instrument-classification-review**

Generated at UTC: `2026-08-13T11:01:21.646807+00:00`

## Executive summary

v2.22C2 classifies residual instrument flags using the full 43,089-row operational dataset, not the capped/sample CSV.

No dataset rows are deleted. No dataset is modified. No scoring is executed.

## Current dataset

`outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv`

Rows: `43089`  
SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`

## Classification result

- Full dataset no-flag rows: `33232`
- Non-blocking equity-context rows: `265`
- Non-blocking in-scope rows: `1`
- Residual review required rows: `9591`
- Expected residual rows from v2.22C_REVIEW: `9591`
- Classification overlay rows: `9857`
- Excluded from common-equity scoring rows: `9591`
- Unknown total rows: `0`

Approved for scoring dry run decision: `True`

Approved for scoring execution: `False`

## Checks

- review_status_expected: PASS (critical) — PRE_SCORING_QUALITY_FINDINGS_REVIEW_COMPLETED_RESIDUAL_REVIEW_REQUIRED_SCORING_DRY_RUN_DEFERRED
- review_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- previous_rows_expected: PASS (critical) — previous_rows=42708
- previous_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- full_dataset_residual_rows_expected: PASS (critical) — residual_rows=9591;expected=9591
- full_dataset_no_flag_rows_expected: PASS (critical) — no_flag_rows=33232;expected=33232
- non_blocking_equity_rows_expected: PASS (critical) — non_blocking_equity=265;expected=265
- non_blocking_scope_rows_expected: PASS (critical) — non_blocking_scope=1;expected=1
- classification_overlay_rows_expected: PASS (critical) — overlay_rows=9857
- excluded_rows_documented: PASS (critical) — excluded_rows=9591
- unknown_rows_documented: PASS (warning) — unknown_total=0;missing_metadata=0;manual=0
- within_quality_floor: PASS (critical) — current_rows=43089;floor=42000
- within_quality_ceiling: PASS (critical) — current_rows=43089;ceiling=45000
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- scoring_not_executed: PASS (critical) — scoring_executed=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707

## Recommended next phase

Primary: `v2.22D - Scoring Dry Run / No Promotion`

Secondary: `v2.22D - Scoring Dry Run / No Promotion`
