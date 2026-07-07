# v2.11D — Cboe Europe Validation

Status: **CBOE_EUROPE_VALIDATION_COMPLETED**

Phase type: **validation-only**

Generated at UTC: `2026-07-07T23:46:24.984663+00:00`

## Hard guards

- Network download performed: false
- Raw files modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Inputs

- Raw directory: `outputs\full_universe_source_acquisition\raw\cboe_europe_v2_11c`
- Manifest: `outputs\full_universe_source_acquisition\cboe_europe_download_manifest_v2_11c.csv`
- Discovered links: `outputs\full_universe_source_acquisition\cboe_europe_discovered_links_v2_11c.csv`
- Baseline universe detected: `data\raw\expanded_universe\expanded_universe_v2_8e.csv`

## CSV validation summary

- Manifest rows: 21
- Discovered links: 16
- CSV files profiled: 16
- Parsed CSV files: 16
- Total CSV rows excluding headers, all CSVs: 89651
- Large CSV rows excluding headers, files >=100KB: 88243
- Tiny files <1KB: 2
- Small files <10KB: 7

## Header capability summary

- Files with symbol-like header: 6
- Files with name-like header: 6
- Files with MIC/venue-like header: 6

## Diagnostic baseline comparison

This is diagnostic only. No accepted net-new filtering or rebuild was performed.

- Baseline tickers loaded: 8920
- Candidate unique symbols: 21288
- Candidate symbol overlap: 133
- Candidate symbols not in baseline: 21155

## Threshold review

- Current expanded rows: 9200
- Rows needed first expansion: 5800
- Rows needed full source: 40800
- First expansion unlocked by raw rows: True
- Full source unlocked by raw rows: True

## Validation decision

- Decision: **CBOE_EUROPE_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW**
- Rebuild allowed by validation: **True**
- Recommended next phase: **v2.11E_REBUILD_EXPANDED_SOURCE_WITH_CBOE_EUROPE_REQUIRES_EXPLICIT_APPROVAL**

## Largest parsed CSV profiles

- `004_csv.csv` — family=symbols_csv_candidate; link=TRF EU; rows=21287; columns=39; notes=SKIPPED_METADATA_ROWS_1
- `005_csv.csv` — family=symbols_csv_candidate; link=TRF UK; rows=21287; columns=39; notes=SKIPPED_METADATA_ROWS_1
- `006_csv.csv` — family=symbols_csv_candidate; link=SIS; rows=21170; columns=39; notes=SKIPPED_METADATA_ROWS_1
- `001_csv.csv` — family=symbols_csv_candidate; link=BXE; rows=9384; columns=39; notes=SKIPPED_METADATA_ROWS_1
- `002_csv.csv` — family=symbols_csv_candidate; link=CXE; rows=9384; columns=39; notes=SKIPPED_METADATA_ROWS_1
- `003_csv.csv` — family=symbols_csv_candidate; link=DXE; rows=5731; columns=39; notes=SKIPPED_METADATA_ROWS_1
- `012_tickcsv.csv` — family=symbols_csv_candidate; link=BXE; rows=398; columns=3; notes=SKIPPED_METADATA_ROWS_1|NO_SYMBOL_LIKE_HEADER|NO_NAME_LIKE_HEADER
- `013_tickcsv.csv` — family=symbols_csv_candidate; link=CXE; rows=398; columns=3; notes=SKIPPED_METADATA_ROWS_1|NO_SYMBOL_LIKE_HEADER|NO_NAME_LIKE_HEADER

## Important caution

BXE, CXE, DXE, TRF and SIS remain source/venue semantics until an explicitly approved rebuild phase.

v2.11D does not decide primary exchange mapping and does not create accepted normalized rows.

## Outputs

- `outputs\full_universe_source_acquisition\cboe_europe_validation_v2_11d.json`
- `outputs\full_universe_source_acquisition\cboe_europe_validation_report_v2_11d.md`
- `outputs\full_universe_source_acquisition\cboe_europe_csv_profile_v2_11d.csv`
- `outputs\full_universe_source_acquisition\cboe_europe_validation_decision_v2_11d.csv`
- `outputs\full_universe_source_acquisition\cboe_europe_baseline_compare_v2_11d.csv`
