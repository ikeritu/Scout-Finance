# v2.22C — Pre-Scoring Data Quality Audit

Status: **PRE_SCORING_DATA_QUALITY_AUDIT_COMPLETED_REVIEW_FINDINGS_DOCUMENTED_SCORING_DRY_RUN_DEFERRED**

Phase type: **pre-scoring-data-quality-audit**

Generated at UTC: `2026-08-13T10:33:06.193510+00:00`

## Executive summary

v2.22C audits the current operational universe through the hardened pointer created in v2.22B.

Current dataset:

`outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv`

Rows: `43089`  
SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`

No scoring is executed. No OpenAI call is made. No broker call is made. full59k remains deprecated/deferred.

## Quality audit result

Audit decision: `AUDIT_COMPLETED_REVIEW_FINDINGS_DOCUMENTED`

Approved for scoring dry run: `False`

Blocking quality findings: `1`

## Key findings

- New rows vs previous operational base: `381` expected `381`
- Full-row duplicate groups: `0`
- Full-row duplicate extra rows: `0`
- Primary-key duplicate groups: `9`
- Primary-key duplicate extra rows: `34082`
- Instrument suitability flagged rows: `9957`
- Bad-width rows current dataset: `0`
- Current column count: `33`
- Remaining capacity vs 45k ceiling: `1911`

## Checks

- pointer_hardening_status_expected: PASS (critical) — OPERATIONAL_POINTER_CONVENTION_HARDENING_COMPLETED_CURRENT_OPERATIONAL_POINTER_CREATED_SCORING_DEFERRED
- pointer_json_exists: PASS (critical) — outputs\full_universe_source_acquisition\current_operational_universe_pointer.json
- pointer_current_dataset_path_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- pointer_declared_rows_expected: PASS (critical) — pointer_rows=43089
- pointer_declared_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- current_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- previous_operational_rows_expected: PASS (critical) — previous_rows=42708
- previous_operational_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- headers_consistent_current_previous: PASS (critical) — current_columns=33;previous_columns=33
- headers_consistent_current_rollback: PASS (critical) — current_columns=33;rollback_columns=33
- current_bad_width_rows_zero: PASS (critical) — bad_width_rows=0
- previous_bad_width_rows_zero: PASS (critical) — bad_width_rows=0
- rollback_bad_width_rows_zero: PASS (critical) — bad_width_rows=0
- within_quality_floor: PASS (critical) — current_rows=43089;floor=42000
- within_quality_ceiling: PASS (critical) — current_rows=43089;ceiling=45000
- remaining_capacity_non_negative: PASS (critical) — remaining_capacity=1911
- new_rows_vs_previous_expected: PASS (warning) — new_rows=381;expected=381
- full_row_duplicates_zero: PASS (warning) — duplicate_full_row_extra_rows=0;groups=0
- primary_key_duplicates_documented: PASS (warning) — duplicate_primary_key_extra_rows=34082;groups=9
- instrument_suitability_flags_documented: PASS (warning) — instrument_flag_total=9957;sample_rows=1000
- identifier_columns_resolved: PASS (critical) — resolved_columns={'isin': 'isin', 'symbol': 'symbol', 'name': 'company_name', 'country': 'country', 'exchange': 'exchange', 'mic': 'mic', 'currency': 'currency', 'source_provider': 'source_provider', 'asset_type': 'asset_type'}
- country_or_exchange_dimension_resolved: PASS (critical) — country=country;exchange=exchange;mic=mic
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- scoring_not_executed: PASS (critical) — scoring_executed=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False

## Recommended next phase

Primary: `v2.22C_REVIEW - Pre-Scoring Quality Findings Review`

Secondary: `v2.22D - Scoring Dry Run / No Promotion`
