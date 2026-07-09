# v2.14E - Deutsche Boerse Xetra Expanded Source Rebuild

Status: **DEUTSCHE_BOERSE_XETRA_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **rebuild-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `2026-07-09T14:11:12.398622+00:00`

## Decision

- Source decision: **DEUTSCHE_BOERSE_XETRA_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE**
- Full source unlocked: **false**
- Full 59k: **blocked**
- Recommended next phase: **v2.14F - Deutsche Boerse Xetra Expanded Validation**

## Counts

- Baseline rows: 36863
- Xetra gross rows reviewed: 5069
- Xetra rows added: 1424
- Xetra rows excluded: 3645
- Expanded rows: 38287
- Expanded delta: 1424
- Duplicate exchange+ticker keys: 0
- Full source threshold: 50000
- Rows needed after Xetra: 11713
- Source-to-50k after Xetra: 76.6%

## Taxonomy rule

Only `Instrument Type = CS` is accepted as equity-like Xetra source row.

All non-CS instrument types are excluded from the expanded source.

## Guards

- Network download performed in v2.14E: false
- Raw files downloaded in v2.14E: false
- Raw files modified after write: false
- Workbook/CSV parsed for rebuild: true
- Normalization performed: true
- Net-new filtering performed: true
- Expanded universe rebuilt: true
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase creates a new expanded source universe only. It does not launch scoring, OpenAI, broker APIs or full 59k.
