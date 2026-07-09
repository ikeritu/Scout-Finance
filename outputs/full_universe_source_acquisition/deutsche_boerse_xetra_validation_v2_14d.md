# v2.14D - Deutsche Boerse Xetra Validation

Status: **DEUTSCHE_BOERSE_XETRA_VALIDATION_NEEDS_MANUAL_REVIEW_FULL_SOURCE_STILL_BLOCKED**

Phase type: **validation-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `2026-07-09T11:53:57.093677+00:00`

## Decision

- Rebuild allowed by validation: **false**
- Recommended next phase: **v2.14D-review - Manual Review Before Rebuild**
- Full source unlocked: **false**
- Full 59k: **blocked**

## Baseline

- Baseline path: `outputs\full_universe_source_acquisition\expanded_universe_v2_13e.csv`
- Baseline rows: 36863
- Baseline ISIN keys: 2748
- Baseline exchange+ticker keys: 36863

## Counts

- Dataset candidates from manifest: 2
- Structured payloads parsed for validation: 11
- Gross structured rows read: 212014
- Equity-like candidates: 0
- Excluded non-common-equity / non-share: 12
- Manual review unknown type: 212002
- Diagnostic not found in baseline: 200900
- Already in baseline by ISIN: 307
- Already in baseline by exchange+ticker: 0
- Critical failed checks: 1
- Warning failed checks: 0

## Checks

- v2_14c_manifest_exists: PASS (critical) — outputs\full_universe_source_acquisition\deutsche_boerse_xetra_download_manifest_v2_14c.json
- dataset_candidates_downloaded: PASS (critical) — dataset_candidate_manifest=2
- structured_payloads_parsed: PASS (critical) — parse_successes=11
- structured_rows_found: PASS (critical) — structured_rows=212014
- baseline_detected: PASS (critical) — baseline_path=outputs\full_universe_source_acquisition\expanded_universe_v2_13e.csv; baseline_rows=36863
- equity_like_candidates_found: FAIL (critical) — equity_like_candidates=0
- full_source_still_blocked: PASS (critical) — full_source_unlocked=False
- no_rebuild_performed: PASS (critical) — expanded_universe_rebuilt=False
- non_equity_filter_needed: PASS (warning) — non_equity=12; unknown=212002

## Dataset projection

- `001_downloads_en_t7-xetr-allTradableInstruments.csv` rows=5071 equity_like=0 excluded=0 unknown=5071 diagnostic_not_found=0
- `20260709_orderProfiles.csv` rows=33 equity_like=0 excluded=0 unknown=33 diagnostic_not_found=0
- `20260709_orderProfileAssignment.csv` rows=167277 equity_like=0 excluded=0 unknown=167277 diagnostic_not_found=166980
- `20260709_tradingSchedule.csv` rows=383 equity_like=0 excluded=0 unknown=383 diagnostic_not_found=0
- `20260709_tradingScheduleAssignment.csv` rows=5069 equity_like=0 excluded=0 unknown=5069 diagnostic_not_found=0
- `20260709_marketSegment.csv` rows=148 equity_like=0 excluded=0 unknown=148 diagnostic_not_found=0
- `20260709_TESProfiles.csv` rows=14226 equity_like=0 excluded=0 unknown=14226 diagnostic_not_found=14226
- `20260709_securitySubType.csv` rows=12 equity_like=0 excluded=12 unknown=0 diagnostic_not_found=0
- `20260709_SRQSRespondentAssignment.csv` rows=14635 equity_like=0 excluded=0 unknown=14635 diagnostic_not_found=14634
- `20260709_SRQSparameters.csv` rows=5069 equity_like=0 excluded=0 unknown=5069 diagnostic_not_found=5060
- `20260709_volatilityCorridorTables.csv` rows=91 equity_like=0 excluded=0 unknown=91 diagnostic_not_found=0

## Guards

- Network download performed in v2.14D: false
- Raw files downloaded in v2.14D: false
- Raw files modified after write: false
- Workbook/CSV parsed for validation: true
- Normalization performed: false
- Final net-new filtering finalized: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase produces validation diagnostics only. It does not create a new expanded source universe.
