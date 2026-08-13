# v2.23F — Calibration Closure Report

Status: **CALIBRATION_CLOSURE_REPORT_COMPLETED_V2_23_CLOSED_PRODUCTION_SCORING_DEFERRED**

Phase type: **calibration-closure-report**

Generated at UTC: `2026-08-13T15:50:34.524483+00:00`

## Closure decision

Closure decision: **V2_23_CLOSED_PRODUCTION_SCORING_DEFERRED**

The v2.23 calibration block is closed as a calibration/design/dry-run/freeze block.

No production scoring has been authorized.

## Closed phases

- `v2.23A` — Scoring Model Calibration Roadmap: Calibration roadmap created; production scoring deferred.
- `v2.23B` — Metadata Coverage Improvement Plan: Metadata gaps identified; no backfill executed.
- `v2.23C` — Scoring Calibration Data Design: Label schema and sample plan designed; no manual labels created.
- `v2.23D` — Scoring Formula Redesign Dry Run: Redesigned dry-run scores created; attractiveness not invented.
- `v2.23E` — Calibration Review / Freeze Decision: Redesigned dry-run scores frozen as non-promoted reference.

## Remaining blockers

- `V23_BLOCKER_001` — blocking `True` — manual_calibration_labels_missing
- `V23_BLOCKER_002` — blocking `True` — attractiveness_score_unavailable
- `V23_BLOCKER_003` — blocking `True` — metadata_gap_remediation_not_executed
- `V23_BLOCKER_004` — blocking `True` — production_scoring_gate_not_approved
- `V23_BLOCKER_005` — blocking `False` — external_enrichment_not_authorized

## Handoff

- `V24_HANDOFF_001` → `v2.24A - Metadata Gap Audit` — Start metadata gap audit from v2.23B findings.
- `V24_HANDOFF_002` → `v2.24B - Country / MIC / Currency Backfill Plan` — Prioritize deterministic mapping for country, MIC and currency.
- `V24_HANDOFF_003` → `v2.24C - Asset Type Normalization Plan` — Normalize asset_type, instrument_type and instrument_scope before production scoring.
- `V24_HANDOFF_004` → `future production scoring gate` — Keep v2.23D redesigned scores as non-promoted reference only.

## References

Current dataset:

`outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv`

Rows: `43089`  
SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`

Legacy v2.22D dry-run score:

`outputs\full_universe_source_acquisition\scoring_dry_run_no_promotion_scores_v2_22d.csv`

Rows: `33498`  
SHA256: `a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1`

Redesigned v2.23D dry-run score:

`outputs\full_universe_source_acquisition\scoring_formula_redesign_dry_run_scores_v2_23d.csv`

Rows: `33498`  
SHA256: `096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb`

## Guardrails

- v2.23 closed: `True`
- Promotion approved: `False`
- Production scoring authorized: `False`
- Scoring promoted: `False`
- Canonical dataset modified: `False`
- Active pointer modified: `False`
- Legacy score output modified: `False`
- Redesigned score output modified: `False`
- Manual labels created: `False`
- Attractiveness score invented: `False`
- Metadata backfill executed: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`
- .gitignore modified: `False`
- .git/info/exclude modified: `False`

## Checks

- v2.23A_status_expected: PASS (critical) — SCORING_MODEL_CALIBRATION_ROADMAP_COMPLETED_PRODUCTION_SCORING_DEFERRED
- v2.23A_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- v2.23B_status_expected: PASS (critical) — METADATA_COVERAGE_IMPROVEMENT_PLAN_COMPLETED_NO_DATASET_MODIFICATION
- v2.23B_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- v2.23C_status_expected: PASS (critical) — SCORING_CALIBRATION_DATA_DESIGN_COMPLETED_NO_LABELS_NO_SCORING_NO_PROMOTION
- v2.23C_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- v2.23D_status_expected: PASS (critical) — SCORING_FORMULA_REDESIGN_DRY_RUN_COMPLETED_NO_PROMOTION_NO_CANONICAL_CHANGE
- v2.23D_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- v2.23E_status_expected: PASS (critical) — CALIBRATION_REVIEW_FREEZE_DECISION_COMPLETED_REDESIGNED_DRY_RUN_FROZEN_NOT_PROMOTED
- v2.23E_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- legacy_scoring_rows_expected: PASS (critical) — legacy_rows=33498
- legacy_scoring_sha_expected: PASS (critical) — a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- redesigned_scoring_rows_expected: PASS (critical) — redesigned_rows=33498
- redesigned_scoring_sha_expected: PASS (critical) — 096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb
- v23e_freeze_decision_expected: PASS (critical) — FREEZE_REDESIGNED_DRY_RUN_AS_NON_PROMOTED_REFERENCE
- v23e_promotion_not_approved: PASS (critical) — promotion_approved=False
- manual_labels_not_created: PASS (critical) — manual_labels_created=False
- attractiveness_not_available: PASS (critical) — attractiveness_score_available=False
- production_scoring_not_authorized: PASS (critical) — production_scoring_authorized=False
- scoring_not_promoted: PASS (critical) — scoring_promoted=False
- canonical_dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- active_pointer_not_modified: PASS (critical) — pointer_sha_after=61ceca33292a20e00f21a1cb34f7c824c50944818111b8c02834a2e7c74eabf4
- legacy_score_output_not_modified: PASS (critical) — legacy_sha_after=a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- redesigned_score_output_not_modified: PASS (critical) — redesigned_sha_after=096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb
- phase_rollup_created: PASS (critical) — phase_rollup_rows=5
- remaining_blockers_created: PASS (critical) — blockers_rows=5
- handoff_created: PASS (critical) — handoff_rows=4
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- gitignore_not_modified_by_phase: PASS (critical) — gitignore_modified=False
- git_info_exclude_not_modified_by_phase: PASS (critical) — git_info_exclude_modified=False

## Recommended next phase

Primary: `v2.24A - Metadata Gap Audit`

Secondary: `v2.24B - Country / MIC / Currency Backfill Plan`
