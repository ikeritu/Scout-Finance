# v2.23C — Scoring Calibration Data Design

Status: **SCORING_CALIBRATION_DATA_DESIGN_COMPLETED_NO_LABELS_NO_SCORING_NO_PROMOTION**

Phase type: **scoring-calibration-data-design**

Generated at UTC: `2026-08-13T14:33:08.333360+00:00`

## Decision

Calibration data decision: **CALIBRATION_DATA_DESIGN_CREATED_NO_LABELS_NO_SCORING**

This phase designs the manual calibration data structure only. It does not create manual labels, execute new scoring, backfill metadata, promote scores, or modify the canonical dataset.

## Inputs

Current dataset:

`outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv`

Rows: `43089`  
SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`

Dry-run scoring output:

`outputs\full_universe_source_acquisition\scoring_dry_run_no_promotion_scores_v2_22d.csv`

Rows: `33498`  
SHA256: `a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1`

## Design outputs

- Label schema rows: `6`
- Sample plan rows: `16`
- Strata profile rows: `16`
- Acceptance criteria rows: `5`
- Target manual review rows: `350`

## Label schema

- `manual_label` — good_candidate|borderline_candidate|bad_candidate|not_common_equity|insufficient_metadata
- `manual_data_quality_label` — high|medium|low|unusable
- `manual_attractiveness_label` — high|medium|low|unknown
- `instrument_validity_label` — common_equity|fund_like|fixed_income|preferred|warrant_right_certificate|unknown
- `reviewer_notes` — free_text
- `review_status` — pending|reviewed|needs_second_review|rejected_from_calibration

## Guardrails

- Manual labels created: `False`
- Production scoring authorized: `False`
- New scoring executed: `False`
- Metadata backfill executed: `False`
- Canonical dataset modified: `False`
- Dry-run score output modified: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

- metadata_plan_status_expected: PASS (critical) — METADATA_COVERAGE_IMPROVEMENT_PLAN_COMPLETED_NO_DATASET_MODIFICATION
- metadata_plan_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- scoring_rows_expected: PASS (critical) — scoring_rows=33498
- scoring_sha_expected: PASS (critical) — a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- score_range_expected: PASS (critical) — min=44.7;max=87.2
- label_schema_created: PASS (critical) — label_schema_rows=6
- sample_plan_created: PASS (critical) — sample_plan_rows=16
- strata_profile_created: PASS (critical) — strata_rows=16
- acceptance_criteria_created: PASS (critical) — acceptance_criteria_rows=5
- manual_labels_not_created: PASS (critical) — manual_labels_created=False
- production_scoring_not_authorized: PASS (critical) — production_scoring_authorized=False
- new_scoring_not_executed: PASS (critical) — new_scoring_executed=False
- metadata_backfill_not_executed: PASS (critical) — metadata_backfill_executed=False
- canonical_dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- dry_run_score_output_not_modified: PASS (critical) — scoring_sha_after=a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.23D - Scoring Formula Redesign Dry Run`

Secondary: `v2.23E - Calibration Review / Freeze Decision`
