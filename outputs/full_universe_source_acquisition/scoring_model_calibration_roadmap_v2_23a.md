# v2.23A — Scoring Model Calibration Roadmap

Status: **SCORING_MODEL_CALIBRATION_ROADMAP_COMPLETED_PRODUCTION_SCORING_DEFERRED**

Phase type: **scoring-model-calibration-roadmap**

Generated at UTC: `2026-08-13T12:19:33.111262+00:00`

## Decision

Calibration decision: **PRODUCTION_SCORING_DEFERRED_CALIBRATION_REQUIRED**

Production scoring remains deferred. v2.23A creates a calibration roadmap only.

## Current reference

Dataset:

`outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv`

Rows: `43089`  
SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`

Dry-run scoring output:

`outputs\full_universe_source_acquisition\scoring_dry_run_no_promotion_scores_v2_22d.csv`

Rows: `33498`  
SHA256: `a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1`

## Dry-run score reference

- Min: `44.7`
- P25: `45.1`
- Median: `52.2`
- P75: `74.7667`
- Max: `87.2`
- Mean: `58.2468`

## Calibration requirements

- `CAL_REQ_001` — critical — Define target scoring objective before production.
- `CAL_REQ_002` — critical — Improve metadata coverage for country, MIC, currency, asset_type and source_provider before production scoring.
- `CAL_REQ_003` — critical — Create benchmark sample with manually reviewed good/bad scoring examples.
- `CAL_REQ_004` — high — Separate data-quality score from investment/attractiveness score.
- `CAL_REQ_005` — high — Define exclusion overlay as reusable production input if accepted.
- `CAL_REQ_006` — critical — Keep OpenAI, broker APIs and full59k disabled unless a separate future gate authorizes them.

## Calibration phases

- `v2.23B` — Metadata Coverage Improvement Plan: Design improvements for country, MIC, currency, asset_type, source_provider and classification coverage.
- `v2.23C` — Scoring Calibration Data Design: Define manual benchmark sample, labelled cases and score acceptance criteria.
- `v2.23D` — Scoring Formula Redesign Dry Run: Create a redesigned deterministic scoring formula in dry-run mode only.
- `v2.23E` — Calibration Review / Freeze Decision: Decide whether redesigned dry-run scoring is still frozen or ready for a future promotion gate.

## Calibration risks

- `CAL_RISK_001` — high — Current score can over-reward providers with complete metadata rather than genuinely better assets. Mitigation: Split data-quality score from investment/selection score.
- `CAL_RISK_002` — high — Missing country values dominate scorable rows. Mitigation: Run metadata coverage improvement before production scoring.
- `CAL_RISK_003` — critical — Dry-run output could be mistaken for production ranking. Mitigation: Keep promotion_approved=False and production_scoring_authorized=False.
- `CAL_RISK_004` — medium — External enrichment may change score semantics if introduced without a gate. Mitigation: Keep OpenAI and broker APIs disabled unless separately approved.

## Guardrails

- Production scoring authorized: `False`
- New scoring executed in this phase: `False`
- Scoring promoted: `False`
- Canonical dataset modified: `False`
- Dry-run score output modified: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

- hygiene_status_expected: PASS (critical) — REPO_HYGIENE_UNTRACKED_FILES_REVIEW_COMPLETED_UNTRACKED_FILES_CLASSIFIED_NO_AUTO_ADD
- hygiene_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- freeze_status_expected: PASS (critical) — SCORING_PROMOTION_FREEZE_DECISION_COMPLETED_DRY_RUN_FROZEN_NOT_PROMOTED
- freeze_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- dry_run_status_expected: PASS (critical) — SCORING_DRY_RUN_NO_PROMOTION_COMPLETED_LOCAL_HEURISTIC_SCORES_CREATED_PROMOTION_DEFERRED
- dry_run_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- scoring_rows_expected: PASS (critical) — scoring_rows=33498
- scoring_sha_expected: PASS (critical) — a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- distribution_rows_expected: PASS (critical) — distribution_rows=5
- components_rows_expected: PASS (critical) — components_rows=6
- calibration_requirements_defined: PASS (critical) — requirements=6
- calibration_phases_defined: PASS (critical) — phases=4
- calibration_risks_defined: PASS (critical) — risks=4
- production_scoring_not_authorized: PASS (critical) — production_scoring_authorized=False
- scoring_not_executed_in_this_phase: PASS (critical) — new_scoring_executed=False
- promotion_not_performed: PASS (critical) — promotion_performed=False
- canonical_dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- dry_run_score_output_not_modified: PASS (critical) — scoring_sha_after=a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.23B - Metadata Coverage Improvement Plan`

Secondary: `v2.23C - Scoring Calibration Data Design`
