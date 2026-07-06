# Scout Finance ? v2.8D Rebuild Expanded Source With Cboe Plan

- Phase: v2.8D
- Method: rebuild_expanded_source_with_cboe_plan_v1
- Created at: 2026-07-06T22:27:20+00:00
- Plan status: **REBUILD_EXPANDED_SOURCE_WITH_CBOE_PLAN_READY_WITH_CONDITIONS**
- Readiness score: **90/100**
- Plan decision: **CBOE_REBUILD_PLAN_APPROVED_WITH_CONDITIONS**
- Recommended next phase: **v2.8E ? Rebuild Expanded Source With Cboe Real**

## Current state

- Current expanded rows: 8007
- Current exclusions rows: 10056
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Full 59k expected rows: 59000

## Cboe candidate summary

- Normalized candidate rows: 1220
- Net-new exchange+ticker rows: 1193
- Projected rows after Cboe: 9200
- Rows needed first expansion after Cboe: 5800
- Rows needed full source after Cboe: 40800
- First expansion unlocked after Cboe: False
- Full source unlocked after Cboe: False

## Decision

```text
CBOE_REBUILD_PLAN_APPROVED_WITH_CONDITIONS
CBOE_CANDIDATE_ROWS_ONLY
FULL_59K_REMAINS_BLOCKED
REBUILD_ALLOWED_ONLY_AS_ISOLATED_V2_8E
```

## Planned outputs for v2.8E

- expanded_universe_with_cboe_csv: `data/raw/expanded_universe/expanded_universe_v2_8e.csv`
- expanded_universe_exclusions_with_cboe_csv: `data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv`
- rebuild_json: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_real_v2_8e.json`
- rebuild_md: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_real_v2_8e.md`
- provider_breakdown_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_provider_breakdown_v2_8e.csv`
- merge_audit_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_merge_audit_v2_8e.csv`
- exclusion_breakdown_csv: `outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_exclusion_breakdown_v2_8e.csv`

## Planned rebuild rules for v2.8E

- Use expanded_universe_v2_7b.csv as immutable input.
- Use expanded_universe_exclusions_v2_7b.csv as immutable input.
- Use cboe_listed_symbols_net_new_candidates_v2_8c.csv as Cboe candidate input.
- Do not use cboe_listed_symbols_raw.csv as ticker source.
- Append only net-new exchange+ticker keys.
- Preserve existing rows exactly where keys already exist.
- Set source_provider to cboe_listed_symbols for appended rows.
- Keep classification confidence conservative because Cboe source semantics require validation.
- Do not overwrite active MVP outputs.
- Do not recalculate scoring.
- Do not call OpenAI.
- Do not call broker APIs.
- Do not launch full 59k universe.

## Planned validation for v2.8F

- Confirm final expanded rows equal 9200 if all 1193 net-new candidates are added.
- Confirm duplicate exchange+ticker keys remain 0.
- Confirm required canonical columns are present.
- Confirm provider breakdown includes Cboe candidate rows.
- Confirm first expansion remains blocked because 9200 < 15000.
- Confirm full source remains blocked because 9200 < 50000.
- Confirm no scoring/OpenAI/broker/full 59k was executed.

## Constraints

- listed_symbols_raw.csv usable as ticker source: false
- Cboe candidates are primary provider rows: false
- Cboe candidates are candidate-provider rows: true
- Rebuild allowed: true
- Active outputs overwrite allowed: false
- Full 59k unlocked after Cboe: false

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
- Plan only: true

## Positives

- v2.8C validation artifact found: outputs/full_universe_source_acquisition/cboe_listed_symbols_validation_v2_8c.json
- v2.8C validation status accepted: CBOE_VALIDATED_WITH_NET_NEW_CANDIDATES
- v2.8C Cboe decision accepted: CBOE_USABLE_AS_CANDIDATE_PROVIDER_PENDING_REBUILD_PLAN
- Required planning input available: outputs/full_universe_source_acquisition/cboe_listed_symbols_net_new_candidates_v2_8c.csv
- Required planning input available: outputs/full_universe_source_acquisition/cboe_listed_symbols_normalized_candidate_v2_8c.csv
- Required planning input available: outputs/full_universe_source_acquisition/cboe_listed_symbols_schema_detail_v2_8c.csv
- Required planning input available: data/raw/expanded_universe/expanded_universe_v2_7b.csv
- Required planning input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_7b.csv

## Blockers

- No blockers detected.

## Warnings

- Cboe listed_symbols_raw.csv is not usable as direct ticker source because no symbol/ticker field was detected.
- Cboe candidates came from symbols_traded/lot-size style data and must remain candidate-provider rows until post-rebuild validation.
- Projected rows after Cboe remain below 15000 and 50000 thresholds.
- Full 59k dry-run remains blocked after this provider even if rebuild succeeds.

## Recommendation

Proceed to v2.8E controlled rebuild with Cboe candidate rows, then validate in v2.8F before any downstream use.

Important: v2.8D is plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.