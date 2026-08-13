# v2.23E — Calibration Review / Freeze Decision

Status: **CALIBRATION_REVIEW_FREEZE_DECISION_COMPLETED_REDESIGNED_DRY_RUN_FROZEN_NOT_PROMOTED**

Phase type: **calibration-review-freeze-decision**

Generated at UTC: `2026-08-13T15:37:21.862676+00:00`

## Decision

Freeze decision: **FREEZE_REDESIGNED_DRY_RUN_AS_NON_PROMOTED_REFERENCE**

The redesigned v2.23D dry-run scoring is frozen as a non-promoted reference.

It is useful for review, but it is **not** production scoring.

## Reasons

- `FREEZE_001` — critical — Redesigned scoring was explicitly created as dry-run only.
- `FREEZE_002` — critical — Manual labels do not exist yet.
- `FREEZE_003` — critical — Attractiveness score is unavailable and was correctly not invented.
- `FREEZE_004` — high — Metadata gaps remain blocking for production scoring readiness.
- `FREEZE_005` — critical — No separate authorization exists for OpenAI, broker APIs, full59k or external enrichment.

## Promotion blockers

- `BLOCKER_001` — blocking `True` — manual_calibration_labels_missing
- `BLOCKER_002` — blocking `True` — attractiveness_score_unavailable
- `BLOCKER_003` — blocking `True` — metadata_gap_remediation_not_executed
- `BLOCKER_004` — blocking `True` — no_production_scoring_gate_approved
- `BLOCKER_005` — blocking `False` — external_enrichment_not_authorized

## Score reference

Redesigned dry-run output:

`outputs\full_universe_source_acquisition\scoring_formula_redesign_dry_run_scores_v2_23d.csv`

Rows: `33498`  
SHA256: `096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb`

- Redesigned min: `38.5`
- Redesigned p25: `44.5`
- Redesigned median: `60.2`
- Redesigned p75: `66.6`
- Redesigned max: `98.5`
- Redesigned mean: `60.6008`

## Guardrails

- Promotion approved: `False`
- Production scoring authorized: `False`
- Scoring promoted: `False`
- Active pointer modified: `False`
- Canonical dataset modified: `False`
- Redesigned score output modified: `False`
- Legacy score output modified: `False`
- Manual labels created: `False`
- Attractiveness score invented: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

- formula_status_expected: PASS (critical) — SCORING_FORMULA_REDESIGN_DRY_RUN_COMPLETED_NO_PROMOTION_NO_CANONICAL_CHANGE
- formula_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- calibration_data_design_status_expected: PASS (critical) — SCORING_CALIBRATION_DATA_DESIGN_COMPLETED_NO_LABELS_NO_SCORING_NO_PROMOTION
- metadata_plan_status_expected: PASS (critical) — METADATA_COVERAGE_IMPROVEMENT_PLAN_COMPLETED_NO_DATASET_MODIFICATION
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- legacy_scoring_rows_expected: PASS (critical) — legacy_rows=33498
- legacy_scoring_sha_expected: PASS (critical) — a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- redesigned_scoring_rows_expected: PASS (critical) — redesigned_rows=33498
- redesigned_scoring_sha_expected: PASS (critical) — 096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb
- distribution_rows_expected: PASS (critical) — distribution_rows=5
- component_weight_rows_expected: PASS (critical) — component_weight_rows=4
- acceptance_review_rows_expected: PASS (critical) — acceptance_review_rows=5
- manual_labels_absent: PASS (critical) — manual_labels_created=False
- attractiveness_score_not_available: PASS (critical) — attractiveness_score_available=False
- attractiveness_score_not_invented: PASS (critical) — attractiveness_score_invented=False
- prior_production_scoring_not_authorized: PASS (critical) — prior_production_scoring_authorized=False
- prior_scoring_not_promoted: PASS (critical) — prior_scoring_promoted=False
- freeze_reasons_defined: PASS (critical) — freeze_reasons=5
- promotion_blockers_defined: PASS (critical) — promotion_blockers=5
- promotion_decision_false: PASS (critical) — promotion_approved=False
- production_scoring_not_authorized: PASS (critical) — production_scoring_authorized=False
- canonical_dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- redesigned_score_output_not_modified: PASS (critical) — redesigned_sha_after=096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb
- legacy_score_output_not_modified: PASS (critical) — legacy_sha_after=a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.23F - Calibration Closure Report`

Secondary: `v2.24A - Metadata Gap Audit`
