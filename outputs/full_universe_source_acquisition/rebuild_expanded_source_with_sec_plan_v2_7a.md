# Scout Finance ? v2.7A Rebuild Expanded Source With SEC Plan

- Phase: v2.7A
- Method: rebuild_expanded_source_with_sec_plan_v1
- Created at: 2026-07-06T13:26:01+00:00
- Plan status: **REBUILD_EXPANDED_SOURCE_WITH_SEC_PLAN_READY**
- Readiness score: **95/100**
- Recommended next phase: **v2.7B ? Rebuild Expanded Source With SEC Real**

## Decision inherited from v2.6E

- Analysis status: **SEC_INCREMENTAL_COVERAGE_USEFUL_BUT_NOT_ENOUGH**
- Decision: **REBUILD_WITH_SEC_USEFUL_BUT_NOT_ENOUGH**
- SEC primary net new keys: 2359
- Planned max rows after SEC rebuild: 8007
- First expansion unlocked: false
- Full source unlocked: false

## Inputs

- current_expanded_csv: `data/raw/expanded_universe/expanded_universe_v2_4b.csv`
- current_exclusions_csv: `data/raw/expanded_universe/expanded_universe_exclusions_v2_4b.csv`
- sec_provider_csv: `data/raw/source_providers/sec_company_tickers_exchange/sec_company_tickers_exchange.csv`
- sec_rebuild_candidates_csv: `outputs/full_universe_source_acquisition/sec_incremental_rebuild_candidates_v2_6e.csv`
- sec_enrichment_csv: `outputs/full_universe_source_acquisition/sec_incremental_enrichment_rows_v2_6e.csv`
- sec_analysis_json: `outputs/full_universe_source_acquisition/sec_incremental_coverage_analysis_v2_6e.json`

## Planned outputs for v2.7B

- expanded_universe_v2_7b_csv: `data/raw/expanded_universe/expanded_universe_v2_7b.csv`
- expanded_universe_exclusions_v2_7b_csv: `data/raw/expanded_universe/expanded_universe_exclusions_v2_7b.csv`
- rebuild_report_json: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_real_v2_7b.json`
- rebuild_report_md: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_real_v2_7b.md`
- provider_breakdown_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_provider_breakdown_v2_7b.csv`
- merge_audit_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_merge_audit_v2_7b.csv`

## Provider precedence

### 1. existing_expanded_universe_v2_4b

- Role: base_validated_source
- Input: `data/raw/expanded_universe/expanded_universe_v2_4b.csv`
- Treatment: Preserve existing validated Nasdaq Trader derived rows unless duplicate policy explicitly replaces metadata.

### 2. sec_company_tickers_exchange_primary_net_new

- Role: partial_provider_and_identifier_enrichment
- Input: `outputs/full_universe_source_acquisition/sec_incremental_rebuild_candidates_v2_6e.csv`
- Treatment: Add only PRIMARY_NET_NEW rows with exchange in NASDAQ, NYSE, CBOE and key not already present as exchange+ticker.

### 3. sec_company_tickers_exchange_enrichment_or_exclusion

- Role: enrichment_exclusion_reference
- Input: `outputs/full_universe_source_acquisition/sec_incremental_enrichment_rows_v2_6e.csv`
- Treatment: Do not add to primary universe. Preserve in exclusions/reference output for future enrichment and provider diagnostics.

## Deduplication rules

- Primary deduplication key: exchange+ticker.
- Normalize ticker as uppercase trimmed string.
- Normalize exchange as trimmed string.
- Existing v2.4B rows win on duplicate exchange+ticker keys.
- SEC primary net-new rows are added only when exchange+ticker key is absent from v2.4B.
- SEC OTC/None/blank exchange rows are never added to primary expanded universe in v2.7B.
- SEC duplicate exchange+ticker count must remain zero, as validated in v2.6D.
- If a SEC row has unknown exchange, route it to exclusions/review, not primary universe.

## Classification rules

- Existing v2.4B classification fields are preserved.
- SEC rows keep instrument_type UNKNOWN_PENDING_CLASSIFICATION unless downstream classification is implemented.
- SEC rows keep instrument_scope UNKNOWN_PENDING_CLASSIFICATION unless downstream classification is implemented.
- SEC rows use classification_confidence LOW until a listing-specific provider confirms instrument class.
- SEC CIK is stored as raw_cik for identifier enrichment.
- SEC raw exchange is preserved as raw_exchange.

## Rebuild impact estimate

- Current expanded rows: 5648
- SEC primary net new keys: 2359
- SEC enrichment/exclusion rows: 2747
- Planned max rows after SEC rebuild: 8007
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Rows still needed for first expansion after SEC: 6993
- Rows still needed for full source after SEC: 41993

## Acceptance criteria for v2.7B

- No network download performed.
- No OpenAI call.
- No broker call.
- No scoring recalculation.
- No full 59k universe launch.
- No active MVP output overwrite.
- Create new versioned expanded_universe_v2_7b.csv only.
- Create new versioned expanded_universe_exclusions_v2_7b.csv only.
- Preserve v2.4B outputs unchanged.
- Final included rows should be approximately 8007 unless duplicate logic reveals a documented variance.
- OTC/None SEC rows must stay out of primary universe.
- Report provider breakdown and merge audit.

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

- v2.6E SEC incremental analysis artifact found: outputs/full_universe_source_acquisition/sec_incremental_coverage_analysis_v2_6e.json
- v2.6E analysis status accepted: SEC_INCREMENTAL_COVERAGE_USEFUL_BUT_NOT_ENOUGH
- v2.6E decision accepted: REBUILD_WITH_SEC_USEFUL_BUT_NOT_ENOUGH
- Required input available: data/raw/expanded_universe/expanded_universe_v2_4b.csv
- Required input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_4b.csv
- Required input available: data/raw/source_providers/sec_company_tickers_exchange/sec_company_tickers_exchange.csv
- Required input available: outputs/full_universe_source_acquisition/sec_incremental_rebuild_candidates_v2_6e.csv
- Required input available: outputs/full_universe_source_acquisition/sec_incremental_enrichment_rows_v2_6e.csv

## Blockers

- No blockers detected.

## Warnings

- SEC rebuild will not unlock first expansion target: 8007 < 15000
- SEC rebuild will not unlock full-source threshold: 8007 < 50000
- SEC OTC/None rows must remain exclusions/enrichment and must not be merged into primary expanded universe.

## Recommendation

Proceed to v2.7B to execute a controlled versioned rebuild with SEC. Do not overwrite v2.4B or active MVP outputs.

Important: v2.7A is a plan-only step. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.