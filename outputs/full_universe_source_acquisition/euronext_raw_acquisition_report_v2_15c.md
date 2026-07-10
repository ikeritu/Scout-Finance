# v2.15C - Euronext Raw Acquisition

Status: **EURONEXT_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS**

Phase type: **acquisition-only**

Generated at UTC: `2026-07-10T22:06:51.976576+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Download summary

- Attempted: 11
- OK count: 11
- Failed count: 0
- HTTP 200 count: 11
- Total bytes: 4001113
- Raw directory: `outputs\full_universe_source_acquisition\raw\euronext_v2_15c`
- Discovered links: 6781

## Downloads

- `euronext_live_all_equities` status=200 ok=True bytes=423012 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_live_all_equities.html` error=``
- `euronext_live_equities_overview` status=200 ok=True bytes=346293 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_live_equities_overview.html` error=``
- `euronext_amsterdam_equities_list` status=200 ok=True bytes=342057 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_amsterdam_equities_list.html` error=``
- `euronext_brussels_equities_list` status=200 ok=True bytes=338285 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_brussels_equities_list.html` error=``
- `euronext_dublin_equities_list` status=200 ok=True bytes=296723 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_dublin_equities_list.html` error=``
- `euronext_lisbon_equities_list` status=200 ok=True bytes=313044 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_lisbon_equities_list.html` error=``
- `euronext_milan_equities_list` status=200 ok=True bytes=380685 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_milan_equities_list.html` error=``
- `euronext_oslo_equities_list` status=200 ok=True bytes=350439 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_oslo_equities_list.html` error=``
- `euronext_paris_equities_list` status=200 ok=True bytes=385397 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_paris_equities_list.html` error=``
- `euronext_advanced_reference_data` status=200 ok=True bytes=409557 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_advanced_reference_data.html` error=``
- `euronext_static_reference_data` status=200 ok=True bytes=415621 raw=`outputs\full_universe_source_acquisition\raw\euronext_v2_15c\euronext_static_reference_data.html` error=``

## Guards

- Network download performed: true
- Raw files downloaded: true
- Raw files modified after write: false
- Workbook/CSV parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase saves raw official source pages/payloads and a lightweight link-discovery manifest only.

It does not parse securities, normalize fields, classify instruments, estimate net-new rows, rebuild the expanded universe, score equities, call OpenAI, call broker APIs or launch full 59k.

## Recommended next phase

`v2.15D - Euronext Validation`
