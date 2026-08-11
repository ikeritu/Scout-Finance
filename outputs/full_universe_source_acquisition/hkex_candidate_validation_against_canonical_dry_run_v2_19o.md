# v2.19O — HKEX Candidate Validation Against Canonical Dry Run

Status: **HKEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NET_NEW_CLASSIFIED_EXPANDED_REBUILD_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **candidate-validation-against-canonical-dry-run-only**

Generated at UTC: `2026-08-11T21:02:51.072314+00:00`

## Executive summary

v2.19O validates HKEX v2.19N dry-run candidates against the active canonical dataset and the current validated candidate dataset.

This phase performs candidate validation against canonical as a dry run only. It does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `38287`
- Current validated candidate rows: `40996`
- Final target candidates: `50000`
- Rows needed to 50k: `9004`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

- `hkex_candidate_rows_input`: `17630` — v2.19N dry-run candidates
- `potential_scope_rows`: `3180` — potential_candidate_pending_canonical_validation
- `reference_scope_rows`: `14450` — excluded before canonical match
- `net_new_pending_expanded_rebuild`: `396` — eligible HKEX candidates not matched to active/current indexes
- `duplicate_existing_universe`: `2782` — hard duplicates by ticker/code/ISIN
- `possible_duplicate_name_review`: `2` — name-only possible duplicates
- `excluded_before_canonical_match`: `14450` — reference/non-candidate scope
- `duplicate_match_rows`: `16528` — all recorded match signals
- `net_new_equity_like_count`: `21` — net new equity-like rows
- `net_new_fund_or_etp_count`: `361` — net new fund/ETP rows
- `net_new_reit_count`: `14` — net new REIT rows
- `net_new_spac_count`: `0` — net new SPAC rows
- `current_validated_candidate_rows`: `40996` — unchanged current validated candidate universe
- `projected_candidate_rows_if_rebuilt`: `41392` — dry-run projection only
- `projected_rows_needed_to_50k`: `8608` — dry-run projection only
- `projected_50k_gate_after_hkex`: `BLOCKED` — dry-run projection only

## Dataset indexes

- `active_canonical`: rows `38287`, tickers `37853`, ISINs `4172`, names `24687`, HKEX codes `2804`
- `current_validated_candidate`: rows `40996`, tickers `41204`, ISINs `6185`, names `26693`, HKEX codes `2804`

## Instrument validation summary

- `debt_security` / `excluded_before_canonical_match`: `1330`
- `derivative_or_warrant` / `excluded_before_canonical_match`: `13081`
- `equity_like` / `duplicate_existing_universe`: `2780`
- `equity_like` / `net_new_pending_expanded_rebuild`: `21`
- `equity_like` / `possible_duplicate_name_review`: `2`
- `fund_or_etp` / `net_new_pending_expanded_rebuild`: `361`
- `other_or_unclassified` / `excluded_before_canonical_match`: `39`
- `reit` / `net_new_pending_expanded_rebuild`: `14`
- `spac` / `duplicate_existing_universe`: `2`

## Next actions

- Phigh `HKEX` — run_expanded_rebuild_candidate — v2.19P - HKEX Expanded Rebuild Candidate
- Phigh `HKEX` — include_net_new_only — v2.19P - HKEX Expanded Rebuild Candidate
- Phigh `50k` — recalculate_projected_gate_after_rebuild — v2.19P - HKEX Expanded Rebuild Candidate

## Checks

- v2_19n_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_candidate_extraction_dry_run_v2_19n.json
- v2_19n_status_expected: PASS (critical) — HKEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_EXTRACTED_CANONICAL_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED
- v2_19n_candidates_exists: PASS (critical) — outputs\full_universe_source_acquisition\hkex_candidate_extraction_dry_run_candidates_v2_19n.csv
- v2_19n_candidate_rows_expected: PASS (critical) — hkex_candidates=17630
- v2_19n_potential_scope_expected: PASS (critical) — potential_scope_rows=3180
- v2_19n_reference_scope_expected: PASS (warning) — reference_scope_rows=14450
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- current_validated_candidate_rows_expected: PASS (critical) — current_candidate_rows=40996
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9004
- canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- active_dataset_index_built: PASS (critical) — active_index_rows=38287
- current_dataset_index_built: PASS (critical) — current_index_rows=40996
- validated_rows_equal_input: PASS (critical) — validated_rows=17630; input=17630
- scope_accounting_balanced: PASS (critical) — 3180+14450=17630
- status_accounting_balanced: PASS (critical) — status_total=17630
- net_new_count_documented: PASS (critical) — net_new_count=396
- duplicate_count_documented: PASS (warning) — duplicate_existing_count=2782
- possible_name_duplicate_count_documented: PASS (warning) — possible_name_duplicate_count=2
- projected_candidate_rows_documented: PASS (critical) — projected=41392
- final_50k_gate_still_blocked_current: PASS (critical) — 40996 < 50000
- network_not_used_by_validation: PASS (critical) — network_download_performed=False
- candidate_validation_against_canonical_performed: PASS (critical) — candidate_validation_against_canonical_performed=True
- candidate_validation_dry_run_only: PASS (critical) — dry_run_only=True
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
- expanded_validation_not_performed: PASS (critical) — expanded_validation_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- current_candidate_dataset_not_modified: PASS (critical) — current_candidate_dataset_modified=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Guards

- Network download performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: true
- Candidate validation dry run only: true
- Canonical comparison performed: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `True`
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Active canonical replaced: false
- New expanded dataset written: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Current final 50k candidate gate: BLOCKED
- Projected 50k gate after HKEX: `BLOCKED`
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`v2.19P - HKEX Expanded Rebuild Candidate`
