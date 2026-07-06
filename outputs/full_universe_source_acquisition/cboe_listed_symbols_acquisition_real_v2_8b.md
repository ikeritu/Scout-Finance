# Scout Finance ? v2.8B Cboe Listed Symbols Acquisition Real

- Phase: v2.8B
- Method: cboe_listed_symbols_acquisition_real_v1
- Created at: 2026-07-06T21:12:57+00:00
- Acquisition status: **CBOE_LISTED_SYMBOLS_ACQUISITION_COMPLETED_WITH_REVIEW_REQUIRED**
- Readiness score: **70/100**
- Recommended next phase: **v2.8C ? Cboe Listed Symbols Validation**

## Summary

- Pages attempted: 2
- Pages fetched OK: 2
- Discovered CSV/XML links: 14
- Candidate downloads attempted: 4
- Successful downloads: 4
- Successful CSV downloads: 2
- Normalized rows: 0

## Page results

- `cboe_us_equities_listed_symbols` ? status `200`, ok `True`, size `1418488`, saved `data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_page.html`
- `cboe_us_equities_symbols_traded_edgx` ? status `200`, ok `True`, size `594567`, saved `data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_page.html`

## Candidate downloads

- `cboe_us_equities_listed_symbols` `csv` ? status `200`, ok `True`, size `61288`, saved `data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.csv`
- `cboe_us_equities_listed_symbols` `xml` ? status `200`, ok `True`, size `187980`, saved `data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.xml`
- `cboe_us_equities_symbols_traded_edgx` `csv` ? status `200`, ok `True`, size `37795`, saved `data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_raw.csv`
- `cboe_us_equities_symbols_traded_edgx` `xml` ? status `200`, ok `True`, size `309345`, saved `data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_raw.xml`

## Outputs

- provider_dir: `data/raw/source_providers/cboe_listed_symbols`
- listed_html: `data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_page.html`
- symbols_traded_html: `data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_page.html`
- listed_csv: `data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.csv`
- listed_xml: `data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.xml`
- symbols_traded_csv: `data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_raw.csv`
- symbols_traded_xml: `data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_raw.xml`
- normalized_csv: `None`
- schema_probe_csv: `outputs/full_universe_source_acquisition/cboe_listed_symbols_schema_probe_v2_8b.csv`
- discovered_links_csv: `outputs/full_universe_source_acquisition/cboe_listed_symbols_discovered_links_v2_8b.csv`
- sample_csv: `None`

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Active outputs overwritten: false
- Expanded universe rebuilt: false
- Network download performed: true
- Raw files preserved: true

## Positives

- v2.8A plan artifact found: outputs/full_universe_source_acquisition/cboe_listed_symbols_route_plan_v2_8a.json
- v2.8A plan status accepted: CBOE_LISTED_SYMBOLS_ROUTE_PLAN_READY
- Raw Cboe page saved: data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_page.html
- Cboe page fetched OK: https://www.cboe.com/us/equities/market_statistics/listed_symbols/
- Raw Cboe page saved: data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_page.html
- Cboe page fetched OK: https://www.cboe.com/us/equities/market_statistics/symbols_traded/?mkt=edgx
- Cboe CSV saved: data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.csv
- CSV parsed for cboe_us_equities_listed_symbols: 1490 rows
- Cboe XML saved: data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.xml
- Cboe CSV saved: data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_raw.csv
- CSV parsed for cboe_us_equities_symbols_traded_edgx: 1220 rows
- Cboe XML saved: data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_raw.xml

## Blockers

- No blockers detected.

## Warnings

- Normalization warning: No symbol/ticker field detected.
- No normalized Cboe listed-symbol rows produced. v2.8C must inspect raw/schema before deciding route usability.

## Recommendation

Proceed to v2.8C to validate Cboe schema, semantics and net new coverage before any rebuild.

Important: v2.8B is acquisition-only. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.