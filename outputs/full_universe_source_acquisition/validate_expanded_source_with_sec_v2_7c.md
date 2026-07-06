# Scout Finance ? v2.7C Validate Expanded Source With SEC

- Phase: v2.7C
- Method: validate_expanded_source_with_sec_v1
- Created at: 2026-07-06T14:34:03+00:00
- Validation status: **EXPANDED_SOURCE_WITH_SEC_VALIDATED_USEFUL_BUT_NOT_ENOUGH**
- Readiness score: **90/100**
- Recommended next phase: **v2.7D ? Expanded Source With SEC Closure Report**

## Row summary

- Expanded rows: 8007
- Expected expanded rows: 8007
- Exclusions rows: 10056
- Expected exclusions rows: 10056
- Duplicate exchange+ticker keys: 0
- Issues count: 0

## Provider counts

- nasdaq_trader_nasdaqlisted: 3244
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359

## Merge action counts

- PRESERVE_EXISTING: 5648
- ADD_SEC_PRIMARY_NET_NEW: 2359

## Exchange counts

- NASDAQ: 4336
- NYSE: 3362
- NYSE American: 265
- CBOE: 27
- NYSE Arca: 13
- Cboe BZX: 4

## Threshold status

- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- First expansion unlocked: False
- Full source unlocked: False
- Rows needed first expansion: 6993
- Rows needed full source: 41993

## Data quality

- Missing columns: []
- Empty ticker: 0
- Empty company_name: 0
- Empty exchange: 0
- Empty country: 0
- Empty source_provider: 0
- Empty instrument_type: 0
- Empty instrument_scope: 0
- Empty classification_confidence: 0
- Empty merge_action: 0
- Empty merge_reason: 0

## Outputs

- provider_validation_csv: `outputs/full_universe_source_acquisition/validate_expanded_source_with_sec_provider_validation_v2_7c.csv`
- issues_csv: `outputs/full_universe_source_acquisition/validate_expanded_source_with_sec_issues_v2_7c.csv`
- duplicates_csv: `outputs/full_universe_source_acquisition/validate_expanded_source_with_sec_duplicates_v2_7c.csv`

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

- v2.7B rebuild artifact found: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_real_v2_7b.json
- v2.7B rebuild status accepted: REBUILD_EXPANDED_SOURCE_WITH_SEC_COMPLETED_USEFUL_BUT_NOT_ENOUGH
- Required validation input available: data/raw/expanded_universe/expanded_universe_v2_7b.csv
- Required validation input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_7b.csv
- Required validation input available: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_provider_breakdown_v2_7b.csv
- Required validation input available: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_merge_audit_v2_7b.csv
- Required validation input available: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_exclusion_breakdown_v2_7b.csv
- Expanded universe canonical schema validated.
- Final expanded row count matches expected: 8007
- Final exclusions row count matches expected: 10056
- Duplicate exchange+ticker keys: 0
- Provider count OK: nasdaq_trader_nasdaqlisted = 3244
- Provider count OK: nasdaq_trader_otherlisted = 2404
- Provider count OK: sec_company_tickers_exchange = 2359
- SEC added rows match expected: 2359

## Blockers

- No blockers detected.

## Warnings

- First expansion target remains blocked: 8007 < 15000
- Full-source threshold remains blocked: 8007 < 50000

## Recommendation

Proceed to v2.7D closure. SEC rebuild is validated as useful but still not enough to unlock first expansion or full-source thresholds.

Important: v2.7C is validation-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.