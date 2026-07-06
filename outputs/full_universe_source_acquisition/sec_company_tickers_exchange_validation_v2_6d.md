# Scout Finance ? v2.6D SEC Company Tickers Exchange Validation

- Phase: v2.6D
- Method: sec_company_tickers_exchange_validation_v1
- Created at: 2026-07-06T11:46:33+00:00
- Validation status: **SEC_COMPANY_TICKERS_EXCHANGE_VALIDATED_WITH_PRIMARY_CANDIDATES**
- Readiness score: **85/100**
- SEC route decision: **USABLE_AS_PARTIAL_PROVIDER_AND_IDENTIFIER_ENRICHMENT**
- Recommended next phase: **v2.6E ? SEC Incremental Coverage Analysis**

## Inputs

- SEC CSV: `data/raw/source_providers/sec_company_tickers_exchange/sec_company_tickers_exchange.csv`
- SEC raw JSON: `data/raw/source_providers/sec_company_tickers_exchange/company_tickers_exchange.json`
- Expanded universe CSV: `data/raw/expanded_universe/expanded_universe_v2_4b.csv`

## Row summary

- SEC rows: 10415
- Expanded universe rows: 5648
- SEC primary exchange candidate rows: 7668
- SEC enrichment/exclusion candidate rows: 2747
- SEC unknown exchange rows: 0

## SEC exchange counts

- NASDAQ: 4329
- NYSE: 3312
- OTC: 2558
- None: 189
- CBOE: 27

## Overlap and new coverage

- Overlap by exchange+ticker: 5309
- New by exchange+ticker: 5106
- Overlap by ticker only: 5590
- New by ticker only: 4825
- Primary new exchange+ticker keys: 2359
- Primary new tickers: 2079

## Rebuild impact estimate

- Current expanded rows: 5648
- Max possible rows after primary SEC merge: 8007
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Rows still needed for first expansion after primary SEC merge: 6993
- Rows still needed for full-source after primary SEC merge: 41993

## Data quality

- Missing SEC columns: []
- Empty ticker: 0
- Empty company_name: 0
- Empty exchange: 0
- Empty raw_cik: 0
- Invalid source_provider: 0
- Duplicate exchange+ticker keys: 0
- Duplicate ticker-only values: 0

## Outputs

- Exchange breakdown CSV: `outputs/full_universe_source_acquisition/sec_company_tickers_exchange_validation_exchange_breakdown_v2_6d.csv`
- Overlap sample CSV: `outputs/full_universe_source_acquisition/sec_company_tickers_exchange_validation_overlap_sample_v2_6d.csv`
- New sample CSV: `outputs/full_universe_source_acquisition/sec_company_tickers_exchange_validation_new_sample_v2_6d.csv`
- Exclusion sample CSV: `outputs/full_universe_source_acquisition/sec_company_tickers_exchange_validation_exclusion_sample_v2_6d.csv`

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

- v2.6C acquisition artifact found: outputs/full_universe_source_acquisition/sec_company_tickers_exchange_acquisition_real_v2_6c.json
- v2.6C acquisition status accepted: SEC_COMPANY_TICKERS_EXCHANGE_ACQUISITION_COMPLETED
- SEC raw JSON found: data/raw/source_providers/sec_company_tickers_exchange/company_tickers_exchange.json
- SEC normalized CSV found: data/raw/source_providers/sec_company_tickers_exchange/sec_company_tickers_exchange.csv
- Expanded universe CSV found: data/raw/expanded_universe/expanded_universe_v2_4b.csv
- SEC canonical schema validated.
- No duplicate SEC exchange+ticker keys detected.
- Primary exchange SEC candidates detected: 7668

## Blockers

- No blockers detected.

## Warnings

- OTC/None/blank SEC rows should be treated as enrichment or exclusion candidates: 2747

## Recommendation

Proceed to v2.6E to quantify incremental coverage and decide whether a controlled rebuild plan is justified.

Important: v2.6D is a validation-only step. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.