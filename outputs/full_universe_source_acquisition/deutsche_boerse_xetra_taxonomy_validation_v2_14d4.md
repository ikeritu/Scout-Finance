# v2.14D4 - Deutsche Boerse Xetra Taxonomy-Corrected Validation

Status: **DEUTSCHE_BOERSE_XETRA_TAXONOMY_VALIDATION_PASSED_FOR_REBUILD_REVIEW_FULL_SOURCE_STILL_BLOCKED**

Phase type: **validation-only-taxonomy-corrected**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `2026-07-09T13:41:37.491219+00:00`

## Decision

- Rebuild allowed by validation: **true**
- Recommended next phase: **v2.14E - Deutsche Boerse Xetra Expanded Source Rebuild**
- Full source unlocked: **false**
- Full 59k: **blocked**

## Taxonomy decision

Only `Instrument Type = CS` is accepted as equity-like candidate in v2.14D4.

ETF, ETN, ETC, ETP, funds, bonds, warrants, certificates, rights, futures and options remain excluded.

## Counts

- Gross rows read: 5069
- Rows with ISIN: 5069
- Rows with mnemonic: 5066
- Rows with instrument ID: 5069
- Equity-like candidates: 1434
- Excluded non-common-equity: 3635
- Manual review unknown type: 0
- Equity-like diagnostic not found in baseline: 1425
- Equity-like already in baseline by ISIN: 9
- Projected rows after rebuild if approved: 38288
- Rows needed after projected rebuild: 11712
- Source-to-50k after projected rebuild: 76.6%
- Critical failed checks: 0
- Warning failed checks: 0

## Top Instrument Type values

- ETF: 3048
- CS: 1434
- ETN: 382
- ETC: 205

## Top Product Assignment Group Description values

- FON0: 1158
- NAM0: 714
- FONA: 695
- FON1: 597
- FON2: 457
- ETN0: 381
- GER0: 255
- ETC1: 206
- FDL0: 80
- SDX1: 73
- LUX0: 64
- UKI0: 60
- MDX1: 53
- FRA0: 52
- DAX1: 43
- FDLA: 42
- SWI0: 30
- SKA0: 30
- ITA0: 23
- AST0: 18

## Baseline

- Baseline path: `outputs\full_universe_source_acquisition\expanded_universe_v2_13e.csv`
- Baseline rows: 36863
- Baseline ISIN keys: 2748
- Baseline exchange+ticker keys: 36863

## Checks

- d2_header_diagnostic_exists: PASS (critical) — outputs\full_universe_source_acquisition\deutsche_boerse_xetra_header_diagnostic_v2_14d2.csv
- corrected_header_used: PASS (critical) — header_line=3
- gross_rows_found: PASS (critical) — gross_rows=5069
- isin_detected: PASS (critical) — rows_with_isin=5069
- mnemonic_detected: PASS (critical) — rows_with_mnemonic=5066
- instrument_type_detected: PASS (critical) — type_col=Instrument Type
- baseline_detected: PASS (critical) — baseline_path=outputs\full_universe_source_acquisition\expanded_universe_v2_13e.csv; baseline_rows=36863
- cs_taxonomy_detected: PASS (critical) — CS_count=1434
- equity_like_candidates_found: PASS (critical) — equity_like_candidates=1434
- equity_like_net_new_found: PASS (critical) — equity_like_diagnostic_not_found_in_baseline=1425
- non_common_equity_excluded: PASS (critical) — excluded_non_common_equity=3635
- full_source_still_blocked: PASS (critical) — full_source_unlocked=False
- no_rebuild_performed: PASS (critical) — expanded_universe_rebuilt=False
- unknown_rows_zero_or_reviewable: PASS (warning) — unknown=0

## Guards

- Network download performed in v2.14D4: false
- Raw files downloaded in v2.14D4: false
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

This phase validates taxonomy and projection only. It does not create a new expanded source universe.
