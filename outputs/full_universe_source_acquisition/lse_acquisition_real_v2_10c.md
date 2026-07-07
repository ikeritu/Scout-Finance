# Scout Finance ? v2.10C LSE Acquisition Real

- Phase: v2.10C
- Method: lse_acquisition_real_v1
- Created at: 2026-07-07T14:27:10+00:00
- Acquisition status: **LSE_ACQUISITION_COMPLETED**
- Readiness score: **70/100**
- Acquisition decision: **LSE_RAW_SOURCE_READY_FOR_VALIDATION**
- Recommended next phase: **v2.10D ? LSE Validation**

## Summary

- Planned page routes: 4
- Successful page downloads: 4
- Discovered links: 48
- Selected download candidates: 0
- Successful candidate downloads: 0
- Probable CSV candidates: 0
- Total probable CSV rows: 0
- Current expanded rows: 9200
- Rows needed first expansion: 5800
- Rows needed full source: 40800

## Page request results

### lse_reports_page_probe

- URL: `https://www.londonstockexchange.com/reports`
- Target: `data/raw/source_providers/lse_issuers_and_instruments_reports/lse_reports_page.html`
- OK: True
- Status code: 200
- Content type: `text/html; charset=utf-8`
- Size bytes: 54995
- SHA256: `c082660492d1bfb06ac164700d1187ed1d47dc1e940d356ff9f622546ef03d25`
- Error: ``

### lse_issuers_reports_tab_probe

- URL: `https://www.londonstockexchange.com/reports?tab=issuers`
- Target: `data/raw/source_providers/lse_issuers_and_instruments_reports/lse_issuers_reports_page.html`
- OK: True
- Status code: 200
- Content type: `text/html; charset=utf-8`
- Size bytes: 54995
- SHA256: `c082660492d1bfb06ac164700d1187ed1d47dc1e940d356ff9f622546ef03d25`
- Error: ``

### lse_instruments_reports_tab_probe

- URL: `https://www.londonstockexchange.com/reports?tab=instruments`
- Target: `data/raw/source_providers/lse_issuers_and_instruments_reports/lse_instruments_reports_page.html`
- OK: True
- Status code: 200
- Content type: `text/html; charset=utf-8`
- Size bytes: 54995
- SHA256: `c082660492d1bfb06ac164700d1187ed1d47dc1e940d356ff9f622546ef03d25`
- Error: ``

### lse_historical_analytics_data_products_probe

- URL: `https://www.londonstockexchange.com/equities-trading/market-data/historical-analytics-data-products`
- Target: `data/raw/source_providers/lse_issuers_and_instruments_reports/lse_historical_analytics_data_products_page.html`
- OK: True
- Status code: 200
- Content type: `text/html; charset=utf-8`
- Size bytes: 54995
- SHA256: `c082660492d1bfb06ac164700d1187ed1d47dc1e940d356ff9f622546ef03d25`
- Error: ``

## Candidate download results

- No candidate downloads selected.

## Schema probes

- No schema probes available.

## Outputs

- Requests CSV: `outputs/full_universe_source_acquisition/lse_request_results_v2_10c.csv`
- Discovered links CSV: `outputs/full_universe_source_acquisition/lse_discovered_links_v2_10c.csv`
- Schema probe CSV: `outputs/full_universe_source_acquisition/lse_schema_probe_v2_10c.csv`
- Sample CSV: `outputs/full_universe_source_acquisition/lse_sample_v2_10c.csv`
- Acquisition JSON: `outputs/full_universe_source_acquisition/lse_acquisition_real_v2_10c.json`
- Acquisition report: `outputs/full_universe_source_acquisition/lse_acquisition_real_v2_10c.md`

## Controls

- Network download performed: true
- Network download scope: LSE_APPROVED_ROUTES_ONLY
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

- v2.10B plan artifact found: outputs/full_universe_source_acquisition/lse_acquisition_plan_v2_10b.json
- v2.10B plan status accepted: LSE_ACQUISITION_PLAN_READY
- v2.10B plan decision accepted: LSE_CONTROLLED_ACQUISITION_APPROVED
- LSE route downloaded: lse_reports_page_probe -> data/raw/source_providers/lse_issuers_and_instruments_reports/lse_reports_page.html
- LSE route downloaded: lse_issuers_reports_tab_probe -> data/raw/source_providers/lse_issuers_and_instruments_reports/lse_issuers_reports_page.html
- LSE route downloaded: lse_instruments_reports_tab_probe -> data/raw/source_providers/lse_issuers_and_instruments_reports/lse_instruments_reports_page.html
- LSE route downloaded: lse_historical_analytics_data_products_probe -> data/raw/source_providers/lse_issuers_and_instruments_reports/lse_historical_analytics_data_products_page.html

## Blockers

- No blockers detected.

## Warnings

- No official LSE report download candidates were selected from discovered links.
- No probable CSV candidate was parsed in v2.10C; XLS/XLSX/ZIP/JSON, if downloaded, must be reviewed in v2.10D.
- v2.10C is acquisition-only. Net-new coverage is not computed until v2.10D.
- Do not rebuild expanded_universe from v2.10C outputs.
- Do not use LSE rows downstream until v2.10D validation.

## Recommendation

Proceed to v2.10D LSE Validation. Do not rebuild until v2.10D confirms schema, duplicate control and net-new coverage.

Important: v2.10C is acquisition-only. It downloads only the LSE routes approved by v2.10B. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.