# Scout Finance ? v2.6C SEC Company Tickers Exchange Acquisition Real

- Phase: v2.6C
- Method: sec_company_tickers_exchange_acquisition_real_v1
- Created at: 2026-07-06T11:21:39+00:00
- Acquisition status: **SEC_COMPANY_TICKERS_EXCHANGE_ACQUISITION_COMPLETED**
- Readiness score: **85/100**
- Provider: **SEC company_tickers_exchange.json**
- Source URL: `https://www.sec.gov/files/company_tickers_exchange.json`
- Network status OK: True
- HTTP status code: 200
- Content type: `application/json`
- Size bytes: 521876
- SHA256: `10cf18f2433682557f1d71c3085c811f20fae4efe660e1cee7e5ce1c341f23f4`
- Raw JSON: `data/raw/source_providers/sec_company_tickers_exchange/company_tickers_exchange.json`
- Normalized CSV: `data/raw/source_providers/sec_company_tickers_exchange/sec_company_tickers_exchange.csv`
- Normalized rows: 10415

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Active outputs overwritten: false
- Expanded universe rebuilt: false

## Schema

- Expected fields: ['cik', 'name', 'ticker', 'exchange']
- Detected fields: ['cik', 'name', 'ticker', 'exchange']
- Raw data records: 10415

## Data quality summary

- Empty tickers: 0
- Empty company names: 0
- Empty exchanges: 0
- Empty CIKs: 0
- Duplicate exchange+ticker keys: 0

## Exchange counts

- NASDAQ: 4329
- NYSE: 3312
- OTC: 2558
- None: 189
- CBOE: 27

## Positives

- v2.6B plan artifact found: outputs/full_universe_source_acquisition/sec_company_tickers_exchange_acquisition_plan_v2_6b.json
- v2.6B plan status accepted: SEC_COMPANY_TICKERS_EXCHANGE_PLAN_READY
- SEC User-Agent configured via SCOUT_FINANCE_SEC_USER_AGENT
- Raw SEC JSON response written: data/raw/source_providers/sec_company_tickers_exchange/company_tickers_exchange.json
- SEC download succeeded: https://www.sec.gov/files/company_tickers_exchange.json
- SEC JSON parsed successfully.
- Normalized SEC CSV written: data/raw/source_providers/sec_company_tickers_exchange/sec_company_tickers_exchange.csv
- SEC sample CSV written: outputs/full_universe_source_acquisition/sec_company_tickers_exchange_sample_v2_6c.csv
- No duplicate exchange+ticker keys detected in SEC normalized rows.
- SEC normalized row count: 10415

## Blockers

- No blockers detected.

## Warnings

- SEC source is acquired and normalized, but must be validated before rebuild or merge.

## Recommendation

Proceed to v2.6D SEC validation before any rebuild or merge.

Important: v2.6C is an isolated SEC provider acquisition step. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.