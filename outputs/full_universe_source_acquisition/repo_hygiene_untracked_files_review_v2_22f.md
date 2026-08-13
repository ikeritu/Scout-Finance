# v2.22F — Repo Hygiene / Untracked Files Review

Status: **REPO_HYGIENE_UNTRACKED_FILES_REVIEW_COMPLETED_UNTRACKED_FILES_CLASSIFIED_NO_AUTO_ADD**

Phase type: **repo-hygiene-untracked-files-review**

Generated at UTC: `2026-08-13T11:44:09.522775+00:00`

## Decision

Repo hygiene decision: **UNTRACKED_FILES_CLASSIFIED_NO_AUTO_ADD**

The persistent untracked files are classified but not automatically added to Git.

## Untracked classification

- `Auditoria_Scout_Finance.docx` — defer_do_not_add_automatically — Manual audit document. Not part of deterministic pipeline outputs and should not be committed without explicit review.
- `outputs\full_universe_source_acquisition\country_breakdown_by_country.csv` — defer_do_not_add_automatically — Ad hoc breakdown artifact. Useful for local inspection but not currently part of versioned v2.22 pipeline.
- `outputs\full_universe_source_acquisition\country_breakdown_by_currency.csv` — defer_do_not_add_automatically — Ad hoc breakdown artifact. Useful for local inspection but not currently part of versioned v2.22 pipeline.
- `outputs\full_universe_source_acquisition\country_breakdown_by_exchange.csv` — defer_do_not_add_automatically — Ad hoc breakdown artifact. Useful for local inspection but not currently part of versioned v2.22 pipeline.
- `outputs\full_universe_source_acquisition\country_breakdown_by_mic.csv` — defer_do_not_add_automatically — Ad hoc breakdown artifact. Useful for local inspection but not currently part of versioned v2.22 pipeline.
- `outputs\full_universe_source_acquisition\country_breakdown_by_source_provider.csv` — defer_do_not_add_automatically — Ad hoc breakdown artifact. Useful for local inspection but not currently part of versioned v2.22 pipeline.

## Guardrails

- Untracked files committed: `False`
- Auto-add recommended: `0`
- .gitignore modified: `False`
- .git/info/exclude modified: `False`
- Canonical dataset modified: `False`
- Scoring output modified: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

- freeze_status_expected: PASS (critical) — SCORING_PROMOTION_FREEZE_DECISION_COMPLETED_DRY_RUN_FROZEN_NOT_PROMOTED
- freeze_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- scoring_rows_expected: PASS (critical) — scoring_rows=33498
- scoring_sha_expected: PASS (critical) — a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- expected_untracked_targets_present: PASS (critical) — present=6;expected=6
- tracked_modifications_absent: PASS (critical) — tracked_modifications=[]
- unexpected_untracked_absent_before_outputs: PASS (critical) — unexpected_untracked=[]
- auto_add_not_recommended: PASS (critical) — auto_add_recommended=0
- defer_recommendations_expected: PASS (critical) — defer_recommended=6
- manual_review_required_zero: PASS (critical) — manual_review_required=0
- canonical_dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- scoring_output_not_modified: PASS (critical) — scoring_sha_after=a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.23A - Scoring Model Calibration Roadmap`

Secondary: `v2.23B - Metadata Coverage Improvement Plan`
