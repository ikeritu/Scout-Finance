# Scout Finance ? v2.6A Next Official Provider Route

- Phase: v2.6A
- Method: next_official_provider_route_v1
- Created at: 2026-07-06T10:09:42+00:00
- Route status: **NEXT_OFFICIAL_PROVIDER_ROUTE_READY**
- Readiness score: **90/100**
- Recommended next phase: **v2.6B ? SEC Company Tickers Exchange Acquisition Plan**

## Current state

- Current included rows: 5648
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Rows needed for first expansion target: 9352
- Rows needed for full-source threshold: 44352
- NYSE decision status: **NYSE_USABILITY_DECISION_DEEP_JS_REVIEW_REQUIRED**
- NYSE usability decision: **REQUIRES_DEEP_JS_PAYLOAD_REVIEW**
- Expanded universe rebuild allowed: false
- Full 59k remains blocked: true

## Provider route ranking

### 1. SEC company_tickers_exchange.json

- Provider ID: `sec_company_tickers_exchange`
- Type: official_regulatory_identifier_mapping
- Route status: **RECOMMENDED_NEXT_CONTROLLED_ROUTE**
- Expected value: HIGH
- Risk: MEDIUM
- Network required: True
- Source URL/reference: `https://www.sec.gov/files/company_tickers_exchange.json`
- Why next: Official SEC file with company name, CIK, ticker and exchange mapping. Useful to expand and validate ticker universe with exchange metadata, although it is not a pure exchange listing file.

Acceptance criteria:
- Download succeeds or fails with controlled report.
- Raw JSON is preserved.
- CSV normalization is produced only if schema is recognized.
- Report row count, exchanges, duplicate ticker/exchange keys and missing fields.

### 2. Cboe Listed Symbols

- Provider ID: `cboe_listed_symbols`
- Type: official_exchange_listing_source
- Route status: **SECOND_ROUTE_AFTER_SEC_OR_PARALLEL_IF_NEEDED**
- Expected value: MEDIUM
- Risk: MEDIUM
- Network required: True
- Source URL/reference: `https://www.cboe.com/us/equities/market_statistics/listed_symbols/`
- Why next: Official Cboe listed-symbol route with CSV/XML indications. Likely useful for BZX-listed securities, but may be narrower than SEC mapping.

Acceptance criteria:
- Identify stable CSV/XML route.
- Download raw file in isolated provider directory.
- Report row count and schema.
- Do not rebuild until validation gate passes.

### 3. Cboe BZX Daily Listed Securities Report

- Provider ID: `cboe_bzx_daily_listed_securities_report`
- Type: official_exchange_listing_report
- Route status: **FOLLOW_UP_IF_CBOE_ROUTE_IS_SELECTED**
- Expected value: MEDIUM
- Risk: MEDIUM
- Network required: True
- Source URL/reference: `Cboe BZX daily listed securities report documentation`
- Why next: Cboe documentation describes a daily listed securities report for issues listed on BZX. Useful if a stable public file route can be confirmed.

Acceptance criteria:
- Confirm public accessibility.
- Confirm format and schema.
- Only then implement real acquisition.

### 4. Third-party aggregated datasets

- Provider ID: `third_party_aggregated_datasets`
- Type: non_primary_external_dataset
- Route status: **DEFER**
- Expected value: VARIABLE
- Risk: HIGH
- Network required: True
- Why next: Could add rows, but license, freshness and provenance risks make it unsuitable before official routes are exhausted.

Acceptance criteria:
- License documented.
- Freshness documented.
- Official source alternatives exhausted.

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

- v2.5G NYSE decision artifact found: outputs/full_universe_source_acquisition/nyse_usability_decision_gate_v2_5g.json
- v2.5A revalidation artifact found: outputs/full_universe_source_acquisition/expanded_source_revalidation_gate_v2_5a.json
- NYSE correctly deferred from rebuild path: REQUIRES_DEEP_JS_PAYLOAD_REVIEW

## Blockers

- No blockers detected.

## Warnings

- Rows still needed for first expansion target: 9352
- Rows still needed for full-source threshold: 44352
- NYSE remains deferred unless deep JS payload review is explicitly chosen later.

## Recommendation

Proceed with v2.6B as a plan-only SEC company_tickers_exchange acquisition route. Do not download until that plan is reviewed.

Important: v2.6A is a route-selection artifact only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.