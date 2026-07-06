# Scout Finance ? v2.8F Validate Expanded Source With Cboe

- Phase: v2.8F
- Method: validate_expanded_source_with_cboe_v1
- Created at: 2026-07-06T23:00:36+00:00
- Validation status: **EXPANDED_SOURCE_WITH_CBOE_VALIDATED_USEFUL_BUT_NOT_ENOUGH**
- Readiness score: **90/100**
- Validation decision: **CBOE_REBUILD_VALIDATED_USEFUL_BUT_NOT_ENOUGH**
- Recommended next phase: **v2.8G ? Expanded Source With Cboe Closure Report OR v2.9A next provider route**

## Row summary

- Expanded rows: 9200
- Expected expanded rows: 9200
- Exclusions rows: 10056
- Expected exclusions rows: 10056
- Duplicate exchange+ticker keys: 0
- Issues count: 1
- Cboe rows: 1193

## Provider validation

- nasdaq_trader_nasdaqlisted: expected 3244, actual 3244, status OK
- nasdaq_trader_otherlisted: expected 2404, actual 2404, status OK
- sec_company_tickers_exchange: expected 2359, actual 2359, status OK
- cboe_listed_symbols: expected 1193, actual 1193, status OK

## Cboe candidate validation

- Cboe confidence counts: `{'LOW': 1193}`
- Cboe scope counts: `{'CANDIDATE_PROVIDER_ROW_PENDING_POST_REBUILD_VALIDATION': 1193}`
- Merge action counts: `{'ADD_CBOE_CANDIDATE_NET_NEW': 1193}`

## Threshold status

- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Expected full rows: 59000
- First expansion unlocked: False
- Full source unlocked: False
- Rows needed first expansion: 5800
- Rows needed full source: 40800

## Data quality

- Missing columns: []
- empty_ticker: 0
- empty_company_name: 1193
- empty_exchange: 0
- empty_country: 0
- empty_source_provider: 0
- empty_instrument_type: 0
- empty_instrument_scope: 0
- empty_classification_confidence: 0
- empty_classification_reason: 0

## Outputs

- provider_validation_csv: `outputs/full_universe_source_acquisition/validate_expanded_source_with_cboe_provider_validation_v2_8f.csv`
- issues_csv: `outputs/full_universe_source_acquisition/validate_expanded_source_with_cboe_issues_v2_8f.csv`
- duplicates_csv: `outputs/full_universe_source_acquisition/validate_expanded_source_with_cboe_duplicates_v2_8f.csv`

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
- Validation only: true

## Positives

- v2.8E rebuild artifact found: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_real_v2_8e.json
- v2.8E rebuild status accepted: REBUILD_EXPANDED_SOURCE_WITH_CBOE_COMPLETED_USEFUL_BUT_NOT_ENOUGH
- Required validation input available: data/raw/expanded_universe/expanded_universe_v2_8e.csv
- Required validation input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv
- Required validation input available: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_provider_breakdown_v2_8e.csv
- Required validation input available: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_merge_audit_v2_8e.csv
- Required validation input available: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_exclusion_breakdown_v2_8e.csv
- Required canonical columns available.
- Expanded row count OK: 9200
- Exclusions row count OK: 10056
- Duplicate exchange+ticker keys: 0
- Provider count OK: nasdaq_trader_nasdaqlisted = 3244
- Provider count OK: nasdaq_trader_otherlisted = 2404
- Provider count OK: sec_company_tickers_exchange = 2359
- Provider count OK: cboe_listed_symbols = 1193
- Cboe row count OK: 1193
- Cboe candidate rows keep LOW confidence.
- Cboe candidate rows use expected pending-validation scope.
- Merge audit Cboe added rows OK: 1193

## Blockers

- No blockers detected.

## Warnings

- empty_company_name: 1193
- First expansion target remains blocked: 9200 < 15000
- Full-source threshold remains blocked: 9200 < 50000
- Cboe provider is useful but not enough to close source expansion.
- Full 59k dry-run remains blocked.

## Recommendation

Close Cboe rebuild as useful but not enough, then decide between closure report and next provider route.

Important: v2.8F is validation-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.