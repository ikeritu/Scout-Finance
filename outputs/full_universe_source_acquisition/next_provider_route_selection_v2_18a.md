# v2.18A - Next Provider Route Selection

Status: **NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_TWSE_TPEX_SELECTED_50K_TARGET_ACTIVE_FULL59K_DEPRECATED**

Phase type: **target-policy-and-provider-route-selection-only**

Generated at UTC: `2026-08-11T08:23:31.992477+00:00`

## Executive summary

v2.18A updates the universe target policy and selects the next provider route.

The active final target is now **50,000 candidates**. The previous 59k objective is deprecated/deferred and must not be launched unless explicitly reopened later.

After NSE India, the validated candidate dataset contains `40300` rows. The remaining gap to 50,000 is `9700` rows.

## Target policy

- `final_target_candidates`: `50000` — ACTIVE — New final operational target. The project no longer needs 59k candidates.
- `validated_candidate_rows_after_nse_india`: `40300` — REFERENCE — Validated candidate dataset from NSE India route.
- `rows_needed_to_final_target`: `9700` — ACTIVE — Remaining rows needed to reach the 50k candidate target.
- `full59k_target`: `deprecated` — DEPRECATED — No full59k dry run or 59k objective should be launched unless explicitly reopened later.
- `stop_condition`: `candidate_dataset_rows >= 50000` — ACTIVE — Provider acquisition can stop once a validated candidate dataset reaches at least 50,000 rows.
- `canonical_promotion`: `requires_explicit_controlled_promotion_phase` — BLOCKED — Validated candidate datasets are not automatically promoted to active canonical.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Validated NSE candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv`
- Validated candidate rows: `40300`
- Final target candidates: `50000`
- Rows needed to 50k: `9700`
- Candidate completion: `80.6%`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Provider route candidates

- Rank 1: `TWSE + TPEx Taiwan` — SELECTED — v2.18B - TWSE + TPEx Acquisition Plan
- Rank 2: `ASX Australia` — RESERVE — v2.19A or fallback after v2.18 closure
- Rank 3: `KRX / HKEX / LSEG / SGX` — DEFERRED — future route selection only if needed

## Route decision

- Selected next provider: `TWSE + TPEx Taiwan`
- Reserve provider: `ASX Australia`
- Deferred pool: `KRX`, `HKEX`, `LSEG`, `SGX`
- Recommended next phase: `v2.18B - TWSE + TPEx Acquisition Plan`

## Checks

- v2_17i_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_closure_report_v2_17i.json
- v2_17i_status_expected: PASS (critical) — NSE_INDIA_CLOSURE_COMPLETED_VALIDATED_CANDIDATE_RETAINED_FULL_SOURCE_STILL_BLOCKED
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- validated_nse_candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- validated_candidate_rows_expected: PASS (critical) — validated_candidate_rows=40300
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9700
- candidate_below_50k: PASS (critical) — 40300 < 50000
- candidate_schema_matches_canonical: PASS (critical) — canonical_cols=33 candidate_cols=33
- canonical_sha_unchanged: PASS (critical) — canonical sha unchanged
- target_50k_active: PASS (critical) — final_target=50000
- full59k_deprecated: PASS (critical) — full59k is deprecated/deferred
- next_provider_selected: PASS (critical) — TWSE + TPEx Taiwan
- reserve_provider_selected: PASS (critical) — ASX Australia
- network_not_used: PASS (critical) — network_download_performed=False
- endpoint_calls_not_used: PASS (critical) — endpoint_calls_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- Target policy written: true
- Provider route selected: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Final target 50k active: true
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Overwrite allowed: false

## Conclusion

v2.18A selects `TWSE + TPEx Taiwan` as the next provider route under the new 50k-only target policy.

## Recommended next phase

`v2.18B - TWSE + TPEx Acquisition Plan`
