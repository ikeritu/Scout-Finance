# v2.22E — Scoring Promotion / Freeze Decision

Status: **SCORING_PROMOTION_FREEZE_DECISION_COMPLETED_DRY_RUN_FROZEN_NOT_PROMOTED**

Phase type: **scoring-promotion-freeze-decision**

Generated at UTC: `2026-08-13T11:38:30.450366+00:00`

## Decision

Promotion decision: **FREEZE_DRY_RUN_SCORE_OUTPUT_AS_NON_PROMOTED_REFERENCE**

The v2.22D scoring dry run is frozen as a non-promoted reference artifact.

## Reasons to freeze

- v2.22D was explicitly dry-run/no-promotion.
- Scores are local deterministic heuristic scores, not calibrated production scores.
- top_country_by_scorable_rows is __MISSING__, indicating metadata coverage should be improved before promotion.
- Promotion/canonical replacement requires a separate explicit future gate.
- OpenAI, broker enrichment, and full59k remain unauthorized/deferred.

## Dry-run scoring reference

`outputs\full_universe_source_acquisition\scoring_dry_run_no_promotion_scores_v2_22d.csv`

Rows: `33498`  
SHA256: `a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1`

## Score summary

- Min: `44.7`
- P25: `45.1`
- Median: `52.2`
- P75: `74.7667`
- Max: `87.2`
- Mean: `58.2468`

## Guardrails

- Promotion approved: `False`
- Scoring promoted: `False`
- Production scoring authorized: `False`
- Canonical dataset modified: `False`
- Active canonical replaced: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

- dry_run_status_expected: PASS (critical) — SCORING_DRY_RUN_NO_PROMOTION_COMPLETED_LOCAL_HEURISTIC_SCORES_CREATED_PROMOTION_DEFERRED
- dry_run_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- scoring_rows_expected: PASS (critical) — scoring_rows=33498
- excluded_rows_expected: PASS (critical) — excluded=9591
- score_min_expected: PASS (critical) — score_min=44.7
- score_median_expected: PASS (critical) — score_median=52.2
- score_max_expected: PASS (critical) — score_max=87.2
- score_mean_expected: PASS (critical) — score_mean=58.2468
- distribution_rows_expected: PASS (critical) — distribution_rows=5
- component_rows_expected: PASS (critical) — component_rows=6
- excluded_summary_rows_expected: PASS (critical) — excluded_summary_rows=16
- promotion_not_approved: PASS (critical) — promotion_approved=False
- scoring_not_promoted: PASS (critical) — scoring_promoted=False
- production_scoring_not_authorized: PASS (critical) — production_scoring_authorized=False
- canonical_dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.22F - Repo Hygiene / Untracked Files Review`

Secondary: `v2.23A - Scoring Model Calibration Roadmap`
