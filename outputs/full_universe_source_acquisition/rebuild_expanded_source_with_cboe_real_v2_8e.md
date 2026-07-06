# Scout Finance ? v2.8E Rebuild Expanded Source With Cboe Real

- Phase: v2.8E
- Method: rebuild_expanded_source_with_cboe_real_v1
- Created at: 2026-07-06T22:41:47+00:00
- Rebuild status: **REBUILD_EXPANDED_SOURCE_WITH_CBOE_COMPLETED_USEFUL_BUT_NOT_ENOUGH**
- Readiness score: **88/100**
- Recommended next phase: **v2.8F ? Validate Expanded Source With Cboe**

## Summary

- Base expanded rows: 8007
- Base exclusions rows: 10056
- Cboe candidate rows input: 1193
- Cboe rows added: 1193
- Cboe rows skipped overlap: 0
- Cboe rows skipped invalid: 0
- Final expanded rows: 9200
- Final exclusions rows: 10056
- Duplicate exchange+ticker keys: 0

## Threshold status

- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- First expansion unlocked: False
- Full source unlocked: False
- Rows needed first expansion: 5800
- Rows needed full source: 40800

## Provider counts

- nasdaq_trader_nasdaqlisted: 3244
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- cboe_listed_symbols: 1193

## Outputs

- expanded_universe_with_cboe_csv: `data/raw/expanded_universe/expanded_universe_v2_8e.csv`
- expanded_universe_exclusions_with_cboe_csv: `data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv`
- provider_breakdown_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_provider_breakdown_v2_8e.csv`
- merge_audit_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_merge_audit_v2_8e.csv`
- exclusion_breakdown_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_exclusion_breakdown_v2_8e.csv`

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: false
- Active outputs overwritten: false
- Expanded universe rebuilt: true
- Active MVP outputs overwritten: false
- Isolated rebuild only: true

## Positives

- v2.8D plan artifact found: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_plan_v2_8d.json
- v2.8D plan status accepted: REBUILD_EXPANDED_SOURCE_WITH_CBOE_PLAN_READY_WITH_CONDITIONS
- v2.8D plan decision accepted: CBOE_REBUILD_PLAN_APPROVED_WITH_CONDITIONS
- Required rebuild input available: data/raw/expanded_universe/expanded_universe_v2_7b.csv
- Required rebuild input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_7b.csv
- Required rebuild input available: outputs/full_universe_source_acquisition/cboe_listed_symbols_net_new_candidates_v2_8c.csv
- Base expanded rows OK: 8007
- Base exclusions rows OK: 10056
- Cboe net-new candidate rows OK: 1193
- Base expanded universe canonical columns available.
- Duplicate exchange+ticker keys after rebuild: 0
- Final expanded rows OK: 9200

## Blockers

- No blockers detected.

## Warnings

- Cboe rows are candidate-provider rows and require v2.8F validation before downstream use.
- First expansion remains blocked: 9200 < 15000
- Full-source threshold remains blocked: 9200 < 50000
- Full 59k dry-run remains blocked.

## Recommendation

Proceed to v2.8F validation before using Cboe-expanded universe downstream.

Important: v2.8E performs an isolated rebuild only. It does not execute scoring, call OpenAI, call a broker, overwrite active MVP outputs, or launch full 59k.