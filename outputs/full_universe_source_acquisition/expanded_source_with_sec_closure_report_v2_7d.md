# Scout Finance ? v2.7D Expanded Source With SEC Closure Report

- Phase: v2.7D
- Method: expanded_source_with_sec_closure_report_v1
- Created at: 2026-07-06T20:08:57+00:00
- Closure status: **EXPANDED_SOURCE_WITH_SEC_CLOSED_USEFUL_BUT_NOT_ENOUGH**
- Readiness score: **95/100**
- Closure decision: **SEC_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH**
- Recommended next phase: **v2.8A ? Cboe Listed Symbols Route Plan OR return to product/MVP**

## Closed block

- v2.7A ? Rebuild Expanded Source With SEC Plan
- v2.7B ? Rebuild Expanded Source With SEC Real
- v2.7C ? Validate Expanded Source With SEC
- v2.7D ? Expanded Source With SEC Closure Report

## Final result

- Expanded universe: `data/raw/expanded_universe/expanded_universe_v2_7b.csv`
- Exclusions: `data/raw/expanded_universe/expanded_universe_exclusions_v2_7b.csv`
- Final expanded rows: 8007
- Final exclusions rows: 10056
- SEC rows added: 2359
- Duplicate exchange+ticker keys: 0
- Issues count: 0

## Provider result

- nasdaq_trader_nasdaqlisted: 3244
- nasdaq_trader_otherlisted: 2404
- sec_company_tickers_exchange: 2359
- Total: 8007

## Threshold status

- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Expected full rows: 59000
- First expansion unlocked: False
- Full source unlocked: False
- Rows needed first expansion: 6993
- Rows needed full source: 41993

## Decision

SEC rebuild is closed as useful but not enough.

```text
SEC_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH
FULL_59K_REMAINS_BLOCKED
NEXT_DECISION_REQUIRED: CBOE_OR_RETURN_TO_PRODUCT
```

## Next options

### Option A ? Continue source expansion

- Next phase: `v2.8A ? Cboe Listed Symbols Route Plan`
- Use if 59k/full-source remains the priority.

### Option B ? Return to product/MVP

- Next phase: product/MVP roadmap refresh.
- Use if practical utility with the validated 8007-row universe is now the priority.

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
- Closure only: true

## Positives

- v2.7C validation artifact found: outputs/full_universe_source_acquisition/validate_expanded_source_with_sec_v2_7c.json
- v2.7B rebuild artifact found: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_real_v2_7b.json
- v2.7A plan artifact found: outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_plan_v2_7a.json
- v2.6E SEC incremental analysis artifact found: outputs/full_universe_source_acquisition/sec_incremental_coverage_analysis_v2_6e.json
- Required source output found: data/raw/expanded_universe/expanded_universe_v2_7b.csv
- Required source output found: data/raw/expanded_universe/expanded_universe_exclusions_v2_7b.csv
- v2.7C validation status accepted: EXPANDED_SOURCE_WITH_SEC_VALIDATED_USEFUL_BUT_NOT_ENOUGH
- v2.7B rebuild status accepted: REBUILD_EXPANDED_SOURCE_WITH_SEC_COMPLETED_USEFUL_BUT_NOT_ENOUGH
- v2.7A plan status accepted: REBUILD_EXPANDED_SOURCE_WITH_SEC_PLAN_READY
- v2.6E SEC decision accepted: REBUILD_WITH_SEC_USEFUL_BUT_NOT_ENOUGH

## Blockers

- No blockers detected.

## Warnings

- First expansion target remains blocked: 8007 < 15000
- Full-source threshold remains blocked: 8007 < 50000
- SEC rebuild is useful, but not enough to close source expansion.
- Next decision required: continue with Cboe/next provider or return to product/MVP with partial expanded universe.

## Recommendation

Close v2.7 with tag and decide whether to continue with v2.8A Cboe route or return to product/MVP with the validated 8007-row universe.

Important: v2.7D is closure-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.