# v2.16I - TMX Closure Report

Status: **TMX_CLOSURE_REPORT_COMPLETED_PLUS1_CANDIDATE_VALIDATED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **provider-closure-report-only**

Generated at UTC: `2026-08-05T21:07:08.007322+00:00`

## Executive closure

TMX is closed as a provider route under the current controlled acquisition pipeline.

The route produced one validated candidate addition in a separate candidate dataset:

- `IRR` `Irruptive Metals Corp.` exchange=`TSXV` confidence=`high` source=`tmx_money_recent_listings`

The active canonical dataset remains unchanged.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Validated candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_tmx_v2_16g.csv`
- Validated candidate rows: `38288`
- Validated candidate delta: `1`
- Full source threshold: `50000`
- Rows needed with active canonical: `11713`
- Rows needed if candidate is promoted later: `11712`
- Active canonical source-to-50k completion: `76.57%`
- Candidate source-to-50k completion: `76.58%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Phase inventory

- **v2.16A — TMX Provider Route Confirmation**: `closed_by_git_history` — TMX selected as next provider route after Euronext closure.
- **v2.16B — TMX Acquisition Plan**: `closed_by_git_history` — TMX source candidates defined.
- **v2.16C — TMX Raw Acquisition**: `ok` — Raw TMX landing/source responses acquired; controlled/paid sources not downloaded.
- **v2.16D — TMX Validation**: `closed_by_git_history` — Raw source validation completed; controlled endpoint probe recommended.
- **v2.16D2 — TMX Controlled Endpoint Probe**: `closed_by_git_history` — No promising endpoint path found; candidate extraction moved to local raw extraction.
- **v2.16E — TMX Candidate Extraction Dry Run**: `ok` — 13 conservative candidates extracted; newsroom false positives removed.
- **v2.16F — TMX Candidate Validation Against Canonical Dry Run**: `ok` — 13 candidates validated; 1 rebuild candidate selected: IRR / Irruptive Metals Corp. / TSXV.
- **v2.16G — TMX Expanded Rebuild Candidate**: `ok` — Separate candidate dataset generated with +1 row; canonical not replaced.
- **v2.16H — TMX Expanded Validation**: `ok` — Candidate dataset validated: canonical +1, IRR/TSXV, full source still blocked.

## Decision log

- **Canonical dataset**: Do not modify expanded_universe_v2_14e.csv in TMX closure. Impact: `Active canonical remains 38,287 rows.`
- **TMX candidate dataset**: Preserve expanded_universe_candidate_tmx_v2_16g.csv as validated candidate artifact. Impact: `Candidate dataset remains available for later controlled promotion if explicitly opened.`
- **TMX source yield**: Close TMX with +1 validated candidate but no full-source unlock. Impact: `Full source gate remains BLOCKED.`
- **Next route**: Move to next provider/source route selection. Impact: `v2.17A - Next Provider Route Selection`

## Checks

- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_tmx_v2_16g.csv
- v2_16e_artifact_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_candidate_extraction_dry_run_v2_16e.json
- v2_16f_artifact_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_candidate_validation_against_canonical_v2_16f.json
- v2_16g_artifact_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_expanded_rebuild_candidate_v2_16g.json
- v2_16h_artifact_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_expanded_validation_v2_16h.json
- v2_16e_status_expected: PASS (critical) — TMX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED
- v2_16f_status_expected: PASS (critical) — TMX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_REBUILD_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED
- v2_16g_status_expected: PASS (critical) — TMX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_ADD1_FULL_SOURCE_STILL_BLOCKED
- v2_16h_status_expected: PASS (critical) — TMX_EXPANDED_VALIDATION_COMPLETED_CANDIDATE_ADD1_VALID_CANONICAL_STILL_UNCHANGED_FULL_SOURCE_STILL_BLOCKED
- canonical_rows_expected: PASS (critical) — canonical_rows=38287
- candidate_rows_expected: PASS (critical) — candidate_rows=38288
- candidate_delta_expected: PASS (critical) — delta=1
- validated_addition_found: PASS (critical) — [{'symbol': 'IRR', 'name': 'Irruptive Metals Corp.', 'exchange': 'TSXV', 'confidence_bucket': 'high', 'source_id': 'tmx_money_recent_listings', 'validation_status': 'net_new_candidate_high_confidence_dry_run', 'rebuild_candidate_reason': 'symbol_absent_from_canonical_high_confidence'}]
- full_source_still_blocked_active_canonical: PASS (critical) — 38287 < 50000
- full_source_still_blocked_candidate: PASS (critical) — 38288 < 50000
- next_phase_selected: PASS (critical) — v2.17A - Next Provider Route Selection
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- candidate_not_promoted_to_canonical: PASS (critical) — candidate_promoted_to_canonical=False
- network_not_used: PASS (critical) — network_download_performed=False
- endpoint_calls_not_performed: PASS (critical) — endpoint_calls_performed=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Phase artifacts read: true
- Canonical dataset read: true
- Candidate dataset read: true
- Canonical dataset modified: false
- Candidate promoted to canonical: false
- Canonical replacement performed: false
- Expanded universe rebuilt as canonical: false
- New expanded dataset written: false
- Net-new filtering applied to canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Closure conclusion

TMX is closed with one validated candidate addition available as a separate candidate artifact.

No canonical promotion is performed in this phase. No rebuild is performed. Full source remains blocked because the active canonical dataset is still below the 50,000-row threshold.

## Recommended next phase

`v2.17A - Next Provider Route Selection`
