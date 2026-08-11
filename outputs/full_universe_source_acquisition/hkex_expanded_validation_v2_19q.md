# v2.19Q — HKEX Expanded Validation

Status: **HKEX_EXPANDED_VALIDATION_COMPLETED_41392_ROWS_VALIDATED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **expanded-validation-only**

Generated at UTC: `2026-08-11T21:34:24.453481+00:00`

## Executive summary

v2.19Q validates the HKEX expanded candidate dataset generated in v2.19P.

This phase validates the candidate dataset only. It does not promote the candidate to canonical, does not replace the active canonical dataset, does not modify the current validated candidate dataset, and does not run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Validation summary

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Expanded candidate rows: `41392`
- Appended HKEX tail rows: `396`
- Rows needed after rebuild: `8608`
- Final 50k candidate gate after validation: `BLOCKED`
- Expanded candidate SHA256: `3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c`
- Schema equal to current candidate: `True`
- Prefix matches current candidate: `True`
- Tail tickers match v2.19P appended audit: `True`
- Critical failed checks: `0`

## Rowcount validation

- `active_canonical_rows`: `38287` / expected `38287` — PASS
- `current_validated_candidate_rows`: `40996` / expected `40996` — PASS
- `expanded_candidate_rows`: `41392` / expected `41392` — PASS
- `appended_tail_rows`: `396` / expected `396` — PASS
- `appended_audit_rows`: `396` / expected `396` — PASS
- `rowcount_arithmetic`: `41392` / expected `41392` — PASS
- `rows_needed_after_rebuild`: `8608` / expected `8608` — PASS
- `final_50k_gate_after_validation`: `BLOCKED` / expected `BLOCKED` — PASS

## Schema validation

- `schema_equal_to_current_candidate`: `True` — PASS
- `current_header_count`: `33` — PASS
- `expanded_header_count`: `33` — PASS
- `ticker_header`: `ticker` — PASS
- `symbol_header`: `symbol` — PASS
- `company_name_header`: `company_name` — PASS
- `provider_header`: `provider` — PASS
- `exchange_header`: `exchange` — PASS
- `mic_header`: `mic` — PASS
- `source_phase_header`: `source_phase` — PASS

## Appended tail validation

- `prefix_matches_current_candidate`: `True` / expected `True` — PASS
- `tail_rows_count`: `396` / expected `396` — PASS
- `tail_tickers_match_appended_audit`: `True` / expected `True` — PASS
- `tail_nonempty_ticker_count`: `396` / expected `396` — PASS
- `tail_nonempty_name_count`: `396` / expected `396` — PASS
- `tail_provider_hkex_count`: `396` / expected `396` — PASS
- `tail_exchange_hkex_count`: `396` / expected `396` — PASS
- `tail_mic_xhkg_count`: `396` / expected `396` — PASS
- `tail_source_phase_v219p_count`: `396` / expected `396` — PASS
- `tail_currency_profile`: `3` / expected `documented` — PASS

## Duplicate validation

- `duplicate_appended_ticker_count`: `0` / expected `0` — PASS
- `duplicate_appended_symbol_count`: `0` / expected `0` — PASS
- `duplicate_appended_isin_count`: `109` / expected `documented` — PASS
- `appended_tickers_already_in_current_count`: `0` / expected `0` — PASS
- `appended_symbols_already_in_current_count`: `0` / expected `0` — PASS
- `appended_isins_already_in_current_count`: `0` / expected `documented` — PASS

## Next actions

- Phigh `HKEX` — write_hkex_closure_report — v2.19R - HKEX Closure Report
- Pmedium `50k` — select_next_provider_route_after_hkex — post-v2.19R route selection

## Checks

- v2_19p_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_expanded_rebuild_candidate_v2_19p.json
- v2_19p_status_expected: PASS (critical) — HKEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_41392_ROWS_EXPANDED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- expanded_candidate_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_hkex_v2_19p.csv
- expanded_candidate_sha_matches_v2_19p: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- expanded_candidate_rows_expected: PASS (critical) — expanded_candidate_rows=41392
- appended_tail_rows_expected: PASS (critical) — tail_rows=396
- appended_audit_rows_expected: PASS (critical) — appended_audit_rows=396
- rowcount_arithmetic_expected: PASS (critical) — 40996+396=41392
- rows_needed_after_rebuild_expected: PASS (critical) — rows_needed_after=8608
- final_50k_gate_after_validation_blocked: PASS (critical) — BLOCKED
- schema_equal_to_current_candidate: PASS (critical) — current_headers=33; expanded_headers=33
- prefix_matches_current_candidate: PASS (critical) — expanded prefix equals current candidate by digest
- tail_tickers_match_appended_audit: PASS (critical) — tail ticker order equals appended audit
- tail_all_tickers_present: PASS (critical) — tickers=396
- tail_all_names_present: PASS (critical) — names=396
- tail_provider_hkex_expected: PASS (critical) — HKEX provider rows=396
- tail_exchange_hkex_expected: PASS (critical) — HKEX exchange rows=396
- tail_mic_xhkg_expected: PASS (critical) — XHKG rows=396
- tail_source_phase_v219p_expected: PASS (critical) — v2.19P rows=396
- duplicate_appended_tickers_zero: PASS (critical) — duplicate_appended_tickers=0
- duplicate_appended_symbols_zero: PASS (critical) — duplicate_appended_symbols=0
- duplicate_appended_isins_documented: PASS (warning) — duplicate_appended_isins=109
- appended_tickers_not_in_current: PASS (critical) — appended_tickers_already_in_current=0
- appended_symbols_not_in_current: PASS (critical) — appended_symbols_already_in_current=0
- appended_isins_not_in_current: PASS (warning) — appended_isins_already_in_current=0
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- current_candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- expanded_validation_performed: PASS (critical) — expanded_validation_performed=True
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- current_candidate_dataset_not_modified: PASS (critical) — current_candidate_dataset_modified=False
- new_expanded_candidate_validated_only: PASS (critical) — no canonical promotion in this phase
- network_not_used_by_validation: PASS (critical) — network_download_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Guards

- Network download performed: false
- Expanded validation performed: true
- Expanded validation only: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `True`
- Expanded candidate dataset modified: false
- Active canonical replaced: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: `BLOCKED`
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`v2.19R - HKEX Closure Report`
