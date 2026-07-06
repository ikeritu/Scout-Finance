# Scout Finance ? v2.6E SEC Incremental Coverage Analysis

- Phase: v2.6E
- Method: sec_incremental_coverage_analysis_v1
- Created at: 2026-07-06T12:17:33+00:00
- Analysis status: **SEC_INCREMENTAL_COVERAGE_USEFUL_BUT_NOT_ENOUGH**
- Readiness score: **90/100**
- Decision: **REBUILD_WITH_SEC_USEFUL_BUT_NOT_ENOUGH**
- Recommended next phase: **v2.7A ? Rebuild Expanded Source With SEC Plan**

## Coverage summary

- Current expanded rows: 5648
- SEC total rows: 10415
- SEC primary candidate keys: 7668
- SEC primary overlap keys: 5309
- SEC primary net new keys: 2359
- SEC enrichment/exclusion rows: 2747
- SEC unknown rows: 0
- SEC incremental gain vs current: 2359 rows (41.77%)

## Rebuild impact estimate

- Max possible rows after SEC rebuild: 8007
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Coverage after SEC vs first expansion target: 53.38%
- Coverage after SEC vs full-source threshold: 16.01%
- Rows still needed for first expansion after SEC: 6993
- Rows still needed for full source after SEC: 41993
- First expansion unlocked: False
- Full source unlocked: False

## SEC exchange counts

- NASDAQ: 4329
- NYSE: 3312
- OTC: 2558
- None: 189
- CBOE: 27

## Primary new exchange counts

- NYSE: 1240
- NASDAQ: 1092
- CBOE: 27

## Outputs

- Primary new rows CSV: `outputs/full_universe_source_acquisition/sec_incremental_primary_new_rows_v2_6e.csv`
- Primary overlap rows CSV: `outputs/full_universe_source_acquisition/sec_incremental_primary_overlap_rows_v2_6e.csv`
- Enrichment rows CSV: `outputs/full_universe_source_acquisition/sec_incremental_enrichment_rows_v2_6e.csv`
- Rebuild candidates CSV: `outputs/full_universe_source_acquisition/sec_incremental_rebuild_candidates_v2_6e.csv`
- Decision breakdown CSV: `outputs/full_universe_source_acquisition/sec_incremental_decision_breakdown_v2_6e.csv`

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

- v2.6D validation artifact found: outputs/full_universe_source_acquisition/sec_company_tickers_exchange_validation_v2_6d.json
- v2.6D validation status accepted: SEC_COMPANY_TICKERS_EXCHANGE_VALIDATED_WITH_PRIMARY_CANDIDATES
- v2.6D SEC route decision accepted: USABLE_AS_PARTIAL_PROVIDER_AND_IDENTIFIER_ENRICHMENT
- SEC CSV found: data/raw/source_providers/sec_company_tickers_exchange/sec_company_tickers_exchange.csv
- Expanded universe CSV found: data/raw/expanded_universe/expanded_universe_v2_4b.csv
- SEC adds net new primary exchange+ticker keys: 2359
- SEC can increase expanded universe from 5648 to 8007 rows before further providers.

## Blockers

- No blockers detected.

## Warnings

- SEC enrichment/exclusion rows should not be merged into primary universe: 2747
- SEC does not unlock first expansion target: 8007 < 15000
- SEC does not unlock full-source threshold: 8007 < 50000

## Recommendation

Proceed to v2.7A with a plan-only rebuild using SEC as partial provider and identifier enrichment. Do not run rebuild yet.

Important: v2.6E is an analysis-only step. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.