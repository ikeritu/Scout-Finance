# Scout Finance ? v2.6B SEC Company Tickers Exchange Acquisition Plan

- Phase: v2.6B
- Method: sec_company_tickers_exchange_acquisition_plan_v1
- Created at: 2026-07-06T10:38:32+00:00
- Plan status: **SEC_COMPANY_TICKERS_EXCHANGE_PLAN_READY**
- Readiness score: **95/100**
- Provider: **SEC company_tickers_exchange.json**
- Provider ID: `sec_company_tickers_exchange`
- Source URL: `https://www.sec.gov/files/company_tickers_exchange.json`
- Real acquisition phase: **v2.6C**
- Mode: **PLAN_ONLY_NO_DOWNLOAD**

## Current state

- Current included rows: 5648
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Rows needed for first expansion target: 9352
- Rows needed for full-source threshold: 44352
- Expanded universe rebuild allowed: false
- Full 59k remains blocked: true

## SEC User-Agent policy

- A declared SEC User-Agent is required before v2.6C.
- Recommended environment variable: `SCOUT_FINANCE_SEC_USER_AGENT`
- Fallback format: `ScoutFinance/1.0 contact@example.com`
- Replace fallback email with a valid contact before real acquisition.

## Expected schema

Top-level SEC JSON structure expected:

- `fields`: ordered list of field names
- `data`: list of records matching field order

Expected fields:
- `cik`
- `name`
- `ticker`
- `exchange`

Canonical columns after normalization:
- `ticker`
- `company_name`
- `exchange`
- `country`
- `source_provider`
- `source_file`
- `instrument_type`
- `instrument_scope`
- `classification_confidence`
- `classification_reason`
- `sector`
- `industry`
- `market_cap`
- `raw_cik`
- `raw_exchange`

## Normalization rules

- Map ticker -> ticker uppercase/trimmed.
- Map name -> company_name.
- Map exchange -> exchange normalized but preserve raw_exchange.
- Map cik -> raw_cik as string without losing leading semantics.
- Set country to USA for SEC mapping source.
- Set source_provider to sec_company_tickers_exchange.
- Set source_file to raw JSON relative path.
- Do not infer instrument_type as COMMON_STOCK solely from SEC mapping.
- Default instrument_type to UNKNOWN_PENDING_CLASSIFICATION unless classified later.
- Default instrument_scope to UNKNOWN_PENDING_CLASSIFICATION unless classified later.
- Do not merge into expanded_universe in v2.6C.

## Acceptance criteria for v2.6C

- Raw JSON exists and is readable.
- Top-level fields/data keys exist.
- Expected fields include cik, name, ticker, exchange.
- Row count is reported.
- Empty ticker/name/exchange/cik counts are reported.
- Duplicate exchange+ticker keys are reported.
- Exchange counts are reported.
- Normalized CSV is written only if schema is recognized.

## Controls for v2.6C

- No OpenAI.
- No broker.
- No scoring recalculation.
- No full 59k universe launch.
- No active output overwrite.
- No expanded_universe rebuild.
- One controlled network request.
- Raw JSON preserved.
- JSON and Markdown acquisition report produced.

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: false
- Active outputs overwritten: false
- Expanded universe rebuilt: false

## Positives

- v2.6A route artifact found: outputs/full_universe_source_acquisition/next_official_provider_route_v2_6a.json
- v2.6A route status accepted: NEXT_OFFICIAL_PROVIDER_ROUTE_READY
- v2.6A recommended phase accepted: v2.6B ? SEC Company Tickers Exchange Acquisition Plan

## Blockers

- No blockers detected.

## Warnings

- Rows still needed for first expansion target before SEC acquisition: 9352
- Rows still needed for full-source threshold before SEC acquisition: 44352

## Recommendation

Proceed to v2.6C for one controlled SEC download after setting a valid SEC User-Agent contact.

Important: v2.6B is a planning artifact only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.