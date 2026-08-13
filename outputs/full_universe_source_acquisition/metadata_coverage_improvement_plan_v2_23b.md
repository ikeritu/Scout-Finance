# v2.23B — Metadata Coverage Improvement Plan

Status: **METADATA_COVERAGE_IMPROVEMENT_PLAN_COMPLETED_NO_DATASET_MODIFICATION**

Phase type: **metadata-coverage-improvement-plan**

Generated at UTC: `2026-08-13T14:14:06.550518+00:00`

## Decision

Metadata decision: **METADATA_COVERAGE_PLAN_CREATED_NO_DATASET_MODIFICATION**

This phase creates a metadata coverage improvement plan only. It does not backfill metadata, execute scoring, promote scoring, or modify the canonical dataset.

## Coverage focus

Coverage metrics created: `24`  
High or critical gap metrics: `12`  
Provider priority rows: `28`

Scorable country top value: `__MISSING__`  
Scorable country missing pct: `35.1961`

## Gap plan

- `META_GAP_001` — critical — country: Design deterministic country backfill from exchange, MIC, source provider or listing suffix.
- `META_GAP_002` — high — mic: Design exchange-to-MIC and provider-specific MIC mapping tables.
- `META_GAP_003` — high — currency: Backfill currency from exchange/MIC/provider where deterministic.
- `META_GAP_004` — critical — asset_type/instrument_type/instrument_scope: Promote a normalized taxonomy design before scoring promotion.
- `META_GAP_005` — medium — source_provider: Create provider quality matrix and prioritize providers with largest missing metadata burden.

## Guardrails

- Production scoring authorized: `False`
- New scoring executed: `False`
- Metadata backfill executed: `False`
- Canonical dataset modified: `False`
- Dry-run score output modified: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

- calibration_status_expected: PASS (critical) — SCORING_MODEL_CALIBRATION_ROADMAP_COMPLETED_PRODUCTION_SCORING_DEFERRED
- calibration_critical_failed_checks_zero: PASS (critical) — critical_failed_checks=0
- pointer_current_dataset_expected: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_21h_activated_operational_reference.csv
- current_rows_expected: PASS (critical) — current_rows=43089
- current_sha_expected: PASS (critical) — 9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- scoring_rows_expected: PASS (critical) — scoring_rows=33498
- scoring_sha_expected: PASS (critical) — a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- coverage_metrics_created: PASS (critical) — coverage_metrics=24
- gap_plan_created: PASS (critical) — gap_plan_rows=5
- provider_priorities_created: PASS (critical) — provider_priority_rows=28
- known_country_gap_documented: PASS (warning) — top_country=__MISSING__;missing_pct=35.1961
- production_scoring_not_authorized: PASS (critical) — production_scoring_authorized=False
- new_scoring_not_executed: PASS (critical) — new_scoring_executed=False
- metadata_backfill_not_executed: PASS (critical) — metadata_backfill_executed=False
- canonical_dataset_not_modified: PASS (critical) — current_sha_after=9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707
- dry_run_score_output_not_modified: PASS (critical) — scoring_sha_after=a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.23C - Scoring Calibration Data Design`

Secondary: `v2.23D - Scoring Formula Redesign Dry Run`
