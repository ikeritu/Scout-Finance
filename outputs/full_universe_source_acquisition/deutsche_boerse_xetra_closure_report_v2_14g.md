# v2.14G - Deutsche Boerse Xetra Closure Report

Status: **DEUTSCHE_BOERSE_XETRA_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED**

Phase type: **closure-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `2026-07-09T22:46:25.542973+00:00`

## Decision

- Source decision: **DEUTSCHE_BOERSE_XETRA_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE**
- Full source unlocked: **false**
- Full 59k: **blocked**
- Recommended next phase: **v2.15A - Next Provider Route For Remaining Full Source Gap**

## Final Xetra outcome

- Baseline before Xetra: 36863
- Xetra rows added: 1424
- Xetra rows excluded: 3645
- Expanded after Xetra: 38287
- Expanded delta: 1424
- Duplicate exchange+ticker keys: 0
- Critical failed checks: 0
- Warning failed checks: 0

## Source progress

- Source-to-50k completed: 76.6%
- Source-to-50k pending: 23.4%
- Rows needed after Xetra: 11713

## Project percentages

- GLOBAL corrected: 42% completed / 58% pending
- Source to 50k: 76.6% completed / 23.4% pending
- Full source gate: 0% completed / 100% pending
- Full 59k dry-run: 0% completed / 100% pending

## Provider breakdown

- cboe_europe_reference_data: 21154
- jpx_listed_securities: 3705
- nasdaq_trader_nasdaqlisted: 3244
- hkex_securities_list: 2804
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- deutsche_boerse_xetra_all_tradable_instruments: 1424
- cboe_listed_symbols: 1193

## Guards

- Network download performed in v2.14G: false
- Raw files downloaded in v2.14G: false
- Raw files modified after write: false
- Workbook/CSV parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase closes Deutsche Börse/Xetra only. It does not modify the expanded universe.
