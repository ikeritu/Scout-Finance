# v2.20A — Quality-First Target Reset and Provider Selection

Status: **QUALITY_FIRST_TARGET_RESET_COMPLETED_42K_45K_OPERATIONAL_ASX_SELECTED_50K_ASPIRATIONAL_FULL59K_DEPRECATED**

Phase type: **strategy-reset-and-provider-selection-only**

Generated at UTC: `2026-08-11T22:22:11.661036+00:00`

## Executive summary

v2.20A resets the expansion strategy from a rigid 50,000-candidate target to a quality-first operational band of **42,000–45,000** validated candidates.

The current validated HKEX candidate dataset has **41,392** rows.

Rows needed:

- To reach 42k quality floor: **608**
- To reach 45k quality ceiling: **3,608**
- To reach 50k aspirational target: **8,608**

50k remains aspirational only. The project should not add low-quality rows, derivative instruments, debt, structured products, illiquid microcaps or duplicate-heavy routes merely to reach 50k.

The selected next provider route is **ASX**, with next phase:

`v2.20B - ASX Quality-First Acquisition Plan`

## Target summary

- Active canonical rows: `38287`
- Current validated candidate rows before HKEX: `40996`
- HKEX validated candidate rows: `41392`
- Operational target floor: `42000`
- Operational target ceiling: `45000`
- Aspirational target: `50000`
- Rows needed to floor: `608`
- Rows needed to ceiling: `3608`
- Rows needed to aspirational 50k: `8608`
- Quality floor gate: `BLOCKED`
- Quality ceiling gate: `BLOCKED`
- 50k aspirational gate: `BLOCKED`
- Selected next provider: `ASX`
- Critical failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Decisions

- `reset_operational_target`: `approved` — Prefer fewer high-quality candidates over reaching 50k by adding noisy instruments.
- `keep_50k_as_aspirational_only`: `approved` — 50k remains useful only if a clean provider produces quality net-new rows without relaxing instrument criteria.
- `select_next_provider`: `selected:ASX` — ASX is selected first because it has high expected equity quality and enough plausible breadth to cross 42k without lowering quality.

## Provider ranking

- #1 `ASX` — score `92` — select_next — Best balance between quality, breadth and likely contribution toward 42k-45k without chasing 50k.
- #2 `TMX_TSX_ONLY` — score `88` — backup_1 — Good quality in TSX, but Venture must stay excluded unless a later quality filter is approved.
- #3 `NASDAQ_NORDIC_MAIN_MARKET` — score `86` — backup_2 — Strong quality profile, especially industrials, health, banks, software and Nordic compounders.
- #4 `SIX` — score `90` — backup_quality — Very high average quality, but probably fewer net-new rows.
- #5 `NSE_BSE_INDIA_INDEX_ONLY` — score `89` — special_phase_only — Excellent opportunity set, but complex enough to require its own controlled phase.
- #6 `B3` — score `78` — defer — Useful but macro/currency/class-share complexity makes it less attractive than ASX/TMX/Nordic.
- #7 `SGX` — score `76` — defer — Good REIT/bank/infrastructure exposure but less likely to add many strong net-new equities.
- #8 `BME_AND_EUROPE_MINOR_MARKETS` — score `75` — complement_only — Good complement but not a primary route for filling the 42k-45k quality band.
- #9 `JSE` — score `70` — defer — Interesting market, but lower priority due to macro/currency/liquidity risk.

## Stop rules

- `STOP_001` — do_not_add_rows_for_volume_only: always → reject_provider_or_subset
- `STOP_002` — provider_minimum_quality_net_new: >= 500 clean net-new rows preferred; < 250 triggers fast closure unless quality is exceptional → continue_only_if_quality_justifies_effort
- `STOP_003` — quality_ceiling_stop: 45,000 validated candidates → freeze_expansion_and_move_to_product_scoring
- `STOP_004` — instrument_scope_guard: no warrants/options/rights/debt/structured products by default → exclude_before_canonical_validation
- `STOP_005` — microcap_liquidity_guard: exclude or flag illiquid speculative microcaps where source allows → do_not_count_as quality net-new unless approved
- `STOP_006` — 50k_aspirational_only: 50,000 → do_not_force_route_selection_to_reach_50k

## Next actions

- Phigh `target_strategy` — adopt_42k_45k_quality_band — v2.20B - ASX Quality-First Acquisition Plan
- Phigh `provider_route` — open_asx_quality_first_acquisition_plan — v2.20B - ASX Quality-First Acquisition Plan
- Pmedium `fallback_route` — prepare_tmx_tsx_only_as_backup — post-ASX route decision

## Checks

- v2_19r_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_closure_report_v2_19r.json
- v2_19r_status_expected: PASS (critical) — HKEX_CLOSURE_REPORT_COMPLETED_41392_ROWS_396_NET_NEW_50K_GATE_STILL_BLOCKED_NEXT_PROVIDER_SELECTION_READY_FULL59K_DEPRECATED
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- hkex_validated_candidate_rows_expected: PASS (critical) — hkex_rows=41392
- active_canonical_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- current_candidate_sha_expected: PASS (critical) — 05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2
- hkex_validated_candidate_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- active_canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- current_candidate_sha_unchanged: PASS (critical) — current candidate sha unchanged
- hkex_candidate_sha_unchanged: PASS (critical) — HKEX validated candidate sha unchanged
- quality_floor_target_expected: PASS (critical) — quality_floor=42000
- quality_ceiling_target_expected: PASS (critical) — quality_ceiling=45000
- aspirational_50k_not_operational: PASS (critical) — 50k retained as aspirational only
- rows_needed_to_quality_floor_expected: PASS (critical) — rows_needed_to_42k=608
- rows_needed_to_quality_ceiling_expected: PASS (critical) — rows_needed_to_45k=3608
- rows_needed_to_aspirational_50k_expected: PASS (warning) — rows_needed_to_50k=8608
- selected_next_provider_asx: PASS (critical) — ASX
- selected_next_phase_asx_plan: PASS (critical) — v2.20B - ASX Quality-First Acquisition Plan
- quality_first_stop_rules_defined: PASS (critical) — stop_rules=6
- provider_ranking_defined: PASS (critical) — providers_ranked=9
- strategy_reset_only: PASS (critical) — strategy reset only
- dataset_not_modified: PASS (critical) — no dataset writes in v2.20A
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- current_candidate_dataset_not_modified: PASS (critical) — current_candidate_dataset_modified=False
- hkex_candidate_dataset_not_modified: PASS (critical) — hkex_candidate_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- acquisition_not_performed: PASS (critical) — raw_acquisition_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Guards

- Strategy reset only: true
- Target reset performed: true
- Old operational 50k target replaced: true
- New operational target: `42000`–`45000`
- 50k retained as aspirational: true
- Selected next provider: `ASX`
- Network download performed: false
- Acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current candidate dataset modified: false
- HKEX candidate dataset modified: false
- Active canonical replaced: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false

## Recommended next phase

`v2.20B - ASX Quality-First Acquisition Plan`
