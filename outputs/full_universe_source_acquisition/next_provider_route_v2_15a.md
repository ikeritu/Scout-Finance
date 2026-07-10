# v2.15A - Next Provider Route For Remaining Full Source Gap

Status: **NEXT_PROVIDER_ROUTE_SELECTED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **route-selection-only**

Generated at UTC: `2026-07-10T20:58:22.859385+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Selected provider

`euronext_official_instruments_equities`

Name: **Euronext official instruments / listed equities**

Region: **Europe**

Route score: **94**

Reason:

Large official European venue group; likely to add listings not fully covered by previous providers while complementing Xetra, HKEX and JPX.

## Candidate ranking

- 94 — `euronext_official_instruments_equities` — Euronext official instruments / listed equities — Large official European venue group; likely to add listings not fully covered by previous providers while complementing Xetra, HKEX and JPX.
- 88 — `tmx_tsx_tsxv_listed_issuers` — TMX / TSX / TSXV listed issuers — Canada can add a meaningful block of common equities and ETFs require filtering; good diversification outside US/Europe/Asia already covered.
- 84 — `asx_official_listed_companies` — ASX official listed companies — Clear official exchange candidate with likely clean symbol/company data and manageable taxonomy.
- 79 — `krx_kind_listed_companies` — KRX / KIND listed companies — Large Asian market candidate; language/access/taxonomy may be more complex than ASX/TMX.
- 73 — `sgx_securities_list` — SGX securities list — Good official venue candidate but likely smaller net-new contribution than Euronext/TMX/ASX.
- 69 — `bme_spanish_listed_instruments` — BME Spanish listed instruments — Relevant European source but may overlap heavily with Cboe Europe and other European coverage.

## Decision

Selected provider for the next cycle:

`euronext_official_instruments_equities`

Recommended next phase:

`v2.15B - Euronext Acquisition Plan`

## Guards

- Network download performed: false
- Raw files downloaded: false
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

This phase only selects the next provider route. It does not download, parse, normalize, rebuild, score, call OpenAI, call brokers or launch full 59k.
