# Scout Finance ? v2.7B Rebuild Expanded Source With SEC Real

- Phase: v2.7B
- Method: rebuild_expanded_source_with_sec_real_v1
- Created at: 2026-07-06T14:07:16+00:00
- Rebuild status: **REBUILD_EXPANDED_SOURCE_WITH_SEC_COMPLETED_USEFUL_BUT_NOT_ENOUGH**
- Readiness score: **90/100**
- Recommended next phase: **v2.7C ? Validate Expanded Source With SEC**

## Rebuild summary

- Current expanded input rows: 5648
- Current exclusions input rows: 7309
- SEC candidate input rows: 2359
- SEC enrichment input rows: 2747
- Final expanded rows: 8007
- Final exclusions rows: 10056
- SEC primary rows added: 2359
- SEC skipped existing overlap: 0
- SEC skipped internal duplicate: 0
- SEC skipped invalid key: 0
- Final duplicate exchange+ticker keys: 0

## Threshold status

- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- First expansion unlocked: False
- Full source unlocked: False
- Rows needed first expansion: 6993
- Rows needed full source: 41993

## Outputs

- expanded_universe_v2_7b_csv: `data/raw/expanded_universe/expanded_universe_v2_7b.csv`
- expanded_universe_exclusions_v2_7b_csv: `data/raw/expanded_universe/expanded_universe_exclusions_v2_7b.csv`
- provider_breakdown_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_provider_breakdown_v2_7b.csv`
- merge_audit_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_merge_audit_v2_7b.csv`
- exclusion_breakdown_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_exclusion_breakdown_v2_7b.csv`

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
- Versioned output only: true

## Positives

- v2.7A plan artifact found: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_plan_v2_7a.json
- v2.7A plan status accepted: REBUILD_EXPANDED_SOURCE_WITH_SEC_PLAN_READY
- Required input available: data/raw/expanded_universe/expanded_universe_v2_4b.csv
- Required input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_4b.csv
- Required input available: outputs/full_universe_source_acquisition/sec_incremental_rebuild_candidates_v2_6e.csv
- Required input available: outputs/full_universe_source_acquisition/sec_incremental_enrichment_rows_v2_6e.csv
- Existing rows preserved or normalized: 5648
- SEC primary net-new rows added: 2359
- SEC enrichment/exclusion rows preserved outside primary universe: 2747

## Blockers

- No blockers detected.

## Warnings

- v2.7B output does not unlock first expansion target: 8007 < 15000
- v2.7B output does not unlock full-source threshold: 8007 < 50000

## Recommendation

Proceed to v2.7C validation. SEC rebuild is useful but still does not unlock first expansion or full-source thresholds.

Important: v2.7B creates versioned source outputs only. It does not execute scoring, call OpenAI, call a broker, overwrite active MVP outputs, or launch full 59k.