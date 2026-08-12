# v2.20J — ASX Candidate Promotion Decision Gate

Status: **ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED**

Phase type: **promotion-decision-gate-only**

Generated at UTC: `2026-08-12T11:23:36.219661+00:00`

## Executive summary

v2.20J is a promotion decision gate for the validated ASX candidate.

Validated ASX candidate:

`outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv`

The ASX candidate contains **42,708** rows and is recommended as the next operational base for a controlled promotion plan.

This phase does **not** promote canonical. It only records that promotion preparation is recommended.

## Decision summary

- Promotion decision: `PROMOTION_RECOMMENDED_READY_FOR_PLAN`
- Promotion recommendation: `PREPARE_CANONICAL_PROMOTION_PLAN`
- Active canonical rows: `38287`
- Current validated candidate rows: `41392`
- Validated ASX candidate rows: `42708`
- ASX net-new rows vs current candidate: `1316`
- Uplift vs active canonical rows: `4421`
- Uplift vs current candidate rows: `1316`
- Quality floor crossed: `True`
- Quality ceiling respected: `True`
- Rows above 42k floor: `708`
- Remaining capacity to 45k ceiling: `2292`
- Rows to 50k aspirational: `7292`
- Canonical promotion performed: `False`
- Critical failed checks: `0`
- Warning failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Promotion readiness

- v2.20G rebuild passed: READY — ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2.20H validation passed: READY — ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED
- v2.20I closure passed: READY — ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED
- 42k floor achieved: READY — 42708 >= 42000
- 45k ceiling respected: READY — 42708 <= 45000
- canonical unchanged: READY — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- ASX candidate immutable during decision gate: READY — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- promotion decision ready: READY — critical_failed_checks=0;warning_failed_checks=0

## Decision register

- `ASX_PROMOTION_GATE_001` — Recommend preparing canonical promotion plan — accepted
- `ASX_PROMOTION_GATE_002` — Prefer validated ASX candidate over current HKEX candidate as next operational base — accepted
- `ASX_PROMOTION_GATE_003` — Do not continue provider expansion by default — accepted
- `ASX_PROMOTION_GATE_004` — Keep full59k deprecated — accepted
- `ASX_PROMOTION_GATE_005` — Require separate promotion phase before replacing canonical — accepted

## Checks

- v2_20g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_rebuild_candidate_v2_20g.json
- v2_20h_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_validation_v2_20h.json
- v2_20i_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_closure_report_v2_20i.json
- v2_20g_status_expected: PASS (critical) — ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20h_status_expected: PASS (critical) — ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED
- v2_20i_status_expected: PASS (critical) — ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED
- v2_20i_next_phase_expected: PASS (critical) — v2.20J - ASX Candidate Promotion Decision Gate
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- pre_hkex_current_candidate_rows_expected: PASS (critical) — pre_hkex_rows=40996
- current_validated_candidate_rows_expected: PASS (critical) — current_validated_rows=41392
- asx_validated_candidate_rows_expected: PASS (critical) — asx_validated_rows=42708
- asx_net_new_rows_expected: PASS (critical) — asx_net_new_rows=1316
- active_canonical_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- pre_hkex_current_candidate_sha_expected: PASS (critical) — 05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2
- current_validated_candidate_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- asx_validated_candidate_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- active_canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- pre_hkex_current_candidate_sha_unchanged: PASS (critical) — pre-HKEX current candidate sha unchanged
- current_validated_candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- asx_validated_candidate_sha_unchanged: PASS (critical) — ASX validated candidate sha unchanged
- quality_floor_crossed: PASS (critical) — asx_validated_rows=42708;floor=42000
- quality_ceiling_not_exceeded: PASS (critical) — asx_validated_rows=42708;ceiling=45000
- rows_above_quality_floor_expected: PASS (critical) — rows_above_floor=708
- remaining_capacity_to_quality_ceiling_expected: PASS (critical) — capacity_to_ceiling=2292
- rows_to_aspirational_50k_expected: PASS (warning) — rows_to_50k=7292
- v2_20h_validation_clean: PASS (critical) — critical=0;warning=0
- v2_20i_closure_successful: PASS (critical) — ASX_PROVIDER_ROUTE_CLOSED_SUCCESSFULLY
- v2_20i_target_result_expected: PASS (critical) — OPERATIONAL_42K_FLOOR_ACHIEVED_WITHOUT_EXCEEDING_45K
- v2_20i_canonical_promotion_status_ready: PASS (critical) — NOT_PROMOTED_DECISION_GATE_READY
- promotion_decision_gate_only: PASS (critical) — promotion decision gate only
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- canonical_promotion_not_performed: PASS (critical) — canonical_promotion_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Next actions

- Phigh `canonical` — prepare_asx_canonical_promotion_plan — v2.20K - ASX Canonical Promotion Plan
- Phigh `audit` — define_rollback_and_sha_controls — v2.20K - ASX Canonical Promotion Plan
- Phigh `quality_target` — freeze_additional_provider_expansion — v2.20K - ASX Canonical Promotion Plan

## Guards

- Promotion decision gate only: true
- Canonical dataset modified: false
- Active canonical replaced: false
- Canonical promotion performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20K - ASX Canonical Promotion Plan`
