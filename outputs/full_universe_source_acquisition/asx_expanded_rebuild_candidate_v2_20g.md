# v2.20G — ASX Expanded Rebuild Candidate

Status: **ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED**

Phase type: **expanded-rebuild-candidate-only**

Generated at UTC: `2026-08-12T10:03:13.894147+00:00`

## Executive summary

v2.20G rebuilds a new ASX-expanded candidate dataset.

Input current candidate:

`outputs\full_universe_source_acquisition\expanded_universe_candidate_hkex_v2_19p.csv`

Input ASX net-new candidates:

`outputs\full_universe_source_acquisition\asx_candidate_validation_net_new_candidates_v2_20f.csv`

Output expanded candidate:

`outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv`

This phase appends **1,316** ASX net-new rows to the current validated candidate of **41,392** rows, producing **42,708** rows.

The rebuild crosses the operational floor of **42,000** and remains below the operational ceiling of **45,000**.

This phase writes a new candidate only. It does **not** promote canonical, does **not** run expanded validation, does **not** run scoring, does **not** call OpenAI, does **not** call brokers, and does **not** launch full59k.

## Rebuild summary

- Current validated candidate rows: `41392`
- ASX net-new rows appended: `1316`
- Expanded candidate rows: `42708`
- Quality floor crossed: `True`
- Quality ceiling not exceeded: `True`
- Rows above 42k floor: `708`
- Remaining capacity to 45k ceiling: `2292`
- Rows to 50k aspirational after rebuild: `7292`
- Schema column count: `33`
- Schema preserved: `True`
- Current prefix preserved: `True`
- Appended tail matches: `True`
- Duplicate appended tickers: `0`
- Duplicate appended symbols: `0`
- Duplicate appended ISINs: `0`
- Appended tickers already current: `0`
- Appended symbols already current: `0`
- Appended ISINs already current: `0`
- Expanded candidate SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Appended rows SHA256: `48cdcc8b28740421740ef6e14c830b37c1efcf03802fc2740f5555d891e23da4`
- Critical failed checks: `0`
- Warning failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Checks

- v2_20f_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_candidate_validation_against_current_dry_run_v2_20f.json
- v2_20f_status_expected: PASS (critical) — ASX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NET_NEW_READY_REBUILD_CANDIDATE_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED
- v2_20f_next_phase_expected: PASS (critical) — v2.20G - ASX Expanded Rebuild Candidate
- v2_20f_net_new_rows_expected: PASS (critical) — v2_20f_net_new=1316
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- pre_hkex_current_candidate_rows_expected: PASS (critical) — pre_hkex_rows=40996
- current_validated_candidate_rows_expected: PASS (critical) — current_validated_rows=41392
- active_canonical_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- pre_hkex_current_candidate_sha_expected: PASS (critical) — 05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2
- current_validated_candidate_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- active_canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- pre_hkex_current_candidate_sha_unchanged: PASS (critical) — pre-HKEX current candidate sha unchanged
- current_validated_candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- current_schema_column_count_expected: PASS (critical) — current_columns=33
- expanded_schema_preserved: PASS (critical) — schema_preserved=True
- appended_schema_preserved: PASS (critical) — appended_schema_preserved=True
- asx_net_new_rows_loaded: PASS (critical) — net_new_rows=1316
- appended_rows_expected: PASS (critical) — appended_rows=1316
- expanded_rows_expected: PASS (critical) — expanded_rows=42708
- row_arithmetic_expected: PASS (critical) — 41392+1316=42708
- quality_floor_crossed: PASS (critical) — expanded_rows=42708;floor=42000
- quality_ceiling_not_exceeded: PASS (critical) — expanded_rows=42708;ceiling=45000
- rows_needed_to_quality_floor_expected: PASS (critical) — rows_needed_to_42k=608
- rows_needed_to_quality_ceiling_expected: PASS (critical) — rows_needed_to_45k=3608
- rows_needed_to_50k_aspirational_expected: PASS (warning) — rows_needed_to_50k=8608
- current_prefix_preserved: PASS (critical) — prefix_matches_current=True
- appended_tail_matches_appended_rows: PASS (critical) — tail_matches=True
- duplicate_appended_tickers_zero: PASS (critical) — duplicate_appended_tickers=0
- duplicate_appended_symbols_zero: PASS (critical) — duplicate_appended_symbols=0
- duplicate_appended_isins_zero: PASS (warning) — duplicate_appended_isins=0
- appended_tickers_not_in_current: PASS (critical) — tickers_already_current=0
- appended_symbols_not_in_current: PASS (critical) — symbols_already_current=0
- appended_isins_not_in_current: PASS (warning) — isins_already_current=0
- expanded_candidate_written: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv
- expanded_rebuild_candidate_only: PASS (critical) — expanded rebuild candidate only
- network_download_not_performed: PASS (critical) — network_download_performed=False
- raw_acquisition_not_performed: PASS (critical) — raw_acquisition_performed=False
- raw_validation_not_performed: PASS (critical) — raw_validation_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- candidate_validation_not_performed: PASS (critical) — candidate_validation_performed=False
- expanded_validation_not_performed: PASS (critical) — expanded_validation_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- pre_hkex_current_candidate_dataset_not_modified: PASS (critical) — pre_hkex_current_candidate_dataset_modified=False
- current_validated_candidate_dataset_not_modified: PASS (critical) — current_validated_candidate_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Next actions

- Phigh `ASX` — run_asx_expanded_validation — v2.20H - ASX Expanded Validation
- Phigh `quality_target` — preserve_42k_45k_operational_band — v2.20H - ASX Expanded Validation
- Phigh `canonical` — defer_canonical_promotion_until_validation_pass — v2.20H - ASX Expanded Validation

## Guards

- Expanded rebuild candidate only: true
- New expanded candidate written: true
- Canonical dataset modified: false
- Current validated candidate dataset modified: false
- Active canonical replaced: false
- Expanded validation performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20H - ASX Expanded Validation`
