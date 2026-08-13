# v2.23D — Scoring Formula Redesign Dry Run

Status: **SCORING_FORMULA_REDESIGN_DRY_RUN_COMPLETED_NO_PROMOTION_NO_CANONICAL_CHANGE**

Phase type: **scoring-formula-redesign-dry-run**

Generated at UTC: `2026-08-13T15:01:54.964767+00:00`

## Decision

Formula decision: **REDESIGNED_SCORING_DRY_RUN_CREATED_NO_PROMOTION**

This phase creates a redesigned deterministic score as a dry-run output only.

It does **not** authorize production scoring, promote scores, modify the canonical dataset, use OpenAI, call broker APIs, or launch full59k.

## Inputs

Current dataset:

`outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv`

Rows: `43089`  
SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`

Legacy dry-run score:

`outputs\full_universe_source_acquisition\scoring_dry_run_no_promotion_scores_v2_22d.csv`

Rows: `33498`  
SHA256: `a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1`

## Redesigned dry-run output

`outputs\full_universe_source_acquisition\scoring_formula_redesign_dry_run_scores_v2_23d.csv`

Rows: `33498`  
SHA256: `096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb`

## Score summary

- Legacy mean: `58.2468`
- Redesigned min: `38.5`
- Redesigned p25: `44.5`
- Redesigned median: `60.2`
- Redesigned p75: `66.6`
- Redesigned max: `98.5`
- Redesigned mean: `60.6008`
- Mean delta vs v2.22D: `2.354`

## Components

- `data_quality_score` — weight `0.7` — included `True`
- `scope_confidence_score` — weight `0.2` — included `True`
- `provider_quality_score` — weight `0.1` — included `True`
- `attractiveness_score` — weight `0.0` — included `False`

## Distribution

- `A_85_100`: 2332 rows (6.9616%)
- `B_70_84`: 5158 rows (15.3979%)
- `C_55_69`: 14218 rows (42.4443%)
- `D_40_54`: 10523 rows (31.4138%)
- `E_0_39`: 1267 rows (3.7823%)

## Guardrails

- Production scoring authorized: `False`
- Scoring promoted: `False`
- Canonical dataset modified: `False`
- Legacy score output modified: `False`
- Attractiveness score invented: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

- calibration_data_design_status_expected: PASS (critical) — SCORING_CALIBRATION_DATA_DESIGN_COMPLETED_NO_LABELS_NO_SCORING_NO_PROMOTION
- calibration_data_design_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- metadata_plan_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- legacy_scoring_rows_expected: PASS (critical) — legacy_scoring_rows=33498
- legacy_scoring_sha_expected: PASS (critical) — a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- redesigned_output_rows_expected: PASS (critical) — redesigned_output_rows=33498
- redesigned_score_range_valid: PASS (critical) — min=38.5;max=98.5
- component_weights_sum_expected: PASS (critical) — weight_sum=1.0
- data_quality_score_separated: PASS (critical) — data_quality_score column created
- attractiveness_score_not_invented: PASS (critical) — attractiveness_score_available=False for all rows
- acceptance_review_all_passed: PASS (critical) — acceptance_passed=5
- production_scoring_not_authorized: PASS (critical) — production_scoring_authorized=False
- scoring_promoted_false: PASS (critical) — scoring_promoted=False
- canonical_dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- legacy_score_output_not_modified: PASS (critical) — legacy_scoring_sha_after=a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.23E - Calibration Review / Freeze Decision`

Secondary: `v2.23F - Calibration Closure Report`
