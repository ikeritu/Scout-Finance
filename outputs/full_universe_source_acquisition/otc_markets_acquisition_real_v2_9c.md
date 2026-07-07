# Scout Finance ? v2.9C OTC Markets Acquisition Real

- Phase: v2.9C
- Method: otc_markets_acquisition_real_v1
- Created at: 2026-07-07T11:33:14+00:00
- Acquisition status: **OTC_MARKETS_ACQUISITION_COMPLETED**
- Readiness score: **85/100**
- Acquisition decision: **OTC_MARKETS_RAW_SOURCE_READY_FOR_VALIDATION**
- Recommended next phase: **v2.9D ? OTC Markets Validation**

## Provider

- Provider ID: `otc_markets_stock_screener`
- Provider dir: `data/raw/source_providers/otc_markets_stock_screener`
- Raw page HTML: `data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_page.html`
- Raw CSV: `data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_raw.csv`

## Request results

### otc_markets_stock_screener_page_probe

- URL: `https://www.otcmarkets.com/research/stock-screener`
- Target: `data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_page.html`
- OK: True
- Status code: 200
- Content type: `text/html; charset=UTF-8`
- Size bytes: 16409
- SHA256: `09917ac15cfbc52f86c6385849600ce64db573cb9f214c5e27ecf5b34a77ff96`
- Error: ``

### otc_markets_stock_screener_download_csv

- URL: `https://www.otcmarkets.com/research/stock-screener/api/downloadCSV?ce=true&sortField=volume&sortOrder=desc`
- Target: `data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_raw.csv`
- OK: True
- Status code: 200
- Content type: `text/csv; charset=utf-8`
- Size bytes: 2073
- SHA256: `b83468aee4590b820ac4a98d873d0cb6cff723058d7eb0e51814cbcf2165b84e`
- Error: ``

## CSV probe

- Exists: True
- Is probable CSV: True
- Row count: 25
- Field count: 9
- Fields: Symbol, Security Name, Tier, Price, Change %, Vol, Sec Type, Country, State
- Schema probe CSV: `outputs/full_universe_source_acquisition/otc_markets_schema_probe_v2_9c.csv`
- Sample CSV: `outputs/full_universe_source_acquisition/otc_markets_sample_v2_9c.csv`
- Sample rows written: 25
- Error: ``

## Current threshold context

- Current expanded rows: 9200
- Rows needed first expansion: 5800
- Rows needed full source: 40800
- Net-new coverage: not computed in v2.9C

## Controls

- Network download performed: true
- Network download scope: OTC_MARKETS_APPROVED_ROUTES_ONLY
- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Active outputs overwritten: false
- Expanded universe rebuilt: false
- Acquisition only: true

## Positives

- v2.9B plan artifact found: outputs/full_universe_source_acquisition/otc_markets_acquisition_plan_v2_9b.json
- v2.9B plan status accepted: OTC_MARKETS_ACQUISITION_PLAN_READY
- v2.9B plan decision accepted: OTC_MARKETS_CONTROLLED_ACQUISITION_APPROVED
- HTML page downloaded: data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_page.html
- CSV candidate downloaded: data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_raw.csv
- CSV schema detected with 9 fields and 25 rows.

## Blockers

- No blockers detected.

## Warnings

- Raw OTC row count may be insufficient to unlock first expansion before net-new validation: 25 < 5800
- v2.9C is acquisition-only. Net-new coverage is not computed until v2.9D.
- Do not rebuild expanded_universe from v2.9C outputs.
- Do not use OTC rows downstream until v2.9D validation.

## Recommendation

Proceed to v2.9D OTC Markets Validation. Do not rebuild until v2.9D confirms schema, duplicate control and net-new coverage.

Important: v2.9C is acquisition-only. It downloads only the OTC Markets routes approved by v2.9B. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.