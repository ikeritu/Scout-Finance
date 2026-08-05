# v2.16F - TMX Candidate Validation Against Canonical Dry Run

Status: **TMX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_REBUILD_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED**

Phase type: **candidate-validation-against-canonical-dry-run-only**

Generated at UTC: `2026-08-05T15:01:33.434993+00:00`

## Current state

- Canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Validation summary

- v2.16E status: `TMX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED`
- v2.16E recommended next phase: `v2.16F - TMX Candidate Validation Against Canonical Dry Run`
- Canonical rows: `38287`
- Candidate rows: `13`
- Validation rows: `13`
- Canonical symbol column: `ticker`
- Canonical exchange column: `exchange`
- Canonical name column: `company_name`
- Canonical ISIN column: `isin`
- Recommended for rebuild candidate: `1`
- Duplicate exact symbol/exchange: `0`
- Possible duplicate symbol review: `1`
- Low evidence review: `11`
- Rejected count: `0`
- Status counts: `{'net_new_candidate_low_evidence_review': 11, 'possible_duplicate_symbol_review': 1, 'net_new_candidate_high_confidence_dry_run': 1}`
- Decision counts: `{'manual_review_required': 11, 'review_duplicate': 1, 'review_net_new_candidate': 1}`
- Source counts: `{'tmx_listed_company_directory': 1, 'tmx_money_recent_listings': 12}`
- Confidence counts: `{'low': 12, 'high': 1}`
- Critical failed checks: `0`

## Validation rows

- `SYMBOL` `Company Name` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `ALCH` `Alchemy Labs Inc.` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `AMAP` `Amapá Minerals Holdings Inc.` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `ATOI` `Asiatel Outsourcing Inc.` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `BUSH.P` `Bushido Capital Corp.` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `CADY` `Cadillac Mines Corporation` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `AKT` `Akita Drilling Ltd.` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `FSTV.P` `Falconstar Ventures Inc.` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `INXS` `Goldinxs Mining Corp.` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `NICE` `Ni-Co Energy Inc.` exchange=`` status=`possible_duplicate_symbol_review` decision=`review_duplicate` rebuild=False reason=`symbol_already_present_any_exchange`
- `OCAL` `OCAL Financial Inc.` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `PCA` `Phoenix Metals Corp.` exchange=`` status=`net_new_candidate_low_evidence_review` decision=`manual_review_required` rebuild=False reason=`symbol_absent_but_exchange_missing`
- `IRR` `Irruptive Metals Corp.` exchange=`TSXV` status=`net_new_candidate_high_confidence_dry_run` decision=`review_net_new_candidate` rebuild=True reason=`symbol_absent_from_canonical_high_confidence`

## Checks

- v2_16e_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_candidate_extraction_dry_run_v2_16e.json
- v2_16e_candidates_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_candidate_extraction_candidates_v2_16e.csv
- v2_16e_status_valid: PASS (critical) — TMX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED
- v2_16e_recommended_f: PASS (critical) — v2.16F - TMX Candidate Validation Against Canonical Dry Run
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- canonical_dataset_rows_expected: PASS (critical) — canonical_rows=38287 expected=38287
- canonical_symbol_column_detected: PASS (critical) — symbol_col=ticker
- candidate_rows_loaded: PASS (critical) — candidate_rows=13
- validation_rows_generated: PASS (critical) — validation_rows=13 candidates=13
- canonical_dataset_read_only: PASS (critical) — canonical_dataset_modified=False
- canonical_comparison_performed: PASS (critical) — canonical_comparison_performed=True
- net_new_dry_run_classification_performed: PASS (critical) — net_new_dry_run_classification_performed=True
- net_new_filtering_not_applied: PASS (critical) — net_new_filtering_applied=False
- expanded_universe_not_rebuilt: PASS (critical) — expanded_universe_rebuilt=False
- network_not_used: PASS (critical) — network_download_performed=False
- endpoint_calls_not_performed: PASS (critical) — endpoint_calls_performed=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- recommended_rebuild_candidates_review: PASS (warning) — recommended_count=1
- duplicates_review: PASS (warning) — duplicate_exact=0; duplicate_symbol_review=1
- low_evidence_review: PASS (warning) — low_evidence=11
- full_source_still_blocked: PASS (critical) — 38287 < 50000

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Candidate rows read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Canonical comparison performed: true
- Net-new dry-run classification performed: true
- Net-new filtering applied: false
- Expanded universe rebuilt: false
- New expanded dataset written: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX candidate validation against canonical completed as a dry run.

This phase reads the v2.16E candidate file and the current canonical expanded universe, classifies candidate overlap against the canonical symbol/exchange universe, and identifies whether any candidate should proceed to a rebuild-candidate phase. It does not modify the canonical dataset, does not write a new expanded universe, does not apply net-new filtering to the canonical dataset and does not rebuild.

## Recommended next phase

`v2.16G - TMX Expanded Rebuild Candidate`
