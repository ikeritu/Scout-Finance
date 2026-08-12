# v2.20F — ASX Candidate Validation Against Current Candidate Dry Run

Status: **ASX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NET_NEW_READY_REBUILD_CANDIDATE_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED**

Phase type: **candidate-validation-against-current-dry-run-only**

Generated at UTC: `2026-08-12T09:41:18.015038+00:00`

## Executive summary

v2.20F validates the ASX included extraction rows against the current validated candidate dataset.

Comparison dataset:

`outputs\full_universe_source_acquisition\expanded_universe_candidate_hkex_v2_19p.csv`

This phase decides which ASX rows are internal duplicates, current-candidate duplicates, review rows, or clean net-new candidates.

This phase performs candidate validation dry run only. It does **not** append rows, does **not** rebuild an expanded candidate, does **not** promote canonical, and does **not** run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

Only rows with `validation_decision=net_new_candidate` are eligible for v2.20G rebuild consideration.

## Validation summary

- Current validated candidate rows: `41392`
- ASX included rows input: `1921`
- ASX deduped rows validated: `1920`
- Internal duplicate rows dropped: `1`
- Duplicate-current rows: `567`
- Review rows: `37`
- Net-new candidate rows: `1316`
- Rows needed to 42k: `608`
- Rows needed to 45k: `3608`
- Net-new covers quality floor gap: `True`
- Post-ASX dry-run rows if all net-new rebuilt: `42708`
- Would exceed 45k ceiling if all net-new rebuilt: `False`
- Critical failed checks: `0`
- Warning failed checks: `0`
- full59k: `DEPRECATED_DEFERRED`

## Validation decisions

- `duplicate_current`: `567`
- `internal_duplicate_dropped`: `1`
- `net_new_candidate`: `1316`
- `review_name_match_only`: `37`

## Match types

- `internal_duplicate`: `1`
- `isin`: `2`
- `name_only`: `37`
- `no_current_match`: `1316`
- `ticker`: `564`
- `ticker+isin`: `1`

## Net-new scope summary

- `a_reit_equity_like`: `12`
- `listed_investment_vehicle_conditional`: `7`
- `ordinary_equity`: `1211`
- `ordinary_or_equity_like_unclassified`: `86`

## Checks

- v2_20e_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\asx_candidate_extraction_dry_run_v2_20e.json
- v2_20e_status_expected: PASS (critical) — ASX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_EXTRACTED_VALIDATION_DRY_RUN_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED
- v2_20e_next_phase_expected: PASS (critical) — v2.20F - ASX Candidate Validation Against Current Candidate Dry Run
- v2_20e_included_rows_expected: PASS (critical) — report=1921;csv=1921
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- pre_hkex_current_candidate_rows_expected: PASS (critical) — pre_hkex_rows=40996
- current_validated_candidate_rows_expected: PASS (critical) — current_validated_rows=41392
- active_canonical_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- pre_hkex_current_candidate_sha_expected: PASS (critical) — 05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2
- current_validated_candidate_sha_expected: PASS (critical) — 3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c
- active_canonical_sha_unchanged: PASS (critical) — active canonical sha unchanged
- pre_hkex_current_candidate_sha_unchanged: PASS (critical) — pre-HKEX current candidate sha unchanged
- current_validated_candidate_sha_unchanged: PASS (critical) — current validated candidate sha unchanged
- quality_floor_target_preserved: PASS (critical) — quality_floor=42000
- quality_ceiling_target_preserved: PASS (critical) — quality_ceiling=45000
- rows_needed_to_quality_floor_expected: PASS (critical) — rows_needed_to_42k=608
- rows_needed_to_quality_ceiling_expected: PASS (critical) — rows_needed_to_45k=3608
- rows_needed_to_50k_aspirational_expected: PASS (warning) — rows_needed_to_50k=8608
- current_candidate_index_loaded: PASS (critical) — current_rows=41392
- current_ticker_index_non_empty: PASS (critical) — ticker_keys=41598
- current_isin_index_non_empty: PASS (warning) — isin_keys=6437
- asx_included_rows_loaded: PASS (critical) — asx_included_rows=1921
- internal_duplicates_documented: PASS (warning) — internal_duplicate_rows=1
- validated_rows_accounting: PASS (critical) — validated=1921;input=1921
- net_new_rows_non_empty: PASS (critical) — net_new_rows=1316
- net_new_rows_cover_quality_floor_gap: PASS (warning) — net_new=1316;needed_to_42k=608
- duplicate_current_rows_documented: PASS (warning) — duplicate_current_rows=567
- review_rows_documented: PASS (warning) — review_rows=37
- would_not_exceed_quality_ceiling_if_rebuilt_all_net_new: PASS (warning) — post_rows=42708;ceiling=45000
- candidate_validation_dry_run_only: PASS (critical) — candidate validation against current dry run only
- network_download_not_performed: PASS (critical) — network_download_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_candidate_performed=False
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

- Phigh `ASX` — append_all_clean_net_new_rows_in_rebuild_candidate — v2.20G - ASX Expanded Rebuild Candidate
- Phigh `ASX_duplicates` — exclude_current_duplicates_and_internal_duplicates — v2.20G - ASX Expanded Rebuild Candidate
- Phigh `quality_target` — preserve_42k_45k_operational_band — v2.20G - ASX Expanded Rebuild Candidate

## Guards

- Candidate validation against current dry run only: true
- Network download performed: false
- Candidate extraction performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current validated candidate dataset modified: false
- Active canonical replaced: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`v2.20G - ASX Expanded Rebuild Candidate`
