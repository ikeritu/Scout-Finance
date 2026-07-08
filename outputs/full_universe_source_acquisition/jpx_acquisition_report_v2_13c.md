# v2.13C - JPX Acquisition Real

Status: **JPX_ACQUISITION_COMPLETED_RAW_ONLY**

Phase type: **acquisition-only**

Generated at UTC: `2026-07-08T14:15:07.203851+00:00`

## Hard guards

- Network download performed: true
- Raw files downloaded: true
- Raw files modified after write: false
- Workbook or CSV parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Acquisition summary

- Manifest rows: 6
- Raw files fetched successfully: 6
- Fetch failures: 0
- Discovered links: 21
- Dataset candidates discovered: 2
- Dataset candidates downloaded: 2
- Dataset files valid workbook or CSV container: 2
- Primary dataset downloaded: True
- Listed issues page fetched: True

## Raw preservation

All successful downloads were written as raw bytes exactly as received.

Raw directory:

`outputs\full_universe_source_acquisition\raw\jpx_v2_13c`

## Files attempted

- jpx_list_of_tse_listed_issues_page: status=FETCHED_RAW_BYTES_PRESERVED; status_code=200; bytes=30059; path=`outputs\full_universe_source_acquisition\raw\jpx_v2_13c\jpx_list_of_tse_listed_issues_page.html`
- jpx_data_portal_catalog: status=FETCHED_RAW_BYTES_PRESERVED; status_code=200; bytes=32360; path=`outputs\full_universe_source_acquisition\raw\jpx_v2_13c\jpx_data_portal_catalog.html`
- jpx_listed_issues_client_portal_entry: status=FETCHED_RAW_BYTES_PRESERVED; status_code=200; bytes=20273; path=`outputs\full_universe_source_acquisition\raw\jpx_v2_13c\jpx_client_portal_listed_issues_entry.html`
- jpx_listed_company_search: status=FETCHED_RAW_BYTES_PRESERVED; status_code=200; bytes=26427; path=`outputs\full_universe_source_acquisition\raw\jpx_v2_13c\jpx_listed_company_search.html`
- jpx_listed_issues_dataset_candidate_001: status=FETCHED_RAW_BYTES_PRESERVED; status_code=200; bytes=861184; path=`outputs\full_universe_source_acquisition\raw\jpx_v2_13c\datasets\001_jpx_dataset_candidate_jpx_discovered_workbook_candidate.xls`
- jpx_listed_issues_dataset_candidate_002: status=FETCHED_RAW_BYTES_PRESERVED; status_code=200; bytes=31847; path=`outputs\full_universe_source_acquisition\raw\jpx_v2_13c\datasets\002_jpx_dataset_candidate_jpx_discovered_workbook_candidate.xlsx`

## Important scope note

v2.13C does not validate whether JPX rows are usable.

v2.13C does not parse workbook/CSV data, classify securities, normalize, filter, rebuild, score or launch the full 59k universe.

All usability decisions belong to v2.13D validation.

## Outputs

- `outputs\full_universe_source_acquisition\jpx_download_manifest_v2_13c.json`
- `outputs\full_universe_source_acquisition\jpx_download_manifest_v2_13c.csv`
- `outputs\full_universe_source_acquisition\jpx_discovered_links_v2_13c.csv`
- `outputs\full_universe_source_acquisition\jpx_acquisition_report_v2_13c.md`
