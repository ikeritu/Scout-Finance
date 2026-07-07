# v2.11C - Cboe Europe Acquisition Real

Status: **CBOE_EUROPE_ACQUISITION_COMPLETED_RAW_ONLY**

Phase type: **acquisition-only**

Generated at UTC: `2026-07-07T22:58:55.620517+00:00`

## Hard guards

- Network download performed: true
- Raw files downloaded or reused: true
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Normalization performed: false
- Net-new filtering performed: false
- Overwrite allowed: false
- Rebuild allowed: false

## Acquisition summary

- Manifest rows: 21
- Discovered CSV links: 16
- CSV download attempts: 16
- Fallback symbols_traded pages planned: 4
- Raw files available successfully: 21
- Raw files reused from partial run: 1
- Fetch failures: 0

## Partial run handling

If `reference_data_page.html` already existed from the initial failed run, it was reused without overwrite.

For reused raw files, HTTP metadata is not available, but byte size and SHA256 are recorded.

## Raw preservation

All successful downloads were written or reused as raw bytes exactly as present on disk.

Raw directory:

`outputs\full_universe_source_acquisition\raw\cboe_europe_v2_11c`

## Outputs

- `outputs\full_universe_source_acquisition\cboe_europe_download_manifest_v2_11c.json`
- `outputs\full_universe_source_acquisition\cboe_europe_download_manifest_v2_11c.csv`
- `outputs\full_universe_source_acquisition\cboe_europe_discovered_links_v2_11c.csv`
- `outputs\full_universe_source_acquisition\cboe_europe_acquisition_report_v2_11c.md`

## Important scope note

v2.11C does not validate whether Cboe Europe rows are usable.

v2.11C does not normalize, filter, rebuild, score or launch the full 59k universe.

All usability decisions belong to v2.11D validation.
