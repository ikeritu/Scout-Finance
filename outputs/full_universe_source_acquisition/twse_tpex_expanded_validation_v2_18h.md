# v2.18H - TWSE + TPEx Expanded Validation

Status: **TWSE_TPEX_EXPANDED_VALIDATION_COMPLETED_40996_ROWS_VALIDATED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **expanded-candidate-validation-only**

Generated at UTC: `2026-08-11T14:34:34.467303+00:00`

## Executive summary

v2.18H validates the TWSE + TPEx expanded candidate generated in v2.18G.

This phase is validation-only. It does not rebuild the candidate, does not replace the active canonical dataset, does not modify canonical, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Base candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv`
- Base candidate rows: `40300`
- Expanded candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv`
- Expanded candidate rows: `40996`
- Added rows: `696`
- Withheld rows: `0`
- Row increment: `696`
- Schema columns: `33`
- Final target candidates: `50000`
- Projected rows needed after TWSE: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

- Base rows: `40300`
- Expanded rows: `40996`
- Added rows: `696`
- Withheld rows: `0`
- Row increment: `696`
- Potential net-new symbols: `696`
- Possible existing symbols not added: `379`
- Existing symbols not added: `0`
- Added ticker duplicate count: `0`
- Added symbol duplicate count: `0`
- Added ticker conflicts with base: `0`
- Added symbol conflicts with base: `0`
- Critical failed checks: `0`

## Checks

- v2_18g_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_expanded_rebuild_candidate_v2_18g.json
- v2_18g_status_expected: PASS (critical) — TWSE_TPEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_40996_ROWS_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- active_canonical_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- base_candidate_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- expanded_candidate_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv
- v2_18g_added_rows_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_expanded_rebuild_added_rows_v2_18g.csv
- v2_18g_withheld_rows_exists: PASS (critical) — outputs\full_universe_source_acquisition\twse_tpex_expanded_rebuild_withheld_rows_v2_18g.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- base_rows_expected: PASS (critical) — base_rows=40300
- expanded_rows_expected: PASS (critical) — expanded_rows=40996
- added_rows_expected: PASS (critical) — added_rows=696
- withheld_rows_expected: PASS (critical) — withheld_rows=0
- row_increment_expected: PASS (critical) — row_increment=696
- schema_equal_base_expanded: PASS (critical) — base header equals expanded header
- schema_equal_base_added: PASS (critical) — base header equals added header
- schema_columns_33: PASS (critical) — schema_columns=33
- base_prefix_unchanged_in_expanded: PASS (critical) — first_mismatches=[]
- added_rows_are_expanded_suffix: PASS (critical) — first_mismatches=[]
- potential_net_new_symbols_expected: PASS (critical) — potential_net_new_symbols=696
- possible_existing_symbols_expected: PASS (critical) — possible_existing_symbols=379
- existing_symbols_expected: PASS (critical) — existing_symbols=0
- added_symbols_match_potential_net_new: PASS (critical) — added_not_potential=0 potential_not_added=0
- possible_existing_not_added: PASS (critical) — possible_existing_in_added=0
- existing_not_added: PASS (critical) — existing_in_added=0
- added_tickers_unique: PASS (critical) — added_ticker_duplicate_count=0
- added_symbols_unique: PASS (critical) — added_symbol_duplicate_count=0
- added_tickers_no_base_conflict: PASS (critical) — added_ticker_conflicts_with_base=0
- added_symbols_no_base_conflict: PASS (critical) — added_symbol_conflicts_with_base=0
- added_tickers_tw_suffix: PASS (critical) — non_tw_tickers=0
- added_exchange_twse: PASS (critical) — non_twse_exchange=0
- added_country_taiwan: PASS (critical) — non_taiwan_country=0
- added_provider_twse: PASS (critical) — non_twse_provider=0
- added_instrument_type_equity: PASS (critical) — non_equity_instrument_type=0
- added_instrument_scope_common_equity: PASS (critical) — non_common_equity_scope=0
- added_source_phase_v2_18g: PASS (critical) — wrong_source_phase=0
- added_required_columns_non_blank: PASS (critical) — {"classification_confidence": 0, "classification_reason": 0, "company_name": 0, "country": 0, "currency": 0, "exchange": 0, "instrument_scope": 0, "instrument_type": 0, "mic": 0, "provider": 0, "security_name": 0, "source_phase": 0, "source_provider": 0, "symbol": 0, "ticker": 0}
- projected_rows_needed_after_twse_expected: PASS (critical) — projected_rows_needed_after_twse=9004
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- base_candidate_sha_unchanged: PASS (critical) — base candidate sha unchanged
- expanded_candidate_sha_unchanged_during_validation: PASS (critical) — expanded candidate sha unchanged during validation
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- network_not_used: PASS (critical) — network_download_performed=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False
- final_50k_gate_still_blocked: PASS (critical) — 40996 < 50000

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: true
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Existing expanded candidate read only: true
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`v2.18I - TWSE + TPEx Closure Report`
