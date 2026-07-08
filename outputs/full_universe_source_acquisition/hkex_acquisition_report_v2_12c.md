# v2.12C — HKEX Acquisition Real

Status: **HKEX_ACQUISITION_COMPLETED_RAW_ONLY**

Phase type: **acquisition-only**

Generated at UTC: `2026-07-08T10:45:58.908308+00:00`

## Hard guards

- Network download performed: true
- Raw files downloaded: true
- Raw files modified after write: false
- Workbook parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Acquisition summary

- Manifest rows: 2
- Raw files fetched successfully: 2
- Fetch failures: 0
- Discovered links: 9
- English XLSX valid ZIP container: True
- Chinese fallback triggered: False

## Raw preservation

All successful downloads were written as raw bytes exactly as received.

Raw directory:

`outputs\full_universe_source_acquisition\raw\hkex_v2_12c`

## Files attempted

- hkex_list_of_securities_xlsx_en: status=FETCHED_RAW_BYTES_PRESERVED; status_code=200; bytes=1379361; path=`outputs\full_universe_source_acquisition\raw\hkex_v2_12c\ListOfSecurities.xlsx`
- hkex_securities_lists_page: status=FETCHED_RAW_BYTES_PRESERVED; status_code=200; bytes=397240; path=`outputs\full_universe_source_acquisition\raw\hkex_v2_12c\securities_lists_page.html`

## Important scope note

v2.12C does not validate whether HKEX rows are usable.

v2.12C does not parse workbook sheets, classify securities, normalize, filter, rebuild, score or launch the full 59k universe.

All usability decisions belong to v2.12D validation.

## Outputs

- `outputs\full_universe_source_acquisition\hkex_download_manifest_v2_12c.json`
- `outputs\full_universe_source_acquisition\hkex_download_manifest_v2_12c.csv`
- `outputs\full_universe_source_acquisition\hkex_discovered_links_v2_12c.csv`
- `outputs\full_universe_source_acquisition\hkex_acquisition_report_v2_12c.md`
