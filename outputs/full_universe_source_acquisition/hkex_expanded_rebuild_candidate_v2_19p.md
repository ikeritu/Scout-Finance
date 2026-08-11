# v2.19P — HKEX Expanded Rebuild Candidate

Status: **HKEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_41392_ROWS_EXPANDED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **expanded-rebuild-candidate-only**

Generated at UTC: `2026-08-11T21:14:46.929834+00:00`

## Executive summary

v2.19P builds a new expanded candidate dataset by appending only HKEX net-new rows validated in v2.19O.

This phase writes a new candidate dataset only. It does not replace the active canonical dataset, does not modify the current validated candidate dataset, does not perform expanded validation, and does not run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Rebuild summary

- Current validated candidate rows: `40996`
- HKEX net-new rows appended: `396`
- Expanded candidate rows: `41392`
- Rows needed before rebuild: `9004`
- Rows needed after rebuild: `8608`
- Final 50k candidate gate after rebuild: `BLOCKED`
- Expanded candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_hkex_v2_19p.csv`
- Expanded candidate SHA256: `3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c`
- Critical failed checks: `0`

## Rowcount audit

- `active_canonical_rows`: `38287` — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- `current_validated_candidate_rows`: `40996` — outputs\full_universe_source_acquisition\expanded_universe_candidate_twse_tpex_v2_18g.csv
- `net_new_rows_input`: `396` — outputs\full_universe_source_acquisition\hkex_candidate_validation_against_canonical_dry_run_net_new_candidates_v2_19o.csv
- `expanded_candidate_rows`: `41392` — outputs\full_universe_source_acquisition\expanded_universe_candidate_hkex_v2_19p.csv
- `rows_needed_before_rebuild`: `9004` — current candidate vs 50k
- `rows_needed_after_rebuild`: `8608` — expanded candidate vs 50k
- `final_50k_gate_after_rebuild`: `BLOCKED` — expanded candidate projection
- `duplicate_appended_ticker_count`: `0` — 
- `duplicate_appended_isin_count`: `109` — HK0000051877,HK0000057395,HK0000071313,HK0000098449,HK0000123577,HK0000125598,HK0000127412,HK0000151925,HK0000151933,HK0000159977,HK0000172681,HK0000182987,HK0000221389,HK0000226149,HK0000248234,HK0000280989,HK0000286804,HK0000297652,HK0000297777,HK0000308293,HK0000313426,HK0000316767,HK0000366176,HK0000366184,HK0000422805,HK0000426384,HK0000433398,HK0000433414,HK0000473303,HK0000507407,HK0000515855,HK0000515871,HK0000516697,HK0000516713,HK0000562634,HK0000562659,HK0000562675,HK0000578549,HK0000591641,HK0000637832,HK0000637857,HK0000643327,HK0000651213,HK0000656956,HK0000701661,HK0000711199,HK0000723178,HK0000736758,HK0000761400,HK0000782851
- `appended_tickers_already_in_current_count`: `0` — 
- `appended_isins_already_in_current_count`: `0` — 
- `appended_instrument_families`: `3` — [["fund_or_etp", 361], ["equity_like", 21], ["reit", 14]]
- `appended_trading_currencies`: `3` — [["HKD", 247], ["USD", 89], ["RMB", 60]]

## Mapping audit

- `company_name` ← `name`: `396` rows
- `country` ← `constant:Hong Kong`: `396` rows
- `currency` ← `trading_currency`: `396` rows
- `exchange` ← `constant:HKEX`: `396` rows
- `isin` ← `isin`: `396` rows
- `mic` ← `constant:XHKG`: `396` rows
- `provider` ← `constant:HKEX`: `396` rows
- `raw_exchange` ← `constant:HKEX`: `396` rows
- `security_name` ← `name`: `396` rows
- `source_file` ← `source_file`: `396` rows
- `source_phase` ← `constant:v2.19P`: `396` rows
- `source_provider` ← `constant:HKEX`: `396` rows
- `symbol` ← `ticker`: `396` rows
- `ticker` ← `ticker`: `396` rows

## Next actions

- Phigh `HKEX` — run_expanded_validation — v2.19Q - HKEX Expanded Validation
- Phigh `50k` — preserve_50k_gate_blocked — v2.19Q - HKEX Expanded Validation

## Checks

- v2_19o_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_candidate_validation_against_canonical_dry_run_v2_19o.json
- v2_19o_status_expected: PASS (critical) — HKEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NET_NEW_CLASSIFIED_EXPANDED_REBUILD_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_19o_net_new_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_candidate_validation_against_canonical_dry_run_net_new_candidates_v2_19o.csv
- net_new_rows_expected: PASS (critical) — net_new_rows=396
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- expanded_candidate_rows_expected: PASS (critical) — expanded_candidate_rows=41392
- rowcount_arithmetic_expected: PASS (critical) — 40996+396=41392
- rows_needed_after_rebuild_expected: PASS (critical) — rows_needed_after=8608
- final_50k_gate_after_rebuild_blocked: PASS (critical) — BLOCKED
- current_headers_preserved: PASS (critical) — header_count=33
- appended_rows_written: PASS (critical) — appended_rows=396
- appended_full_audit_written: PASS (critical) — appended_full_rows=396
- duplicate_appended_tickers_zero: PASS (critical) — duplicate_appended_tickers=0
- duplicate_appended_isins_documented: PASS (warning) — duplicate_appended_isins=109
- appended_tickers_not_in_current: PASS (critical) — appended_tickers_already_in_current=0
- appended_isins_not_in_current: PASS (warning) — appended_isins_already_in_current=0
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- current_candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- new_expanded_candidate_written: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_hkex_v2_19p.csv
- expanded_dataset_is_new_candidate_only: PASS (critical) — active canonical not replaced
- network_not_used_by_rebuild: PASS (critical) — network_download_performed=False
- candidate_validation_against_canonical_not_performed: PASS (critical) — candidate_validation_against_canonical_performed=False
- expanded_rebuild_candidate_performed: PASS (critical) — expanded_rebuild_candidate_performed=True
- expanded_validation_not_performed: PASS (critical) — expanded_validation_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- current_candidate_dataset_not_modified: PASS (critical) — current_candidate_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Guards

- Network download performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: true
- Expanded rebuild candidate only: true
- Expanded validation performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: true
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

`v2.19Q - HKEX Expanded Validation`
