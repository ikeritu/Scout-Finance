# v2.14D3 - Deutsche Boerse Xetra Corrected Validation

Status: **DEUTSCHE_BOERSE_XETRA_CORRECTED_VALIDATION_NEEDS_MANUAL_REVIEW_FULL_SOURCE_STILL_BLOCKED**

Phase type: **validation-only-corrected**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `2026-07-09T12:25:47.207151+00:00`

## Decision

- Rebuild allowed by validation: **false**
- Recommended next phase: **v2.14D-review - Manual Review Before Rebuild**
- Full source unlocked: **false**
- Full 59k: **blocked**

## Corrected parser

- Source file: `outputs\full_universe_source_acquisition\raw\deutsche_boerse_xetra_v2_14c\datasets\001_downloads_en_t7-xetr-allTradableInstruments.csv`
- Member: `001_downloads_en_t7-xetr-allTradableInstruments.csv`
- Header line: 3
- Delimiter: `;`
- ISIN column: `ISIN`
- Mnemonic column: `Mnemonic`
- Instrument ID column: `Instrument ID`
- Group column: `Product Assignment Group`
- Type column: `Instrument Type`

## Counts

- Gross rows read: 5069
- Equity-like candidates: 0
- Excluded non-common-equity: 3635
- Manual review unknown type: 1434
- Equity-like diagnostic not found in baseline: 0
- Equity-like already in baseline by ISIN: 0
- Critical failed checks: 1
- Warning failed checks: 0

## Baseline

- Baseline path: `outputs\full_universe_source_acquisition\expanded_universe_v2_13e.csv`
- Baseline rows: 36863
- Baseline ISIN keys: 2748
- Baseline exchange+ticker keys: 36863

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

## Top Instrument Type values

- ETF: 3048
- CS: 1434
- ETN: 382
- ETC: 205

## Checks

- d2_header_diagnostic_exists: PASS (critical) — outputs\full_universe_source_acquisition\deutsche_boerse_xetra_header_diagnostic_v2_14d2.csv
- corrected_header_used: PASS (critical) — header_line=3
- gross_rows_found: PASS (critical) — gross_rows=5069
- isin_detected: PASS (critical) — isin_col=ISIN
- mnemonic_detected: PASS (critical) — mnemonic_col=Mnemonic
- instrument_type_detected: PASS (critical) — type_col=Instrument Type
- baseline_detected: PASS (critical) — baseline_path=outputs\full_universe_source_acquisition\expanded_universe_v2_13e.csv; baseline_rows=36863
- equity_like_candidates_found: FAIL (critical) — equity_like_candidates=0
- full_source_still_blocked: PASS (critical) — full_source_unlocked=False
- no_rebuild_performed: PASS (critical) — expanded_universe_rebuilt=False
- manual_review_unknown_low_enough_for_rebuild_review: PASS (warning) — unknown=1434; gross_rows=5069

## Guards

- Network download performed in v2.14D3: false
- Raw files downloaded in v2.14D3: false
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

This phase corrects the v2.14D header issue and produces validation diagnostics only. It does not create a new expanded source universe.
