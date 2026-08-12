# v2.20H — ASX Expanded Validation

Status: **ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED**

Phase type: **expanded-validation-only**

Generated at UTC: `2026-08-12T10:42:18.962764+00:00`

## Executive summary

v2.20H validates the ASX-expanded candidate dataset created in v2.20G.

Validated candidate:

`outputs\full_universe_source_acquisition\expanded_universe_candidate_asx_v2_20g.csv`

The candidate contains **42,708** rows. It preserves the current validated candidate prefix of **41,392** rows and appends **1,316** validated ASX net-new rows.

The candidate crosses the operational floor of **42,000** and remains below the operational ceiling of **45,000**.

This phase validates the expanded candidate only. It does **not** promote canonical, does **not** rebuild again, does **not** run scoring, does **not** call OpenAI, does **not** call brokers, and does **not** launch full59k.

## Validation summary

- Active canonical rows: `38287`
- Current validated candidate rows: `41392`
- ASX appended rows: `1316`
- Expanded candidate rows: `42708`
- Row arithmetic: `41392+1316=42708`
- Quality floor crossed: `True`
- Quality ceiling not exceeded: `True`
- Rows above 42k floor: `708`
- Remaining capacity to 45k ceiling: `2292`
- Rows to 50k aspirational after rebuild: `7292`
- Schema column count: `33`
- Schema preserved: `True`
- Current prefix preserved: `True`
- Appended tail matches appended rows: `True`
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

- v2_20g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_expanded_rebuild_candidate_v2_20g.json
- v2_20g_status_expected: PASS (critical) — ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED
- v2_20g_next_phase_expected: PASS (critical) — v2.20H - ASX Expanded Validation
- v2_20g_expanded_rows_expected: PASS (critical) — v2_20g_expanded_rows=42708
- v2_20g_appended_rows_expected: PASS (critical) — v2_20g_appended_rows=1316
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- pre_hkex_current_candidate_rows_expected: PASS (critical) — pre_hkex_rows=40996
- current_validated_candidate_rows_expected: PASS (critical) — current_validated_rows=41392
- expanded_candidate_rows_expected: PASS (critical) — expanded_rows=42708
- appended_rows_expected: PASS (critical) — appended_rows=1316
- appended_audit_rows_expected: PASS (critical) — appended_audit_rows=1316
- row_arithmetic_expected: PASS (critical) — 41392+1316=42708
- active_canonical_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- pre_hkex_current_candidate_sha_expected: PASS (critical) — 05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2
- current_validated_candidate_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- expanded_candidate_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- appended_rows_sha_expected: PASS (critical) — 48cdcc8b28740421740ef6e14c830b37c1efcf03802fc2740f5555d891e23da4
- active_canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- pre_hkex_current_candidate_sha_unchanged: PASS (critical) — pre-HKEX current candidate sha unchanged
- current_validated_candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- expanded_candidate_sha_unchanged: PASS (critical) — expanded candidate sha unchanged during validation
- appended_rows_sha_unchanged: PASS (critical) — appended rows sha unchanged during validation
- schema_column_count_expected: PASS (critical) — expanded_columns=33
- schema_preserved_vs_current: PASS (critical) — schema_preserved=True
- appended_schema_preserved_vs_current: PASS (critical) — appended_schema_preserved=True
- current_prefix_preserved: PASS (critical) — prefix_matches_current=True
- appended_tail_matches_appended_rows: PASS (critical) — tail_matches_appended_rows=True
- quality_floor_crossed: PASS (critical) — expanded_rows=42708;floor=42000
- quality_ceiling_not_exceeded: PASS (critical) — expanded_rows=42708;ceiling=45000
- rows_above_quality_floor_expected: PASS (critical) — rows_above_floor=708
- remaining_capacity_to_quality_ceiling_expected: PASS (critical) — capacity_to_ceiling=2292
- rows_to_aspirational_50k_expected: PASS (warning) — rows_to_50k=7292
- duplicate_appended_tickers_zero: PASS (critical) — duplicate_appended_tickers=0
- duplicate_appended_symbols_zero: PASS (critical) — duplicate_appended_symbols=0
- duplicate_appended_isins_zero: PASS (warning) — duplicate_appended_isins=0
- appended_tickers_not_in_current: PASS (critical) — tickers_already_current=0
- appended_symbols_not_in_current: PASS (critical) — symbols_already_current=0
- appended_isins_not_in_current: PASS (warning) — isins_already_current=0
- appended_required_ticker_non_empty: PASS (critical) — ticker_non_empty=True
- appended_required_name_non_empty: PASS (critical) — name_non_empty=True
- appended_required_isin_non_empty: PASS (warning) — isin_non_empty=True
- appended_tickers_ax_suffix: PASS (critical) — tickers_ax_suffix=True
- appended_all_exchange_asx: PASS (critical) — {'ASX': 1316}
- appended_all_country_australia: PASS (critical) — {'Australia': 1316}
- appended_all_provider_asx: PASS (critical) — {'ASX': 1316}
- appended_all_currency_aud: PASS (critical) — {'AUD': 1316}
- appended_all_mic_xasx: PASS (critical) — {'XASX': 1316}
- appended_all_source_phase_v220g: PASS (critical) — {'v2.20G': 1316}
- appended_all_merge_action_append_net_new: PASS (critical) — {'append_net_new': 1316}
- appended_instrument_types_allowed: PASS (critical) — {'equity': 1211, 'reit': 12, 'equity_like': 86, 'listed_investment_vehicle': 7}
- appended_instrument_scopes_allowed: PASS (critical) — {'ordinary_equity': 1211, 'a_reit_equity_like': 12, 'ordinary_or_equity_like_unclassified': 86, 'listed_investment_vehicle_conditional': 7}
- expanded_validation_only: PASS (critical) — expanded validation only
- network_download_not_performed: PASS (critical) — network_download_performed=False
- raw_acquisition_not_performed: PASS (critical) — raw_acquisition_performed=False
- raw_validation_not_performed: PASS (critical) — raw_validation_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- candidate_validation_not_performed: PASS (critical) — candidate_validation_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- pre_hkex_current_candidate_dataset_not_modified: PASS (critical) — pre_hkex_current_candidate_dataset_modified=False
- current_validated_candidate_dataset_not_modified: PASS (critical) — current_validated_candidate_dataset_modified=False
- expanded_candidate_dataset_not_modified: PASS (critical) — expanded_candidate_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Next actions

- Phigh `ASX` — prepare_asx_closure_report — v2.20I - ASX Closure Report
- Phigh `canonical` — keep_canonical_unchanged_until_explicit_promotion — v2.20I - ASX Closure Report
- Phigh `quality_target` — record_quality_first_target_achieved — v2.20I - ASX Closure Report

## Guards

- Expanded validation only: true
- Canonical dataset modified: false
- Current validated candidate dataset modified: false
- Expanded candidate dataset modified: false
- Active canonical replaced: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20I - ASX Closure Report`
